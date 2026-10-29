"""Temporary probe: new studios. Delete after use."""
import json, re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url, data=None, ctype=None):
    h = {"User-Agent": UA, "Accept": "text/html,application/json,application/xml,*/*", "Accept-Language": "en-US,en;q=0.9"}
    if ctype: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=40) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
def sq(t): return re.sub(r"\s+", " ", t)
MARK = r"(greenhouse\.io[^\"' <]*|lever\.co[^\"' <]*|workable\.com[^\"' <]*|smartrecruiters\.com[^\"' <]*|teamtailor[^\"' <]*|ashbyhq\.com[^\"' <]*|personio\.[a-z]+[^\"' <]*|recruitee\.com[^\"' <]*|myworkdayjobs\.com[^\"' <]*|phenompeople|phApp\.ddo|avature[^\"' <]*|icims\.com[^\"' <]*|successfactors[^\"' <]*|bamboohr\.com[^\"' <]*|jobvite\.com[^\"' <]*|breezy\.hr[^\"' <]*|comeet\.(?:com|co)[^\"' <]*|pinpointhq\.com[^\"' <]*|rippling[^\"' <]*|join\.com[^\"' <]*|hibob[^\"' <]*|factorial[^\"' <]*|eightfold[^\"' <]*|wp-json/wp/v2/[^\"' <]*)"
for k, u in {"eve": "https://eve.games/home/careers/", "tiltingpoint": "https://www.tiltingpoint.com/careers",
             "aristocrat": "https://careers.aristocrat.com/en/", "breach": "https://thebreachstudios.com/careers",
             "bluetile": "https://www.bluetile.com/contact.html", "uplay": "https://www.uplayonline.com/index.html%3Fp=1645.html"}.items():
    print("=" * 20, k, u)
    try:
        st, f, t = get(u); print(st, f, len(t))
        print("markers:", sorted(set(m[:110] for m in re.findall(MARK, t, re.I)))[:20])
        print("job links:", sorted(set(re.findall(r'href="([^"]*(?:job|career|position|opening|vacan|apply)[^"]*)"', t, re.I)))[:20])
        m = re.search(r"phApp\.ddo\s*=\s*(\{.*?\});\s*phApp\.", t, re.S)
        if m:
            e = json.loads(m.group(1)).get("eagerLoadRefineSearch") or {}
            print("PHENOM", e.get("totalHits"), re.findall(r'"(?:locale|country|refNum)"\s*:\s*"[^"]*"', t)[:4])
        i = t.lower().find("opening"); print("snippet:", sq(t[i-200:i+800]) if i > 0 else "")
    except Exception as ex:
        print("ERR", ex)
for b in ["tangelo-games", "bandainamcomobile"]:
    for u in [f"https://{b}.jobs.personio.com/xml?language=en", f"https://{b}.jobs.personio.de/xml?language=en"]:
        try:
            st, f, t = get(u); print("=" * 10, u, st, len(t)); print(t[:1500])
            print("positions:", t.count("<position>"), re.findall(r"<name>([^<]+)</name>\s*", t)[:15], re.findall(r"<office>([^<]+)</office>", t)[:15])
            break
        except Exception as ex: print(u, "ERR", ex)
for org in ["tiltingpoint", "tilting-point"]:
    for u in [f"https://boards-api.greenhouse.io/v1/boards/{org}/jobs", f"https://api.lever.co/v0/postings/{org}?mode=json",
              f"https://api.ashbyhq.com/posting-api/job-board/{org}", f"https://apply.workable.com/api/v1/widget/accounts/{org}"]:
        try:
            st, f, t = get(u); print("TP OK", u, len(t), t[:300])
        except Exception as ex: print("TP", u, ex)
