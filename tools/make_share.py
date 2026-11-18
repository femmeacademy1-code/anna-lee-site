"""Builds the shareable preview of the lecture page (plus the three legal pages) into the folder given."""
import re, sys, os
D = sys.argv[1]
LEGAL = {"/privacy": "privacy.html", "/accessibility": "accessibility.html", "/terms": "terms.html"}
# every page of the preview opens at its top (the viewer would otherwise keep the scroll of the last page)
TOP = '<script>if(!location.hash){try{history.scrollRestoration="manual"}catch(e){}scrollTo(0,0);addEventListener("load",function(){scrollTo(0,0)})}</script>'
def fix(t):
    for k, v in LEGAL.items():
        t = t.replace(f'href="{k}"', f'href="{v}"')
    return t.replace('"/static/', '"static/').replace("'/static/", "'static/")
h = open("site/lectures/al-kotzim.html", encoding="utf-8").read()
head = re.search(r"<head>(.*?)</head>", h, re.S).group(1)
body = re.search(r"<body[^>]*>(.*)</body>", h, re.S).group(1)
head = re.sub(r'<meta charset[^>]*>|<meta name="viewport"[^>]*>', '', head)
head = re.sub(r"<title>.*?</title>", "<title>על קוצים</title>", head, 1)
guard = '<script>document.addEventListener("submit",function(e){e.preventDefault();e.stopImmediatePropagation();var b=e.target.querySelector("button[type=submit],.btn");if(b){b.disabled=true;}},true);</script>'
out = '<script>document.documentElement.lang="he";document.documentElement.dir="rtl"</script>' + TOP + head + "\n" + guard + "\n" + '<script>document.body.classList.add("lp")</script>' + body
open(os.path.join(D, "index.html"), "w", encoding="utf-8").write(fix(out))
for f in LEGAL.values():
    t = open("site/" + f, encoding="utf-8").read()
    t = re.sub(r'<button class="nav-toggle".*?</button>\s*<nav.*?</nav>', '', t, flags=re.S)
    t = re.sub(r'<ul class="footer-links" aria-label="קישורים">.*?</ul>', '', t, flags=re.S)
    t = t.replace('<a class="brand" href="/">', '<a class="brand" href="index.html">').replace("</head>", TOP + "</head>", 1)
    open(os.path.join(D, f), "w", encoding="utf-8").write(fix(t))
c = open("static/site.css", encoding="utf-8").read().replace('url("/static/fonts/', 'url("fonts/')
open(os.path.join(D, "static/site.css"), "w", encoding="utf-8").write(c)
open(os.path.join(D, "static/app.js"), "w", encoding="utf-8").write(
    open("static/app.js", encoding="utf-8").read().replace('href="/accessibility"', 'href="accessibility.html"'))
print("ok")
