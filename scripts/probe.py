"""Temporary probe: new companies. Delete after use."""
import json, re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url, data=None, ctype=None):
    h = {"User-Agent": UA, "Accept": "text/html,application/json,*/*", "Accept-Language": "en-US,en;q=0.9"}
    if ctype: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=30) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
MARK = r"(boards\.greenhouse\.io/[\w-]+|job-boards(?:\.eu)?\.greenhouse\.io/[\w-]+|greenhouse\.io/embed/job_board/js\?for=[\w-]+|jobs\.lever\.co/[\w-]+|apply\.workable\.com/[\w-]+|jobs\.smartrecruiters\.com/[\w-]+|careers\.smartrecruiters\.com/[\w-]+|[\w-]+\.teamtailor\.com|jobs\.ashbyhq\.com/[\w-]+|[\w-]+\.jobs\.personio\.(?:de|com)|[\w-]+\.recruitee\.com|[\w-]+\.wd\d+\.myworkdayjobs\.com/[\w/-]+|phenompeople|avature|icims\.com|successfactors|bamboohr\.com|jobvite\.com/[\w-]+|breezy\.hr|comeet\.(?:com|co)/jobs/[\w-]+|pinpointhq\.com|join\.com/companies/[\w-]+|factorialhr|hibob|eightfold|oraclecloud\.com[^\"' ]{0,60}|wp-json/wp/v2/[\w-]+)"
PAGES = {
 "alike": "https://www.alikestudio.com", "disney": "https://www.disneycareers.com/en/search-jobs/Marvel",
 "pixar": "https://www.pixar.com/careers", "athletic": "https://www.athletic-club.eus/es/",
 "anchor": "https://www.anchor-point.com/", "anchor2": "https://www.anchor-point.com/careers",
 "saber": "https://saber.games/", "saber2": "https://www.saber.games/careers", "saber3": "https://saberinteractive.com/careers/",
 "pentasia": "https://www.pentasia.com/cm/candidates/jobs",
}
for k, u in PAGES.items():
    try:
        st, f, t = get(u)
        print("==", k, st, f, len(t))
        print("   markers:", sorted(set(m[:90] for m in re.findall(MARK, t, re.I)))[:12])
        if k == "pentasia":
            i = t.find("job"); print("   links:", sorted(set(re.findall(r'href="([^"]*(?:/jobs?/|job-)[^"]*)"', t)))[:20])
            print("   api:", sorted(set(re.findall(r"[\"'](/[\w/-]*(?:api|search|jobs)[\w/.?=&-]*)[\"']", t)))[:20])
            print("   next:", "__NEXT_DATA__" in t, "ld+json JobPosting:", t.count('"JobPosting"'))
    except Exception as e:
        print("==", k, "ERR", u, e)
SLUGS = ["anchorpoint", "anchorpointstudios", "anchor-point", "saber", "saberinteractive", "saber-interactive", "alike", "alikestudio", "pixar", "disney", "marvel", "athletic-club", "athleticclub"]
for s in SLUGS:
    for name, u in [("gh", f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs"), ("lever", f"https://api.lever.co/v0/postings/{s}?mode=json"),
                    ("ashby", f"https://api.ashbyhq.com/posting-api/job-board/{s}"), ("workable", f"https://apply.workable.com/api/v1/widget/accounts/{s}"),
                    ("sr", f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=1"), ("personio", f"https://{s}.jobs.personio.com/xml"),
                    ("tt", f"https://{s}.teamtailor.com/jobs.rss")]:
        try:
            st, f, t = get(u)
            n = json.loads(t).get("totalFound", 0) if name == "sr" else (t.count("<position>") + t.count("<item>") if name in ("personio", "tt") else t.count('"id"'))
            if n: print("OK", name, s, "items~", n)
        except Exception:
            pass
# Pentasia structure
st, f, t = get("https://www.pentasia.com/cm/candidates/jobs")
i = t.find("JobPosting"); print("PENT ld snippet:", re.sub(r"\s+", " ", t[max(0,i-300):i+1200]))
links = sorted(set(re.findall(r'href="([^"]*(?:/job/|/jobs/)[^"]*)"', t)))
print("PENT links", len(links), links[:15])
for kw in ["pagination", "page=", "results", "Barcelona", "Game Designer", "UX"]:
    for m in list(re.finditer(kw, t))[:2]: print("PENT ctx", kw, re.sub(r"\s+", " ", t[max(0, m.start()-250):m.start()+250]))
print("PENT scripts", sorted(set(re.findall(r'src="([^"]+\.js[^"]*)"', t)))[:10])
