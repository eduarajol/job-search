"""Temporary probe: inspects career sites to design new readers. Delete after use."""
import json, re, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

def get(url, data=None, ctype=None):
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
    if ctype: h["Content-Type"] = ctype
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")

def ddo(text):
    m = re.search(r"phApp\.ddo\s*=\s*(\{.*?\});\s*phApp\.", text, re.S)
    if not m:
        return None
    return json.loads(m.group(1))

for name, url in [("KING", "https://careers.king.com/us/en/search-results"),
                  ("KING-P2", "https://careers.king.com/us/en/search-results?from=10&s=1"),
                  ("ACTI", "https://careers.activision.com/us/en/search-results"),
                  ("BLIZ", "https://careers.blizzard.com/global/en/search-results")]:
    print("=" * 20, name)
    try:
        st, final, t = get(url)
        print(st, final, len(t))
        print("phApp" in t, "eagerLoadRefineSearch" in t, "workday" in t.lower())
        d = ddo(t)
        if d is None:
            i = t.find("phApp.ddo"); print("ddo snippet:", t[i:i+400])
            continue
        print("ddo keys:", list(d.keys())[:40])
        e = d.get("eagerLoadRefineSearch") or {}
        print("eager keys:", list(e.keys()), "totalHits", e.get("totalHits"), "hits", e.get("hits"))
        jobs = (e.get("data") or {}).get("jobs") or []
        print("jobs on page:", len(jobs))
        if jobs:
            print(json.dumps(jobs[0], ensure_ascii=False)[:1500])
            for j in jobs[:10]:
                print(" -", j.get("jobId"), j.get("title"), "|", j.get("location") or j.get("cityStateCountry"), "|", j.get("postedDate"))
        m = re.search(r'"refNum"\s*:\s*"([^"]+)"', t); print("refNum", m and m.group(1))
        print("siteConfig?", re.findall(r'"(?:locale|siteType|deviceType|country|lang)"\s*:\s*"[^"]*"', t)[:8])
    except Exception as ex:
        print("ERR", ex)

print("=" * 20, "KING widgets POST")
try:
    body = {"lang": "en_us", "deviceType": "desktop", "country": "us", "pageName": "search-results",
            "ddoKey": "refineSearch", "sortBy": "", "subsearch": "", "from": 0, "jobs": True, "counts": True,
            "all_fields": ["category", "country", "city"], "size": 50, "clearAll": False, "jdsource": "facets",
            "isSliderEnable": False, "keywords": "", "global": True, "selected_fields": {}, "locationData": {}}
    st, final, t = get("https://careers.king.com/widgets", json.dumps(body).encode(), "application/json")
    print(st, len(t)); d = json.loads(t)
    rs = d.get("refineSearch") or {}
    print("totalHits", rs.get("totalHits"), "jobs", len((rs.get("data") or {}).get("jobs") or []))
    for j in ((rs.get("data") or {}).get("jobs") or [])[:5]:
        print(" -", j.get("jobId"), j.get("title"), "|", j.get("location"), "|", j.get("postedDate"))
except Exception as ex:
    print("ERR", ex)

print("=" * 20, "ANGRY MOB")
for url in ["https://www.angrymobgames.com/",
            "https://www.angrymobgames.com/wp-json/wp/v2/types",
            "https://www.angrymobgames.com/wp-json/wp/v2/project?per_page=50&_fields=id,slug,date,modified,link,title,project_category,project_tag",
            "https://www.angrymobgames.com/project/gameplay-designer/"]:
    try:
        st, final, t = get(url)
        print("--", url, st, len(t))
        if url.endswith(".com/"):
            i = t.lower().find("current job openings")
            print("section at", i)
            print(re.sub(r"\s+", " ", t[i:i+4000]))
            print("project links:", sorted(set(re.findall(r'https?://www\.angrymobgames\.com/project/[\w-]+/?', t))))
        elif "wp-json" in url:
            print(t[:3000])
        else:
            print(re.findall(r'<meta[^>]+(?:published_time|modified_time|og:title|description)[^>]*>', t)[:6])
            print(re.findall(r'"date(?:Published|Modified)"\s*:\s*"[^"]+"', t)[:4])
            print(re.findall(r'<h1[^>]*>.*?</h1>', t, re.S)[:3])
            print(re.findall(r'class="[^"]*(?:entry-content|project-content|portfolio)[^"]*"', t)[:6])
    except Exception as ex:
        print("--", url, "ERR", ex)
