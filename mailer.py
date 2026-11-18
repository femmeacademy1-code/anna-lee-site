"""Brevo: contacts, the lecture emails, and a note to Anna Lee for every new lead.

Settings come from the environment (the .env file next to this one):
  BREVO_API_KEY            the key from Brevo (Settings > SMTP & API > API Keys)
  BREVO_LIST_REGISTRANTS   list number for everyone who registers to the lecture
  BREVO_LIST_ID            list number for the newsletter (only with marketing consent)
  BREVO_SENDER_EMAIL       the "from" address (must be a verified sender in Brevo)
  BREVO_SENDER_NAME        the "from" name
  NOTIFY_EMAIL             where Anna Lee gets a note about every new lead

Without BREVO_API_KEY nothing is sent: every email is written to data/outbox/ instead,
so the texts can be checked in a browser.

Reminders are not scheduled in Brevo. They wait in the email_jobs table and a small
loop in the server sends them when they are due, so they always carry the current
Zoom link from config.json, even for women who registered before it existed.
"""
import html
import json
import os
import pathlib
import re
import sqlite3
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone

import emails

ROOT = pathlib.Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "site.db"
OUTBOX = DATA_DIR / "outbox"
ISRAEL = timezone(timedelta(hours=2))  # winter time; the lecture is in November
LATE_GRACE = timedelta(minutes=50)  # a reminder that is later than this is skipped, not sent late


def load_env(path=ROOT / ".env"):
    """KEY=value lines; values already in the environment win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def env(k, default=""):
    return os.environ.get(k, default).strip()


def cfg():
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def log(msg):
    print(f"[brevo] {msg}", flush=True)


# ---------- Brevo API ----------

def _api(method, path, payload):
    key = env("BREVO_API_KEY")
    req = urllib.request.Request("https://api.brevo.com/v3" + path, method=method,
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"api-key": key, "Content-Type": "application/json",
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status


def add_contact(email, name, list_ids):
    list_ids = [int(x) for x in list_ids if str(x).isdigit()]
    if not env("BREVO_API_KEY") or not list_ids:
        return
    try:
        _api("POST", "/contacts", {"email": email, "attributes": {"FIRSTNAME": name},
                                   "listIds": list_ids, "updateEnabled": True})
    except Exception as e:  # the lead is already saved; never lose it over this
        log(f"could not add contact to lists {list_ids}: {e}")


def _wrap(body, footer=True):
    foot = f'<p class="foot">{html.escape(emails.FOOTER)}</p>' if footer else ""
    return f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<style>
body{{margin:0;background:#FBF6EF;font-family:Arial,Helvetica,sans-serif;color:#4C392F}}
.card{{max-width:560px;margin:0 auto;padding:36px 28px;background:#FBF6EF;font-size:17px;line-height:1.7;text-align:right}}
.card strong{{color:#3A2620}}
.btn{{display:inline-block;background:#94455A;color:#FFF8F3 !important;text-decoration:none;border-radius:999px;padding:12px 28px;font-weight:bold}}
.foot{{font-size:13px;color:#6E5648;border-top:1px solid #EAD9CF;padding-top:16px;margin-top:28px}}
</style></head><body><div class="card">{body}{foot}</div></body></html>"""


def send(to_email, to_name, subject, body, footer=True, tag=""):
    """Sends one email through Brevo, or writes it to data/outbox/ when there is no key."""
    page = _wrap(body, footer)
    if not env("BREVO_API_KEY"):
        OUTBOX.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", f"{tag}-{to_email}".lower()).strip("-")
        f = OUTBOX / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slug}.html"
        f.write_text(f"<!-- to: {to_name} <{to_email}> | subject: {subject} -->\n" + page, encoding="utf-8")
        log(f"no API key, wrote {f.name}")
        return True
    sender = {"email": env("BREVO_SENDER_EMAIL") or cfg().get("email", ""),
              "name": env("BREVO_SENDER_NAME") or cfg().get("site_name", "")}
    try:
        _api("POST", "/smtp/email", {"sender": sender, "to": [{"email": to_email, "name": to_name or to_email}],
                                     "subject": subject, "htmlContent": page, "tags": [tag] if tag else []})
        return True
    except Exception as e:
        log(f"could not send '{tag}' to {to_email}: {e}")
        return False


# ---------- the lecture ----------

def lecture():
    c = cfg().get("lecture", {})
    start = datetime.strptime(f'{c["date"]} {c["time"]}', "%Y-%m-%d %H:%M").replace(tzinfo=ISRAEL)
    return c, start


def is_lecture(item):
    return "על קוצים" in (item or "")


def _fill(tpl, name, extra=None):
    c, start = lecture()
    site = cfg().get("domain", "").rstrip("/")
    zoom = c.get("zoom_link", "").strip()
    days = ["יום שני", "יום שלישי", "יום רביעי", "יום חמישי", "יום שישי", "שבת", "יום ראשון"]
    v = {"name": html.escape(name.split()[0] if name else ""), "title": html.escape(emails.LECTURE_TITLE),
         "when": f"{days[start.weekday()]}, {start.strftime('%d.%m')}", "time": start.strftime("%H:%M"),
         "zoom": html.escape(zoom), "kit": site + "/static/files/first-aid-kit.pdf", "site": site}
    v["zoom_block"] = emails.ZOOM_BLOCK.format(**v) if zoom else emails.ZOOM_LATER
    offer = c.get("workshop_offer", "").strip()
    v["offer_block"] = f"<p>{offer}</p>" if offer else ""
    v.update(extra or {})
    return tpl["subject"].format(**v), tpl["body"].format(**v)


def init_jobs():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS email_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER, email TEXT NOT NULL, name TEXT,
            kind TEXT NOT NULL, due_at TEXT NOT NULL, sent_at TEXT, status TEXT NOT NULL DEFAULT 'waiting',
            UNIQUE(email, kind))""")


def on_lead(lead_id, name, email, phone, item, message, marketing):
    """Called (in a thread) after a lead is saved."""
    try:
        c = cfg()
        topic = item or "פנייה כללית"
        # 1. Anna Lee hears about it
        notify = env("NOTIFY_EMAIL")
        if notify:
            msg = f"<p><strong>הודעה:</strong><br>{html.escape(message)}</p>" if message else ""
            s, b = _fill(emails.NOTIFY, name, {
                "name": html.escape(name), "topic": html.escape(topic), "email": html.escape(email or "-"),
                "phone": html.escape(phone or "-"), "consent": "כן" if marketing else "לא", "message_block": msg})
            send(notify, c.get("site_name", ""), s, b, footer=False, tag="notify")
        if not email:
            return
        # 2. the lists
        lists = []
        if is_lecture(item):
            lists.append(env("BREVO_LIST_REGISTRANTS"))
        if marketing:
            lists.append(env("BREVO_LIST_ID"))
        add_contact(email, name, lists)
        # 3. the lecture emails
        if is_lecture(item):
            s, b = _fill(emails.CONFIRM, name)
            send(email, name, s, b, tag="confirm")
            _, start = lecture()
            jobs = [("reminder_day", start - timedelta(days=1)), ("reminder_hour", start - timedelta(hours=1)),
                    ("after", start + timedelta(minutes=45))]
            now = datetime.now(ISRAEL)
            with sqlite3.connect(DB_PATH) as conn:
                for kind, due in jobs:
                    if due > now:
                        conn.execute("INSERT OR IGNORE INTO email_jobs (lead_id, email, name, kind, due_at) VALUES (?,?,?,?,?)",
                                     (lead_id, email, name, kind, due.isoformat()))
    except Exception as e:
        log(f"lead follow-up failed: {e}")


TEMPLATES = {"reminder_day": emails.REMINDER_DAY, "reminder_hour": emails.REMINDER_HOUR, "after": emails.AFTER}


def run_due_jobs(now=None):
    now = now or datetime.now(ISRAEL)
    c, _ = lecture()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM email_jobs WHERE status='waiting' AND due_at <= ?", (now.isoformat(),)).fetchall()
        for r in rows:
            due = datetime.fromisoformat(r["due_at"])
            if r["kind"] == "after" and not c.get("after_email_ready"):
                continue  # waits until the text and the offer are approved
            if r["kind"] != "after" and now - due > LATE_GRACE:
                conn.execute("UPDATE email_jobs SET status='skipped' WHERE id=?", (r["id"],))
                continue
            s, b = _fill(TEMPLATES[r["kind"]], r["name"] or "")
            ok = send(r["email"], r["name"], s, b, tag=r["kind"])
            conn.execute("UPDATE email_jobs SET status=?, sent_at=? WHERE id=?",
                         ("sent" if ok else "failed", now.isoformat(), r["id"]))


def start_scheduler(every=60):
    init_jobs()

    def loop():
        while True:
            try:
                run_due_jobs()
            except Exception as e:
                log(f"scheduler: {e}")
            time.sleep(every)
    threading.Thread(target=loop, daemon=True).start()
