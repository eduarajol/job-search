"""Builds index.html for GitHub Pages from src/page.html.

src/page.html is written without <html>/<head>/<body> so it can also be
published as a Claude artifact. This wraps it in a full document.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEAD = (
    "<!doctype html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
    "<link rel=\"icon\" type=\"image/png\" sizes=\"32x32\" href=\"icons/favicon-32.png\">\n"
    "<link rel=\"icon\" type=\"image/png\" sizes=\"192x192\" href=\"icons/icon-192.png\">\n"
    "<link rel=\"apple-touch-icon\" href=\"icons/apple-touch-icon.png\">\n"
    "<meta name=\"apple-mobile-web-app-title\" content=\"Job Search\">\n"
    "<style>body{margin:0}</style>\n</head>\n<body>\n"
)
for src, out in (("page.html", "index.html"), ("games.html", "games.html"), ("applied.html", "applied.html"), ("people.html", "people.html")):
    page = (ROOT / "src" / src).read_text(encoding="utf-8")
    (ROOT / out).write_text(HEAD + page + "\n</body>\n</html>\n", encoding="utf-8")

# Starting jobs.json, so the page renders before the first daily run.
jobs = ROOT / "jobs.json"
if not jobs.exists():
    companies = json.loads((ROOT / "companies.json").read_text(encoding="utf-8"))
    out = []
    for c in companies:
        e = {k: c.get(k) for k in ("id", "name", "group", "note", "domain", "careers")}
        e["status"] = "pending" if c.get("source") else "manual"
        e["jobs"] = None
        out.append(e)
    jobs.write_text(json.dumps({"updated": None, "companies": out}, ensure_ascii=False, indent=1), encoding="utf-8")
