"""Temporary probe, round 2. Delete after use."""
import json, re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url, data=None, ctype=None):
    h = {"User-Agent": UA, "Accept": "text/html,application/json,*/*", "Accept-Language": "en-US,en;q=0.9"}
    if ctype: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=30) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
def show(label, url, n=1500, data=None, ctype=None):
    print("=" * 20, label, url)
    try:
        st, final, t = get(url, data, ctype); print(st, final, len(t)); print(t[:n]); return t
    except Exception as ex:
        print("ERR", ex); return ""
# Activision widgets
body = {"lang": "en_us", "deviceType": "desktop", "country": "us", "pageName": "search-results", "ddoKey": "refineSearch",
        "from": 0, "jobs": True, "counts": False, "all_fields": [], "size": 5, "clearAll": False, "jdsource": "facets",
        "keywords": "", "global": True, "selected_fields": {}, "locationData": {}}
t = show("ACTI widgets", "https://careers.activision.com/widgets", 300, json.dumps(body).encode(), "application/json")
# Larian lever
t = show("LARIAN lever", "https://api.lever.co/v0/postings/larian?mode=json", 300)
try: print("larian count", len(json.loads(t)), [ (j["text"], j["categories"].get("location")) for j in json.loads(t)[:8]])
except Exception as e: print(e)
# Moon Active: find ashby org
st, f, t = get("https://www.moonactive.com/careers/")
print("MOON ashby refs:", sorted(set(re.findall(r"ashbyhq\.com[^\"' <]{0,80}", t)))[:10])
print("MOON sre:", sorted(set(re.findall(r"wp-json/sre/v1/[^\"' <]{0,80}", t)))[:10])
for org in ["moonactive", "moon-active", "MoonActive"]:
    t = show("MOON ashby " + org, f"https://api.ashbyhq.com/posting-api/job-board/{org}", 200)
    if t:
        try:
            d = json.loads(t); print("count", len(d.get("jobs", [])), [(j["title"], j.get("location"), j.get("publishedAt")) for j in d["jobs"][:6]])
        except Exception as e: print(e)
show("MOON sre search", "https://www.moonactive.com/wp-json/sre/v1/jobs_search?phrase=", 1200)
# Voodoo
for u in ["https://api.lever.co/v0/postings/voodoo?mode=json", "https://api.ashbyhq.com/posting-api/job-board/voodoo",
          "https://boards-api.greenhouse.io/v1/boards/voodoo/jobs", "https://apply.workable.com/api/v1/widget/accounts/voodoo"]:
    show("VOODOO", u, 400)
t = show("VOODOO module", "https://framerusercontent.com/sites/5aSGBHah2ySP0946zU9pHh/Jobs.C9yUBY2G.mjs", 0)
print("VOODOO module urls:", sorted(set(re.findall(r"https?://[\w.-]+/[^\"'\s`]{0,80}", t)))[:30])
print("VOODOO module snippet:", re.sub(r"\s+", " ", t[:1500]))
# Rovio feed + wp types
show("ROVIO feed", "https://www.rovio.com/open-positions/feed/", 2500)
t = show("ROVIO types", "https://www.rovio.com/wp-json/wp/v2/types", 0)
try: print({k: v.get("rest_base") for k, v in json.loads(t).items()})
except Exception as e: print(e)
# Nomada page content
t = show("NOMADA page", "https://nomada.studio/wp-json/wp/v2/pages/1466?_fields=title,content,modified", 0)
try: print(re.sub(r"<[^>]+>", " ", json.loads(t)["content"]["rendered"])[:1500])
except Exception as e: print(e)
# EA Avature: list page structure
st, f, t = get("https://jobs.ea.com/es_ES/careers")
i = t.find("JobDetail"); print("EA snippet:", re.sub(r"\s+", " ", t[i-1500:i+1500]))
print("EA pagination:", sorted(set(re.findall(r'href="([^"]*(?:jobOffset|jobRecordsPerPage|SearchJobs)[^"]*)"', t)))[:10])
print("EA total:", re.findall(r"(?i)(\d+)\s*(?:results|resultados|jobs|ofertas)", t)[:5])
show("EA feed", "https://jobs.ea.com/en_US/careers/SearchJobs/feed/?jobRecordsPerPage=5", 1500)
# Keywords
st, f, t = get("https://www.keywordsstudios.com/en/careers/browse-careers/")
print("KW scripts:", sorted(set(re.findall(r'src="([^"]+\.js[^"]*)"', t)))[:20])
print("KW api-ish:", sorted(set(re.findall(r"[\"'](/[\w/-]*(?:api|jobs|vacanc|careers)[\w/.-]*)[\"']", t)))[:30])
print("KW external:", sorted(set(re.findall(r"https?://[\w.-]*(?:workday|smartrecruiters|greenhouse|lever|teamtailor|icims|successfactors|recruitee|personio|jobvite|taleo|avature|eightfold|oracle)[\w./-]*", t)))[:20])
i = t.lower().find("browse careers"); print("KW snippet:", re.sub(r"\s+", " ", t[i:i+2000]))
