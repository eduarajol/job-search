"""Temporary probe 2: Tilting Point and Aristocrat Workday. Delete after use."""
import json, re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url, data=None, ctype=None):
    h = {"User-Agent": UA, "Accept": "text/html,application/json,*/*", "Accept-Language": "en-US,en;q=0.9"}
    if ctype: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=40) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
def sq(t): return re.sub(r"\s+", " ", t)
st, f, t = get("https://www.tiltingpoint.com/vacancy"); print("TP", st, f, len(t))
print("scripts:", sorted(set(re.findall(r'src="([^"]+)"', t)))[:20])
print("urls:", sorted(set(re.findall(r"https?://[\w.-]+/[^\"'\s<>]{0,80}", t)))[:40])
for kw in ["vacanc", "position", "Designer", "location", "__NEXT", "api"]:
    for m in list(re.finditer(kw, t))[:2]: print("ctx", kw, sq(t[max(0, m.start()-200):m.start()+300]))
for q in ["Product Madness", ""]:
    body = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": q}
    st, f, d = get("https://aristocrat.wd3.myworkdayjobs.com/wday/cxs/aristocrat/AristocratExternalCareersSite/jobs", json.dumps(body).encode(), "application/json")
    j = json.loads(d); print("WD", repr(q), "total", j.get("total"))
    for p in j.get("jobPostings", [])[:20]: print("  -", p.get("title"), "|", p.get("locationsText"), "|", p.get("postedOn"), "|", p.get("externalPath"))
    print("facets:", [ (x.get("facetParameter"), [ (v.get("descriptor"), v.get("count")) for v in (x.get("values") or [])][:12]) for x in j.get("facets", [])][:6])
