"""Temporary probe, round 3. Delete after use."""
import json, re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url, data=None, ctype=None, extra=None):
    h = {"User-Agent": UA, "Accept": "text/html,application/json,*/*", "Accept-Language": "en-US,en;q=0.9"}
    if ctype: h["Content-Type"] = ctype
    if extra: h.update(extra)
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=40) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
def sq(t): return re.sub(r"\s+", " ", t)
# ROVIO listing HTML
st, f, t = get("https://www.rovio.com/open-positions/")
i = t.find("head-of-business-development"); print("ROVIO around job:", sq(t[i-2500:i+1200]))
# EA: page size and feed size
st, f, t = get("https://jobs.ea.com/en_US/careers/Home/?jobRecordsPerPage=100&jobOffset=0")
arts = re.findall(r'<article class="article article--result.*?</article>', t, re.S)
print("EA articles at 100/page:", len(arts)); print("EA article sample:", sq(arts[0])[:1500] if arts else "")
st, f, t = get("https://jobs.ea.com/en_US/careers/SearchJobs/feed/?jobRecordsPerPage=500")
print("EA feed items at 500:", t.count("<item>"))
# KEYWORDS
st, f, t = get("https://www.keywordsstudios.com/assets/js/filters/dist/main.js?v=1")
print("KW main.js len", len(t))
print("KW urls:", sorted(set(re.findall(r"[\"'`](/[\w/.-]*|https?://[^\"'`\s]+)[\"'`]", t)))[:60])
for kw in ["fetch(", "ajax", "XMLHttpRequest", "endpoint", "api", "json", "careers"]:
    for m in list(re.finditer(re.escape(kw), t))[:3]:
        print("KW ctx", kw, ":", sq(t[max(0, m.start()-200):m.start()+250]))
st, f, t = get("https://www.keywordsstudios.com/en/careers/browse-careers/")
for kw in ["data-endpoint", "data-url", "data-api", "filters", "careers-list", "job-list", "base_url"]:
    for m in list(re.finditer(kw, t))[:2]:
        print("KW page ctx", kw, ":", sq(t[max(0, m.start()-300):m.start()+400]))
