"""Temporary probe, round 5 (dates on EA and Keywords offer pages). Delete after use."""
import re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as r:
        return r.read().decode("utf-8", "replace")
def sq(t): return re.sub(r"\s+", " ", t)
for u in ["https://jobs.ea.com/en_US/careers/JobDetail/Assistant-Content-Designer-EA-SPORTS-NHL/216318",
          "https://www.keywordsstudios.com/en/careers/browse-careers/xgJ-technical-designer-remote-talent-pipeline/",
          "https://www.keywordsstudios.com/en/careers/browse-careers/ADB-combat-designer/"]:
    t = get(u); print("=" * 10, u, len(t))
    print("ld+json:", [sq(x)[:700] for x in re.findall(r'(?s)<script type="application/ld\+json">(.*?)</script>', t)])
    for m in list(re.finditer(r"(?i)date|posted|publish", t))[:12]:
        print("  ctx:", sq(t[max(0, m.start()-120):m.start()+160]))
