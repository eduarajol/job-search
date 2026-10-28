"""Temporary probe, round 4 (Keywords). Delete after use."""
import json, re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url):
    h = {"User-Agent": UA, "Accept": "text/html,application/json,*/*", "X-Requested-With": "XMLHttpRequest"}
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
def sq(t): return re.sub(r"\s+", " ", t)
st, f, t = get("https://www.keywordsstudios.com/en/careers/browse-careers/")
for kw in ["_filter_streaming", "_filter_data", "_limit", "_offset", "data_url"]:
    for m in list(re.finditer(kw, t))[:2]:
        print("CTX", kw, ":", sq(t[max(0, m.start()-200):m.start()+600]))
m = re.search(r"data_url\s*:\s*['\"]([^'\"]+)['\"]", t)
if m:
    u = m.group(1).replace("\\/", "/")
    if u.startswith("/"): u = "https://www.keywordsstudios.com" + u
    print("DATA URL", u)
    st, f, d = get(u + ("&" if "?" in u else "?") + "offset=0&limit=3")
    print(st, len(d)); print(d[:3000])
    st, f, d = get(u + ("&" if "?" in u else "?") + "offset=0&limit=2000")
    try:
        arr = json.loads(d); print("count", len(arr)); print("keys", list(arr[0].keys()))
        bcn = [x for x in arr if "barcelona" in json.dumps(x).lower()]
        print("barcelona", len(bcn)); print(json.dumps(bcn[:1], ensure_ascii=False)[:2500])
    except Exception as e: print("parse", e, d[:300])
