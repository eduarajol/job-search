"""Temporary probe round 3: Pentasia structure and Disney Workday. Delete after use."""
import json, re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url, data=None, ctype=None):
    h = {"User-Agent": UA, "Accept": "text/html,application/json,*/*", "Accept-Language": "en-US,en;q=0.9"}
    if ctype: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=30) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
sq = lambda t: re.sub(r"\s+", " ", t)
st, f, t = get("https://www.pentasia.com/cm/candidates/jobs")
cards = re.findall(r'(?s)<div class="JobItem_card[^"]*">.*?<span class="JobItem_bg', t)
print("cards", len(cards)); [print("CARD", sq(c)[:900]) for c in cards[:2]]
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', t, re.S)
d = json.loads(m.group(1))
found = []
def walk(x, path):
    if isinstance(x, list) and x and all(isinstance(i, dict) for i in x[:3]) and any("title" in i for i in x[:3]):
        found.append((path, len(x), list(x[0].keys())[:30], json.dumps(x[0])[:900]))
    if isinstance(x, dict):
        for k, v in x.items(): walk(v, path + "/" + k)
    elif isinstance(x, list):
        for i, v in enumerate(x[:3]): walk(v, path + f"[{i}]")
walk(d, "")
for p in found[:6]: print("LIST", p)
pages = re.findall(r'jobs\?page=(\d+)', t); print("max page", max(map(int, pages)) if pages else None)
for q in ["Marvel", "Pixar"]:
    for tenant, wd, site in [("disney", "wd5", "disneycareer"), ("pixar", "wd501", "Pixar_External_Career_Site")]:
        try:
            body = {"appliedFacets": {}, "limit": 5, "offset": 0, "searchText": q if tenant == "disney" else ""}
            st, f, x = get(f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs", json.dumps(body).encode(), "application/json")
            j = json.loads(x); print("WD", tenant, q, "total", j.get("total"), [(p.get("title"), p.get("locationsText")) for p in j.get("jobPostings", [])[:5]])
        except Exception as e: print("WD", tenant, q, "ERR", e)
