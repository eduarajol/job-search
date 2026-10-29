"""Finds a thumbnail for every game in games.json and writes game_images.json.

Mobile games: App Store icon (iTunes Search API). PC/console games: Steam
header image. A result is only accepted when the title matches and the
developer/publisher matches one of the company's names, so a generic title
like "Solitaire" never picks another company's game.
Run by hand from the "Update game images" workflow.
"""

import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (job-search personal dashboard)"

ALIASES = {
    "scopely": ["scopely", "niantic", "foxnext"], "king": ["king"], "socialpoint": ["social point", "socialpoint"],
    "gameloft": ["gameloft"], "ubisoft": ["ubisoft"], "tripledot": ["tripledot", "zephyr", "lion studios"],
    "voodoo": ["voodoo"], "zynga": ["zynga", "peak", "small giant", "naturalmotion"], "moonactive": ["moon active"],
    "rovio": ["rovio"], "outfit7": ["outfit7"], "zeptolab": ["zeptolab"], "larian": ["larian"],
    "ioi": ["io interactive", "ioi"], "activision": ["activision", "infinity ward", "treyarch", "toys for bob", "vicarious"],
    "blizzard": ["blizzard"], "ea": ["electronic arts", "ea swiss", "ea sports", "respawn", "dice", "maxis", "bioware", "motive", "full circle"],
    "riot": ["riot"], "wargaming": ["wargaming"], "taketwo": ["rockstar", "2k", "take-two", "gearbox", "firaxis", "hangar 13", "visual concepts"],
    "digitalextremes": ["digital extremes"], "nomada": ["nomada", "devolver"], "keywords": ["forgotten empires", "world's edge", "xbox game studios", "microsoft"],
    "angrymob": ["angry mob"], "productmadness": ["product madness", "aristocrat"], "tangelo": ["tangelo", "akamon", "mundi"],
    "tiltingpoint": ["tilting point", "nukebox", "edgeworks", "hunted cow", "plamee", "ftx", "metagame", "big wolf", "vrtron", "an games"],
    "breach": ["breach"], "bluetile": ["bluetile"], "uplay": ["u-play", "uplay", "raiser"],
    "infinitethread": ["infinite thread"],
    "jamcity": ["jam city"], "scorewarrior": ["scorewarrior"], "cdpr": ["cd projekt"],
    "playstation": ["sony", "playstation", "naughty dog", "guerrilla", "santa monica", "sucker punch", "insomniac", "polyphony", "team asobi", "arrowhead", "nixxes"],
    "insomniac": ["insomniac", "playstation", "sony", "nixxes"], "nintendo": ["nintendo"], "crystal": ["crystal dynamics", "square enix", "eidos"],
    "saber": ["saber", "focus"], "marvelent": ["netease", "scopely", "foxnext", "second dinner", "nuverse", "insomniac", "playstation", "skydance", "arc system"], "loom": ["loom"], "herobeat": ["herobeat", "hook"],
}


def norm(s):
    s = re.sub(r"[™®©]", "", s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def get_json(url, tries=4):
    """Both stores throttle (the App Store allows ~20 searches a minute):
    wait and retry on errors or empty answers."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            if data is not None:
                return data
        except Exception as e:
            if i == tries - 1:
                raise
        time.sleep(6 * (i + 1))
    return {}


# Matches that look right by title but are another game (or a DLC): never use them.
SKIP = {
    "larian:Divinity", "riot:League of Legends", "taketwo:Grand Theft Auto VI", "taketwo:BioShock",
    "ioi:Hitman 2", "ioi:Hitman 3", "ioi:Hitman (2016)",
}
EXTRA_WORDS = re.compile(r"^(?:[a-z]+ ?)*(game|games|puzzle|casino|slots|classic|adventure|rpg|edition|definitive edition|enhanced|remastered|online|now)?$")


def title_ok(game, found):
    """Same title, or the same title followed by a subtitle ("Dragon City: Battle
    Adventure!"). A following number means a different game ("Divinity 2")."""
    g, f = norm(game), norm(found)
    if not g or not (f == g or f.startswith(g + " ")):
        return False
    rest = f[len(g):].strip()
    if not rest:
        return True
    if re.match(r"^\d", rest) or rest.split()[0] in ("ii", "iii", "iv", "2", "3"):
        return False
    return bool(re.search(r"[:\-–—™®]", found)) or len(rest.split()) <= 3


def dev_ok(cid, *names):
    text = norm(" ".join(n for n in names if n))
    return any(norm(a) in text.split() or norm(a) in text for a in ALIASES.get(cid, []))


def app_store(cid, game):
    for country in ("us", "es"):
        q = urllib.parse.urlencode({"term": game, "entity": "software", "limit": 15, "country": country})
        try:
            res = get_json(f"https://itunes.apple.com/search?{q}").get("results", [])
        except Exception as e:
            print(f"  itunes error {game}: {e}", file=sys.stderr)
            res = []
        for r in res:
            if title_ok(game, r.get("trackName", "")) and dev_ok(cid, r.get("artistName"), r.get("sellerName")):
                return {"img": r.get("artworkUrl512") or r.get("artworkUrl100"), "src": "appstore",
                        "url": r.get("trackViewUrl", "").split("?")[0], "match": r.get("trackName")}
        time.sleep(3.2)
    return None


def steam(cid, game):
    q = urllib.parse.urlencode({"term": game, "cc": "us", "l": "english"})
    try:
        items = get_json(f"https://store.steampowered.com/api/storesearch/?{q}").get("items", [])
    except Exception as e:
        print(f"  steam error {game}: {e}", file=sys.stderr)
        return None
    for it in items[:8]:
        if not title_ok(game, it.get("name", "")):
            continue
        app = it.get("id")
        try:
            d = get_json(f"https://store.steampowered.com/api/appdetails?appids={app}&filters=basic,developers,publishers")
            data = (d.get(str(app)) or {}).get("data") or {}
        except Exception:
            data = {}
        if dev_ok(cid, *(data.get("developers") or []), *(data.get("publishers") or [])):
            return {"img": data.get("header_image") or f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app}/header.jpg",
                    "src": "steam", "url": f"https://store.steampowered.com/app/{app}/", "match": it.get("name")}
        time.sleep(0.4)
    return None


def main():
    games = json.loads((ROOT / "games.json").read_text(encoding="utf-8"))["studios"]
    groups = {c["id"]: c["group"] for c in json.loads((ROOT / "companies.json").read_text(encoding="utf-8"))}
    out_path = ROOT / "game_images.json"
    old = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    out = {}
    for cid, info in games.items():
        for g in info.get("games", []):
            key = f"{cid}:{g['n']}"
            if "sin anunciar" in g["n"] or key in SKIP:
                continue
            first, second = (steam, app_store) if groups.get(cid) == "pc" else (app_store, steam)
            hit = first(cid, g["n"]) or second(cid, g["n"]) or old.get(key)
            if hit:
                out[key] = hit
            print(("ok   " if hit else "miss ") + key + (f"  ->  {hit['src']}: {hit['match']}" if hit else ""))
            time.sleep(1.5)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
