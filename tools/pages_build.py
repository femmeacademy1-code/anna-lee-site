#!/usr/bin/env python3
"""Build a GitHub Pages copy of the site into docs/.

Pages serves a repo from /<repo-name>/, so root-absolute links ("/about", "/static/x")
are rewritten to include that prefix. Forms cannot reach server.py on Pages, so the
copy of static/app.js falls back to opening WhatsApp with the details.

Usage:  python3 build.py && python3 tools/pages_build.py [/anna-lee-site]
"""
import re, shutil, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cms_tags import connect

root = Path(__file__).resolve().parent.parent
base = (sys.argv[1] if len(sys.argv) > 1 else "/anna-lee-site").rstrip("/")
out = root / "docs"
# cms/ holds the client's saved edits and uploads (Femme CMS): keep it across rebuilds.
keep = None
if (out / "cms").exists():
    keep = Path(tempfile.mkdtemp()) / "cms"
    shutil.copytree(out / "cms", keep)
if out.exists():
    shutil.rmtree(out)
shutil.copytree(root / "site", out)
shutil.copytree(root / "static", out / "static")
(out / ".nojekyll").write_text("")
if keep:
    shutil.copytree(keep, out / "cms")

ATTR = re.compile(r'(\b(?:href|src|action|data-next|data-download)=")/(?!/)')
for f in out.rglob("*.html"):
    s = f.read_text(encoding="utf-8")
    s = ATTR.sub(lambda m: m.group(1) + base + "/", s)
    f.write_text(s, encoding="utf-8")

for f in (out / "static").glob("*.css"):
    s = f.read_text(encoding="utf-8")
    s = s.replace('url("/static/', 'url("' + base + '/static/').replace("url(/static/", "url(" + base + "/static/")
    f.write_text(s, encoding="utf-8")

js = out / "static" / "app.js"
s = js.read_text(encoding="utf-8")
s = s.replace('href="/accessibility"', 'href="' + base + '/accessibility"')
s = s.replace('"/articles/"', '"' + base + '/articles/"').replace("'/articles/'", "'" + base + "/articles/'")
fallback = (
    'msg.className = "form-msg ok"; '
    'var wa = "https://wa.me/972506651451?text=" + encodeURIComponent("שלום, אני " + body.name + ". " + (body.message || "אשמח שתחזרי אליי") + " טלפון: " + body.phone + " מייל: " + body.email); '
    'msg.innerHTML = \'לשליחת הפרטים לאנה, <a target="_blank" rel="noopener" href="\' + wa + \'">לחצי כאן לוואטסאפ</a>.\'; '
    'window.open(wa, "_blank");'
)
old = 'msg.className = "form-msg err";\n        msg.textContent = "אין חיבור לשרת כרגע. נסי שוב מאוחר יותר.";'
assert old in s, "lead-form catch block not found"
s = s.replace(old, fallback)
js.write_text(s, encoding="utf-8")
tagged = connect(out, base)
print("built", out, "with base", base, "| CMS tag on", tagged, "pages")
