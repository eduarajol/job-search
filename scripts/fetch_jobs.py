"""Daily job fetcher for the Job Search page.

Reads companies.json, asks each company's public job board for its open
positions, keeps the ones that are design/UX roles or are based in
Barcelona/Spain/remote, and writes jobs.json for index.html.

Uses only the Python standard library, so the GitHub Action needs no installs.
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPANIES = ROOT / "companies.json"
OUTPUT = ROOT / "jobs.json"

UA = "Mozilla/5.0 (job-search personal dashboard)"
TIMEOUT = 30

DESIGN = re.compile(
    r"design|\bux\b|\bui\b|user experience|user research|usability",
    re.I,
)
NOT_DESIGN = re.compile(
    r"sound|audio|graphic|motion|hardware|fashion|instructional|interior|"
    r"lighting|vfx|artist|marketing design|brand design|packaging",
    re.I,
)
LOCAL = re.compile(r"barcelona|spain|españa|espana|catalonia|cataluña|catalunya", re.I)
REMOTE = re.compile(r"remote|remoto|anywhere|work from home|wfh", re.I)
EUROPE = re.compile(r"europe|emea|eu\b|spain|españa|worldwide|global|anywhere", re.I)
NON_EU_ONLY = re.compile(
    r"\b(usa?|united states|canada|north america|latam|apac|india|china|japan|"
    r"australia|brazil|mexico|israel|uk only)\b",
    re.I,
)


def get_json(url, data=None):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def job(id_, title, location, url, remote=False, posted=None):
    return {
        "id": str(id_),
        "title": (title or "").strip(),
        "location": (location or "").strip(),
        "url": url,
        "remote": bool(remote),
        "posted": posted,
    }


# ---------- one reader per job board system ----------

def read_greenhouse(src):
    boards = src["board"] if isinstance(src["board"], list) else [src["board"]]
    host = "boards-api.eu.greenhouse.io" if src.get("region") == "eu" else "boards-api.greenhouse.io"
    out, errors = [], []
    for board in boards:
        try:
            data = get_json(f"https://{host}/v1/boards/{board}/jobs")
        except Exception as e:  # try the next board name
            errors.append(f"{board}: {e}")
            continue
        for j in data.get("jobs", []):
            loc = (j.get("location") or {}).get("name", "")
            out.append(job(
                j["id"], j.get("title"), loc, j.get("absolute_url"),
                remote=bool(REMOTE.search(loc)),
                posted=j.get("first_published") or j.get("updated_at"),
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


READERS = {
    "greenhouse": read_greenhouse,
    "lever": read_lever,
    "smartrecruiters": read_smartrecruiters,
    "workable": read_workable,
}


# ---------- classification ----------

def is_design(title):
    return bool(DESIGN.search(title)) and not NOT_DESIGN.search(title)


def is_local(j):
    loc = j["location"]
    if LOCAL.search(loc):
        return True
    if j["remote"]:
        # Remote counts unless it is clearly limited to a non-European region.
        if NON_EU_ONLY.search(loc) and not EUROPE.search(loc):
            return False
        return True
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
    for c in companies:
        entry = {k: c.get(k) for k in ("id", "name", "group", "note", "domain", "careers")}
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
            jobs.sort(key=lambda j: (not j["design"], not j["local"], j["title"].lower()))
            entry.update(status="ok", total=len(raw), jobs=jobs)
            print(f"ok    {c['name']}: {len(raw)} open, {len(jobs)} kept")
        except Exception as e:
            entry.update(status="error", error=str(e)[:200], jobs=None)
            print(f"error {c['name']}: {e}", file=sys.stderr)
        result.append(entry)
        time.sleep(0.5)

    OUTPUT.write_text(
        json.dumps({"updated": now, "companies": result}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
