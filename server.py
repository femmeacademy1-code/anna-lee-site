#!/usr/bin/env python3
"""Serves the generated site, the public API, and the admin area.

Standard library only. Requires the ADMIN_PASSWORD environment variable.
Optional: ADMIN_USER (default "admin"), PORT (default 8000), HOST (default 127.0.0.1).

  export ADMIN_PASSWORD='choose-a-long-password'
  python3 build.py
  python3 server.py
"""
import base64
import csv
import hmac
import html
import io
import json
import os
import threading
import urllib.request
import os
import pathlib
import re
import sqlite3
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "site"
STATIC = ROOT / "static"
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "site.db"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

import mailer  # noqa: E402  (Brevo; also loads the .env file)
mailer.load_env()

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))

SERVICES = {"therapy", "breathwork", "workshop", "lecture", "free", "general"}
LEAD_STATUSES = ["חדש", "נוצר קשר", "שיחת היכרות נקבעה", "נסגר", "לא רלוונטי"]
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CATEGORIES = []  # free text, but the admin suggests existing ones

RATE = {}  # ip -> list of timestamps, simple in-memory limit for lead submissions
RATE_WINDOW = 3600
RATE_MAX = 15


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def db():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS leads (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              name TEXT NOT NULL,
              phone TEXT,
              email TEXT,
              service TEXT NOT NULL,
              item TEXT,
              message TEXT,
              marketing_consent INTEGER NOT NULL DEFAULT 0,
              consent_at TEXT,
              source TEXT,
              status TEXT NOT NULL DEFAULT 'חדש',
              notes TEXT
            );
            CREATE TABLE IF NOT EXISTS articles (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              slug TEXT NOT NULL UNIQUE,
              title TEXT NOT NULL,
              category TEXT,
              excerpt TEXT,
              body TEXT NOT NULL DEFAULT '',
              sources TEXT,
              author TEXT NOT NULL DEFAULT 'אנה לי מילשטיין',
              seo_title TEXT,
              meta_description TEXT,
              image_url TEXT,
              image_alt TEXT,
              featured INTEGER NOT NULL DEFAULT 0,
              published INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at);
            CREATE INDEX IF NOT EXISTS idx_articles_pub ON articles(published, updated_at);
            """
        )


# ---------- helpers ----------

def clean(value, limit):
    return (str(value or "")).strip()[:limit]


def article_blocks(body):
    """Body text: a line starting with '## ' is a subheading, other non-empty lines are paragraphs."""
    blocks = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## "):
            blocks.append({"type": "h2", "text": line[3:].strip()})
        else:
            blocks.append({"type": "p", "text": line})
    return blocks


def article_out(row, with_body=True):
    out = {
        "id": row["id"],
        "slug": row["slug"],
        "title": row["title"],
        "category": row["category"] or "",
        "excerpt": row["excerpt"] or "",
        "author": row["author"],
        "seo_title": row["seo_title"] or row["title"],
        "meta_description": row["meta_description"] or row["excerpt"] or "",
        "image_url": row["image_url"] or "",
        "image_alt": row["image_alt"] or "",
        "featured": bool(row["featured"]),
        "updated_date": (row["updated_at"] or "")[:10],
    }
    if with_body:
        out["blocks"] = article_blocks(row["body"] or "")
        out["sources"] = [s.strip() for s in (row["sources"] or "").splitlines() if s.strip()]
        out["related"] = related_articles(row["id"], row["category"])
    return out


def related_articles(article_id, category):
    if not category:
        return []
    with db() as conn:
        rows = conn.execute(
            "SELECT slug, title FROM articles WHERE published=1 AND category=? AND id<>? ORDER BY updated_at DESC LIMIT 3",
            (category, article_id),
        ).fetchall()
    return [{"slug": r["slug"], "title": r["title"]} for r in rows]


def rate_ok(ip):
    t = time.time()
    hits = [x for x in RATE.get(ip, []) if t - x < RATE_WINDOW]
    if len(hits) >= RATE_MAX:
        RATE[ip] = hits
        return False
    hits.append(t)
    RATE[ip] = hits
    return True


def admin_ok(header):
    if not ADMIN_PASSWORD or not header or not header.startswith("Basic "):
        return False
    try:
        raw = base64.b64decode(header[6:]).decode("utf-8")
    except Exception:
        return False
    user, _, pwd = raw.partition(":")
    return hmac.compare_digest(user, ADMIN_USER) and hmac.compare_digest(pwd, ADMIN_PASSWORD)


def esc(v):
    return html.escape(str(v if v is not None else ""), quote=True)


def admin_shell(title, body):
    return f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow">
<title>{esc(title)} | ניהול</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#FDF9F6;color:#3A2E2A;line-height:1.6}}
header{{background:#3A2E2A;color:#fff;padding:.8rem 1rem;display:flex;gap:1rem;flex-wrap:wrap;align-items:center}}
header a{{color:#F9EAE1}} main{{padding:1rem;max-width:1100px;margin:auto}}
table{{width:100%;border-collapse:collapse;background:#fff;font-size:.92rem}}
th,td{{border-bottom:1px solid #e7d6cc;padding:.45rem;text-align:start;vertical-align:top}}
input,select,textarea,button{{font:inherit;padding:.45rem;border:1px solid #cdb9ab;border-radius:6px;max-width:100%}}
button,.btn{{background:#DA627D;border:0;color:#2b1d1a;font-weight:bold;cursor:pointer;text-decoration:none;padding:.5rem .9rem;border-radius:999px;display:inline-block}}
.field{{display:grid;gap:.25rem;margin-bottom:.8rem}} .row{{display:flex;gap:.6rem;flex-wrap:wrap;align-items:center}}
.muted{{color:#6b5b54;font-size:.9rem}} .msg{{background:#e8f3e8;padding:.5rem;border-radius:6px}}
</style></head><body>
<header><strong>ניהול האתר</strong>
<a href="/admin">לידים</a><a href="/admin/articles">מאמרים</a><a href="/admin/articles/new">מאמר חדש</a><a href="/" target="_blank">לאתר</a></header>
<main>{body}</main></body></html>"""


# ---------- request handler ----------


class Handler(BaseHTTPRequestHandler):
    server_version = "AnnaSite/1.0"

    def log_message(self, fmt, *args):
        return  # keep the console quiet; leads are never logged

    # low-level responses
    def send_body(self, status, content_type, data, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "DENY")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def send_json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_body(status, "application/json; charset=utf-8", data, {"Cache-Control": "no-store"})

    def send_html(self, status, text, extra=None):
        self.send_body(status, "text/html; charset=utf-8", text.encode("utf-8"), extra)

    def redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def read_body(self, limit=64 * 1024):
        length = int(self.headers.get("Content-Length") or 0)
        if length > limit:
            return None
        return self.rfile.read(length) if length else b""

    def require_admin(self):
        if not ADMIN_PASSWORD:
            self.send_html(503, "<p>לא הוגדר ADMIN_PASSWORD בשרת.</p>")
            return False
        if admin_ok(self.headers.get("Authorization")):
            return True
        self.send_body(401, "text/plain; charset=utf-8", "נדרשת התחברות".encode("utf-8"),
                       {"WWW-Authenticate": 'Basic realm="admin"'})
        return False

    # routing
    def do_GET(self):
        self.route("GET")

    def do_HEAD(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def route(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            return self.api(method, path, parsed.query)
        if path == "/admin" or path.startswith("/admin/"):
            if not self.require_admin():
                return
            return self.admin(method, path, parsed.query)
        if method == "POST":
            return self.send_json(405, {"error": "לא נתמך"})
        return self.public(path)

    # public site
    def public(self, path):
        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            target = (STATIC / rel).resolve()
            if STATIC.resolve() not in target.parents or not target.is_file():
                return self.send_html(404, self.not_found_html(), {})
            ctype = {
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".webp": "image/webp", ".svg": "image/svg+xml",
                ".woff2": "font/woff2", ".ttf": "font/ttf", ".pdf": "application/pdf",
            }.get(target.suffix.lower(), "application/octet-stream")
            return self.send_body(200, ctype, target.read_bytes(), {"Cache-Control": "public, max-age=3600"})

        if path == "/robots.txt" or path == "/sitemap.xml":
            f = SITE / path.lstrip("/")
            if f.exists():
                ctype = "text/plain; charset=utf-8" if path.endswith(".txt") else "application/xml; charset=utf-8"
                return self.send_body(200, ctype, f.read_bytes())

        if path.startswith("/articles/"):
            slug = path[len("/articles/"):].strip("/")
            if slug and SLUG_RE.match(slug):
                with db() as conn:
                    row = conn.execute("SELECT id FROM articles WHERE slug=? AND published=1", (slug,)).fetchone()
                if row:
                    return self.send_html(200, (SITE / "article.html").read_text(encoding="utf-8"))
            return self.send_html(404, self.not_found_html())

        clean_path = path.rstrip("/") or "/"
        if clean_path == "/":
            target = SITE / "index.html"
        else:
            target = (SITE / (clean_path.lstrip("/") + ".html")).resolve()
            if SITE.resolve() not in target.parents:
                return self.send_html(404, self.not_found_html())
        if target.is_file():
            return self.send_html(200, target.read_text(encoding="utf-8"))
        return self.send_html(404, self.not_found_html())

    def not_found_html(self):
        f = SITE / "404.html"
        if f.exists():
            return f.read_text(encoding="utf-8")
        return "<!doctype html><meta charset='utf-8'><p>העמוד לא נמצא</p>"

    # public API
    def api(self, method, path, query):
        q = parse_qs(query)
        if path == "/api/articles" and method == "GET":
            limit = min(int(q.get("limit", ["50"])[0] or 50), 50)
            sql = "SELECT * FROM articles WHERE published=1"
            args = []
            if q.get("featured", [""])[0] == "1":
                sql += " AND featured=1"
            if q.get("category", [""])[0]:
                sql += " AND category=?"
                args.append(q["category"][0])
            sql += " ORDER BY featured DESC, updated_at DESC LIMIT ?"
            args.append(limit)
            with db() as conn:
                rows = conn.execute(sql, args).fetchall()
            items = [article_out(r, with_body=False) for r in rows]
            return self.send_json(200, {"articles": items})

        if path.startswith("/api/articles/") and method == "GET":
            slug = path[len("/api/articles/"):]
            if not SLUG_RE.match(slug):
                return self.send_json(404, {"error": "המאמר לא נמצא"})
            with db() as conn:
                row = conn.execute("SELECT * FROM articles WHERE slug=? AND published=1", (slug,)).fetchone()
            if not row:
                return self.send_json(404, {"error": "המאמר לא נמצא"})
            return self.send_json(200, article_out(row))

        if path == "/api/leads" and method == "POST":
            return self.create_lead()

        return self.send_json(404, {"error": "לא נמצא"})

    def create_lead(self):
        ip = self.client_address[0]
        if not rate_ok(ip):
            return self.send_json(429, {"error": "שלחת כמה פניות בזמן קצר. נסי שוב מאוחר יותר."})
        raw = self.read_body()
        if raw is None:
            return self.send_json(413, {"error": "הבקשה גדולה מדי."})
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return self.send_json(400, {"error": "הבקשה אינה תקינה."})

        # honeypot: bots fill the hidden field; pretend success and store nothing
        if clean(data.get("website"), 200):
            return self.send_json(200, {"message": "התקבל. נחזור אלייך בתוך 48 שעות."})

        name = clean(data.get("name"), 100)
        phone = clean(data.get("phone"), 30)
        email = clean(data.get("email"), 120)
        service = clean(data.get("service"), 30) or "general"
        item = clean(data.get("item"), 200)
        message = clean(data.get("message"), 2000)
        marketing = bool(data.get("marketing_consent"))
        source = clean(data.get("source"), 200)

        if len(name) < 2:
            return self.send_json(400, {"error": "נא להזין שם."})
        if not phone and not email:
            return self.send_json(400, {"error": "נא להזין טלפון או מייל."})
        if phone and not PHONE_RE.match(phone):
            return self.send_json(400, {"error": "מספר הטלפון אינו נראה תקין."})
        if email and not EMAIL_RE.match(email):
            return self.send_json(400, {"error": "כתובת המייל אינה נראית תקינה."})
        if service not in SERVICES:
            return self.send_json(400, {"error": "סוג השירות אינו תקין."})

        ts = now_iso()
        with db() as conn:
            cur = conn.execute(
                """INSERT INTO leads (created_at, name, phone, email, service, item, message,
                   marketing_consent, consent_at, source, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (ts, name, phone, email, service, item, message,
                 1 if marketing else 0, ts if marketing else None, source, "חדש"),
            )
            lead_id = cur.lastrowid
        # Brevo: lists, lecture emails, a note to Anna Lee. In a thread, so the visitor never waits.
        threading.Thread(target=mailer.on_lead, args=(lead_id, name, email, phone, item, message, marketing),
                         daemon=True).start()
        return self.send_json(200, {"message": "התקבל. נחזור אלייך בתוך 48 שעות."})

    # admin
    def admin(self, method, path, query):
        init_db()
        if path == "/admin" and method == "GET":
            return self.admin_leads(query)
        if path == "/admin/leads.csv" and method == "GET":
            return self.admin_leads_csv(query)
        if path.startswith("/admin/leads/") and path.endswith("/status") and method == "POST":
            lead_id = path.split("/")[3]
            form = parse_qs(self.read_body().decode("utf-8"))
            status = form.get("status", [""])[0]
            notes = clean(form.get("notes", [""])[0], 2000)
            if status not in LEAD_STATUSES or not lead_id.isdigit():
                return self.send_html(400, admin_shell("שגיאה", "<p>נתונים לא תקינים.</p>"))
            with db() as conn:
                conn.execute("UPDATE leads SET status=?, notes=? WHERE id=?", (status, notes, int(lead_id)))
            return self.redirect("/admin")
        if path == "/admin/articles" and method == "GET":
            return self.admin_articles()
        if path == "/admin/articles/new":
            if method == "GET":
                return self.admin_article_form(None)
            return self.admin_article_save(None)
        m = re.match(r"^/admin/articles/(\d+)/(edit|delete)$", path)
        if m:
            aid, action = int(m.group(1)), m.group(2)
            if action == "edit" and method == "GET":
                return self.admin_article_form(aid)
            if action == "edit" and method == "POST":
                return self.admin_article_save(aid)
            if action == "delete" and method == "POST":
                with db() as conn:
                    conn.execute("DELETE FROM articles WHERE id=?", (aid,))
                return self.redirect("/admin/articles")
        return self.send_html(404, admin_shell("לא נמצא", "<p>העמוד לא נמצא.</p>"))

    def admin_leads(self, query):
        q = parse_qs(query)
        status = q.get("status", [""])[0]
        sql = "SELECT * FROM leads"
        args = []
        if status in LEAD_STATUSES:
            sql += " WHERE status=?"
            args.append(status)
        sql += " ORDER BY created_at DESC LIMIT 500"
        with db() as conn:
            rows = conn.execute(sql, args).fetchall()
            counts = conn.execute("SELECT status, COUNT(*) c FROM leads GROUP BY status").fetchall()
        count_text = " · ".join(f"{esc(r['status'])}: {r['c']}" for r in counts) or "אין פניות עדיין"
        options = "".join(f'<option value="{esc(s)}"{" selected" if s == status else ""}>{esc(s)}</option>' for s in [""] + LEAD_STATUSES)
        trs = []
        for r in rows:
            status_opts = "".join(f'<option{" selected" if s == r["status"] else ""}>{esc(s)}</option>' for s in LEAD_STATUSES)
            consent = "כן" if r["marketing_consent"] else "לא"
            trs.append(f"""<tr>
<td>{esc(r['created_at'][:16].replace('T', ' '))}</td>
<td><strong>{esc(r['name'])}</strong><br><span class="muted">{esc(r['phone'])}<br>{esc(r['email'])}</span></td>
<td>{esc(r['service'])}<br><span class="muted">{esc(r['item'])}</span></td>
<td>{esc(r['message'])}</td>
<td>תוכן שיווקי: {consent}<br><span class="muted">{esc(r['source'])}</span></td>
<td><form method="post" action="/admin/leads/{r['id']}/status">
  <select name="status">{status_opts}</select>
  <textarea name="notes" rows="2" placeholder="הערה פנימית">{esc(r['notes'])}</textarea>
  <button type="submit">שמירה</button>
</form></td></tr>""")
        body = f"""<h1>פניות ולידים</h1>
<p class="muted">{count_text}</p>
<div class="row">
  <form method="get" action="/admin"><select name="status" onchange="this.form.submit()">{options}</select>
  <noscript><button>סינון</button></noscript></form>
  <a class="btn" href="/admin/leads.csv{('?status=' + esc(status)) if status else ''}">ייצוא לאקסל (CSV)</a>
</div>
<p class="muted">הפרטים כאן פנימיים בלבד. אל תשתפי אותם מחוץ למערכת.</p>
<table><thead><tr><th>תאריך</th><th>פרטים</th><th>שירות</th><th>הודעה</th><th>הסכמה ומקור</th><th>טיפול</th></tr></thead>
<tbody>{''.join(trs) or '<tr><td colspan="6">אין פניות להצגה.</td></tr>'}</tbody></table>"""
        return self.send_html(200, admin_shell("פניות", body))

    def admin_leads_csv(self, query):
        status = parse_qs(query).get("status", [""])[0]
        sql = "SELECT created_at, name, phone, email, service, item, message, marketing_consent, consent_at, source, status, notes FROM leads"
        args = []
        if status in LEAD_STATUSES:
            sql += " WHERE status=?"
            args.append(status)
        sql += " ORDER BY created_at DESC"
        with db() as conn:
            rows = conn.execute(sql, args).fetchall()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["תאריך", "שם", "טלפון", "מייל", "שירות", "כלי או מוצר", "הודעה", "הסכמה לתוכן שיווקי", "מועד ההסכמה", "מקור", "סטטוס", "הערות"])
        for r in rows:
            writer.writerow([r["created_at"], r["name"], r["phone"], r["email"], r["service"], r["item"],
                             r["message"], "כן" if r["marketing_consent"] else "לא", r["consent_at"] or "",
                             r["source"], r["status"], r["notes"] or ""])
        # UTF-8 with BOM so Hebrew opens correctly in Excel
        data = ("﻿" + buf.getvalue()).encode("utf-8")
        fname = f"leads-{datetime.now().strftime('%Y%m%d-%H%M')}.csv"
        return self.send_body(200, "text/csv; charset=utf-8", data,
                              {"Content-Disposition": f'attachment; filename="{fname}"'})

    def admin_articles(self):
        with db() as conn:
            rows = conn.execute("SELECT id, slug, title, category, published, featured, updated_at FROM articles ORDER BY updated_at DESC").fetchall()
        trs = "".join(
            f"""<tr><td>{esc(r['title'])}<br><span class="muted">/articles/{esc(r['slug'])}</span></td>
<td>{esc(r['category'])}</td><td>{'מפורסם' if r['published'] else 'טיוטה'}{' · מומלץ' if r['featured'] else ''}</td>
<td>{esc(r['updated_at'][:10])}</td>
<td><a href="/admin/articles/{r['id']}/edit">עריכה</a>
<form method="post" action="/admin/articles/{r['id']}/delete" onsubmit="return confirm('למחוק את המאמר?')"><button>מחיקה</button></form></td></tr>"""
            for r in rows
        )
        body = f"""<h1>מאמרים</h1><p><a class="btn" href="/admin/articles/new">מאמר חדש</a></p>
<table><thead><tr><th>כותרת</th><th>קטגוריה</th><th>מצב</th><th>עודכן</th><th></th></tr></thead>
<tbody>{trs or '<tr><td colspan="5">אין מאמרים עדיין.</td></tr>'}</tbody></table>"""
        return self.send_html(200, admin_shell("מאמרים", body))

    def admin_article_form(self, aid):
        row = None
        if aid is not None:
            with db() as conn:
                row = conn.execute("SELECT * FROM articles WHERE id=?", (aid,)).fetchone()
            if not row:
                return self.send_html(404, admin_shell("לא נמצא", "<p>המאמר לא נמצא.</p>"))
        v = lambda k: esc(row[k]) if row is not None and row[k] is not None else ""
        checked = lambda k: " checked" if row is not None and row[k] else ""
        action = f"/admin/articles/{aid}/edit" if aid is not None else "/admin/articles/new"
        body = f"""<h1>{'עריכת מאמר' if aid else 'מאמר חדש'}</h1>
<form method="post" action="{action}">
<div class="field"><label>כותרת (H1)<input name="title" required value="{v('title')}"></label></div>
<div class="field"><label>כתובת (slug), באנגלית ובמקפים בלבד, למשל: anxiety-and-thoughts<input name="slug" required pattern="[a-z0-9]+(-[a-z0-9]+)*" value="{v('slug')}"></label></div>
<div class="field"><label>קטגוריה<input name="category" value="{v('category')}" placeholder="חרדה, ויסות רגשי, טראומה..."></label></div>
<div class="field"><label>תקציר (מוצג בכרטיסייה)<textarea name="excerpt" rows="2">{v('excerpt')}</textarea></label></div>
<div class="field"><label>תוכן. שורה שמתחילה ב-## היא כותרת משנה. כל שורה אחרת היא פסקה.<textarea name="body" rows="18" required>{v('body')}</textarea></label></div>
<div class="field"><label>מקורות ומחקרים (שורה לכל מקור). מלאי רק מקורות שאימתת.<textarea name="sources" rows="3">{v('sources')}</textarea></label></div>
<div class="field"><label>כותרת SEO<input name="seo_title" maxlength="70" value="{v('seo_title')}"></label></div>
<div class="field"><label>תיאור מטא<textarea name="meta_description" maxlength="180" rows="2">{v('meta_description')}</textarea></label></div>
<div class="field"><label>תמונה ראשית (כתובת קובץ מתיקיית static, למשל /static/img/article1.jpg)<input name="image_url" value="{v('image_url')}"></label></div>
<div class="field"><label>טקסט חלופי לתמונה<input name="image_alt" value="{v('image_alt')}"></label></div>
<div class="row">
<label><input type="checkbox" name="published"{checked('published')}> מפורסם באתר</label>
<label><input type="checkbox" name="featured"{checked('featured')}> מומלץ בעמוד הבית</label>
</div>
<p class="muted">תאריך העדכון יישמר אוטומטית. השם המוצג הוא אנה לי מילשטיין.</p>
<button type="submit">שמירה</button>
</form>"""
        return self.send_html(200, admin_shell("עריכת מאמר", body))

    def admin_article_save(self, aid):
        raw = self.read_body(limit=512 * 1024)
        if raw is None:
            return self.send_html(413, admin_shell("שגיאה", "<p>המאמר גדול מדי.</p>"))
        f = parse_qs(raw.decode("utf-8"))
        g = lambda k: clean(f.get(k, [""])[0], 20000)
        title = g("title")[:200]
        slug = g("slug")[:120]
        if not title or not SLUG_RE.match(slug):
            return self.send_html(400, admin_shell("שגיאה", "<p>כותרת וכתובת תקינה הם שדות חובה.</p>"))
        ts = now_iso()
        published = 1 if "published" in f else 0
        featured = 1 if "featured" in f else 0
        values = (title, slug, g("category")[:80], g("excerpt")[:500], g("body"), g("sources"),
                  g("seo_title")[:70], g("meta_description")[:180], g("image_url")[:300], g("image_alt")[:200],
                  featured, published, ts)
        try:
            with db() as conn:
                if aid is None:
                    conn.execute(
                        """INSERT INTO articles (title, slug, category, excerpt, body, sources, seo_title,
                           meta_description, image_url, image_alt, featured, published, updated_at, created_at)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        values + (ts,),
                    )
                else:
                    conn.execute(
                        """UPDATE articles SET title=?, slug=?, category=?, excerpt=?, body=?, sources=?, seo_title=?,
                           meta_description=?, image_url=?, image_alt=?, featured=?, published=?, updated_at=? WHERE id=?""",
                        values + (aid,),
                    )
        except sqlite3.IntegrityError:
            return self.send_html(400, admin_shell("שגיאה", "<p>כתובת המאמר הזו כבר קיימת. בחרי כתובת אחרת.</p>"))
        return self.redirect("/admin/articles")


def main():
    if not ADMIN_PASSWORD:
        print("Set ADMIN_PASSWORD before starting the server. The admin area stays closed without it.")
    init_db()
    mailer.start_scheduler()
    if not os.environ.get("BREVO_API_KEY"):
        print("No BREVO_API_KEY: emails are written to data/outbox/ instead of being sent.")
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving on http://{HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
