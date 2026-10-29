"""Temporary probe: new companies. Delete after use."""
import json, re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url, data=None, ctype=None):
    h = {"User-Agent": UA, "Accept": "text/html,application/json,*/*", "Accept-Language": "en-US,en;q=0.9"}
    if ctype: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=30) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
MARK = r"(boards\.greenhouse\.io/[\w-]+|job-boards(?:\.eu)?\.greenhouse\.io/[\w-]+|greenhouse\.io/embed/job_board/js\?for=[\w-]+|jobs\.lever\.co/[\w-]+|apply\.workable\.com/[\w-]+|jobs\.smartrecruiters\.com/[\w-]+|careers\.smartrecruiters\.com/[\w-]+|[\w-]+\.teamtailor\.com|jobs\.ashbyhq\.com/[\w-]+|[\w-]+\.jobs\.personio\.(?:de|com)|[\w-]+\.recruitee\.com|[\w-]+\.wd\d+\.myworkdayjobs\.com/[\w-/]+|phenompeople|avature|icims\.com|successfactors|bamboohr\.com|jobvite\.com/[\w-]+|breezy\.hr|comeet\.(?:com|co)/jobs/[\w-]+|pinpointhq\.com|join\.com/companies/[\w-]+|factorialhr|hibob|eightfold|oraclecloud\.com[^\"' ]{0,60}|wp-json/wp/v2/[\w-]+)"
PAGES = {
 "alike": "https://www.alikestudio.com", "cdpr": "https://www.cdprojektred.com/en/jobs",
 "jamcity": "https://www.jamcity.com/careers", "disney": "https://www.disneycareers.com/en/search-jobs/Marvel",
 "pixar": "https://www.pixar.com/careers", "athletic": "https://www.athletic-club.eus/es/club/ofertas-de-empleo/",
 "sie": "https://www.playstation.com/en-us/corporate/playstation-careers/", "nintendo": "https://careers.nintendo.com/",
 "noe": "https://www.nintendo.com/en-gb/Corporate/Nintendo-of-Europe/Careers/Careers-at-Nintendo-of-Europe-2071010.html",
 "insomniac": "https://insomniac.games/careers/", "crystal": "https://crystaldynamics.com/careers/",
 "scorewarrior": "https://scorewarrior.com/careers", "anchorpoint": "https://www.anchorpointstudios.com/careers",
 "fortis": "https://www.fortis.gg/careers", "saber": "https://saber.games/careers/",
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
SLUGS = ["cdprojektred", "cdprojekt", "jamcity", "jamcityinc", "sonyinteractiveentertainmentglobal", "insomniacgames", "insomniac",
         "crystaldynamics", "scorewarrior", "anchorpointstudios", "anchorpoint", "fortisgames", "fortis", "saberinteractive", "saber",
         "alikestudio", "pentasia", "athleticclub", "nintendo"]
for s in SLUGS:
    for name, u in [("gh", f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs"), ("lever", f"https://api.lever.co/v0/postings/{s}?mode=json"),
                    ("ashby", f"https://api.ashbyhq.com/posting-api/job-board/{s}"), ("workable", f"https://apply.workable.com/api/v1/widget/accounts/{s}"),
                    ("sr", f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=1"), ("personio", f"https://{s}.jobs.personio.com/xml"),
                    ("tt", f"https://{s}.teamtailor.com/jobs.rss")]:
        try:
            st, f, t = get(u)
            n = t.count('"id"') if name != "personio" and name != "tt" else t.count("<position>") + t.count("<item>")
            if name == "sr":
                n = json.loads(t).get("totalFound", 0)
            if n: print("OK", name, s, "items~", n)
        except Exception:
            pass
