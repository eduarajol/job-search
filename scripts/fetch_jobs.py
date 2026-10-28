"""Daily job fetcher for the Job Search page.

Reads companies.json, asks each company's public job board for its open
positions, keeps the ones that are design/UX roles or are based in
Barcelona/Spain/remote, and writes jobs.json for index.html.

Uses only the Python standard library, so the GitHub Action needs no installs.
"""

import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPANIES = ROOT / "companies.json"
OUTPUT = ROOT / "jobs.json"
DETAILS = ROOT / "details.json"
DESC_LIMIT = 7000

UA = "Mozilla/5.0 (job-search personal dashboard)"
TIMEOUT = 30

DESIGN = re.compile(
    r"design|\bux\b|\bui\b|user experience|user research|usability",
    re.I,
)
NOT_DESIGN = re.compile(
    r"sound|audio|graphic|motion|hardware|fashion|instructional|interior|"
    r"lighting|vfx|artist|programmer|engineer|developer|scientist|analyst|"
    r"recruit|marketing design|brand design|packaging",
    re.I,
)
LOCAL = re.compile(r"barcelona|spain|españa|espana|catalonia|cataluña|catalunya", re.I)
REMOTE = re.compile(r"remote|remoto|anywhere|work from home|wfh", re.I)
EUROPE = re.compile(r"europe|emea|eu\b|spain|españa|worldwide|global|anywhere", re.I)


def get_json(url, data=None):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def iso_date(value):
    """Publication date as ISO 8601. Boards send ISO strings, RFC 822 dates
    (Teamtailor RSS) or epoch milliseconds (Lever)."""
    if value in (None, ""):
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000, timezone.utc).replace(microsecond=0).isoformat()
        text = str(value).strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}", text):
            return text
        return parsedate_to_datetime(text).isoformat()
    except Exception:
        return None


def job(id_, title, location, url, remote=False, posted=None, desc=None):
    return {
        "id": str(id_),
        "title": (title or "").strip(),
        "location": (location or "").strip(),
        "url": url,
        "remote": bool(remote),
        "posted": iso_date(posted),
        "_desc": desc,
    }


def plain(text):
    """Turn job-board HTML into readable plain text."""
    if not text:
        return ""
    t = html.unescape(text)
    t = re.sub(r"(?i)<\s*(br|/p|/li|/h\d|/div)\s*/?>", "\n", t)
    t = re.sub(r"(?i)<\s*li[^>]*>", "\n- ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()[:DESC_LIMIT]


# ---------- one reader per job board system ----------

def read_greenhouse(src):
    boards = src["board"] if isinstance(src["board"], list) else [src["board"]]
    host = "boards-api.eu.greenhouse.io" if src.get("region") == "eu" else "boards-api.greenhouse.io"
    out, errors = [], []
    for board in boards:
        try:
            data = get_json(f"https://{host}/v1/boards/{board}/jobs?content=true")
        except Exception as e:  # try the next board name
            errors.append(f"{board}: {e}")
            continue
        for j in data.get("jobs", []):
            loc = (j.get("location") or {}).get("name", "")
            out.append(job(
                j["id"], j.get("title"), loc, j.get("absolute_url"),
                remote=bool(REMOTE.search(loc)),
                posted=j.get("first_published") or j.get("updated_at"),
                desc=j.get("content"),
            ))
    if not out and errors:
        raise RuntimeError("; ".join(errors))
    return out


def read_lever(src):
    data = get_json(f"https://api.lever.co/v0/postings/{src['company']}?mode=json")
    out = []
    for j in data:
        cats = j.get("categories") or {}
        locs = cats.get("allLocations") or [cats.get("location") or ""]
        loc = " · ".join(l for l in locs if l)
        remote = j.get("workplaceType") == "remote" or bool(REMOTE.search(loc))
        created = j.get("createdAt")
        posted = (
            datetime.fromtimestamp(created / 1000, timezone.utc).isoformat()
            if isinstance(created, (int, float)) else None
        )
        out.append(job(j["id"], j.get("text"), loc, j.get("hostedUrl"), remote, posted))
    return out


def read_smartrecruiters(src):
    company = src["company"]
    out, offset = [], 0
    while True:
        data = get_json(
            f"https://api.smartrecruiters.com/v1/companies/{company}/postings"
            f"?limit=100&offset={offset}"
        )
        content = data.get("content", [])
        for j in content:
            l = j.get("location") or {}
            loc = l.get("fullLocation") or ", ".join(
                x for x in [l.get("city"), l.get("country", "").upper()] if x
            )
            out.append(job(
                j["id"], j.get("name"), loc,
                f"https://jobs.smartrecruiters.com/{company}/{j['id']}",
                remote=bool(l.get("remote")) or bool(REMOTE.search(loc)),
                posted=j.get("releasedDate"),
            ))
        offset += len(content)
        if not content or offset >= data.get("totalFound", 0) or offset > 5000:
            break
        time.sleep(0.3)
    return out


def read_workable(src):
    acct = src["account"]
    data = get_json(f"https://apply.workable.com/api/v1/widget/accounts/{acct}")
    out = []
    for j in data.get("jobs", []):
        loc = ", ".join(x for x in [j.get("city"), j.get("country")] if x)
        out.append(job(
            j.get("shortcode") or j.get("id"), j.get("title"), loc,
            j.get("url") or j.get("application_url"),
            remote=bool(j.get("telecommuting")) or bool(REMOTE.search(loc)),
            posted=j.get("published_on") or j.get("created_at"),
        ))
    return out


def read_teamtailor(src):
    """Teamtailor career sites publish an RSS feed at /jobs.rss."""
    import xml.etree.ElementTree as ET
    req = urllib.request.Request(f"https://{src['host']}/jobs.rss", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        root = ET.fromstring(resp.read())
    out = []
    for item in root.iter("item"):
        def text(tag):
            el = item.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""
        # Locations live in Teamtailor's own namespace: gather every city/country found.
        places = []
        for el in item.iter():
            name = el.tag.split("}")[-1].lower()
            if name in ("city", "country", "name") and el.text and el.text.strip() not in places:
                if el is not item.find("title"):
                    places.append(el.text.strip())
        remote_hint = " ".join(
            (el.text or "") for el in item.iter() if "remote" in el.tag.lower()
        )
        loc = ", ".join(places)
        remote = bool(REMOTE.search(loc + " " + remote_hint)) and "none" not in remote_hint.lower()
        out.append(job(
            text("guid") or text("link"), text("title"), loc, text("link"),
            remote=remote, posted=text("pubDate") or None,
            desc=text("description"),
        ))
    return out


def read_phenom(src):
    """Phenom career sites (King, Blizzard) answer a JSON search at /widgets.
    Offers are published on Workday; applyUrl minus "/apply" is the offer page."""
    host, country, lang = src["host"], src.get("country", "us"), src.get("lang", "en_us")
    out, start, size = [], 0, 100
    while True:
        body = {
            "lang": lang, "deviceType": "desktop", "country": country,
            "pageName": "search-results", "ddoKey": "refineSearch", "sortBy": "",
            "subsearch": "", "from": start, "jobs": True, "counts": False,
            "all_fields": [], "size": size, "clearAll": False, "jdsource": "facets",
            "isSliderEnable": False, "keywords": "", "global": True,
            "selected_fields": {}, "locationData": {},
        }
        data = get_json(f"https://{host}/widgets", body)
        rs = data.get("refineSearch") or {}
        page = (rs.get("data") or {}).get("jobs") or []
        for j in page:
            locs = j.get("multi_location") or [j.get("location") or j.get("cityStateCountry") or ""]
            loc = "; ".join(l for l in locs if l)
            apply_url = j.get("applyUrl") or ""
            url = re.sub(r"/apply/?$", "", apply_url) or f"https://{host}/{src.get('path', 'us/en')}/job/{j.get('jobId')}"
            remote = (j.get("checkRemote") or "").lower() == "remote" or bool(REMOTE.search(loc))
            out.append(job(
                j.get("jobId") or j.get("reqId"), j.get("title"), loc, url,
                remote=remote, posted=j.get("postedDate") or j.get("dateCreated"),
                desc=None,
            ))
            out[-1]["_teaser"] = j.get("descriptionTeaser") or ""
            out[-1]["_workday"] = apply_url
        start += len(page)
        if not page or start >= (rs.get("totalHits") or 0) or start > 3000:
            break
        time.sleep(0.3)
    return out


def workday_description(apply_url):
    """Full text from Workday's public JSON for one offer page."""
    m = re.match(r"https://([\w.-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/]+)(/job/.+?)(?:/apply)?/?$", apply_url or "")
    if not m:
        return ""
    tenant, wd, site, path = m.groups()
    d = get_json(f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}{path}")
    return (d.get("jobPostingInfo") or {}).get("jobDescription") or ""


def read_wordpress(src):
    """Studios that post offers as WordPress entries (Angry Mob Games):
    every entry of the given post type and category is an open offer."""
    base = src["site"].rstrip("/")
    ptype, cat = src.get("type_slug", "posts"), src.get("category")
    url = f"{base}/wp-json/wp/v2/{ptype}?per_page=100&_fields=id,date,link,title,content"
    if cat:
        tax = src.get("taxonomy", "categories")
        terms = get_json(f"{base}/wp-json/wp/v2/{tax}?slug={cat}")
        if not terms:
            raise RuntimeError(f"category '{cat}' not found")
        url += f"&{tax}={terms[0]['id']}"
    out = []
    for j in get_json(url):
        title = html.unescape(re.sub(r"<[^>]+>", "", (j.get("title") or {}).get("rendered", "")))
        loc = src.get("location", "")
        out.append(job(
            j.get("id"), title, loc, j.get("link"),
            remote=bool(REMOTE.search(loc)), posted=j.get("date"),
            desc=(j.get("content") or {}).get("rendered", ""),
        ))
    return out


def describe(src, j):
    """Full description for one job, fetched only for the shortlisted ones."""
    if j.get("_desc"):
        return plain(j["_desc"])
    try:
        if src["type"] == "smartrecruiters":
            d = get_json(f"https://api.smartrecruiters.com/v1/companies/{src['company']}/postings/{j['id']}")
            secs = (d.get("jobAd") or {}).get("sections") or {}
            parts = [(secs.get(k) or {}).get("text", "") for k in
                     ("jobDescription", "qualifications", "additionalInformation")]
            return plain("\n".join(parts))
        if src["type"] == "phenom":
            return plain(workday_description(j.get("_workday")) or j.get("_teaser") or "")
        if src["type"] == "workable":
            d = get_json(f"https://apply.workable.com/api/v2/accounts/{src['account']}/jobs/{j['id']}")
            return plain("\n".join(d.get(k) or "" for k in ("description", "requirements")))
    except Exception as e:
        print(f"  no description for {j['title']}: {e}", file=sys.stderr)
    return ""


READERS = {
    "teamtailor": read_teamtailor,
    "greenhouse": read_greenhouse,
    "lever": read_lever,
    "smartrecruiters": read_smartrecruiters,
    "workable": read_workable,
    "phenom": read_phenom,
    "wordpress": read_wordpress,
}


# ---------- classification ----------

def is_design(title):
    return bool(DESIGN.search(title)) and not NOT_DESIGN.search(title)


def is_local(j):
    loc = j["location"]
    if LOCAL.search(loc):
        return True
    if j["remote"] or REMOTE.search(loc):
        # Remote counts when it is open to Europe or has no region attached.
        if EUROPE.search(loc):
            return True
        rest = re.sub(r"\b(or|and|fully|only|hybrid)\b", " ", REMOTE.sub(" ", loc), flags=re.I)
        return not re.sub(r"[\s,;:()|/·\-–]+", "", rest)
    return False


def main():
    companies = json.loads(COMPANIES.read_text(encoding="utf-8"))
    previous = {}
    if OUTPUT.exists():
        try:
            prev = json.loads(OUTPUT.read_text(encoding="utf-8"))
            for c in prev.get("companies", []):
                for j in c.get("jobs") or []:
                    previous[(c["id"], j["id"])] = j.get("firstSeen")
        except Exception:
            pass

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    result = []
    details = {}
    for c in companies:
        entry = {k: c.get(k) for k in ("id", "name", "group", "note", "domain", "careers", "logos")}
        src = c.get("source")
        if not src:
            entry.update(status="manual", jobs=None)
            result.append(entry)
            continue
        try:
            raw = READERS[src["type"]](src)
            jobs = []
            seen = set()
            for j in raw:
                if not j["title"] or j["id"] in seen:
                    continue
                seen.add(j["id"])
                j["design"] = is_design(j["title"])
                j["local"] = is_local(j)
                if not (j["design"] or j["local"]):
                    continue
                j["firstSeen"] = previous.get((c["id"], j["id"])) or now
                jobs.append(j)
            for j in jobs:
                if j["design"] and j["local"]:
                    details[f"{c['id']}:{j['id']}"] = {
                        "company": c["name"], "title": j["title"], "location": j["location"],
                        "url": j["url"], "firstSeen": j["firstSeen"],
                        "description": describe(src, j),
                    }
                for k in ("_desc", "_teaser", "_workday"):
                    j.pop(k, None)
            jobs.sort(key=lambda j: (not j["design"], not j["local"], j["title"].lower()))
            entry.update(status="ok", total=len(raw), jobs=jobs)
            print(f"ok    {c['name']}: {len(raw)} open, {len(jobs)} kept")
        except Exception as e:
            entry.update(status="error", error=str(e)[:200], jobs=None)
            print(f"error {c['name']}: {e}", file=sys.stderr)
        result.append(entry)
        time.sleep(0.5)

    DETAILS.write_text(
        json.dumps({"updated": now, "jobs": details}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    OUTPUT.write_text(
        json.dumps({"updated": now, "companies": result}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
