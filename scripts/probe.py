"""Temporary probe: which job platform each career site uses. Delete after use."""
import json, re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url, data=None, ctype=None):
    h = {"User-Agent": UA, "Accept": "text/html,application/json,*/*", "Accept-Language": "en-US,en;q=0.9"}
    if ctype: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=30) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
MARK = r"(greenhouse\.io[^\"' ]*|lever\.co[^\"' ]*|workable\.com[^\"' ]*|smartrecruiters\.com[^\"' ]*|teamtailor[^\"' ]*|ashbyhq\.com[^\"' ]*|personio\.[a-z]+[^\"' ]*|recruitee\.com[^\"' ]*|myworkdayjobs\.com[^\"' ]*|phenompeople|avature[^\"' ]*|icims\.com[^\"' ]*|successfactors[^\"' ]*|bamboohr\.com[^\"' ]*|jobvite\.com[^\"' ]*|breezy\.hr[^\"' ]*|comeet\.(?:com|co)[^\"' ]*|pinpointhq\.com[^\"' ]*|rippling[^\"' ]*|join\.com[^\"' ]*|hibob[^\"' ]*|factorial[^\"' ]*|welcometothejungle[^\"' ]*|wp-json[^\"' ]*)"
SITES = {
 "voodoo": "https://voodoo.io/careers",
 "moonactive": "https://www.moonactive.com/careers/",
 "rovio": "https://www.rovio.com/open-positions/",
 "larian": "https://larian.com/careers",
 "activision": "https://careers.activision.com/search-results",
 "ea": "https://jobs.ea.com/es_ES/careers",
 "nomada": "https://nomada.studio/careers/",
 "keywords": "https://www.keywordsstudios.com/en/careers/browse-careers/",
}
for k, u in SITES.items():
    print("=" * 25, k, u)
    try:
        st, final, t = get(u)
        print(st, final, len(t))
        marks = sorted(set(m[:120] for m in re.findall(MARK, t, re.I)))
        print("markers:", marks[:25])
        m = re.search(r"phApp\.ddo\s*=\s*(\{.*?\});\s*phApp\.", t, re.S)
        if m:
            d = json.loads(m.group(1)); e = d.get("eagerLoadRefineSearch") or {}
            print("PHENOM totalHits", e.get("totalHits"), re.findall(r'"(?:locale|country|refNum)"\s*:\s*"[^"]*"', t)[:6])
            for j in ((e.get("data") or {}).get("jobs") or [])[:3]: print("  -", j.get("title"), "|", j.get("location"), "|", j.get("applyUrl"))
        if "__NEXT_DATA__" in t: print("NEXT_DATA present")
        titles = re.findall(r'(?i)(?:job|position|opening|career)[^<>]{0,40}</?[a-z]+[^>]*>\s*([A-Z][^<>]{4,70})<', t)[:8]
        print("text near job words:", titles)
        links = sorted(set(re.findall(r'href="([^"]*(?:job|career|position|opening|vacan)[^"]*)"', t, re.I)))[:25]
        print("job links:", links)
    except Exception as ex:
        print("ERR", ex)
# Activision Phenom: try with locale path and widgets
for u in ["https://careers.activision.com/us/en/search-results", "https://careers.activision.com/global/en/search-results"]:
    try:
        st, final, t = get(u); m = re.search(r"phApp\.ddo\s*=\s*(\{.*?\});\s*phApp\.", t, re.S)
        print("ACTI", u, st, final, bool(m), re.findall(r'"(?:locale|country|refNum)"\s*:\s*"[^"]*"', t)[:5])
        if m:
            e = json.loads(m.group(1)).get("eagerLoadRefineSearch") or {}; print(" totalHits", e.get("totalHits"))
    except Exception as ex: print("ACTI", u, "ERR", ex)
