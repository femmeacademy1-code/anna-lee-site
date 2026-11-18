"""Femme CMS helpers: add/refresh the one <script> tag that loads cms/cms-kit.js on every page of docs/.

Same logic as the admin's "חיבור לעריכה" (worker/src/index.js addKitTag): the tag is inserted right after the
charset meta, with a version hash of the kit so a new kit is never served from an old cache.
"""
import hashlib, json, re
from pathlib import Path

ORIGIN = "https://femme-cms.femmeacademy1.workers.dev"
EMPTY_EDITS = {"v": 1, "global": {}, "pages": {}}
EXISTING = re.compile(r'<script[^>]*cms/cms-kit\.js[^>]*></script>', re.I)

def kit_version(kit: Path) -> str:
    return hashlib.sha256(kit.read_bytes()).hexdigest()[:10]

def add_tag(html: str, prefix: str, ver: str) -> str:
    tag = f'<script src="{prefix}cms/cms-kit.js?v={ver}" data-admin-origin="{ORIGIN}"></script>'
    if EXISTING.search(html):
        return EXISTING.sub(lambda m: tag, html, count=1)
    m = re.search(r'<meta[^>]*charset[^>]*>', html, re.I) or re.search(r'<head[^>]*>', html, re.I)
    if not m:
        raise SystemExit("no <head> found")
    return html[:m.end()] + "\n" + tag + html[m.end():]

def connect(docs: Path, base: str, kit_src: Path | None = None) -> int:
    cms = docs / "cms"
    cms.mkdir(exist_ok=True)
    if kit_src is not None:
        (cms / "cms-kit.js").write_bytes(kit_src.read_bytes())
    kit = cms / "cms-kit.js"
    if not kit.exists():
        return 0
    if not (cms / "edits.json").exists():
        (cms / "edits.json").write_text(json.dumps(EMPTY_EDITS, indent=2) + "\n")
    ver = kit_version(kit)
    n = 0
    for f in sorted(docs.rglob("*.html")):
        rel = f.relative_to(docs)
        if rel.parts[0] == "cms":
            continue
        # Pages are served at /<repo>/…; the tag's path is relative to the page, as the admin writes it.
        prefix = "../" * (len(rel.parts) - 1)
        f.write_text(add_tag(f.read_text(encoding="utf-8"), prefix, ver), encoding="utf-8")
        n += 1
    return n
