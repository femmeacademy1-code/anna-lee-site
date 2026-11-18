"""Builds one self-contained preview page with every public view.

Each page is a view shown by its name in the hash (#therapy, #about, ...), so the
links in the menu and the buttons work inside the single preview file.
"""
import base64, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
PAGES = [
    ("index.html", "home"),
    ("about.html", "about"),
    ("therapy.html", "therapy"),
    ("breathwork.html", "breathwork"),
    ("workshops.html", "workshops"),
    ("workshops/calm-in-the-storm.html", "calm-in-the-storm"),
    ("workshops/nervous-system-course.html", "nervous-system-course"),
    ("workshops/rebirthing-after-birth.html", "rebirthing-after-birth"),
    ("lectures.html", "lectures"),
    ("lectures/al-kotzim.html", "al-kotzim"),
    ("lectures/work-under-pressure.html", "work-under-pressure"),
    ("lectures/education-teams.html", "education-teams"),
    ("articles.html", "articles"),
    ("contact.html", "contact"),
    ("free.html", "free"),
    ("tashlich.html", "tashlich"),
    ("tashlich-thanks.html", "tashlich-thanks"),
    ("first-aid-kit-thanks.html", "first-aid-kit-thanks"),
    ("privacy.html", "privacy"),
    ("accessibility.html", "accessibility"),
]

def rewrite_links(fragment):
    # /about -> #about, / -> #home, /workshops/x -> #x
    def repl(m):
        path = m.group(1).strip("/")
        if path.startswith("_blob/"):
            return m.group(0)  # a file in the preview's own storage
        if not path:
            return 'href="#home"'
        name = path.split("/")[-1]
        return f'href="#{name}"'
    fragment = re.sub(r'data-next="(/[^"]*)"', lambda m: 'data-next="#' + m.group(1).strip("/").split("/")[-1] + '"', fragment)
    return re.sub(r'href="(/[^"]*)"', repl, fragment)

def title_of(html_text):
    m = re.search(r"<title>(.*?)</title>", html_text, re.S)
    return (m.group(1).split(" | ")[0] if m else "").strip()

home = (SITE / "index.html").read_text(encoding="utf-8")
draft = re.search(r'<div class="draft-banner">.*?</div>', home, re.S).group(0)
header = re.search(r'<header class="site-header">.*?</header>', home, re.S).group(0)
footer = re.search(r'<footer class="site-footer">.*?</footer>', home, re.S).group(0)

import html as _html
import json as _json
import sqlite3 as _sqlite

def _load_articles():
    db = _sqlite.connect(str(ROOT / "data/site.db"))
    db.row_factory = _sqlite.Row
    rows = db.execute(
        "SELECT slug,title,category,excerpt,body,sources,author,created_at,updated_at "
        "FROM articles WHERE published=1 ORDER BY created_at DESC, id DESC"
    ).fetchall()
    db.close()
    return rows

def _body_html(body):
    out = []
    for line in body.split("\n"):
        line = line.strip()
        if not line:
            continue
        tag = "h2" if line.startswith("## ") else "p"
        text = line[3:] if tag == "h2" else line
        out.append(f"<{tag}>{_html.escape(text)}</{tag}>")
    return "".join(out)

_ARTICLES = _load_articles()
ARTICLE_CARDS = "".join(
    f'<article class="card"><span class="tag">{_html.escape(a["category"] or "")}</span>'
    f'<h3><a href="#article-{_html.escape(a["slug"])}">{_html.escape(a["title"])}</a></h3>'
    f'<p>{_html.escape(a["excerpt"] or "")}</p>'
    f'<a class="more" href="#article-{_html.escape(a["slug"])}">לקריאה</a></article>'
    for a in _ARTICLES
)
ARTICLE_VIEWS = []
for a in _ARTICLES:
    sources = _json.loads(a["sources"]) if a["sources"] else []
    src = ""
    if sources:
        src = '<div class="sources"><strong>מקורות</strong><ul>' + "".join(f"<li>{_html.escape(x)}</li>" for x in sources) + "</ul></div>"
    date = (a["updated_at"] or a["created_at"] or "")[:10]
    ARTICLE_VIEWS.append(
        f'<div data-view="article-{_html.escape(a["slug"])}" data-title="{_html.escape(a["title"])}" hidden>\n'
        f'<section class="ph"><div class="wrap article-wrap">\n'
        f'<p class="kicker"><a href="#articles">כל המאמרים</a></p>\n'
        f'<article><h1>{_html.escape(a["title"])}</h1>'
        f'<p class="byline">מאת {_html.escape(a["author"] or "")}, עודכן {date}</p>'
        f'<div class="article-body">{_body_html(a["body"])}</div>{src}'
        f'<p class="article-next"><a class="btn" href="#contact">לשיחת היכרות ללא עלות</a></p>'
        f'</article></div></section>\n</div>'
    )

FILES = {
    "first-aid-kit.pdf": "/_blob/4d404e5a97ebc4f60afefb2c2e2e6eca",
    "tashlich.pdf": "/_blob/1cd97f29564c3b27af13acc85b6168f7",
    "first-aid-kit-card.jpg": "/_blob/c183e86fe11d1dd61a9b4f6bb158d281",
}
views = []
for file, name in PAGES:
    text = (SITE / file).read_text(encoding="utf-8")
    main = re.search(r'<main id="main">(.*?)</main>', text, re.S).group(1)
    # the free files live in the preview's own storage
    for path, blob in FILES.items():
        main = main.replace(f'"/static/files/{path}"', f'"{blob}"')
    main = rewrite_links(main)
    if name == "articles":
        # the preview carries the published articles from the local database
        main = main.replace("data-article-list", "data-preview-articles")
        main = re.sub(r'<label class="search">.*?</label>', "", main, flags=re.S)
        main = re.sub(r'<p><button[^>]*data-more[^>]*>.*?</button></p>', "", main, flags=re.S)
        main = main.replace('<div class="filters" hidden></div>', "")
        main = main.replace('<div class="grid cols-3"></div>', '<div class="grid cols-3">' + ARTICLE_CARDS + '</div>')
    views.append(f'<div data-view="{name}" data-title="{title_of(text)}" hidden>\n{main}\n</div>')

views.extend(ARTICLE_VIEWS)
# the Spotify player cannot load inside the preview frame; the play button and link stay
views = [re.sub(r'<iframe class="spotify"[^>]*></iframe>', '', v) for v in views]
header = rewrite_links(header)
footer = rewrite_links(footer)
draft = rewrite_links(draft)

css = (ROOT / "static/site.css").read_text(encoding="utf-8")
def _font(m):
    f = ROOT / "static" / "fonts" / m.group(1)
    return 'url("data:font/woff2;base64,' + base64.b64encode(f.read_bytes()).decode("ascii") + '")'
css = re.sub(r'url\("/static/fonts/([^"]+)"\)', _font, css)
css += """
:root { color-scheme: light; }
.site-header { top: env(safe-area-inset-top, 0px); }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--cream); }
"""
# embed every photo in static/img so the single preview file shows all of them
def _embed(view_html):
    def repl(m):
        f = ROOT / "static" / m.group(1)
        if not f.exists():
            return m.group(0)
        mime = "image/webp" if f.suffix == ".webp" else "image/jpeg"
        uri = f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode("ascii")
        return f'src="{uri}"'
    return re.sub(r'src="/static/(img/[^"]+)"', repl, view_html)
views = [_embed(v) for v in views]
header = _embed(header)
footer = _embed(footer)

js = (ROOT / "static/app.js").read_text(encoding="utf-8")
js_editor = (ROOT / "preview/photo_editor.js").read_text(encoding="utf-8")
# The preview has no server: sending a form here shows what a visitor would see next,
# and nothing is saved.
js = """
(function () {
  var real = window.fetch;
  window.fetch = function (u, o) {
    if (String(u).indexOf("/api/leads") !== -1) {
      return Promise.resolve(new Response(JSON.stringify({ message: "תצוגה מקדימה: הפרטים לא נשמרו." }), { status: 200, headers: { "Content-Type": "application/json" } }));
    }
    return real.apply(this, arguments);
  };
})();
""" + js
css += (ROOT / "preview/photo_editor.css").read_text(encoding="utf-8")
router = """
(function () {
  var views = [].slice.call(document.querySelectorAll('[data-view]'));
  function show() {
    var navEl = document.querySelector('#site-nav'), tg = document.querySelector('.nav-toggle');
    if (navEl) navEl.classList.remove('open');
    if (tg) tg.setAttribute('aria-expanded', 'false');
    var h = (location.hash || '#home').slice(1);
    var parts = h.split('#'), id = parts[0], anchor = parts[1];
    var target = views.filter(function (v) { return v.getAttribute('data-view') === id; })[0];
    if (!target) {
      // an anchor inside the page on screen, such as #form or #register
      var cur = views.filter(function (v) { return !v.hidden; })[0];
      var el = cur && cur.querySelector('[id="' + h + '"]');
      if (el) { el.scrollIntoView({ behavior: 'smooth' }); return; }
      target = views[0];
    }
    views.forEach(function (v) { v.hidden = v !== target; });
    var name = target.getAttribute('data-view');
    document.querySelectorAll('.nav a').forEach(function (a) {
      if (a.getAttribute('href') === '#' + name) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    if (target.getAttribute('data-title')) document.title = target.getAttribute('data-title') + ' | אנה לי מילשטיין';
    var a = anchor && target.querySelector('[id="' + anchor + '"]');
    if (a) setTimeout(function () { a.scrollIntoView(); }, 30); else window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', show);
  show();
})();
"""

head = ('<title>אתר אנה לי מילשטיין</title>\n'

        '<style>\n' + css + '</style>\n')
body = (draft + "\n" + header + '\n<main id="main">\n' + "\n".join(views) + "\n</main>\n"
        + footer + "\n<script>\n" + js + "\n" + router + "\n" + js_editor + "\n</script>\n")
out = head + body
(ROOT / "preview/home-preview.html").write_text(out, encoding="utf-8")
print("preview written", len(out), "views:", len(views))
