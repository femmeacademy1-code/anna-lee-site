#!/usr/bin/env python3
"""Generates the public pages in site/ from config.json and products.json.

Run:  python3 build.py
Articles are not generated here. They are served from the database by server.py.

Every page is assembled from a few shared pieces, so the whole site keeps one look:
  page_head()   the top of an inner page: title, short facts, quick links, a photo or the ring mark
  sec()         a section; its colour says what kind of content it holds:
                light paper for reading, sage for how things work, blush for the event and for action
  box(), duo()  group related content side by side
  card()        one item in a list of lectures, workshops, tools
  form_sec()    the form, in a box beside its text
"""
import html
import re
import json
import pathlib
import shutil
from datetime import date

import boho

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "site"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
DATA = json.loads((ROOT / "products.json").read_text(encoding="utf-8"))
PRODUCTS = DATA["products"]
FREE = DATA["free"]
TODAY = date.today().isoformat()


def E(value):
    return html.escape(str(value), quote=True)


NAV = [
    ("/about", "נעים להכיר"),
    ("/therapy", "מפגשים בקליניקה"),
    ("/breathwork", "ריברסינג"),
    ("/workshops", "סדנאות"),
    ("/lectures", "הרצאות"),
    ("/articles", "מאמרים"),
    ("/free", "כלים חינמיים"),
    ("/contact", "צרו קשר"),
]

SERVICES = [
    ("therapy", "טיפול רגשי פרטני"),
    ("breathwork", "ריברסינג ונשימה מעגלית"),
    ("workshop", "סדנה או קורס"),
    ("lecture", "הרצאה לארגון"),
    ("free", "כלי חינמי"),
    ("general", "שאלה כללית"),
]

# The site's mark: a small circle with two rings of breath around it.
MARK = ('<svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true">'
        '<circle cx="16" cy="16" r="5.5" fill="#B06F4F"/>'
        '<circle cx="16" cy="16" r="10" fill="none" stroke="#B06F4F" stroke-opacity=".6"/>'
        '<circle cx="16" cy="16" r="15" fill="none" stroke="#B06F4F" stroke-opacity=".3"/></svg>')


# The landing page's mark: a lotus opening above still water, with a seed of light over it.
LP_MARK = ('<svg class="brand-mark lp-mark" viewBox="0 0 40 40" aria-hidden="true">'
           '<g stroke="#8A4F36" stroke-width=".9" stroke-linejoin="round">'
           '<path d="M20 30C11 31 5 26 3 20c6-1 12 3 17 10z" fill="#EFC6B5"/>'
           '<path d="M20 30c9 1 15-4 17-10-6-1-12 3-17 10z" fill="#EFC6B5"/>'
           '<path d="M20 30c-7-2-11-9-10-17 5 2 9 8 10 17z" fill="#E0A48F"/>'
           '<path d="M20 30c7-2 11-9 10-17-5 2-9 8-10 17z" fill="#E0A48F"/>'
           '<path d="M20 9c5 6 5 15 0 21-5-6-5-15 0-21z" fill="#B06F4F"/></g>'
           '<path d="M9 34.5c7-2 15-2 22 0" fill="none" stroke="#B06F4F" stroke-width="1" stroke-linecap="round" opacity=".6"/>'
           '<circle cx="20" cy="4.2" r="1.7" fill="#C98A70"/></svg>')

# the lotus is the mark of the whole site now (it replaced the three rings in November 2026)
MARK = LP_MARK


# ---------- shared pieces ----------

def nav_links(active):
    out = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == active else ""
        out.append(f'<a href="{href}"{current}>{E(label)}</a>')
    return "".join(out)


def whatsapp_link():
    number = CFG.get("whatsapp", "").replace("+", "").replace(" ", "").replace("-", "")
    if not number:
        return ""
    return f"https://wa.me/{number}"


def phone_tel():
    phone = CFG.get("phone", "")
    return phone, (("+972" + phone.lstrip("0")) if phone else "")


def contact_lines():
    phone, tel = phone_tel()
    lines = ""
    if phone:
        lines += f'<li><a href="tel:{E(tel)}">{E(phone)}</a></li>'
    if CFG.get("email"):
        lines += f'<li><a href="mailto:{E(CFG["email"])}">{E(CFG["email"])}</a></li>'
    return f'<ul class="contact-lines">{lines}</ul>' if lines else ""


def lead_form(service, item="", note_label="מה הביא אותך לפנות עכשיו? (אופציונלי)", extra_select=None,
              download="", register=False, button="שליחה", success="", next_page="", choose=False):
    """The one form of the site. register=True gives the short event registration:
    name and email, phone optional, no service menu."""
    attrs = ""
    if download:
        attrs += f' data-download="{E(download)}"'
    if success:
        attrs += f' data-success="{E(success)}"'
    if next_page:
        attrs += f' data-next="{E(next_page)}"'
    if register:
        fields = f"""
  <div class="field half"><label>שם<input name="name" required autocomplete="name" minlength="2"></label></div>
  <div class="field half"><label>מייל<input name="email" type="email" required autocomplete="email" inputmode="email"></label></div>
  <div class="field"><label>טלפון (אופציונלי)<input name="phone" type="tel" autocomplete="tel" inputmode="tel"></label></div>
  <input type="hidden" name="service" value="{E(service)}">
  <input type="hidden" name="item" value="{E(item)}">"""
    else:
        options = "".join(
            f'<option value="{v}"{" selected" if v == service else ""}>{E(t)}</option>' for v, t in SERVICES
        )
        service_field = (f'<div class="field"><label>במה אפשר לעזור<select name="service">{options}</select></label></div>'
                         if choose else f'<input type="hidden" name="service" value="{E(service)}">')
        item_field = ""
        if extra_select:
            # an option may be (title, page that opens after sending)
            opts = "".join(
                f'<option data-next="{E(o[1])}">{E(o[0])}</option>' if isinstance(o, tuple) and o[1]
                else f"<option>{E(o[0] if isinstance(o, tuple) else o)}</option>"
                for o in extra_select)
            item_field = (
                f'<div class="field"><label>על איזה כלי?<select name="item">'
                f'<option value="">בחרי</option>{opts}</select></label></div>'
            )
        elif item:
            item_field = f'<input type="hidden" name="item" value="{E(item)}">'
        fields = f"""
  <div class="field half"><label>שם<input name="name" required autocomplete="name" minlength="2"></label></div>
  <div class="field half"><label>טלפון<input name="phone" type="tel" autocomplete="tel" inputmode="tel"></label></div>
  <div class="field"><label>מייל<input name="email" type="email" autocomplete="email" inputmode="email"></label></div>
  {service_field}
  {item_field}
  <div class="field"><label>{E(note_label)}<textarea name="message" rows="3"></textarea></label></div>"""
    return f"""
<form class="lead-form" data-lead-form novalidate{attrs}>{fields}
  <label class="consent"><input type="checkbox" name="marketing"> אני מסכימה לקבל תכנים, הרצאות והצעות מהקליניקה במייל ובוואטסאפ. ההסכמה אופציונלית ואינה תנאי לפנייה.</label>
  <input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
  <button class="btn" type="submit">{E(button)}</button>
  <p class="form-msg" role="status" aria-live="polite"></p>
  <p class="fine">הפרטים נשמרים כדי לחזור אלייך לגבי הפנייה. אין חובה חוקית למסור אותם, אבל בלעדיהם לא אוכל לחזור אלייך. הם נשמרים אצלי ובמערכת המיילים Brevo. <a href="/privacy">למדיניות הפרטיות</a></p>
</form>"""


def layout(path, title, description, main, active=None, noindex=None, extra_head="", body_class="", og_image="", landing=False):
    # a landing page stands alone: the name without a link and no menu, so the way out is not
    # one tap away; the footer keeps only the legal links
    if landing:
        header = f'''<header class="site-header lp-header">
  <div class="wrap"><span class="brand">{LP_MARK}<strong>{E(CFG['site_name'])}</strong></span></div>
</header>'''
        footer_nav = ""
    else:
        header = f'''<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/">{MARK}<strong>{E(CFG['site_name'])}</strong></a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="site-nav">תפריט</button>
    <nav class="nav" id="site-nav" aria-label="ניווט ראשי">
      {nav_links(active)}
    </nav>
  </div>
</header>'''
        footer_nav = f'''<ul class="footer-links" aria-label="קישורים">
      {''.join(f'<li><a href="{h}">{E(t)}</a></li>' for h, t in NAV)}
    </ul>'''
    if noindex is None:
        noindex = CFG["draft"]
    robots = '<meta name="robots" content="noindex, nofollow">' if noindex else ""
    draft = (
        f'<div class="draft-banner">טיוטה. האתר עדיין לא פורסם.</div>'
        if CFG["draft"] else ""
    )
    url = CFG["domain"].rstrip("/") + path
    insta = (f'<li><a href="{E(CFG["instagram"])}" target="_blank" rel="noopener">אינסטגרם</a></li>'
             if CFG.get("instagram") else "")
    mail = f'<li><a href="mailto:{E(CFG["email"])}">{E(CFG["email"])}</a></li>' if CFG.get("email") else ""
    return f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{E(title)} | {E(CFG['site_name'])}</title>
<meta name="description" content="{E(description)}">
<link rel="canonical" href="{E(url)}">
{robots}
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description)}">
<meta property="og:locale" content="he_IL">
{('<meta property="og:image" content="' + E(CFG["domain"].rstrip("/") + og_image) + '">') if og_image else ""}
<link rel="preload" href="/static/fonts/heebo-hebrew-300-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/static/fonts/heebo-hebrew-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/static/site.css">
{extra_head}
</head>
<body{(' class="' + body_class + '"') if body_class else ""}>
<a class="skip" href="#main">מעבר לתוכן</a>
{draft}
{header}
<main id="main">
{main}
</main>
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <p class="footer-brand">{LP_MARK if landing else MARK}{E(CFG['site_name'])}</p>
      <p>פסיכותרפיסטית הוליסטית, מטפלת רגשית ומרצה. בהרצליה ובזום.</p>
      <p class="legal">האתר אינו מחליף ייעוץ, טיפול רפואי או טיפול נפשי. במצב של סכנה מיידית יש לפנות ל-101 או ל-112.</p>
    </div>
{footer_nav}
    <ul class="footer-links" aria-label="מידע ויצירת קשר">
      {mail}
      {insta}
      <li><a href="/privacy">מדיניות פרטיות</a></li>
      <li><a href="/accessibility">הצהרת נגישות</a></li>
      <li><a href="/terms">תקנון</a></li>
    </ul>
  </div>
  <div class="wrap"><p class="footer-bottom">© {date.today().year} {E(CFG['site_name'])}. כל הזכויות שמורות.</p></div>
</footer>
<script src="/static/app.js" defer></script>
</body>
</html>
"""



def photo_style(pos="", zoom=1):
    css = []
    if pos:
        css.append(f"object-position:{pos}")
    if zoom and float(zoom) > 1:
        css.append(f"transform:scale({float(zoom):.2f});transform-origin:{pos or '50% 50%'}")
    return f' style="{";".join(css)}"' if css else ""


def print_photo(src, alt, caption="", wide=False, pos="", stamp_html="", slot="", zoom=1):
    """slot names the place on the site, so a photo there can be swapped and placed on its own."""
    attrs = photo_style(pos, zoom) + (f' data-slot="{slot}"' if slot else "")
    cap = f"<figcaption>{E(caption)}</figcaption>" if caption else ""
    fig = (f'<figure class="print{" wide" if wide else ""}"><div class="frame">'
           f'<img src="{src}" alt="{E(alt)}" loading="lazy"{attrs}></div>{cap}</figure>')
    if stamp_html:
        return f'<div class="print-wrap">{stamp_html}{fig}</div>'
    return fig


def rings_mark(inner=""):
    return f'<div class="rings-mark" aria-hidden="true"><span></span><span></span><span></span><span></span>{inner}</div>'


def media_photo(*args, **kwargs):
    return f'<div class="ph-media">{print_photo(*args, **kwargs)}</div>'


def media_art(svg):
    """A boho illustration in the page head, where the page has no photo of its own."""
    return f'<div class="ph-media art">{svg}</div>'


def media_rings(inner=""):
    return ""  # page heads without a photo are text only


def toc(items):
    """Quick links to the sections of a long page (removed in the cleanup)."""
    return ""
    links = "".join(f'<a href="#{i}">{E(t)}</a>' for i, t in items)
    return f'<nav class="toc" aria-label="בעמוד הזה"><span>בעמוד הזה</span>{links}</nav>'


def page_head(kicker, title, lead="", extra="", media="", sub="", nav="", variant="", ground=""):
    """The top of an inner page. The text always sits beside the picture; the shapes differ:
      panel      text on a coloured panel, a portrait photo rising out of its top (people and places)
      side wide  text beside a landscape photo, no panel (practices, workshops, talks)
      side       text beside a drawing, or an event photo with its date stamp
      center     text only, centred
    ground is a drawing of earth the photo stands on, wider than the photo, so its two ends
    show at either side."""
    v = variant or ("side" if media else "center")
    if ground and media.startswith('<div class="ph-media">'):
        media = media.replace('<div class="ph-media">', f'<div class="ph-media has-ground"><div class="ground" aria-hidden="true">{ground}</div>', 1)
    kick = f'<p class="kicker">{kicker}</p>' if kicker else ""
    subp = f'<p class="sub">{sub}</p>' if sub else ""
    leadp = f'<p class="lead">{lead}</p>' if lead else ""
    if v == "banner":
        return (f'<div class="ph banner"><div class="wrap"><div class="ph-cols"><div>{kick}<h1>{E(title)}</h1></div>'
                f'<div>{subp}{leadp}{extra}</div></div>{media}</div></div>')
    if v == "center":
        return (f'<div class="ph center"><div class="wrap"><div class="ph-text">{kick}<h1>{E(title)}</h1>'
                f'{subp}{leadp}{extra}</div></div></div>')
    return (f'<div class="ph {v}"><div class="wrap"><div class="ph-grid"><div class="ph-text">{kick}<h1>{E(title)}</h1>'
            f'{subp}{leadp}{extra}</div>{media}</div>{nav}</div></div>')


def sec(title, body, tone="", hid="", intro="", wide=False, center=False, kicker=""):
    """One section. tone: light, sage (how it works), blush (action), paper; empty alternates."""
    t = f"tone-{tone}" if tone else "tone-auto"
    if tone.startswith("deep"):
        t += " on-deep"  # a deep surface: cream text, the colours flipped
    idattr = f' id="{hid}"' if hid else ""
    head = ""
    if title or intro or kicker:
        k = f'<p class="kicker">{kicker}</p>' if kicker else ""
        h = f"<h2>{E(title)}</h2>" if title else ""
        i = f"<p>{intro}</p>" if intro else ""
        head = f'<div class="sec-head{" center" if center else ""}">{k}{h}{i}</div>'
    return (f'<section class="sec {t}"{idattr}><div class="wrap">{head}'
            f'<div class="sec-body{" wide" if wide else ""}">{body}</div></div></section>')


def assemble(*parts):
    """Gives every section without a set tone the opposite of the one before it,
    so neighbouring sections are always told apart."""
    out, prev = [], "light"
    for p in parts:
        m = re.search(r'class="sec tone-(\w+)', p)
        if m:
            t = m.group(1)
            if t == "auto":
                t = "light" if prev == "paper" else "paper"
                p = p.replace("tone-auto", "tone-" + t, 1)
            prev = t
        out.append(p)
    return "".join(out)


def box(inner, tint=""):
    return f'<div class="box{" " + tint if tint else ""}">{inner}</div>'


def duo(a, b, stretch=False):
    return f'<div class="duo{" stretch" if stretch else ""}">{a}{b}</div>'


def callout(text):
    return f'<p class="callout">{text}</p>'


def rings_list(items, two=False):
    return f'<ul class="rings{" two" if two else ""}">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def steps(items):
    """items: (title, text, duration or "")"""
    out = ""
    for t, p, dur in items:
        d = f'<span class="dur">{E(dur)}</span>' if dur else ""
        out += f"<li>{d}<h3>{E(t)}</h3><p>{p}</p></li>"
    return f'<ol class="steps">{out}</ol>'


def qa(pairs, title=""):
    head = f'<h3 class="qa-title">{E(title)}</h3>' if title else ""
    return '<div class="qa-group">' + head + '<div class="qa">' + "".join(
        f"<details><summary>{E(q)}</summary><p>{a}</p></details>" for q, a in pairs
    ) + "</div></div>"


def chips(items, highlight_first=False):
    return ""  # removed in the cleanup: the same facts are said once, in the text
    out = ""
    for k, x in enumerate(items):
        cls = ' class="hl"' if highlight_first and k == 0 else ""
        out += f"<li{cls}>{x}</li>"
    return f'<ul class="chips">{out}</ul>'


def tiles(pairs):
    return f'<div class="tiles{" three" if len(pairs) % 3 == 0 else ""}">' + "".join(f"<div><span>{E(a)}</span><strong>{b}</strong></div>" for a, b in pairs) + "</div>"


def stamp(day, when, note="", small=False):
    n = f'<span class="d3">{E(note)}</span>' if note else ""
    return (f'<p class="stamp{" small" if small else ""}" aria-label="{E(day)} {E(when)}">'
            f'<span class="d1">{E(day)}</span><span class="d2">{E(when)}</span>{n}</p>')


DOT = '<span class="dot"></span>'


def card(title, href, text, meta="", mark=None, link="לפרטים", tint="", external=False):
    target = ' target="_blank" rel="noopener"' if external else ""
    m = f'<div class="mark">{mark}</div>' if mark is not None else ""
    mt = f'<span class="meta">{meta}</span>' if meta else ""
    return (f'<li class="card{" " + tint if tint else ""}">{m}{mt}<h3><a href="{href}"{target}>{E(title)}</a></h3>'
            f'<p>{text}</p><span class="more" aria-hidden="true">{E(link)}</span></li>')


def cards(items):
    return '<ul class="cards">' + "".join(items) + "</ul>"


def form_box(form):
    return f'<div class="form-box">{form}</div>'


def form_sec(title, text, form, hid="form", tone="blush", side=""):
    """The form section: text on one side, the form in a box on the other."""
    return (f'<section class="sec tone-{tone}" id="{hid}"><div class="wrap contact-grid">'
            f'<div>{side}<h2>{E(title)}</h2>{text}</div>{form_box(form)}</div></section>')


def cta_sec(title="הצעד הראשון הוא פשוט לדבר", text="", href="/contact", label="לשיחת היכרות", tone="blush"):
    t = text or f"שיחת היכרות של כ-{CFG['intro_call_minutes']} דקות, ללא עלות. נבדוק יחד מה מתאים לך."
    return (f'<section class="sec tone-{tone} cta"><div class="wrap">'
            f'<h2>{E(title)}</h2><p>{t}</p><p><a class="btn" href="{href}">{E(label)}</a></p></div></section>')


def write(path, content):
    target = SITE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


# ---------- illustrations ----------
# Printed-ink drawings: flat shapes in the site colours, a grainy ink texture, a soft offset shadow.
INK, SAGE, ROSE, TAUPE, CREAM = "#4B3027", "#A4AC86", "#BF6A79", "#A39171", "#F9EAE1"


def _ink_filter(n):
    return (f'<filter id="ik-{n}" x="-8%" y="-8%" width="116%" height="116%">'
            '<feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="2" result="w"/>'
            '<feDisplacementMap in="SourceGraphic" in2="w" scale="2.2" xChannelSelector="R" yChannelSelector="G" result="d"/>'
            '<feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="1" seed="5" result="g"/>'
            '<feColorMatrix in="g" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2.4 0 0 0 -.12" result="m"/>'
            '<feComposite in="d" in2="m" operator="in"/></filter>')


def _shadowed(body):
    plain = re.sub(r' fill="[^"]*"', ' fill="#3A2E24"', body)
    return f'<g transform="translate(2.5 2.5)" opacity=".3">{plain}</g>{body}'


_SK = [0]


def sketch(body):
    _SK[0] += 1
    n = _SK[0]
    return (f'<div class="sketch" aria-hidden="true"><svg viewBox="0 0 200 150" preserveAspectRatio="xMidYMid meet">'
            f'<defs>{_ink_filter(n)}</defs>'
            f'<g filter="url(#ik-{n})">{_shadowed(body)}</g></svg></div>')


def _figure(x, color, head_y=58, r=10):
    return (f'<circle cx="{x}" cy="{head_y}" r="{r}" fill="{color}"/>'
            f'<path d="M{x-21} 128 C{x-21} 100 {x-11} {head_y+28} {x} {head_y+28} C{x+11} {head_y+28} {x+21} 100 {x+21} 128 Z" fill="{color}"/>')


SKETCHES = {
    # two people side by side, a heart between them: the meeting in the clinic, and help for someone close
    "first-aid-kit": sketch(
        f'<circle cx="54" cy="50" r="12" fill="{INK}"/>'
        f'<path d="M30 128 C30 96 40 84 54 84 C68 84 78 96 78 128 Z" fill="{INK}"/>'
        f'<circle cx="146" cy="50" r="12" fill="{SAGE}"/>'
        f'<path d="M122 128 C122 96 132 84 146 84 C160 84 170 96 170 128 Z" fill="{SAGE}"/>'
        f'<path d="M100 80 C94 74 90 70 90 66 C90 62 93 60 96 60 C98 60 99.5 61.5 100 63 C100.5 61.5 102 60 104 60 C107 60 110 62 110 66 C110 70 106 74 100 80 Z" fill="{ROSE}"/>'),
    # three stacked books and a pencil
    "workbooks": sketch(
        f'<rect x="40" y="104" width="94" height="17" rx="2" fill="{INK}"/>'
        f'<rect x="132" y="108" width="3" height="9" fill="{CREAM}" opacity=".7"/>'
        f'<rect x="50" y="86" width="82" height="17" rx="2" fill="{SAGE}"/>'
        f'<rect x="124" y="90" width="3" height="9" fill="{CREAM}" opacity=".7"/>'
        f'<rect x="46" y="68" width="86" height="17" rx="2" fill="{ROSE}"/>'
        f'<rect x="124" y="72" width="3" height="9" fill="{CREAM}" opacity=".7"/>'
        f'<path d="M126 44 L136 34 L143 41 L133 51 Z" fill="{TAUPE}"/>'
        f'<path d="M126 44 L121 55 L133 51 Z" fill="{INK}"/>'),
    # a seated figure in stillness, with a soft rose halo of breath
    "meditation": sketch(
        f'<circle cx="100" cy="74" r="50" fill="{ROSE}" opacity=".16"/>'
        f'<circle cx="100" cy="50" r="11" fill="{INK}"/>'
        f'<path d="M86 68 C86 62 114 62 114 68 L121 94 C123 102 110 106 100 106 C90 106 77 102 79 94 Z" fill="{INK}"/>'
        f'<path d="M60 116 C70 100 130 100 140 116 C142 124 58 124 60 116 Z" fill="{SAGE}"/>'),
    # a sunset over the sea, and a small paper boat carrying what is let go
    "tashlich-ritual": sketch(
        f'<path d="M70 100 A30 30 0 0 1 130 100 Z" fill="{ROSE}" opacity=".85"/>'
        f'<path d="M22 104 q9 -6 18 0 t18 0 t18 0 t18 0 t18 0 t18 0 t18 0 t18 0" stroke="{SAGE}" stroke-width="3" fill="none" stroke-linecap="round"/>'
        f'<path d="M30 124 q9 -6 18 0 t18 0 t18 0 t18 0 t18 0 t18 0" stroke="{TAUPE}" stroke-width="3" fill="none" stroke-linecap="round" opacity=".8"/>'
        f'<path d="M116 130 L154 130 L146 140 L124 140 Z" fill="{TAUPE}"/>'
        f'<path d="M136 128 L136 108 L150 126 Z" fill="{CREAM}"/>'
        f'<circle cx="136" cy="100" r="3" fill="{ROSE}"/>'),
    # a woman on a stool, speaking, a breath sun beside her
    "lecture": sketch(
        f'<circle cx="152" cy="34" r="16" fill="{ROSE}" opacity=".85"/>'
        f'<circle cx="96" cy="38" r="11" fill="{INK}"/>'
        f'<path d="M84 60 C84 50 106 50 108 60 L114 100 C115 106 110 108 102 108 L90 108 C84 108 82 104 83 100 Z" fill="{INK}"/>'
        f'<rect x="84" y="106" width="34" height="5" rx="2" fill="{TAUPE}"/>'
        f'<path d="M92 111 L86 128 M110 111 L116 128" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
        f'<rect x="36" y="128" width="128" height="2" fill="{SAGE}"/>'),
    # three people together, a soft halo behind them: a group
    "group": sketch(
        f'<circle cx="100" cy="80" r="52" fill="{ROSE}" opacity=".14"/>'
        + _figure(58, SAGE) + _figure(142, TAUPE) + _figure(100, INK, head_y=50, r=11)),
}

# A drawing for each card, made for that item; none is shared with a page head.
CARD_ART = {"work-under-pressure": boho.card_pressure, "education-teams": boho.card_education,
            "calm-in-the-storm": boho.card_calm, "nervous-system-course": boho.card_nervous,
            "rebirthing-after-birth": boho.card_birth, "first-aid-kit": boho.card_kit,
            "workbooks": boho.card_workbooks, "tashlich-ritual": boho.card_tashlich, "meditation": boho.card_meditation}


def card_art(key):
    return f'<span class="card-art">{CARD_ART[key]()}</span>' if key in CARD_ART else ""


FREE_LINKS = {"tashlich-ritual": ("/tashlich", "לפרטים ולקבלה")}


# ---------- the free lecture ----------

LECTURE_DAY, LECTURE_DATE = "יום ראשון", "29.11.26"
LECTURE_TIME = "20:30"


def kotzim_fig(uid="", words=True):
    """The lecture "on thorns": one line, sharp like thorns, softening into a wave with flowers,
    and the three words that move with it (inside the same drawing, on one clock)."""
    return f'<figure class="kotzim-fig">{boho.kotzim_line(words=words)}</figure>'


def kotzim_mark(uid=""):
    """For the lecture's card: the line alone; the date is in the card's meta line."""
    return f'<span class="kotzim-mark">{boho.kotzim_line(words=False)}</span>'


LECTURE_WHEN = f"{LECTURE_DAY} {LECTURE_DATE}"

LECTURES = [
    {
        "slug": "al-kotzim",
        "name": "על קוצים",
        "title": "למה הגוף שלך כל הזמן בכוננות ואיך מפסיקים לפחד מהחרדה",
        "meta": "הרצאה חינמית בזום",
        "summary": "30 דקות בלייב, אונליין ובחינם. מה קורה בגוף כשהחרדה עולה, ואילו כלים עוזרים לחזור ליותר יציבות.",
        "free": True,
    },
    {
        "slug": "work-under-pressure",
        "title": "לעבוד תחת לחץ, מבלי לחיות בלחץ",
        "meta": "הרצאה לארגונים",
        "summary": "סטרס, שחיקה, ויסות מערכת העצבים וכלים קצרים להתמודדות עם עומס בחיי העבודה.",
        "free": False,
    },
    {
        "slug": "education-teams",
        "title": "הרצאה לצוותי חינוך",
        "meta": "לצוותי חינוך",
        "summary": "שחיקה, ויסות רגשי וכלים להתמודדות עם עומס. הפרטים יעודכנו בקרוב.",
        "free": False,
        "edu": True,
    },
]

FREE_TITLE_TASHLICH = "טקס תשליך אישי על חוף הים"
FREE_TITLE_WEBINAR = "הרצאה חינמית - על קוצים - למה הגוף שלך כל הזמן בכוננות ואיך מפסיקים לפחד מהחרדה"
SPOTIFY_EMBED = "https://open.spotify.com/embed/show/{id}?theme=0"


# ---------- pages ----------

# the four ways on the home page, each in a real photo (the slot lets the photos be swapped in the preview)
WAY_PHOTO = {
    "first-aid-kit": ("clinic-entrance.jpg", "50% 40%"),
    "meditation": ("breathwork-lying.jpg", "30% 50%"),
    "group": ("therapy-session.jpg", "50% 50%"),
    "lecture": ("lecture-chin.jpg", "56% 40%"),
}
WAY_ART = {"first-aid-kit": boho.way_therapy, "meditation": boho.way_breath, "group": boho.way_group, "lecture": boho.way_lecture}


def page_home():
    wa = whatsapp_link()
    hero = f"""<section class="sec tone-paper hero"><div class="wrap hero-grid">
  <div class="hero-text">
    <p class="kicker">פסיכותרפיה הוליסטית בהרצליה ובזום</p>
    <h1>אנה לי מילשטיין</h1>
    <p class="lead">מטפלת רגשית לנשים ולגברים שמתמודדים עם <strong class="key">חרדה, טראומה וקושי בויסות רגשי</strong>, בגישה רכה, עמוקה ופרקטית, <strong class="key">שמחברת אותך עוד לעצמך.</strong></p>
    <div class="actions"><a class="btn" href="/contact">לשיחת היכרות</a></div>
  </div>
  <div class="breath">
    <span class="ring outer"></span><span class="ring inner"></span>
    <span class="photo"><img src="/static/img/portrait.jpg" alt="אנה לי מילשטיין, מחייכת" width="900" height="879" data-slot="home-portrait"></span>
  </div>
</div></section>"""

    def way(title, href, text, sk, link):
        photo, pos = WAY_PHOTO[sk]
        return (f'<li class="way"><a href="{href}"><span class="way-photo"><span class="disc">'
                f'<img src="/static/img/{photo}" alt="" loading="lazy" style="object-position:{pos}" data-orig-pos="{pos}" data-slot="way-{sk}">'
                f'</span></span><h3>{E(title)}</h3><p>{text}</p><span class="more">{E(link)}</span></a></li>')
    ways = sec("איך אפשר לעבוד איתי", '<ul class="ways">' + "".join([
        way("מפגשים בקליניקה", "/therapy", "תהליכים רגשיים ועמוקים לנשים ולגברים, בהרצליה או בזום.", "first-aid-kit", "לפרטים"),
        way("ריברסינג", "/breathwork", "נשימה מעגלית, כשמבינה הכול בראש אבל משהו עדיין תקוע בגוף.", "meditation", "לפרטים"),
        way("סדנאות וקורסים", "/workshops", "עבודה קבוצתית ליצירת ויסות, חיבור ומשאבים ליציבות רגשית.", "group", "לסדנאות"),
        way("הרצאות", "/lectures", "סטרס, שחיקה וויסות מערכת העצבים, לארגונים ולצוותים.", "lecture", "להרצאות"),
    ]) + "</ul>", tone="paper", wide=True, center=True)

    # the one event on the page: a deep berry panel set into the paper, like an invitation
    feature = f"""<section class="sec tone-light feature"><div class="wrap"><div class="feature-panel event on-deep"><div class="feature-grid">
  <div class="kotzim-feature">{kotzim_fig("home")}</div>
  <div>
    <p class="kicker">הרצאה חינמית בזום, {LECTURE_WHEN}</p>
    <h2>על קוצים</h2>
    <p class="sub">למה הגוף שלך כל הזמן בכוננות, ואיך מפסיקים לפחד מהחרדה</p>
    <p class="feature-meta">30 דקות בלייב, ללא עלות. בסוף ההרצאה תקבלי ערכת ויסות לשמירה בטלפון.</p>
    <div class="actions"><a class="btn" href="/lectures/al-kotzim">להרשמה חינמית</a></div>
  </div>
</div></div></div></section>"""

    about = f"""<section class="sec tone-paper about-band"><div class="wrap split">
  {print_photo("/static/img/about-seated.jpg", "אנה לי מילשטיין יושבת בשיכול רגליים, בנשימה ושקט", pos="50% 17%", slot="home-about")}
  <div>
    <h2>קצת עליי</h2>
    <p>נעים מאוד ואיזה כיף שאת פה! אני אנה לי מילשטיין, מטפלת משנת 2020 בנשים ובגברים המתמודדים עם קושי בויסות רגשי, <strong class="key">חרדות, התקפי זעם ופוסט טראומה.</strong></p>
    <p>אני כאן כדי ללוות אותך בתהליך עמוק ואמיתי שיחבר אותך מחדש לעצמך, מתוך גישה רכה, חמלה, נשימה ושיח, המשולבת עם כלים פרקטיים שיעזרו לך <strong class="key">להתחיל לייצר את השינוי שאת רוצה בחיים שלך.</strong></p>
    {chips(["משנת 2020", "בהרצליה ובזום", "נשים וגברים"])}
    <div class="actions"><a class="more" href="/about">הסיפור שלי</a></div>
  </div>
</div></section>"""

    med = ""
    if CFG.get("meditation_url"):
        url = CFG["meditation_url"]
        m = re.search(r"open\.spotify\.com/(show|episode|playlist|track)/([A-Za-z0-9]+)", url)
        player = ""
        if m:
            src = f"https://open.spotify.com/embed/{m.group(1)}/{m.group(2)}?theme=0"
            player = (f'<iframe class="spotify" src="{E(src)}" title="מדיטציות מודרכות של אנה לי בספוטיפיי" loading="lazy" '
                      'allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>')
        play = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4.5v15L19.5 12z" fill="currentColor"/></svg>')
        # the cover breathes: rings around it widen and settle, and the words follow the breath
        med = f"""<section class="sec med"><div class="wrap med-grid">
  <div class="med-art">
    <span class="ring r3"></span><span class="ring r2"></span><span class="ring r1"></span>
    <a class="cover" href="{E(url)}" target="_blank" rel="noopener" aria-label="להאזנה למדיטציה בספוטיפיי">
      <img src="/static/img/meditation-cover.jpg" alt="מדיטציה לפתיחת הבוקר, אנה לי מילשטיין" width="1000" height="1000" loading="lazy">
    </a>
    <p class="guide" aria-hidden="true"><span class="in">שאיפה</span><span class="out">נשיפה</span></p>
  </div>
  <div class="med-text">
    <p class="kicker">מדיטציות מודרכות בספוטיפיי</p>
    <h2>מדיטציה מודרכת לפתיחת הבוקר</h2>
    <p class="sub">כמה דקות של נשימה ושקט, לפני שהיום מתחיל.</p>
    <p>אפשר להאזין בכל זמן, מהטלפון או מהמחשב.</p>
    {player}
    <div class="actions"><a class="btn light" href="{E(url)}" target="_blank" rel="noopener">{play}להאזנה בספוטיפיי</a></div>
  </div>
</div></section>"""

    wa_link = f'<p><a class="more" href="{E(wa)}" rel="noopener">לשיחה בוואטסאפ</a></p>' if wa else ""
    contact = form_sec("ליצירת קשר",
                       f"<p>הפגישות מתקיימות בהרצליה או בזום. אפשר להשאיר פרטים, ואחזור אלייך לתיאום שיחת היכרות של כ-20 דקות, ללא עלות.</p>{contact_lines()}{wa_link}",
                       lead_form("therapy"))
    return layout(
        "/",
        "טיפול רגשי ופסיכותרפיה הוליסטית בהרצליה ובזום",
        "טיפול רגשי לנשים ולגברים שמתמודדים עם חרדה, טראומה וקושי בוויסות רגשי. בהרצליה ובזום.",
        hero + ways + feature + med + about + contact,
        active="/",
    )


def page_about():
    # 1. who I am, in two lines, with her photo
    head = page_head(
        "", "נעים להכיר, אני אנה לי",
        lead="פסיכותרפיסטית הוליסטית, מטפלת רגשית ומנחת ריברסינג. מטפלת משנת 2020 בנשים ובגברים המתמודדים עם קושי בויסות רגשי, חרדות, התקפי זעם ופוסט טראומה.",
        extra='<p>המפגשים מתקיימים בקליניקה בהרצליה או אונליין.</p>',
        media=media_photo("/static/img/lecture-chin.jpg", "אנה לי מילשטיין בקליניקה, מקשיבה", pos="56% 40%", slot="about"), variant="panel", ground=boho.ground_about(),
    )
    # 2. the story, in one reading column
    story = f"""<section class="sec tone-auto"><div class="wrap"><div class="sec-body">
    <h2>איך הגעתי לכאן</h2>
    <p>כל חיי התמודדתי עם קושי עמוק בוויסות רגשי. חוויתי חרדות, חוסר שקט פנימי, תחושת חוסר ערך, התקפי זעם, בלבול וחיפוש עצמי בלתי נגמר – למרות שהכל נראה "בסדר מבחוץ". הרגשתי שאין מקום לכל מה שאני באמת מרגישה, שאין לי שפה פנימית שמכילה אותי.</p>
    <p>מתוך השבר הזה – ומתוך הכמיהה להבין את עצמי באמת – יצאתי למסע האישי שלי בעולם הטיפול, כמטופלת. זה היה מסע ארוך, כואב ועמוק, אבל דרכו גיליתי אפשרות חדשה לחיים.</p>
    <p>היום, מתוך הדרך האישית הזו ולימודים מקצועיים, אני פוגשת נשים בדיוק במקום הזה – מהמקום הכי רגיש וכנה, מתוך חמלה עמוקה, ומציעה להן את המרחב שכה הייתי צריכה בעצמי פעם.</p>
    {callout("היום אני חיה חיים טובים ומלאים יותר. יש לי קליניקה פעילה, אני בזוגיות יציבה עם יובל ואמא של נגה, ועדיין ממשיכה בעצמי בדרך הזו – ללמוד, להרגיש, לטעות, ולצמוח.")}
</div></div></section>"""
    # 3. education and background, side by side
    learning = sec("השכלה ורקע מקצועי", duo(
        "<div><h3>השכלה ותעודות</h3>" + rings_list([
            "תואר ראשון במדעי הטבע – האוניברסיטה העברית בירושלים",
            "לימודי פסיכותרפיה הוליסטית – מסלול ארבע-שנתי במכללת רידמן",
            'התמחות בטיפול ממוקד חמלה לנפגעי פוסט טראומה – בהנחיית ד"ר רוני ברגר',
            "הנחיית קבוצות מדיטציה ודמיון מודרך",
            "הכשרה כמטפלת ומנחת ריברסינג",
            "הכשרה בטיפול אנרגטי (הילינג)",
            "הכשרה בטיפול SE",
            "היכרות ויישום של גישת ACT – טיפול מבוסס קבלה ומחויבות",
            "מיודעת ומתבססת על התיאוריה הפוליוגאלית",
        ]) + "</div>",
        "<div><h3>רקע מקצועי</h3>" + rings_list([
            "מנחה במכללת רידמן",
            "מנחת קבוצות מדיטציה, דמיון מודרך וריברסינג.",
            "בעלת ניסיון בעבודה עם מתמודדי נפש",
            "חלק מצוות המטפלים במרכז לליווי רגיש של רותם כהני",
        ]) + "<p>בתהליך הטיפולי שלי אני מלווה נשים במסע רגשי עמוק של חיבור וריפוי, באמצעות שיח, טכניקות גופניות, נשימות מודעות, עבודה אנרגטית ותמיכה בדמיון מודרך.</p></div>",
    ), wide=True)
    return layout("/about", "נעים להכיר", "הסיפור האישי של אנה לי מילשטיין, ההשכלה והרקע המקצועי.",
                  head + assemble(story, learning, cta_sec()), active="/about")


def page_therapy():
    head = page_head(
        "טיפול רגשי", "מפגשים בקליניקה", sub="תהליכים רגשיים ועמוקים לנשים ולגברים.",
        extra=f"""<p>מרחב טיפולי שמאפשר לעצור רגע, להבין מה קורה מתחת לפני השטח וללמוד להחזיק את עצמך אחרת. כדי להרגיש יותר יציבה, מחוברת ונינוחה בתוך החיים שלך.</p>
""",
        media=media_photo("/static/img/clinic-entrance.jpg", "הכניסה לקליניקה בהרצליה, שביל עץ בין צמחייה ירוקה", slot="therapy"), variant="panel", ground=boho.ground_therapy(),
        nav=toc([("who", "למי זה מתאים"), ("how", "איך זה עובד"), ("process", "התהליך"), ("details", "פרטים ומחיר"), ("questions", "שאלות")]),
    )
    who = sec("למי הטיפול מתאים", """<p>הטיפול מתאים גם לנשים וגם לגברים.</p>
<p>הטיפול מתאים לנשים שמרגישות שהן "מבינות הכל" ועדיין לא מצליחות להשתחרר מדפוסים שמכאיבים להן. לנשים שמתמודדות עם קושי בוויסות רגשי, חרדות, תחושת ריקנות או תקיעות מתמשכת.</p>
<p>זה מתאים גם למי שכבר הייתה בטיפול בעבר – אבל מרגישה שהגיעה לתקרת זכוכית ורוצה לגעת ברבדים עמוקים יותר.</p>"""
              + callout("אם את מרגישה מוצפת, אם את חווה התקפי זעם, אם את מרגישה שחסרה לך גישה לחלקים רגשיים או רוחניים בתוכך – יש מקום אמיתי בשבילך כאן."), hid="who")
    how = sec("על השיטה", """<p>אני עובדת בגישה הוליסטית – שרואה את הקשר העמוק בין הנפש, הגוף והחיים עצמם.</p>
<p>השיטה שלי מתבססת על עקרונות של פסיכותרפיה, כלומר תהליך של הבנה, חקירה ושינוי של דפוסים רגשיים וחשיבתיים – אבל בצורה שמכילה גם את מה שלא תמיד אפשר להסביר במילים.</p>
<p>במהלך המפגשים אני משלבת שיח רגשי, תרגולי נשימה, דמיון מודרך, תנועה, מגע אנרגטי וכלים מעשיים – כדי לעזור לך לא רק להבין את עצמך, אלא גם להרגיש יותר יציבות, הקלה וחיבור מבפנים.</p>""", hid="how")
    meeting = f"""<section class="sec tone-auto"><div class="wrap split">
  {print_photo("/static/img/clinic-session.jpg", "אנה לי מילשטיין מניחה ידיים בעדינות על מטופלת השוכבת מכוסה בשמיכה, בקליניקה", wide=True, pos="42% 50%", slot="therapy-session")}
  <div>
    <h2>איך נראה מפגש</h2>
<p>המפגשים מתקיימים בקליניקה בהרצליה או בזום, באורך של שעה. בפגישות הראשונות נכיר, נחדד יחד את המטרות שלך, ונבנה מסגרת שמתאימה לקצב שלך.</p>
<p>העבודה נעשית בעיקר דרך שיח – אך במידת הצורך אני משלבת גם עבודה עם הגוף, תרגילי נשימה, דמיון מודרך, קלפים טיפוליים וטכניקות רגשיות עמוקות.</p>
<p>המטרה היא לעזור לך ליצור שיח פנימי מדויק ומרפא – כזה שמאפשר לך לפגוש את עצמך באמת, ולבנות בתוכך תחושת יציבות, ביטחון ובהירות.</p>  </div>
</div></section>"""
    process = sec("איך נראה התהליך", steps([
        ("מכירות ומנסחות מטרה", "בתחילת הדרך אנחנו מגדירות יחד מטרה טיפולית שתשמש כמגדלור לאורך התהליך.", ""),
        ("מבינות את הדפוסים", "נותנות מקום למה שקורה במחשבות, ברגשות, ביחסים ובחיים עצמם.", ""),
        ("משלבות את הגוף", "בהתאם לצורך משלבות נשימה, ציור, עבודה עם הגוף ללא מגע ותרגול של ויסות מערכת העצבים.", ""),
        ("בונות דרך שמתאימה לך", "מתקדמות בקצב מותאם, ולעיתים מוסיפות תרגולים בין המפגשים.", ""),
    ]) + '<p class="fine">זהו תיאור כללי של התהליך, אין פרוטוקול אחיד, וכל תהליך מותאם אישית למטרה, לקצב ולמה שאפשרי עבורך בכל שלב.</p>',
        tone="deep-clay", hid="process", wide=True)
    details = sec("פרטים ומחיר", tone="sage", body=tiles([
        ("מיקום", "קליניקה בהרצליה או בזום"),
        ("משך מפגש", f"{CFG['therapy_session_minutes']} דקות"),
        ("עלות", f"{CFG['therapy_price_ils']} ₪"),
        ("תדירות מומלצת", "פעם בשבוע"),
        ("שיחת היכרות", f"כ-{CFG['intro_call_minutes']} דקות, ללא עלות"),
    ]) + '<p class="fine">ריברסינג: אפשר לשלב בתיאום מראש במפגש של שעה וחצי, בהתאם לצורך ולהתאמה.</p>', hid="details", wide=True)
    questions = sec("שאלות ומחשבות", duo(
        qa([
            ('"אני לא יודעת להסביר בדיוק מה עובר עליי"', "לא צריך להגיע עם אבחנה או עם ניסוח מדויק. שיחת ההיכרות נועדה בדיוק לזה, כדי להתחיל להבין יחד."),
            ('"כבר ניסיתי טיפול בעבר"', "אפשר לבדוק יחד מה עזר, מה היה חסר ומה נכון לך עכשיו. אין הבטחה שהגישה תתאים, ולכן מתחילות בשיחת היכרות."),
            ('"אני חוששת להיות מוצפת בטיפול"', "התהליך מותאם לרמת הפניות ולמידת ההצפה שלך. לא חייבים להיכנס לכל דבר מיד."),
            ('"אני לא מתחברת לעבודה עם הגוף"', "לא כל כלי מתאים לכל אחת. העבודה אינה במגע, ונשלב רק את מה שמתאים לך ובהסכמה."),
            ('"אני לא בטוחה אם עדיף לי להגיע לקליניקה או להיפגש בזום"', "אפשר לדבר על שתי האפשרויות בשיחת ההיכרות ולבדוק יחד מה מתאים לך."),
        ], title="מחשבות שעולות לפני שמתחילות"),
        qa([
            ("האם הטיפול מבטיח להעלים חרדה?", "לא. אני לא מבטיחה להעלים חרדה או למחוק טראומה. המטרה היא להבין את התגובות שלך וללמוד כלים להתמודדות."),
            ("האם יש טיפול בזום?", "כן. אפשר להתחיל בקליניקה בהרצליה או בזום."),
            ("אני לא יודעת להסביר מה לא בסדר. זה בסדר?", "כן. לא צריך לדעת מראש. השיחה הראשונה נועדה בדיוק לזה."),
            ("כבר הייתי בטיפול. למה לנסות שוב?", "לפעמים נשאר משהו עמוק יותר שצריך מקום, גם אחרי ניסיונות קודמים."),
            ("האם צריך להתחייב לכמה מפגשים?", "השיחה הראשונה היא ללא עלות, ומשם מחליטים יחד על ההמשך."),
        ], title="שאלות נפוצות"),
    ), hid="questions", wide=True)
    form = form_sec("שיחת היכרות", f"<p>אפשר להשאיר פרטים, ואחזור אלייך בתוך {E(CFG['response_time'])} לתיאום שיחת היכרות של כ-{CFG['intro_call_minutes']} דקות, ללא עלות.</p>{contact_lines()}", lead_form("therapy"))
    return layout(
        "/therapy",
        "טיפול רגשי בהרצליה ובזום",
        "טיפול רגשי פרטני לנשים ולגברים עם חרדה, הצפה וקושי בוויסות. מפגש של 60 דקות, שיחת היכרות ללא עלות.",
        head + assemble(who, how, meeting, process, details, questions, form),
        active="/therapy",
    )


def page_breathwork():
    mins = CFG["breathwork_session_minutes"]
    n = CFG["breathwork_series_sessions"]
    head = page_head(
        "ריברסינג", "לפגוש את עצמך גם דרך הגוף והנשימה",
        lead="כשכבר מבינה הכול בראש, אבל משהו עדיין מרגיש תקוע בגוף.",
        extra=f"""<p>ריברסינג הוא טיפול בנשימה מעגלית שמאפשר לצאת לרגע מהניתוחים והמחשבות, להיכנס אל הגוף ולפגוש את מה שאנחנו סוחבות איתנו כבר הרבה זמן.</p>
""",
        media=media_photo("/static/img/breathwork-session.jpg", "אנה לי מלווה מפגש ריברסינג: משתתף שוכב על מזרן עם כרית תמיכה", wide=True, pos="50% 67%", slot="breathwork"), variant="side wide", ground=boho.ground_breathwork(),
        nav=toc([("what", "מה זה ריברסינג"), ("session", "איך נראה מפגש"), ("prices", "מחירים"), ("fit", "למי זה מתאים")]),
    )
    what = sec("אז מה זה בעצם ריברסינג?", """<p>ריברסינג הוא תהליך טיפולי המבוסס על נשימה מעגלית ורציפה. בעזרת הנשימה אנחנו מאפשרות לעצמנו לפגוש רבדים שלא תמיד נגישים לנו ביומיום.</p>
<p>במהלך התהליך יכולות לעלות תחושות גוף, רגשות, זיכרונות או חוויות שונות. המטרה היא לא "להכריח" משהו לקרות, אלא ליצור מרחב שבו אפשר לפגוש את מה שנמצא שם, בקצב שמתאים לך, עם ליווי לאורך הדרך.</p>"""
               + callout("המטרה היא לא להבטיח שדבר מסוים ייעלם, אלא ליצור דרך נוספת לפגוש עומס, סטרס, חרדה ותחושת תקיעות, ולאפשר התחלה של תנועה במקום שבו מילים והבנה לבדן כבר לא מספיקות."), hid="what")
    session = sec("איך נראה מפגש?", steps([
        ("שיחה ומיקוד", "מתחילות בשיחה קצרה על מה שאת מגיעה איתו ומה היית רוצה לפגוש או לעבוד עליו במפגש.", "20 דקות"),
        ("דמיון מודרך, נשימה והרפיה", "עוברות לעבודה עם הגוף והנשימה. אני נמצאת איתך לאורך כל התהליך, מנחה, מלווה ועוזרת להתאים את הקצב למה שקורה ברגע הזה.", "50 דקות"),
        ("עיבוד וקרקוע", "בסיום אנחנו לא קמות ופשוט ממשיכות הלאה. יש זמן לחזור, להתקרקע, לדבר על מה שעלה ולעבד את החוויה.", "20 דקות"),
    ]) + box("""<h3>מה יכול לקרות בזמן הנשימה?</h3>
<p>לפעמים עולים רגשות או זיכרונות, לפעמים בכי או צחוק, ולעיתים מופיעות תחושות גופניות כמו רעד או תנועה. יכולות להיות גם חוויות של שקט, שמחה, אהבה, חיבור או תחושת התרחבות.</p>
<p><strong class="key">אין חוויה "נכונה" שצריכה לקרות.</strong> התהליך אינו נמדד לפי עוצמת החוויה, וכל מה שעולה מקבל מקום מתוך הקשבה וללא צורך לייצר משהו בכוח.</p>"""),
        tone="deep-clay", hid="session", wide=True)
    prices = sec("מפגש אחד או סדרה קצרה?", tone="sage", body=f"""<div class="offers">
  <div class="offer"><h3>מפגש ריברסינג חד-פעמי</h3><p class="price">{CFG['breathwork_single_price_ils']} ₪</p><p>{mins} דקות. מרחב לחוויה ראשונה.</p></div>
  <div class="offer rec"><span class="badge">מומלץ</span><h3>סדרה של {n} מפגשים</h3><p class="price">{CFG['breathwork_series_price_ils']:,} ₪<span class="was">{CFG['breathwork_series_original_ils']:,} ₪</span></p><p>{n} מפגשים של {mins} דקות. מרחב להעמקה והמשכיות.</p></div>
</div>
<p>אם יש נושא מסוים שאת רוצה לעבוד איתו, אני ממליצה על סדרה קצרה של 3 מפגשים, כדי לאפשר יותר זמן להעמקה, עיבוד והמשכיות. אם את לא בטוחה מה נכון עבורך, נדבר על זה יחד בשיחת ההיכרות.</p>""",
                 intro="אפשר להגיע למפגש ריברסינג חד-פעמי, כחוויה בפני עצמה, או לסדרה קצרה.", hid="prices")
    fit = sec("למי זה מתאים ומתי לא?", duo(
        box("<h3>יכול להתאים לך כשאת מתמודדת עם</h3>" + rings_list([
            "סטרס או חרדה", "תחושת תקיעות", "עומס רגשי", "קושי לשחרר", "רצון להעמיק את החיבור לגוף ולעצמה"]), "sage"),
        box("<h3>חשוב לדעת: לא מתאים במקרים הבאים</h3>" + rings_list([
            "נשים בהריון", "לחץ תוך עיני (גלאוקומה)", "אבחנות פסיכיאטריות מסוימות", "התמודדות עם מחלת סרטן"])
            + '<p class="fine">ההתאמה לתהליך נבדקת מראש בשיחת ההיכרות. הרשימה אינה תחליף לייעוץ רפואי. אם יש מצב רפואי או נפשי רלוונטי, יש להתייעץ עם הגורם המטפל לפני המפגש.</p>', "clay"),
        stretch=True), hid="fit", wide=True)
    about = sec("נעים להכיר", """<p>אני משלבת בעבודה שלי שיח טיפולי עם כלים מעולמות הגוף, הנשימה, מערכת העצבים, מיינדפולנס וגישות טיפוליות נוספות.</p>
<p>העבודה שלי מבוססת על מקצועיות, קבלה, התאמה אישית והקשבה לקצב של מי שנמצאת מולי. מקום לגוף. מקום לרגש. מקום לקצב שלך.</p>""")
    form = form_sec("הצעד הראשון הוא פשוט לדבר", "<p>אפשר להשאיר פרטים ואחזור אלייך עד 48 שעות לתיאום שיחת היכרות של כ-20 דקות, ללא עלות. בשיחה תוכלי לספר לי בקצרה מה מביא אותך, לשאול שאלות ולבדוק יחד אם זה התהליך שמתאים לך.</p>", lead_form("breathwork"))
    return layout(
        "/breathwork",
        "ריברסינג ונשימה מעגלית בהרצליה",
        "ריברסינג ונשימה מעגלית בקליניקה בהרצליה. מפגש של 90 דקות, עם בדיקת התאמה מראש.",
        head + assemble(what, session, prices, fit, about, form),
        active="/breathwork",
    )


def product_meta(p):
    kind = "סדנה" if p["kind"] == "workshop" else "קורס"
    status = "ההרשמה פתוחה" if p.get("status") == "open" else "הרשמה בקרוב"
    return f"{kind}, {status}"


# photos for workshop pages that have one that fits
PRODUCT_PHOTO = {"calm-in-the-storm": ("/static/img/meditation-standing.jpg", "אנה לי עומדת בעיניים עצומות, ידיים פתוחות לצדדים, בנשימה")}

PRODUCT_SKETCH = {"calm-in-the-storm": "meditation", "nervous-system-course": "workbooks", "rebirthing-after-birth": "group"}


def page_workshops():
    head = page_head(
        "סדנאות וקורסים", "ללמוד, לתרגל, ולהרגיש פחות לבד",
        lead="הסדנאות והקורסים הקבוצתיים מציגים את החרדה ומערכת העצבים, ומלמדים כלים מעשיים לוויסות.",
        media=media_photo("/static/img/workshops-group.jpg", "סדנה קבוצתית תחת סככת קש: משתתפים שוכבים על מזרנים צבעוניים", wide=True, pos="50% 50%", slot="workshops"), variant="side wide", ground=boho.ground_workshops(),
    )
    items = sec("", cards([
        card(p["title"], f"/workshops/{p['slug']}", E(p["summary"]), meta=product_meta(p),
             mark=card_art(p["slug"]))
        for p in PRODUCTS
    ]), wide=True)
    later = sec("בהמשך", box(rings_list(["סדנאות נשימה", "סדנאות ייעודיות לנשים", "קורסים מקצועיים למטפלים"])
                            + '<p><a class="more" href="/free">לכלים החינמיים</a></p>'))
    return layout(
        "/workshops",
        "סדנאות וקורסים בנושא חרדה וויסות",
        "סדנאות וקורסים בנושא חרדה, ויסות מערכת העצבים וכלים מעשיים.",
        head + assemble(items, later),
        active="/workshops",
    )


def page_workshop(p):
    if p["slug"] == "rebirthing-after-birth":
        return page_birth_workshop(p)
    if p["slug"] == "calm-in-the-storm":
        return page_calm_landing(p)
    price = f"{p['price_ils']:,} ₪" if p.get("price_ils") else "המחיר יפורסם בקרוב"
    fl = ["סדנה" if p["kind"] == "workshop" else "קורס", price]
    if p.get("duration"):
        fl.append(E(p["duration"]))
    fl.append("הרשמה בקרוב" if p.get("status") != "open" else "ההרשמה פתוחה")
    head = page_head(
        '<a href="/workshops">סדנאות וקורסים</a>', p["title"], lead=E(p["summary"]),
        media=(media_photo(*PRODUCT_PHOTO[p["slug"]], wide=True, slot=p["slug"]) if p["slug"] in PRODUCT_PHOTO
               else media_art(boho.nervous_system())),
        variant=("side wide" if p["slug"] in PRODUCT_PHOTO else "side"),
        ground=(boho.ground_calm() if p["slug"] == "calm-in-the-storm" else ""),
    )
    body = f"<p>{E(p['audience'])}</p>"
    if p.get("points"):
        body += box("<h3>מה לומדים</h3>" + rings_list([E(x) for x in p["points"]]))
    parts = [sec("למי זה מתאים", body)]
    for s in p.get("sections", []):
        b = "".join(f"<p>{E(x)}</p>" for x in s.get("paragraphs", []))
        if s.get("list"):
            b += box(rings_list([E(x) for x in s["list"]]))
        parts.append(sec(s["heading"], b))
    parts.append(form_sec("להשאיר פרטים", "<p>אחזור אלייך עם פרטים על המועד והמחיר כשיתפרסמו.</p>", lead_form("workshop", item=p["title"])))
    return layout(f"/workshops/{p['slug']}", p["title"], p["summary"], head + assemble(*parts), active="/workshops")


# The workshop's own five icons (same line style as the lecture's, other drawings): it is a path of five steps
CALM_ICONS = [
    # 1. getting to know my anxiety: an open eye, and a quiet pulse line under it
    '''<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 54c12-20 28-30 48-30s36 10 48 30c-12 20-28 30-48 30S24 74 12 54z"/>
  <circle cx="60" cy="54" r="15" fill="currentColor" fill-opacity=".14"/>
  <circle cx="60" cy="54" r="5" fill="currentColor" stroke="none"/>
  <path d="M26 100h22l6-10 8 18 7-12 5 4h20" opacity=".65"/>
</svg>''',
    # 2. no longer fighting: open hands, holding what is there
    '''<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M18 66c0 20 18 34 42 34s42-14 42-34"/>
  <path d="M30 70c4 10 14 16 30 16s26-6 30-16" opacity=".55"/>
  <circle cx="60" cy="48" r="14" fill="currentColor" fill-opacity=".18"/>
  <path d="M60 22v-6M42 30l-4-4M78 30l4-4M30 48h-6M96 48h-6" opacity=".7"/>
</svg>''',
    # 3. getting to know what helps me: a flower of five petals
    '''<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <g transform="translate(60 56)" fill="currentColor" fill-opacity=".14">
    <ellipse cx="0" cy="-24" rx="11" ry="21"/>
    <ellipse cx="0" cy="-24" rx="11" ry="21" transform="rotate(72)"/>
    <ellipse cx="0" cy="-24" rx="11" ry="21" transform="rotate(144)"/>
    <ellipse cx="0" cy="-24" rx="11" ry="21" transform="rotate(216)"/>
    <ellipse cx="0" cy="-24" rx="11" ry="21" transform="rotate(288)"/>
  </g>
  <circle cx="60" cy="56" r="6" fill="currentColor" stroke="none"/>
  <path d="M60 94v14" opacity=".7"/>
</svg>''',
    # 4. supporting myself in everyday life: a sun rising over still water
    '''<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M14 78h92"/>
  <path d="M36 78a24 24 0 0 1 48 0" fill="currentColor" fill-opacity=".16"/>
  <path d="M60 36v-8M34 46l-6-5M86 46l6-5M20 62h-6M106 62h-6" opacity=".7"/>
  <path d="M26 92c8-5 14 5 22 0s14 5 22 0 14 5 22 0" opacity=".65"/>
</svg>''',
    # 5. my personal protocol: a compass
    '''<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="60" cy="60" r="40"/>
  <path d="M60 28l9 32-9 32-9-32z" fill="currentColor" fill-opacity=".2"/>
  <path d="M60 28v8M60 92v-8M28 60h8M92 60h-8" opacity=".7"/>
  <circle cx="60" cy="60" r="4" fill="currentColor" stroke="none"/>
</svg>''',
]

_EMPH = re.compile(r"(ביחד|ביטחון|הכלים|כלים|נתנסה|התנסות|תמיכה)")


def emph(text):
    """Soft emphasis on the words of the workshop: together, confidence, tools, experiencing, support."""
    return _EMPH.sub(r'<span class="lp-em">\1</span>', text)


def page_calm_landing(p):
    """The landing page of the workshop "רגועה בעין הסערה", in the soft design of the lecture
    (static/landing.css), with the site menu, but with its own character: five steps as a path,
    its own icons and a place of its own for the personal protocol. The copy comes from Anna Lee's
    brief (the docx of 19.11.2026) and her notes of 25.11.2026. Date: 27.12, 20:30. Price: 189 NIS,
    150 NIS for early registration until Thursday 3.12.2026 (after that the page shows only 189)."""
    title = p["title"]
    CTA = "אני רוצה ללמוד איך לתמוך בעצמי"

    def photo(name, cls, pos="", size=""):
        st = f"--calm-photo:url(/static/img/{name})" + (f";--pos:{pos}" if pos else "") + (f";--size:{size}" if size else "")
        return f'<div class="calm-photo {cls}" style="{st}" aria-hidden="true"></div>'

    hero = f"""<section class="lp-sec lp-hero calm-hero">
  {photo("calm-sunset-walk.jpg", "calm-photo-hero", "50% 55%")}
  <div class="lp-wrap lp-narrow calm-hero-text">
    <p class="lp-kicker">סדנת זום חווייתית</p>
    <h1 class="lp-title"><span class="lp-title-glow" aria-hidden="true"></span>{E(title)}</h1>
    <p class="lp-sub"><strong>החרדה לא חייבת לנהל אותך.</strong> <br>בואי נבין ביחד מה קורה לך בגוף ונלמד איך לתמוך בעצמנו גם כשהכול מרגיש יותר מדי.</p>
    <p class="lp-when"><strong>27.12</strong><span aria-hidden="true">·</span><strong>20:30</strong><span aria-hidden="true">·</span><strong>90 דקות</strong><span aria-hidden="true">·</span>בזום</p>
    <p class="lp-when-sub">ידע, תרגול וכלים לחיים</p>
    <p><a class="lp-btn" href="#register">{CTA}</a></p>
  </div>
</section>"""
    problem = f"""<section class="lp-sec lp-problem calm-problem">
  <div class="lp-wrap">
    <p>יכול להיות שאת מכירה את התחושה הזאת, <br>שהחיים ממשיכים כרגיל, את מתפקדת, עובדת, דואגת לכולם, <br>אבל משהו בתוכך מתקשה להרפות.</p>
    <p>גם ברגעים שבהם הכל בסדר, הגוף שלך עדיין דרוך. <br>לפעמים המחשבות לא מפסיקות לרוץ, <br>לפעמים את מוצפת מדברים שנראים קטנים <br>ולפעמים את פשוט מפחדת שהחרדה תגיע שוב.</p>
    <p>ואולי את כבר כל כך עסוקה בניסיון להימנע מהחרדה, <br>שאת מרגישה שהמאבק בה הפך להיות חלק מהיום־יום שלך.</p>
    <p><span class="lp-key">אם את מזהה את עצמך כאן, את ממש לא לבד.</span></p>
    <p>אפשר ללמוד להכיר את התגובות של הגוף שלך, <br>להבין מה הוא מנסה לספר לך <br>ולגלות איך לתמוך בעצמך ברגעים שבהם הכל מרגיש קצת יותר מדי.</p>
    <div class="lp-note">
      <span class="lp-note-flower" aria-hidden="true">{LP_MARK}</span>
      <p class="lp-hand">אפשר להפסיק להילחם בחרדה <br>וללמוד איך להיות שם בשביל עצמך כשהיא מגיעה.</p>
    </div>
  </div>
</section>"""
    mood = """<section class="lp-sec lp-mood calm-soft" aria-label="משפט מתוך הסדנה">
  <div class="lp-wrap lp-narrow">
    <p class="lp-hand lp-hand-xl">מה אם במקום להילחם בגוף שלך, <br>תלמדי לעבוד איתו?</p>
  </div>
</section>"""
    steps = [
        ("להכיר את החרדה שלי", "נעמיק בהבנה של מה שקורה בגוף ובמערכת העצבים בזמן חרדה ונלמד לזהות את הסימנים המוקדמים של הצפה."),
        ("להפסיק להילחם בחרדה", "נבין איך הפחד מהחרדה והניסיון להימנע ממנה יכולים להזין אותה, ונכיר דרכים אחרות לפגוש את מה שקורה לנו."),
        ("להכיר את מה שעוזר לי", "נלמד ונתנסה ביחד במגוון כלים מעשיים מעולמות הנשימה, הקרקוע והוויסות. נבדוק איך הגוף שלנו מגיב לכלים השונים ומה מרגיש לנו נכון."),
        ("לתמוך בעצמי גם בשגרה", "נבין איך אפשר לתמוך במערכת העצבים שלנו בתוך החיים העמוסים שאנחנו מנהלות, גם כשאנחנו לא נמצאות ברגע של חרדה."),
        ("לבנות את פרוטוקול הוויסות האישי שלי", "נאסוף את ההבנות והכלים מתוך הסדנה ונבנה תוכנית אישית, שתעזור לכל אחת לדעת איך לתמוך בעצמה כשהחרדה מגיעה וגם בשגרה."),
    ]
    journey = "".join(
        f'<li class="{"calm-final" if i == 5 else ""}"><span class="calm-ic" aria-hidden="true">{CALM_ICONS[i-1]}</span>'
        f'<div class="calm-step"><p class="calm-step-no">שלב {i}</p><h3>{E(t)}</h3><p>{emph(E(x))}</p></div></li>'
        for i, (t, x) in enumerate(steps, 1))
    plan = f"""<section class="lp-sec lp-plan calm-plan">
  <div class="lp-wrap lp-narrow">
    <h2>מה נלמד ונגלה ביחד?</h2>
    <p>אנחנו לא חייבות להעלים את החרדה כדי להרגיש יותר <span class="lp-em">ביטחון</span> בחיים שלנו. אנחנו יכולות ללמוד להבין אותה, לזהות מה קורה לנו כשהיא מגיעה, להכיר את <span class="lp-em">הכלים</span> שעוזרים לנו ולפתח בהדרגה את הביטחון ביכולת שלנו להתמודד איתה.</p>
    <ol class="calm-journey">{journey}</ol>
    <p class="calm-versus">״על קוצים״ היא טעימה והיכרות. בסדנה הזאת אנחנו מעמיקות: מתנסות ב<span class="lp-em">כלים</span> ובונות פרוטוקול אישי. גם מי שלא השתתפה ב״על קוצים״ יכולה להצטרף. <a class="more" href="/lectures/al-kotzim">להרצאה החינמית על קוצים</a></p>
    <p class="lp-soft lp-after-steps">יהיה מקום גם לשאלות. אין צורך בידע קודם.</p>
  </div>
</section>"""
    protocol_items = [
        "מהם הסימנים שהגוף שלך מתחיל לצאת מאיזון.",
        "אילו כלים עוזרים לך להתקרקע.",
        "מה יכול לתמוך בך ברגעים של הצפה.",
        "איך וממי את יכולה לבקש תמיכה.",
        "מה את יכולה לעשות בשגרה כדי לתמוך במערכת העצבים שלך.",
    ]
    protocol = f"""<section class="lp-sec calm-protocol">
  <div class="lp-wrap lp-narrow">
    <span class="calm-compass" aria-hidden="true">{CALM_ICONS[4]}</span>
    <p class="lp-hand lp-hand-lg">פרוטוקול ויסות אישי</p>
    <h2>כי ברגע של חרדה, <br>לא תמיד קל להיזכר במה שיכול לעזור לנו.</h2>
    <p>במהלך הסדנה תבני לעצמך פרוטוקול ויסות אישי, מעין מפת דרכים שתוכלי לחזור אליה ברגעים של חרדה והצפה.</p>
    <div class="calm-map">
      <p class="calm-map-title">ביחד נזהה:</p>
      <ul>{"".join(f"<li>{emph(E(x))}</li>" for x in protocol_items)}</ul>
    </div>
    <p>לכל אחת מאיתנו יש מערכת עצבים אחרת, היסטוריה אחרת וצרכים אחרים. לכן חשוב לי שלא תצאי רק עם רשימה של תרגילים, אלא עם <span class="lp-em">כלים</span> שלמדת להכיר ולהתאים לעצמך.</p>
  </div>
</section>"""
    fit_items = [
        "למי שמתפקדת מבחוץ אבל מרגישה מוצפת או דרוכה מבפנים.",
        "למי שחווה חרדה, התקפי חרדה או פחד מההתקף הבא.",
        "למי שהחרדה שלה נראית כמו עצבנות, התפרצויות, חשיבת יתר או קושי לנוח.",
        "למי שמתקשה עם חוסר ודאות ומרגישה שהיא חייבת להיות בשליטה.",
        "למי שרוצה כלים מעשיים שמערבים גם את הגוף, ולא רק הסברים או חשיבה חיובית.",
    ]
    fit = f"""<section class="lp-sec lp-for calm-for">
  {photo("calm-veil.jpg", "calm-photo-for", "50% 42%")}
  <div class="lp-wrap lp-narrow">
    <h2>למי הסדנה מתאימה?</h2>
    <ul class="calm-boxes">{"".join(f"<li>{E(x)}</li>" for x in fit_items)}</ul>
  </div>
</section>"""
    take = """<section class="lp-sec lp-take calm-take">
  <div class="lp-wrap lp-narrow">
    <p class="lp-hand lp-hand-lg">עם מה תצאי?</p>
    <p>עם הבנה בהירה יותר של החרדה שלך, <br>פחות בהלה מתגובות הגוף, <br>כמה דרכי ויסות שתוכלי להמשיך לתרגל, <br>פרוטוקול ויסות אישי שבנית בעצמך, <br><strong>ותחושה שיש לך אפשרות להשפיע על הדרך שבה את פוגשת רגעים קשים.</strong></p>
  </div>
</section>"""
    dream = f"""<section class="lp-sec lp-dream" aria-label="משפט מתוך הסדנה">
  {photo("calm-water-hand.jpg", "calm-photo-dream", "50% 45%")}
  <div class="lp-wrap lp-narrow">
    <p class="lp-hand lp-hand-xl">לא חיים בלי פחד, <br>אלא חיים שבהם הפחד כבר לא מנהל אותך.</p>
    <p class="lp-soft">אפשר להרגיש יציבה גם כשהכול מסביב סוער.</p>
  </div>
</section>"""
    story = """<section class="lp-sec lp-story calm-story">
  <div class="lp-wrap">
    <p class="lp-hand lp-hand-lg calm-story-title">עליי, והסיבה שהסדנה הזו כל כך קרובה לליבי</p>
    <div class="calm-story-grid">
      <div class="calm-story-text">
        <p>אני אנה לי מילשטיין, מטפלת רגשית בפסיכותרפיה הוליסטית ומרצה במכללת רידמן.</p>
        <p><strong>אבל חרדה היא לא משהו שאני מכירה רק מהלימודים או מהקליניקה.</strong></p>
        <p>לפני שנתיים חוויתי התקף חרדה כל כך מפחיד שהייתי בטוחה שזהו, השתגעתי, שעוד רגע מגיעים האנשים בחלוקים הלבנים לקחת אותי לאשפוז.</p>
        <p>אבל בתוך כל הפחד הזה ידעתי מה לעשות, איך להיתמך ואיך לתמוך בעצמי. הבנתי שמשהו עמוק השתנה בי לאורך השנים. התפתחה בי תחושת ביטחון ביכולת שלי להתמודד גם ברגעים שבהם אני מרגישה שאני מאבדת שליטה.</p>
      </div>
      <div class="calm-story-media">
        <span class="lp-glow lp-glow-about" aria-hidden="true"></span>
        <img class="calm-story-img" src="/static/img/anna-seated-cutout.png" alt="אנה לי מילשטיין יושבת בקליניקה" width="1035" height="1275" loading="lazy">
      </div>
    </div>
    <div class="lp-narrow calm-story-end">
      <div class="lp-note calm-quote-box"><p class="lp-hand lp-hand-lg">היום אני יודעת שיש לי אותי.</p></div>
      <p>בקליניקה אני מלווה אנשים שמתמודדים עם חרדה, דריכות והצפה, ועוזרת להם להכיר את הגוף שלהם, למצוא את הכלים שנכונים עבורם וללמוד לסמוך על עצמם גם ברגעים של קושי.</p>
      <p>וזאת בדיוק החוויה שאני רוצה לאפשר לך דרך הסדנה הזאת.</p>
    </div>
  </div>
</section>"""
    form = lead_form("workshop", item=title, register=True, button=CTA,
                     success="קיבלתי את הפרטים שלך. אחזור אלייך עם פרטי ההרשמה והתשלום.")
    price = """<div class="calm-price" data-early-until="2026-12-04T00:00:00+02:00">
      <div class="calm-price-row">
        <p class="calm-price-box"><span class="calm-price-label">מחיר מלא לסדנה</span><span class="calm-price-full">189 ₪</span></p>
        <p class="calm-price-box calm-price-early"><span class="calm-price-label">מחיר בהטבת הרשמה מוקדמת</span><span class="calm-price-now">150 ₪</span></p>
      </div>
      <p class="calm-price-note">ההטבה בתוקף עד יום חמישי, 3.12.2026, כולל.</p>
    </div>
    <script>(function(){var e=document.querySelector(".calm-price");if(e&&Date.now()>=Date.parse(e.getAttribute("data-early-until")))e.classList.add("ended")})();</script>"""
    register = f"""<section class="lp-sec calm-register lp-register" id="register">
  <div class="lp-wrap lp-narrow">
    <p class="lp-hand lp-hand-lg">ניפגש ב״רגועה בעין הסערה״</p>
    <h2>את לא צריכה לחכות שהחיים יירגעו <br><strong>כדי להתחיל להרגיש בהם יותר יציבה.</strong></h2>
    <p>אני מזמינה אותך להגיע כמו שאת, עם השאלות, החששות וכל מה שאת סוחבת. נלמד יחד להבין את הגוף, לפגוש את החרדה קצת אחרת ולתרגל דרכים לעזור לעצמנו.</p>
    <p class="lp-when"><strong>27.12</strong><span aria-hidden="true">·</span><strong>20:30</strong><span aria-hidden="true">·</span><strong>90 דקות</strong><span aria-hidden="true">·</span>בזום</p>
    {price}
    <div class="lp-form">{form}</div>
    <div class="lp-wa-direct">
      <p class="lp-hand">מתלבטת? אני זמינה עבורך</p>
      <a class="lp-wa-btn" href="{whatsapp_link()}" target="_blank" rel="noopener">{WA_ICON}לשליחת הודעה בוואטסאפ</a>
    </div>
    <p class="fine">אחזור אלייך עם פרטי ההרשמה והתשלום. <br>ההרשמה אינה מותנית באישור דיוור, ואפשר להסיר את עצמך מהרשימה בכל עת.</p>
    <div class="lp-wa">
      <p class="lp-hand">מתווסתים פה עם אנה לי מילשטיין</p>
      <p>קבוצת וואטסאפ שקטה למי שרוצה להכיר את מערכת העצבים שלה קצת יותר טוב. אני משתפת שם ידע בגובה העיניים, תרגולים קצרים, כלים להתמודדות עם חרדה והצפה ועדכונים על הרצאות וסדנאות. בלי רעש מיותר.</p>
      <a class="lp-wa-btn" href="{WHATSAPP_GROUP}" target="_blank" rel="noopener">{WA_ICON}להצטרפות לקבוצה השקטה</a>
    </div>
    <p class="fine lp-disclaimer">זו סדנה לימודית וחווייתית, לא תחליף לטיפול נפשי אישי או רפואי. תרגולים מותאמים לבחירה ולנוחות של המשתתפות.</p>
  </div>
</section>"""
    fonts = "".join(f'<link rel="preload" href="/static/fonts/{f}.ttf" as="font" type="font/ttf" crossorigin>'
                    for f in ("PloniRegular", "PloniYadRegular"))
    float_btn = LP_FLOAT.replace("שמרי לי מקום בהרצאה", CTA)
    return layout(
        f"/workshops/{p['slug']}",
        f"{title}: סדנת זום להבנת החרדה",
        "סדנת זום חווייתית בת 90 דקות: מבינים ביחד את החרדה, מתנסים בכלים לוויסות ובונים פרוטוקול ויסות אישי.",
        hero + problem + mood + plan + protocol + fit + take + dream + story + register + float_btn,
        active="/workshops",
        extra_head=fonts + '<link rel="stylesheet" href="/static/landing.css">',
        body_class="lp lp-calm",
    )


def page_birth_workshop(p):
    head = page_head(
        "סדנת ריברסינג לנשים אחרי לידה", "הלידה הסתיימה.",
        sub="אבל אולי משהו ממנה עדיין נשאר איתך.",
        extra="""<p>מרחב לעצור, לפגוש את חוויית הלידה שלך ולתת מקום למה שנשאר בגוף וברגש, באמצעות נשימה מודעת וליווי מקצועי.</p>
<p>לא משנה אם ילדת לפני חודשים או לפני שנים, ואם כבר דיברת על הלידה שלך. לפעמים משהו מהחוויה עדיין מבקש מקום.</p>"""
              + '<p class="fine">פרטי הסדנה יעודכנו בקרוב. לפני ההרשמה יש שאלון התאמה ושיחה אישית.</p>',
        media=media_photo("/static/img/session-kneeling.jpg", "אנה לי יושבת לצד משתתף ומלווה את תהליך הנשימה", pos="40% 70%", slot="birth-workshop"), variant="panel", ground=boho.ground_birth(),
        nav=toc([("room", "למה הסדנה"), ("flow", "איך נראה המפגש"), ("fit", "האם זה מתאים לך"), ("details", "פרטים")]),
    )
    room = sec("לא תמיד יש לנו מקום לעבד את מה שעברנו בלידה", """<p>אחרי הלידה החיים ממשיכים. יש תינוק או תינוקת לטפל בהם, שגרה חדשה להתרגל אליה, והרבה פעמים כל תשומת הלב עוברת למה שקורה עכשיו.</p>"""
               + "<p><strong class=\"key\">אבל מה איתך?</strong></p>" + """<p>אולי יש רגעים מהלידה שאת ממשיכה לחזור אליהם במחשבות. אולי משהו בה היה מפחיד, כואב, מציף או פשוט שונה ממה שדמיינת.</p>
<p>ואולי כבר דיברת על הלידה שלך, עברת עיבוד לידה, הבנת מה קרה שם, אבל את עדיין מרגישה שאת סוחבת משהו בתוכך.</p>
<p><strong class="key">לא חייבים לעבור לידה טראומטית כדי להרגיש שמשהו מהחוויה עדיין מבקש מקום.</strong></p>""", hid="room")
    breath = f"""<section class="sec tone-auto"><div class="wrap split">
  {print_photo("/static/img/breathwork-lying.jpg", "אישה שוכבת ונושמת במהלך תהליך ריברסינג", wide=True, pos="30% 50%", slot="birth-workshop-breath")}
  <div>
    <h2>לפעמים לא מספיק רק לדבר על מה שעברנו.</h2>
    <p>ריברסינג הוא תהליך של נשימה מודעת ורציפה, שעשוי לאפשר לפגוש תחושות ורגשות שלא תמיד נגישים דרך השיחה בלבד.</p>
    <p>תרגול נשימה אינטנסיבית אינו מתאים לכל אחת, ולכן נדרשת התאמה מקדימה.</p>
    <p>בסדנה ניצור מרחב קשוב, מכבד ולא שיפוטי שבו תוכלי לפגוש את חוויית הלידה בקצב שמתאים לך.</p>
  </div>
</div></section>"""
    flow = sec("איך נראה המפגש", steps([
        ("היכרות ותחושת ביטחון", "היכרות, הכנה לתרגול וביסוס תחושת ביטחון.", ""),
        ("נשימה מודעת", "תרגול נשימה מודעת בליווי ובהתאמה אישית, עם אפשרות להאט או לעצור.", ""),
        ("עיבוד וכתיבה", "זמן למנוחה, אינטגרציה ועיבוד של מה שעלה, לצד תרגיל כתיבה לעיבוד החוויה.", ""),
    ]) + callout("המטרה היא לא לשנות את מה שהיה, אלא לתת מקום לחוויה כפי שהיא נוכחת בך היום. אין חובה לשתף בקבוצה."),
        tone="deep-clay", hid="flow", wide=True)
    fit = sec("האם הסדנה מתאימה לך?", duo(
        box("""<h3>למי היא מתאימה?</h3>
<p>לכל אישה שילדה ומרגישה שמשהו מחוויית הלידה שלה עדיין נוכח בה.</p>
<p>אולי נשארו פחד, כעס, עצב, אכזבה או תחושה שמשהו שם לא נסגר. אולי כבר עברת עיבוד לידה, אבל עדיין מרגישה שאת סוחבת משהו בתוכך. ואולי אין לך מילים מדויקות לזה, רק תחושה שמשהו עדיין מבקש מקום.</p>
<p>לא משנה אם ילדת לפני כמה חודשים או לפני שנים. את לא צריכה לעבור לידה טראומטית כדי לרצות לעבד את חוויית הלידה שלך.</p>""", "sage"),
        box("<h3>למי הסדנה אינה מיועדת ללא בירור מתאים?</h3>" + rings_list([
            "נשים בהריון.",
            "נשים שעדיין בתקופת משכב הלידה.",
            "נשים עם לחץ תוך עיני מוגבר.",
            "נשים עם אבחנות פסיכיאטריות: נדרש בירור מקצועי והתאמה פרטנית.",
            "מצבים רפואיים ונפשיים נוספים, על פי שאלון ההתאמה.",
        ]) + '<p class="fine">ההשתתפות מותנית במילוי שאלון רפואי ובשיחת התאמה אישית.</p>', "clay"),
        stretch=True), hid="fit", wide=True)
    about = sec("נעים להכיר, אני אנה לי.", """<p>אני אנה לי מילשטיין, פסיכותרפיסטית הוליסטית, מטפלת רגשית ומנחת ריברסינג.</p>
<p>אני בעלת חמש שנות ניסיון בקליניקה, בוגרת ארבע שנות לימודי פסיכותרפיה הוליסטית במכללת רידמן, ומשלבת בעבודתי נשימה מודעת, מיינדפולנס, ACT, טיפול ממוקד חמלה וכלים מעבודה עם הגוף ומערכת העצבים.</p>
<p>אני מאמינה שלא כל מה שאנחנו עוברות אפשר לעבד רק דרך מילים. חשוב לי ליצור מרחב מקצועי, אנושי ולא שיפוטי, שבו אפשר לפגוש גם רגשות מורכבים בלי למהר לשנות אותם.</p>"""
                + "<p>בסדנה אני מזמינה אותך להביא את חוויית הלידה שלך, בדיוק כפי שהיא.</p>")
    soon = "יעודכן בקרוב"
    details = sec("לתת מקום גם לסיפור הלידה שלך.", tone="sage", body=tiles([
        ("תאריך", soon), ("שעה", soon), ("מיקום", soon), ("משך הסדנה", soon), ("מחיר", soon), ("מספר משתתפות", soon),
    ]) + "<p>ההרשמה כוללת שאלון בריאות ושיחת התאמה אישית לפני אישור ההשתתפות.</p>", hid="details", wide=True)
    form = form_sec("אני רוצה לתת מקום ללידה שלי",
                    "<p>ההרשמה תיפתח בקרוב. אפשר להשאיר פרטים כבר עכשיו, ואחזור אלייך כשייקבע מועד, יחד עם שאלון ההתאמה.</p>",
                    lead_form("workshop", item=p["title"], note_label="משהו שחשוב לך שאדע (אופציונלי)", button="להשארת פרטים"))
    return layout(f"/workshops/{p['slug']}", p["title"], p["summary"],
                  head + assemble(room, breath, flow, fit, about, details, form), active="/workshops")


def page_lectures():
    head = page_head(
        "הרצאות", "הרצאות שמביאות ידע וכלים לחיים",
        lead="הרצאה חינמית לכל מי שמרגישה שהחרדה מנהלת אותה, והרצאות לארגונים ולצוותי חינוך על סטרס ושחיקה.",
        media=media_art(boho.lectures()),
    )
    items = []
    for l in LECTURES:
        if l.get("free"):
            items.append(card(f"{l['name']}: {l['title']}", f"/lectures/{l['slug']}", E(l["summary"]),
                              meta=f'{E(l["meta"])}, {LECTURE_WHEN}', mark=kotzim_mark("lectures"), link="להרשמה חינמית", tint="event on-deep"))
        else:
            items.append(card(l["title"], f"/lectures/{l['slug']}", E(l["summary"]), meta=E(l["meta"]),
                              mark=card_art(l["slug"])))
    grid = sec("", cards(items), wide=True)
    cta = cta_sec("רוצים הרצאה לארגון?", "ספרו לי על הארגון ועל הקהל, ואחזור אליכם עם הצעה מתאימה.",
                  "/lectures/work-under-pressure#request", "לבקשת פרטים")
    return layout(
        "/lectures",
        "הרצאות על חרדה, סטרס ושחיקה",
        "הרצאה חינמית על חרדה בלייב, והרצאות לארגונים על סטרס, שחיקה וויסות מערכת העצבים.",
        head + assemble(grid, cta),
        active="/lectures",
    )


# Line drawings for the three steps of the lecture, in the hand colour of the page.
LP_ICONS = [
    # 1. understanding the body: a figure with the nervous system as a calm line through it, and the heart
    '''<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="60" cy="30" r="11"/>
  <path d="M40 104c0-26 6-48 20-52 14 4 20 26 20 52"/>
  <path d="M60 44v58" stroke-dasharray="1 6"/>
  <path d="M60 70c-5-6-14-3-12 4 2 6 12 11 12 11s10-5 12-11c2-7-7-10-12-4z" fill="currentColor" fill-opacity=".18"/>
  <path d="M18 66c6-6 10 6 16 0M86 66c6-6 10 6 16 0"/>
</svg>''',
    # 2. no longer fighting each feeling: the sharp line of the thorns softens into a wave and opens into a flower
    '''<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
  <g transform="translate(120 0) scale(-1 1)">
    <path d="M10 66l6-14 6 14 6-14 6 14 6-14 6 14c5-9 11-9 16 0s11 9 16 0 10-8 14-4"/>
    <path d="M94 58c2-10 0-18-4-24"/>
    <path d="M90 34c-6-2-10 2-9 7 5 1 9-2 9-7zM90 34c4-5 10-4 11 1-4 3-9 3-11-1zM90 34c0-6 4-9 8-8 0 5-3 8-8 8z" fill="currentColor" fill-opacity=".2"/>
    <circle cx="90" cy="34" r="2" fill="currentColor" stroke="none"/>
  </g>
</svg>''',
    # 3. tools for regulation: a leaf of breath, and the breath moving in soft lines
    '''<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M62 98C38 92 30 64 44 40c10-16 30-20 46-20 2 18-2 40-14 56-4 6-9 14-14 22z" fill="currentColor" fill-opacity=".14"/>
  <path d="M62 98c2-24 8-44 22-66"/>
  <path d="M70 62l-14-6M76 48l-12-6"/>
  <path d="M14 78c8 0 10-6 18-6M10 92c10 0 14-8 24-8" opacity=".6"/>
</svg>''',
]

# The quiet WhatsApp group for updates (announcements only)
WHATSAPP_GROUP = "https://chat.whatsapp.com/HudDWsgkCzMGpflVoHzecB"
WA_ICON = ('<svg class="lp-wa-icon" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2c-1.5 0-3-.4-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.5.1-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1 2.7c.1.2 1.8 2.8 4.4 3.9 1.6.7 2.3.8 3.1.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3z"/></svg>')

# The floating button on the landing page: shows once the hero's own button is gone, and steps
# aside when the form is on screen.
LP_FLOAT = """<a class="lp-float" href="#register" hidden>שמרי לי מקום בהרצאה</a>
<script>
(function () {
  var b = document.querySelector(".lp-float"), hero = document.querySelector(".lp-hero .lp-btn"),
      form = document.querySelector("#register .lp-form") || document.getElementById("register");
  if (!b || !("IntersectionObserver" in window)) { if (b) b.hidden = false; return; }
  b.hidden = false;
  var heroOn = true, formOn = false;
  function show() { b.classList.toggle("on", !heroOn && !formOn); }
  new IntersectionObserver(function (e) { heroOn = e[0].isIntersecting; show(); }).observe(hero);
  new IntersectionObserver(function (e) { formOn = e[0].isIntersecting; show(); }, { rootMargin: "0px 0px -15% 0px" }).observe(form);
})();
</script>"""


def page_free_lecture(l):
    """The landing page of the free lecture. Its own soft design (static/landing.css):
    Ploni and Ploni Yad, everything centred, sections that melt into each other,
    and Anna Lee cut out of her photo like a sticker."""
    when = f"{LECTURE_DAY} {LECTURE_DATE}"
    hero = f"""<section class="lp-sec lp-hero">
  <div class="lp-wrap lp-hero-grid">
    <div class="lp-hero-text">
      <p class="lp-kicker">הרצאה חינמית, בלייב בזום</p>
      <h1 class="lp-title"><span class="lp-title-glow" aria-hidden="true"></span>{E(l["name"])}</h1>
      <p class="lp-sub">למה הגוף שלך כל הזמן בכוננות <br><strong>ואיך מפסיקים לפחד מהחרדה</strong></p>
      <p class="lp-when"><strong>{E(when)}</strong><span aria-hidden="true">·</span><strong>{E(LECTURE_TIME)}</strong><span aria-hidden="true">·</span>בזום</p>
      <p><a class="lp-btn" href="#register">שמרי לי מקום בהרצאה</a></p>
    </div>
    <div class="lp-hero-media">
      <span class="lp-glow" aria-hidden="true"></span>
      <img class="lp-sticker" src="/static/img/anna-chair-cutout.png" alt="אנה לי מילשטיין יושבת בכורסה ומחייכת" width="1209" height="1313">
    </div>
  </div>
</section>"""
    problem = f"""<section class="lp-sec lp-problem">
  <div class="lp-wrap lp-narrow">
    {kotzim_fig("page")}
    <h2>מבחוץ את מתפקדת. <br><strong>מבפנים הגוף לא תמיד מקבל את ההודעה שהכול בסדר.</strong></h2>
    <p>אולי את מכירה את הרגע הזה שבו הלב מתחיל לדפוק מהר, המחשבות רצות, הגוף מתכווץ, <br>ואת רק רוצה שזה כבר יעבור.</p>
    <p>ואולי לפעמים החרדה בכלל לא כאן, <br><strong>אבל את כבר עסוקה בלפחד מהרגע שבו היא תחזור.</strong></p>
    <div class="lp-note">
      <span class="lp-note-flower" aria-hidden="true">{LP_MARK}</span>
      <p class="lp-hand">זה מתיש. אבל אפשר ללמוד להבין את מה שקורה לך <br>ולהגיב לזה אחרת.</p>
    </div>
  </div>
</section>"""
    mood = """<section class="lp-sec lp-mood" aria-label="משפט מתוך ההרצאה">
  <div class="lp-wrap lp-narrow">
    <p class="lp-hand lp-hand-xl">מה אם במקום לנסות לשלוט בחרדה, <br>תלמדי מה לעשות כשהיא מגיעה?</p>
  </div>
</section>"""
    plan_items = [
        ("להבין מה קורה בגוף", "מה קורה למערכת העצבים כשהחרדה עולה, <br>ולמה לפעמים קשה להירגע <strong>גם כשאת יודעת שאין סכנה מיידית.</strong>"),
        ("להפסיק להילחם בכל תחושה", "איך הפחד מהחרדה עצמה עלול להעצים את המעגל, <br>ואיך אפשר <strong>להתחיל לשנות את התגובה אליו.</strong>"),
        ("להכיר כלים לוויסות", "התנסות בכלים פשוטים שעוזרים לגוף ולמערכת העצבים <br><strong>לחזור בהדרגה ליותר יציבות.</strong>"),
    ]
    plan = f"""<section class="lp-sec lp-plan">
  <div class="lp-wrap">
    <h2>מה נעשה בהרצאה</h2>
    <ol class="lp-steps">{"".join(f'<li><span class="lp-icon" aria-hidden="true">{LP_ICONS[i-1]}<span class="lp-num">{i}</span></span><h3>{E(t)}</h3><p>{p}</p></li>' for i, (t, p) in enumerate(plan_items, 1))}</ol>
  </div>
</section>"""
    gift = """<section class="lp-sec lp-gift">
  <div class="lp-gift-photo" aria-hidden="true"></div>
  <div class="lp-wrap lp-narrow">
    <p class="lp-hand lp-hand-lg">ובסוף, מתנה לקחת איתך</p>
    <h2>ערכת ויסות, עזרה ראשונה לרגעי הצפה</h2>
    <p>דף קצר ונגיש עם כלים שתוכלי לשמור כצילום מסך בטלפון, <br><strong>כדי שיהיה לך משהו לחזור אליו ברגעים שבהם קשה לחשוב בבהירות.</strong></p>
    <p class="lp-soft">את הערכה תקבלי בסיום ההרצאה החיה.</p>
  </div>
</section>"""
    about = """<section class="lp-sec lp-about">
  <div class="lp-wrap lp-about-grid">
    <div class="lp-about-media">
      <span class="lp-glow lp-glow-about" aria-hidden="true"></span>
      <img class="lp-sticker lp-sticker-sm" src="/static/img/anna-seated-cutout.png" alt="אנה לי מילשטיין יושבת בקליניקה" width="1035" height="1275" loading="lazy">
    </div>
    <div class="lp-about-text">
      <p class="lp-hand lp-hand-lg">נעים להכיר, אני אנה לי</p>
      <p>אני פסיכותרפיסטית הוליסטית, מטפלת רגשית ומנחת ריברסינג. <br>בקליניקה שלי בהרצליה ובזום אני מלווה נשים שמתמודדות עם חרדה, הצפה רגשית, מתח וקושי בוויסות.</p>
      <p>אני מאמינה שידע הוא חלק משמעותי מהיכולת שלנו להתמודד עם מה שקורה בתוכנו. <br><strong>כשמבינים מה קורה לנו, אפשר לפתח יותר אפשרויות בחירה, במקום להרגיש שהחרדה מנהלת אותנו.</strong></p>
    </div>
  </div>
</section>"""
    form = lead_form("free", item=FREE_TITLE_WEBINAR, register=True, button="שמרי לי מקום",
                     success="נרשמת להרצאה. מייל אישור עם קישור לזום יישלח אלייך לכתובת שמסרת.")
    register = f"""<section class="lp-sec lp-register" id="register">
  <div class="lp-wrap lp-narrow">
    <p class="lp-hand lp-hand-lg">{E(when)}, {E(LECTURE_TIME)}, בזום</p>
    <h2>שמרי לי מקום בהרצאה</h2>
    <p>החרדה לא חייבת להחליט בשבילך איך ייראה היום שלך. <br><strong>בואי להקדיש לעצמך 30 דקות של הבנה, תרגול וכלים ראשוניים.</strong></p>
    <div class="lp-form">{form}</div>
    <div class="lp-wa-direct">
      <p class="lp-hand">מתלבטת? אני זמינה עבורך</p>
      <a class="lp-wa-btn" href="{whatsapp_link()}" target="_blank" rel="noopener">{WA_ICON}לשליחת הודעה בוואטסאפ</a>
    </div>
    <p class="fine">אחרי ההרשמה יישלח אלייך מייל אישור עם קישור לזום. <br>ההרשמה אינה מותנית באישור דיוור, ואפשר להסיר את עצמך מהרשימה בכל עת.</p>
    <div class="lp-wa">
      <p class="lp-hand">לא מסתדר לך הפעם?</p>
      <p>מוזמנת להצטרף לקבוצת וואטסאפ שקטה, <br>ולשמוע על ההרצאות והמפגשים הבאים.</p>
      <a class="lp-wa-btn" href="{WHATSAPP_GROUP}" target="_blank" rel="noopener">{WA_ICON}להצטרפות לקבוצה השקטה</a>
    </div>
  </div>
</section>"""
    fonts = "".join(f'<link rel="preload" href="/static/fonts/{f}.ttf" as="font" type="font/ttf" crossorigin>'
                    for f in ("PloniRegular", "PloniYadRegular"))
    return layout(
        f"/lectures/{l['slug']}",
        f"{l['name']}: {l['title']}",
        "הרצאה חינמית בלייב, 30 דקות, אונליין: מה קורה בגוף כשהחרדה עולה, ואילו כלים עוזרים, ובסוף ערכת ויסות לשמירה בטלפון.",
        hero + problem + mood + plan + gift + about + register + LP_FLOAT,
        active="/lectures",
        extra_head=fonts + '<link rel="stylesheet" href="/static/landing.css">',
        body_class="lp",
        og_image="/static/img/og-kotzim.jpg",
        landing=True,
    )


def page_lecture(l):
    if l.get("edu"):
        head = page_head(
            E(l["meta"]), "הרצאה וסדנה לצוותי חינוך",
            lead="שחיקה, ויסות רגשי וכלים מעשיים להתמודדות עם עומס בתוך הצוות.",
            extra='<p class="fine">הפרטים יעודכנו בקרוב.</p>',
            media=media_art(boho.education()),
        )
        what = sec("על מה זה", """<p>ההרצאה והסדנה מיועדות לצוותי חינוך, ועוסקות בשחיקה, בוויסות רגשי ובכלים קצרים שאפשר ליישם בתוך יום העבודה.</p>
<p>הפרטים, כולל המועד, המשך והמחיר, יעודכנו בקרוב. אפשר להשאיר פרטים עכשיו, ואחזור אלייך.</p>""")
        form = form_sec("בקשת פרטים", "<p>ספרי לי על הצוות ועל המוסד, ואחזור אלייך.</p>",
                        lead_form("lecture", item=l["title"], note_label="ספרי קצת על הצוות והמוסד (אופציונלי)"), hid="request")
        return layout(f"/lectures/{l['slug']}", "הרצאה וסדנה לצוותי חינוך",
                      "הרצאה וסדנה לצוותי חינוך על שחיקה, ויסות רגשי וכלים להתמודדות עם עומס.",
                      head + assemble(what, form), active="/lectures")
    head = page_head(
        E(l["meta"]), l["title"],
        lead="הרצאה על סטרס, שחיקה, מערכת העצבים וכלים מעשיים להתמודדות בחיי העבודה.",
        media=media_photo("/static/img/meditation-hands-open.jpg", "אנה לי מילשטיין נושמת בעיניים עצומות, ידיים פתוחות", wide=True, pos="50% 40%", slot="work-under-pressure"), variant="side wide", ground=boho.ground_pressure(),
    )
    what = sec("על מה ההרצאה", """<p>ההרצאה עוסקת בסטרס ובשחיקה, בהבנה של מה שקורה למערכת העצבים כשהעומס גדל, ובדרכים קצרות ומעשיות לחזור לתחושת יציבות ולריכוז.</p>"""
               + callout("המטרה היא לא לבטל את הלחץ, אלא ללמוד לזהות אותו מוקדם, ולהתמודד איתו בלי שהוא ינהל את היום."))
    take = sec("מה המשתתפים לוקחים איתם", duo(
        box("<h3>מה לוקחים מההרצאה</h3>" + rings_list([
            "זיהוי מוקדם של עומס ושחיקה",
            "הבנת השפעת הלחץ על הגוף ועל הריכוז",
            "כלים קצרים שאפשר ליישם בין 2 ל-5 דקות",
            "התמודדות עם מצבי לחץ ואי ודאות",
            "טיפוח חוסן אישי וארגוני",
        ])),
        box("""<h3>למי ההרצאה מתאימה</h3>
<p>למנהלות משאבי אנוש, למנהלים, למוסדות חינוך ולארגונים שרוצים להביא לצוותים שלהם כלים להתמודדות עם עומס.</p>
<p>גם לצוותי חינוך יש מקום להרצאה ולסדנה, בדגש על שחיקה, ויסות רגשי וכלים להתמודדות עם עומס.</p>
<p><a class="more" href="/lectures/education-teams">להרצאה לצוותי חינוך</a></p>"""),
        stretch=True), wide=True)
    form = form_sec("בקשת פרטים והצעת מחיר", "<p>ספרי לי על הארגון ועל הקהל, ואחזור אלייך עם הצעה מתאימה.</p>",
                    lead_form("lecture", item=l["title"], note_label="ספרי קצת על הארגון והקהל (אופציונלי)"), hid="request")
    return layout(f"/lectures/{l['slug']}", l["title"],
                  "הרצאה לארגונים על סטרס, שחיקה וויסות מערכת העצבים. בקשת פרטים והצעת מחיר.",
                  head + assemble(what, take, form), active="/lectures")


def page_articles():
    head = page_head(
        "ספריית ידע מקצועית", "מאמרים",
        lead="ידע מקצועי בשפה פשוטה ואנושית, על חרדה, ויסות רגשי, טראומה, גבולות ושחיקה.",
        media=media_art(boho.articles()),
    )
    listing = """<section class="sec tone-light articles-index" data-article-list><div class="wrap">
  <label class="search">חיפוש מאמרים<input type="search" placeholder="למשל: חרדה, נשימה, גבולות"></label>
  <div class="filters" hidden></div>
  <div class="grid cols-3"></div>
  <div class="empty" hidden>המאמרים הראשונים יתפרסמו בקרוב.</div>
  <p><button class="btn ghost" type="button" data-more hidden>טעינת מאמרים נוספים</button></p>
</div></section>"""
    return layout("/articles", "מאמרים על חרדה, ויסות רגשי וטראומה",
                  "ספריית מאמרים מקצועית על חרדה, ויסות רגשי, התקפי זעם, טראומה, גבולות ושחיקה.",
                  head + listing, active="/articles")


def page_article_template():
    main = """<section class="ph"><div class="wrap article-wrap">
  <p class="kicker"><a href="/articles">כל המאמרים</a></p>
  <article data-article-slug="">
    <h1></h1>
    <p class="byline" data-byline></p>
    <div class="article-body" data-body></div>
    <div class="sources" data-sources hidden><strong>מקורות</strong><ul></ul></div>
    <p class="article-next"><a class="more" href="/contact">לשיחת היכרות ללא עלות</a></p>
    <div data-related hidden><h2>מאמרים קשורים</h2><ul></ul></div>
  </article>
</div></section>"""
    return layout("/articles/_template", "מאמר", "מאמר מקצועי מאנה לי מילשטיין.", main, active="/articles", noindex=True)


def page_contact():
    wa = whatsapp_link()
    wa_btn = f'<a class="btn ghost" href="{E(wa)}" rel="noopener">לשלוח הודעה בוואטסאפ</a>' if wa else ""
    head = page_head(
        "יצירת קשר", "שיחת היכרות",
        lead=f"שיחת היכרות של כ-{CFG['intro_call_minutes']} דקות, ללא עלות. אחזור אלייך בתוך {E(CFG['response_time'])}.",
        extra=chips([f"קליניקה ב{E(CFG['clinic_location'])}", "או בזום", "ללא עלות"]) + f'<div class="actions">{wa_btn}</div>',
        media=media_photo("/static/img/about-chair.jpg", "אנה לי מילשטיין יושבת בכורסה בקליניקה", pos="50% 30%", slot="contact"), variant="panel", ground=boho.ground_contact(),
    )
    form = form_sec("השאירי פרטים", f"<p>אפשר גם להתקשר או לכתוב:</p>{contact_lines()}", lead_form("therapy", choose=True), hid="form")
    return layout("/contact", "יצירת קשר ושיחת היכרות", "השאירי פרטים לשיחת היכרות ללא עלות עם אנה לי מילשטיין.",
                  head + form, active="/contact")


def page_tashlich():
    head = page_head(
        "מתנה אישית לקראת השנה החדשה", "טקס תשליך אישי על חוף הים",
        sub="מה את בוחרת לא לקחת איתך לשנה החדשה?",
        extra="""<p>טקס תשליך אישי, קצר וחינמי, שיעזור לך לעצור, להתבונן בשנה שחלפה ולבחור מה תרצי לקחת איתך הלאה. הטקס יישלח אלייך מיד לאחר ההרשמה.</p>"""
              + chips(["ללא עלות", "מסמך דיגיטלי", "בזמן ובקצב שלך"])
              + '<div class="actions"><a class="btn" href="#get">לקבלת הטקס</a></div>',
        media=media_art(boho.tashlich()),
    )
    why = sec("לפעמים אנחנו ממשיכות לשאת דברים שכבר מעייפים אותנו", """<p>מחשבה שלא עוזבת, פחד שמעכב, כעס ישן, אשמה, ביקורת עצמית או הרגל שכבר לא מתאים לך.</p>
<p>אנחנו רגילות להמשיך, לתפקד ולעבור לדבר הבא. אבל עמוק בפנים עולה הצורך לעצור ולשאול בכנות: ממה אני כבר מוכנה להיפרד?</p>"""
              + "<p>לא צריך לדעת מראש את כל התשובות. רק להסכים לרגע להקשיב.</p>")
    lighter = sec("להיכנס לשנה החדשה מעט קלה, בהירה ומדויקת יותר", """<p>הטקס מאפשר לך לעצור בתוך רצף החיים, לתת מקום למה שאת מרגישה ולזהות מה מכביד עלייך.</p>
<p>באמצעות שאלות פשוטות וכתיבה אישית, תוכלי לנסח את מה שאת רוצה להניח ולבחור את הכוונות שאיתן תרצי להיכנס לשנה החדשה.</p>
<p>זה אינו ניסיון למחוק את מה שהיה או לפתור הכול ברגע אחד, אלא רגע סמלי ומשמעותי של הכרה, בחירה והתחלה חדשה.</p>""")
    inside = sec("מה מחכה לך במסמך", box(rings_list([
        "טקס שלם, פשוט ונגיש",
        "פתיחה קצרה והכנה לטקס",
        "שאלות נגישות להתבוננות בשנה שעברה",
        "זיהוי הדברים שמכבידים עלייך",
        "כתיבה על הדברים שאת מבקשת לשחרר",
        "בחירה במה שתרצי לקחת איתך לשנה החדשה",
        "ניסוח כוונות ורצונות לשנה הקרובה",
        "פעולה סמלית של השלכה ושחרור",
    ], two=True)) + callout("״שחרור לא אומר למחוק את מה שהיה, אלא לבחור בעדינות איך אנחנו רוצות להמשיך מכאן.״"))
    how = sec("איך הטקס עובד", steps([
        ("לעצור", "להקדיש לעצמך רגע ולהתבונן בשנה שעברה.", ""),
        ("להכיר", "לזהות בכנות ובחמלה את מה שמכביד עלייך כיום.", ""),
        ("לבחור", "להניח את מה שאינך רוצה לשאת ולנסח את מה שתרצי לטפח.", ""),
    ]), tone="deep-clay", intro="שלושה צעדים עדינים פנימה.", wide=True)
    about = sec("נעים להכיר", duo(
        box("<h3>למה יצרתי את הטקס?</h3><p>ראש השנה הוא הזדמנות טבעית לעצור ולעשות חשבון נפש. פעמים רבות אנחנו מתמקדות במה שנרצה להשיג ולהוסיף, ושוכחות לשאול מה אנחנו כבר לא רוצות לקחת איתנו. יצרתי את הטקס כדי לתת לנשים רגע פשוט ונגיש לפגוש את עצמן בכנות ובחמלה.</p>"),
        box("""<h3>אנה לי מילשטיין</h3><p>פסיכותרפיסטית הוליסטית ומטפלת רגשית בנשים. בקליניקה שלי בהרצליה ובזום אני מלווה נשים שמתמודדות עם חרדה, הצפה רגשית, ביקורת עצמית ותחושה שהן חזקות ומתפקדות כלפי חוץ, אבל בפנים כבר עייפות מלסחוב הכול לבד.</p>
<p>בעבודה שלי אני משלבת שיח טיפולי, מיינדפולנס, עבודה עם הגוף והנשימה וכלים לוויסות מערכת העצבים. יצרתי את הטקס מתוך רצון להנגיש רגע של התבוננות וחיבור פנימי גם מחוץ לחדר הטיפולים.</p>"""),
        stretch=True), wide=True)
    form = form_sec("מתנה אישית, ללא עלות",
                    "<p>קחי לעצמך רגע של עצירה. השאירי פרטים וקבלי את טקס התשליך האישי בחינם. אפשר לעשות אותו בבית, בטבע או ליד הים, בזמן ובקצב שלך.</p>"
                    "<p class=\"fine\">הפרטים שלך יישמרו לצורך שליחת הטקס ועדכונים הקשורים אליו. ההסכמה לדיוור שיווקי נפרדת ואופציונלית, ואפשר להסיר את עצמך בכל עת.</p>",
                    lead_form("free", item=FREE_TITLE_TASHLICH, register=True, button="לקבלת הטקס", success="תודה. הטקס נפתח עכשיו.",
                              next_page=GIFTS["tashlich-ritual"]["page"]),
                    hid="get")
    return layout("/tashlich", "טקס תשליך אישי על חוף הים",
                  "טקס תשליך אישי, קצר וחינמי, לקראת השנה החדשה. לעצור, להתבונן ולבחור מה לקחת איתך הלאה.",
                  head + assemble(why, lighter, inside, how, about, form), active="/free")


def page_free():
    head = page_head(
        "כלים חינמיים", "כלים חינמיים להרגעה",
        lead="כלים קצרים ופשוטים, לשמור בטלפון ולחזור אליהם ברגעים שקשה.",
        extra="<p>הרצאה בלייב, ערכת עזרה ראשונה, חוברות עבודה, טקס תשליך ומדיטציה מודרכת. הכול ללא עלות.</p>",
        media=media_art(boho.free_head()),
    )
    items = [card("על קוצים: הרצאה חינמית בזום", "/lectures/al-kotzim",
                  "למה הגוף שלך כל הזמן בכוננות, ואיך מפסיקים לפחד מהחרדה. 30 דקות בלייב, ובסוף ערכת ויסות לשמור בטלפון.",
                  meta=f"הרצאה בזום, {LECTURE_WHEN}", mark=kotzim_mark("free"), link="להרשמה", tint="event on-deep")]
    for f in FREE:
        if f["slug"] == "intro-lecture":
            continue
        href, label = FREE_LINKS.get(f["slug"], ("#get", "לקבלה"))
        items.append(card(f["title"], href, E(f["summary"]), mark=card_art(f["slug"]), link=label))
    if CFG.get("meditation_url"):
        items.append(card("מדיטציה מודרכת לפתיחת הבוקר", E(CFG["meditation_url"]), "כמה דקות של נשימה ושקט לפני שהיום מתחיל. להאזנה בספוטיפיי.",
                          mark=card_art("meditation"), link="להאזנה", external=True, tint="clay"))
    tools = sec("", cards(items), wide=True)
    options = [(f["title"], GIFTS.get(f["slug"], {}).get("page", "")) for f in FREE if f["slug"] not in ("intro-lecture", "tashlich-ritual")]
    form = form_sec("לקבלת הכלים", "<p>הכלים נשלחים למייל שתמסרי. ההסכמה לתוכן שיווקי נפרדת ואופציונלית, ואינה נדרשת לקבלת הכלים.</p>",
                    lead_form("free", note_label="הערה (אופציונלי)", extra_select=options), hid="get")
    return layout("/free", "כלים חינמיים להרגעה", "ערכת עזרה ראשונה, חוברות עבודה, טקס תשליך ומדיטציה מודרכת. כלים חינמיים בנושא חרדה וויסות.",
                  head + assemble(tools, form), active="/free")


# The free files. After the form is sent, the visitor lands on the gift's own page,
# which opens the PDF once it is placed in static/files/<file>.
GIFTS = {
    "tashlich-ritual": {"page": "/tashlich-thanks", "file": "tashlich.pdf", "kicker": "טקס תשליך אישי",
                        "ready": "תודה, הטקס שלך כאן", "ready_lead": "אפשר לפתוח אותו עכשיו, לשמור, ולחזור אליו בזמן ובקצב שלך."},
    "first-aid-kit": {"page": "/first-aid-kit-thanks", "file": "first-aid-kit.pdf", "card": "first-aid-kit-card.jpg", "kicker": "ערכת עזרה ראשונה",
                      "ready": "תודה, הערכה שלך כאן", "ready_lead": "אפשר לפתוח אותה עכשיו, לשמור בטלפון, ולחזור אליה ברגע שצריך."},
}


GIFT_ART = {"tashlich-ritual": boho.gift_tashlich, "first-aid-kit": boho.gift_kit}


def page_gift(slug):
    g = GIFTS[slug]
    pdf = f"/static/files/{g['file']}"
    if (ROOT / "static" / "files" / g["file"]).exists():
        head = page_head(g["kicker"], g["ready"], lead=g["ready_lead"],
                         extra=f'<div class="actions"><a class="btn" href="{pdf}" target="_blank" rel="noopener">לפתיחת הקובץ</a>'
                               f'<a class="more" href="{pdf}" download>להורדה</a></div>',
                         media=media_art(GIFT_ART[slug]()))
        body = ""
        if g.get("card"):
            card_src = f"/static/files/{g['card']}"
            body += f"""<section class="sec tone-sage"><div class="wrap split">
  <figure class="print gift-card"><div class="frame"><img src="{card_src}" alt="כרטיס סיכום: מישהו לידי בחרדה, מה אפשר לעשות? ארבעה צעדים: לשים לב, להיות שם, להציע קרקוע, להחזיר בחירה" loading="lazy"></div></figure>
  <div>
    <h2>כרטיס הסיכום, לשמור בטלפון</h2>
    <p>ארבעת הצעדים של הערכה בעמוד אחד: לשים לב, להיות שם, להציע קרקוע ולהחזיר בחירה. הכרטיס נמצא גם בעמוד האחרון של הערכה.</p>
    <p>בטלפון: לחיצה ארוכה על הכרטיס ושמירה לתמונות.</p>
    <div class="actions"><a class="btn" href="{card_src}" download>להורדת הכרטיס</a></div>
  </div>
</div></section>"""
        body += sec("", f'<object class="pdf-view" data="{pdf}" type="application/pdf" aria-label="{E(g["kicker"])}">'
                        f'<p>אפשר לפתוח את הקובץ בכפתור למעלה.</p></object>', tone="light", wide=True)
    else:
        head = page_head(g["kicker"], "תודה, הפרטים התקבלו", lead="הקובץ עדיין בהכנה, והוא יופיע בעמוד הזה בקרוב.",
                         extra='<div class="actions"><a class="more" href="/free">לכלים החינמיים</a></div>',
                         media=media_art(GIFT_ART[slug]()))
        body = ""
    return layout(g["page"], g["kicker"], g["ready_lead"], head + body, active="/free", noindex=True)


def page_legal(path, title, body):
    head = page_head("", title)
    main = head + f'<section class="sec tone-light"><div class="wrap legal-body">{body}</div></section>'
    return layout(path, title, f"{title} של אנה לי מילשטיין.", main, noindex=True)


def _legal(key, what):
    """A business detail for the legal pages, or a visible marker until Anna Lee supplies it."""
    v = str(CFG.get("legal", {}).get(key, "") or "").strip()
    return E(v) if v else f'<mark class="todo">[להשלמה: {E(what)}]</mark>'


def _owner():
    """Who runs the site, as the legal pages name her."""
    return (f"{_legal('business_name', 'שם העסק או השם המלא')}, "
            f"{_legal('business_id', 'מספר עוסק או ת.ז.')}, "
            f"{_legal('business_address', 'כתובת למשלוח דואר')}")


def _contact():
    return (f'מייל: <a href="mailto:{E(CFG["email"])}">{E(CFG["email"])}</a>, '
            f'טלפון: <a href="tel:{E(CFG["phone"])}">{E(CFG["phone"])}</a>')


def privacy_body():
    L = CFG.get("legal", {})
    return f"""
<p>מדיניות זו מסבירה אילו פרטים נאספים באתר של אנה לי מילשטיין, למה, אצל מי הם נשמרים ומה הזכויות שלך.
היא נכתבה לפי חוק הגנת הפרטיות, התשמ"א-1981, ותיקון 13 לחוק, ולפי תקנות הגנת הפרטיות (אבטחת מידע), התשע"ז-2017.
המדיניות מנוסחת בלשון נקבה מטעמי נוחות, והיא מתייחסת לכל המינים.</p>
<p><strong>עדכון אחרון:</strong> {E(L.get("updated", ""))}</p>

<h2>מי אחראית על המידע</h2>
<p>האתר והמידע שנאסף בו באחריות: {_owner()}.<br>{_contact()}.</p>

<h2>אילו פרטים נאספים</h2>
<ul>
<li><strong>בטופס פנייה:</strong> שם, טלפון, מייל, השירות שמעניין אותך, והודעה אם בחרת לכתוב אחת.</li>
<li><strong>בהרשמה להרצאה או לסדנה:</strong> שם, מייל, וטלפון אם בחרת למסור.</li>
<li><strong>בהורדת תוכן חינמי:</strong> שם ומייל.</li>
<li><strong>הסכמה לדיוור:</strong> האם סימנת שאת מסכימה לקבל תכנים והצעות. התיבה אינה מסומנת מראש.</li>
<li><strong>מידע טכני:</strong> שרת האתר רושם באופן אוטומטי נתונים בסיסיים כמו כתובת IP, סוג הדפדפן ושעת הביקור, לצורך תפעול ואבטחה בלבד.</li>
</ul>
<p><strong>אין חובה חוקית למסור את הפרטים.</strong> בלי שם ודרך ליצירת קשר לא אוכל לחזור אלייך או לרשום אותך.</p>
<p><strong>מידע רגיש:</strong> אין צורך לפרט בטופס מידע רפואי או נפשי. אם בחרת לכתוב מידע כזה בהודעה, הוא יישמר בסודיות ובאבטחה מוגברת וישמש רק כדי לחזור אלייך.</p>

<h2>למה הפרטים נאספים</h2>
<ul>
<li>כדי לחזור אלייך לגבי הפנייה ולתאם שיחה או פגישה.</li>
<li>כדי לרשום אותך להרצאה או לסדנה, ולשלוח לך מייל אישור, תזכורות וחומרים שהובטחו (למשל קישור לזום או ערכה להורדה).</li>
<li>כדי לשלוח לך תכנים, עדכונים והצעות, <strong>רק אם נתת לכך הסכמה נפרדת</strong>.</li>
<li>כדי לתפעל את האתר, לשמור על אבטחתו ולעמוד בדרישות החוק.</li>
</ul>
<p>הפרטים לא נמכרים ולא מועברים לאחרים לשימוש שלהם.</p>

<h2>מי עוד מקבל גישה לפרטים</h2>
<p>הפרטים נשמרים אצלי, ובנוסף אצל ספקי שירות שעוזרים לי להפעיל את האתר, ורק במידה הנדרשת לכך:</p>
<ul>
<li><strong>Brevo</strong>: מערכת לשליחת מיילים ולניהול רשימות דיוור. השרתים שלה נמצאים באיחוד האירופי.</li>
<li><strong>חברת אחסון האתר</strong>, שבשרתיה פועל האתר ונשמרות הפניות.</li>
<li><strong>Zoom</strong>: אם נרשמת להרצאה, תצטרפי אליה דרך קישור. ההצטרפות כפופה למדיניות הפרטיות של Zoom.</li>
<li><strong>WhatsApp</strong>: אם בחרת לפנות בוואטסאפ או להצטרף לקבוצה, השיחה כפופה למדיניות הפרטיות של WhatsApp.</li>
</ul>
<p>ייתכן שהמידע יישמר על שרתים מחוץ לישראל, במדינות שבהן רמת ההגנה על מידע אישי מוכרת כמתאימה.</p>

<h2>דיוור והסרה מרשימת התפוצה</h2>
<p>מיילים ותכנים שיווקיים נשלחים רק למי שנתנה הסכמה מפורשת, לפי סעיף 30א לחוק התקשורת (בזק ושידורים).
בכל מייל שיווקי יש אפשרות להסרה. אפשר גם להשיב למייל או לכתוב אלי, ואסיר אותך מהרשימה.</p>
<p>מיילים שקשורים ישירות לשירות שביקשת, כמו אישור הרשמה ותזכורת לפני הרצאה, יישלחו גם בלי הסכמה לדיוור.</p>

<h2>עוגיות ואחסון בדפדפן</h2>
<p>האתר לא משתמש בעוגיות פרסום, בכלי מעקב או בכלי ניתוח של צד שלישי.
האתר שומר בדפדפן שלך רק את העדפות הנגישות שבחרת (למשל גודל טקסט), כדי שיישארו גם בביקור הבא. אפשר למחוק אותן בכל עת דרך תפריט הנגישות או בהגדרות הדפדפן.</p>

<h2>כמה זמן הפרטים נשמרים</h2>
<p>{E(CFG['privacy_retention']) if CFG.get('privacy_retention') else _legal('retention', 'כמה זמן שומרים פרטי פניות ונרשמות, למשל שנתיים מהפנייה האחרונה')}</p>

<h2>אבטחת מידע</h2>
<p>האתר פועל בחיבור מאובטח (HTTPS), הגישה לפניות מוגנת בסיסמה ומוגבלת לי בלבד, ואני נוקטת אמצעים סבירים כדי להגן על המידע.
אם יתברר שהייתה פגיעה באבטחת המידע, אפעל לפי מה שהחוק מחייב.</p>

<h2>הזכויות שלך</h2>
<ul>
<li>לעיין במידע שנשמר עלייך (סעיף 13 לחוק).</li>
<li>לבקש לתקן או למחוק מידע שאינו נכון, שלם, ברור או מעודכן (סעיף 14 לחוק).</li>
<li>לבקש שהמידע לא ישמש לדיוור ישיר, ולבקש להימחק מרשימת התפוצה (סעיף 17ו לחוק).</li>
</ul>
<p>כדי לממש את הזכויות, כתבי אלי: {_contact()}. אענה תוך 30 יום.</p>

<h2>שינויים במדיניות</h2>
<p>המדיניות עשויה להתעדכן מעת לעת. הנוסח המחייב הוא זה שמופיע בעמוד הזה, עם תאריך העדכון האחרון.</p>
"""


def accessibility_body():
    L = CFG.get("legal", {})
    return f"""
<p>אני רואה חשיבות רבה בכך שכל אחת ואחד יוכלו להשתמש באתר בנוחות, כולל אנשים עם מוגבלות.
האתר הותאם לפי תקנות שוויון זכויות לאנשים עם מוגבלות (התאמות נגישות לשירות), התשע"ג-2013,
ולפי התקן הישראלי 5568, שמבוסס על הנחיות WCAG 2.0, ברמה AA.</p>
<p><strong>עדכון אחרון של ההצהרה:</strong> {E(L.get("updated", ""))}</p>

<h2>מה הותאם באתר</h2>
<ul>
<li>אפשר לנווט בכל האתר עם המקלדת בלבד, והאלמנט שבפוקוס מסומן בבירור.</li>
<li>בראש כל עמוד יש קישור "מעבר לתוכן", שמדלג ישירות לתוכן העמוד.</li>
<li>מבנה העמודים מסודר בכותרות, רשימות ואזורים, כך שתוכנות הקראה מזהות אותו.</li>
<li>לתמונות יש טקסט חלופי, ותמונות קישוטיות מוסתרות מתוכנות הקראה.</li>
<li>לכל שדה בטופס יש תווית ברורה, והודעות הצלחה ושגיאה מוקראות.</li>
<li>הטקסט נקרא על רקע בניגודיות מספקת.</li>
<li>האתר מותאם לטלפון, לטאבלט ולמחשב, ואפשר להגדיל בו את הטקסט עד 200% בלי לאבד תוכן.</li>
<li>אנימציות נעצרות אוטומטית למי שהגדירה במכשיר "הפחתת תנועה".</li>
</ul>

<h2>תפריט הנגישות</h2>
<p>בכל עמוד יש כפתור נגישות קבוע בפינה. התפריט מאפשר:</p>
<ul>
<li>להגדיל ולהקטין את הטקסט.</li>
<li>לעבור לניגודיות גבוהה או לגווני אפור.</li>
<li>להדגיש קישורים ולהדגיש את הפוקוס של המקלדת.</li>
<li>לעבור לגופן פשוט וקריא יותר, ולהגדיל את המרווח בין השורות.</li>
<li>לעצור אנימציות ותנועה.</li>
<li>לאפס את כל ההגדרות בלחיצה אחת.</li>
</ul>
<p>ההגדרות נשמרות בדפדפן שלך, כך שיישארו גם בביקור הבא.</p>

<h2>מה עוד לא נגיש במלואו</h2>
<ul>
<li>תכנים חיצוניים שהאתר מקשר אליהם, כמו Zoom, WhatsApp, Instagram ו-Spotify, אינם בשליטתי, ורמת הנגישות שלהם נקבעת על ידי החברות שמפעילות אותם.</li>
<li>קבצים להורדה, כמו ערכות PDF, עדיין לא הונגשו במלואם. אפשר לבקש אותם בפורמט נגיש, ואשלח.</li>
</ul>
<p>בדיקת נגישות מקצועית ומלאה של האתר תיעשה לפני העלייה לאוויר, וההצהרה תעודכן לפי תוצאותיה. אני ממשיכה לבדוק ולשפר את הנגישות. אם מצאת משהו שלא עובד, אשמח לדעת.</p>

<h2>נגישות הקליניקה</h2>
<p>הקליניקה נמצאת ב{E(CFG['clinic_location'])}. {_legal('clinic_access', 'פרטי הנגישות הפיזית של הקליניקה: קומה, מעלית, חניית נכים, שירותים נגישים')}</p>
<p>מפגשים בזום זמינים כחלופה למי שמעדיפה.</p>

<h2>רכזת הנגישות ופנייה בנושא נגישות</h2>
<p>אם נתקלת בקושי, או שיש לך הצעה לשיפור, אפשר לפנות אלי:</p>
<p><strong>רכזת הנגישות:</strong> {_legal('accessibility_coordinator', 'שם רכזת הנגישות')}<br>{_contact()}</p>
<p>כדאי לצרף לפנייה תיאור קצר של הבעיה, את העמוד שבו היא קרתה ואת הדפדפן או תוכנת העזר שבהם השתמשת.
אחזור אלייך תוך {E(CFG.get('response_time', '48 שעות'))}.</p>
"""


def terms_body():
    L = CFG.get("legal", {})
    return f"""
<p>ברוכה הבאה לאתר של אנה לי מילשטיין. התקנון הזה מסדיר את השימוש באתר, את ההרשמה להרצאות ולסדנאות ואת קביעת הפגישות.
השימוש באתר מהווה הסכמה לתקנון. התקנון מנוסח בלשון נקבה מטעמי נוחות, והוא מתייחס לכל המינים.</p>
<p><strong>עדכון אחרון:</strong> {E(L.get("updated", ""))}</p>

<h2>1. מי מפעילה את האתר</h2>
<p>האתר מופעל על ידי: {_owner()}.<br>{_contact()}.</p>

<h2>2. מה יש באתר</h2>
<p>האתר מציג מידע על טיפול רגשי, פסיכותרפיה הוליסטית, ריברסינג, סדנאות והרצאות, וכולל מאמרים ותכנים חינמיים.
אפשר להשאיר בו פרטים ליצירת קשר, להירשם להרצאות ולהוריד תכנים.</p>

<h2>3. המידע באתר אינו תחליף לטיפול</h2>
<p>התכנים באתר, בהרצאות ובחומרים החינמיים נועדו להעשרה ולמידה כללית. הם אינם אבחון, ייעוץ רפואי או טיפול נפשי,
ואינם מחליפים פנייה לרופאה, לפסיכיאטר או לאיש מקצוע מוסמך.</p>
<p><strong>במצב של סכנה מיידית לך או לאחרים יש לפנות מיד למד"א בטלפון 101, למשטרה בטלפון 100, או לחדר מיון.
לתמיכה רגשית מיידית אפשר לפנות לער"ן בטלפון 1201.</strong></p>

<h2>4. הרשמה להרצאות ולסדנאות</h2>
<ul>
<li>ההרשמה נעשית בטופס באתר. אחרי ההרשמה יישלח אלייך מייל אישור.</li>
<li>הרצאות חינמיות מתקיימות בזום. קישור ההצטרפות נשלח במייל, והוא אישי ואין להעבירו לאחרים.</li>
<li>אלא אם נאמר אחרת, ההרצאות אינן מוקלטות. אין להקליט, לצלם או להפיץ את ההרצאה או את המשתתפות בה.</li>
<li>מועד, משך ותוכן של הרצאה או סדנה עשויים להשתנות. במקרה כזה אודיע מראש במייל.</li>
<li>הרשמה לסדנה בתשלום נעשית מול אנה לי ישירות. המחיר, המועדים ותנאי התשלום יימסרו לפני התשלום.</li>
</ul>

<h2>5. ביטול עסקה והחזרים</h2>
<p>ביטול עסקה בשירות שנרכש מרחוק (בטלפון, במייל או באתר) כפוף לחוק הגנת הצרכן, התשמ"א-1981, ולתקנות הגנת הצרכן (ביטול עסקה), התשע"א-2010:</p>
<ul>
<li>אפשר לבטל תוך 14 יום מיום ביצוע העסקה או מיום קבלת המסמך שמפרט את תנאיה, המאוחר מביניהם, ובלבד שהביטול נעשה לפחות 2 ימי עסקים לפני מועד תחילת השירות.</li>
<li>בביטול כזה יוחזר התשלום בניכוי דמי ביטול של 5% מהמחיר או 100 ש"ח, הנמוך מביניהם.</li>
<li>הודעת ביטול נשלחת במייל או בטלפון, לפרטים שבסעיף 1.</li>
<li>אם אני מבטלת הרצאה או סדנה, יוחזר מלוא התשלום.</li>
</ul>
<p>{_legal('refund_extra', 'מדיניות ביטול מעבר לחוק, אם יש: למשל ביטול סדנה פחות מ-2 ימי עסקים לפני מועדה, או מעבר למחזור הבא')}</p>

<h2>6. פגישות טיפול</h2>
<ul>
<li>פגישה נקבעת בתיאום אישי, בקליניקה ב{E(CFG['clinic_location'])} או בזום.</li>
<li>ביטול או שינוי של פגישה יש להודיע לפחות {E(str(L.get('session_cancel_hours', 24)))} שעות מראש. פגישה שבוטלה בהתראה קצרה יותר תחויב במלואה, למעט מקרים חריגים.</li>
<li>התשלום על פגישה מתבצע {_legal('payment_terms', 'מתי ואיך משלמים: בסוף הפגישה, בהעברה, בביט')}. תינתן קבלה כחוק.</li>
<li>כל מה שנאמר בפגישות נשמר בסודיות, למעט מקרים שבהם החוק מחייב אחרת, למשל סכנה ממשית לחיים.</li>
</ul>

<h2>7. קניין רוחני</h2>
<p>כל התכנים באתר, כולל טקסטים, מאמרים, איורים, תמונות, ערכות להורדה ומדיטציות, שייכים לאנה לי מילשטיין או לבעלי הזכויות בהם.
מותר לשתף קישור לעמוד או לשמור חומר לשימוש אישי. אסור להעתיק, לפרסם, למכור או להשתמש בתכנים לצורך מסחרי בלי אישור בכתב.</p>

<h2>8. קישורים ושירותים חיצוניים</h2>
<p>באתר יש קישורים לשירותים חיצוניים, כמו Zoom, WhatsApp, Instagram ו-Spotify. השימוש בהם כפוף לתנאים ולמדיניות הפרטיות שלהם,
ואין לי שליטה על התוכן או על הזמינות שלהם.</p>

<h2>9. פרטיות ודיוור</h2>
<p>הפרטים שנמסרים באתר נשמרים ומשמשים לפי <a href="/privacy">מדיניות הפרטיות</a>. מיילים שיווקיים נשלחים רק למי שהסכימה לכך, ובכל אחד מהם יש אפשרות להסרה.</p>

<h2>10. אחריות</h2>
<p>אני משתדלת שהמידע באתר יהיה מדויק ועדכני, ושהאתר יפעל בלי תקלות. עם זאת, ייתכנו טעויות, שינויים או הפסקות בפעילות האתר.
האחריות לשימוש בתכנים ובכלים שמוצגים באתר היא שלך, וכל אחת מוזמנת להתאים אותם לעצמה ולהתייעץ עם איש מקצוע במידת הצורך.</p>

<h2>11. שינויים בתקנון</h2>
<p>התקנון עשוי להתעדכן מעת לעת. הנוסח המחייב הוא זה שמופיע בעמוד הזה, עם תאריך העדכון האחרון.</p>

<h2>12. דין וסמכות שיפוט</h2>
<p>על התקנון ועל השימוש באתר חלים דיני מדינת ישראל. סמכות השיפוט הבלעדית נתונה לבתי המשפט המוסמכים במחוז תל אביב.</p>

<h2>13. יצירת קשר</h2>
<p>לכל שאלה על התקנון: {_contact()}.</p>
"""


def page_404():
    head = page_head("", "העמוד לא נמצא", lead="אפשר לחזור לדף הבית או לכל המאמרים.",
                     extra='<div class="actions"><a class="btn" href="/">לדף הבית</a><a class="more" href="/articles">למאמרים</a></div>',
                     media=media_art(boho.lost()))
    return layout("/404", "העמוד לא נמצא", "העמוד לא נמצא.", head, noindex=True)


# ---------- build ----------

def build():
    if SITE.exists():
        for child in SITE.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    SITE.mkdir(exist_ok=True)

    write("index.html", page_home())
    write("about.html", page_about())
    write("therapy.html", page_therapy())
    write("breathwork.html", page_breathwork())
    write("workshops.html", page_workshops())
    write("lectures.html", page_lectures())
    for l in LECTURES:
        write(f"lectures/{l['slug']}.html", page_free_lecture(l) if l["free"] else page_lecture(l))
    write("articles.html", page_articles())
    write("article.html", page_article_template())
    write("contact.html", page_contact())
    write("free.html", page_free())
    write("tashlich.html", page_tashlich())
    for slug, g in GIFTS.items():
        write(g["page"].strip("/") + ".html", page_gift(slug))
    write("privacy.html", page_legal("/privacy", "מדיניות פרטיות", privacy_body()))
    write("accessibility.html", page_legal("/accessibility", "הצהרת נגישות", accessibility_body()))
    write("terms.html", page_legal("/terms", "תקנון האתר", terms_body()))
    write("404.html", page_404())
    for p in PRODUCTS:
        write(f"workshops/{p['slug']}.html", page_workshop(p))

    # sitemap and robots, only when the site is public
    urls = ["/", "/about", "/therapy", "/breathwork", "/workshops", "/lectures", "/articles", "/contact", "/free", "/tashlich", "/privacy", "/accessibility", "/terms"]
    urls += [f"/lectures/{l['slug']}" for l in LECTURES]
    urls += [f"/workshops/{p['slug']}" for p in PRODUCTS]
    base = CFG["domain"].rstrip("/")
    if not CFG["draft"]:
        sitemap = "".join(f"<url><loc>{E(base + u)}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls)
        write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sitemap}</urlset>')
        write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: {base}/sitemap.xml\n")
    else:
        write("robots.txt", "User-agent: *\nDisallow: /\n")

    print(f"built {len(list(SITE.rglob('*.html')))} html files into {SITE}")


if __name__ == "__main__":
    build()
