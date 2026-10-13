"""Geocode verified HQ addresses with OpenStreetMap Nominatim (free, no key).

Respects the Nominatim usage policy: 1 request per second, identifying User-Agent,
results cached in data/geocode.json so an address is never requested twice.
Usage: python scripts/geocode.py
build_site.py then adds lat/lng to each startup whose address is in the cache.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

from common import ROOT

CACHE = ROOT / "data" / "geocode.json"
API = "https://nominatim.openstreetmap.org/search"
UA = "toronto-startups-directory/1.0 (github.com/BastDy/toronto-startups)"
# Rough GTA bounding box: lon_min, lat_max, lon_max, lat_min
VIEWBOX = "-80.2,44.3,-78.6,43.3"


def geocode(address):
    q = urllib.parse.urlencode({
        "q": address, "format": "json", "limit": 1,
        "countrycodes": "ca", "viewbox": VIEWBOX, "bounded": 1,
    })
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        hits = json.load(resp)
    return [round(float(hits[0]["lat"]), 6), round(float(hits[0]["lon"]), 6)] if hits else None


def simplify(address):
    """'333 Bay St, Suite 3400, Toronto, ON M5H 2S7' -> '333 Bay St, Toronto, ON'.

    Nominatim matches street + city well but fails on suite/unit/floor parts and postal codes.
    """
    parts = [p.strip() for p in address.split(",")]
    noise = re.compile(r"^(suite|unit|ste\.?|floor|fl\.?|#|\d+(st|nd|rd|th) floor|.*building)\b", re.I)
    parts = [p for p in parts if p and not noise.match(p)]
    parts = [re.sub(r"\s+[A-Z]\d[A-Z]\s?\d[A-Z]\d$", "", p) for p in parts]  # Canadian postal code
    return ", ".join(parts)


def main():
    retry = "--retry" in sys.argv  # also retry addresses cached as not found
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    rows = json.loads((ROOT / "data" / "candidates.json").read_text(encoding="utf-8"))
    wanted = {r["address"].strip() for r in rows if r.get("address")}
    todo = sorted(a for a in wanted if a not in cache or (retry and cache[a] is None))
    print(f"{len(todo)} addresses to geocode ({len(cache)} cached)")
    for i, addr in enumerate(todo, 1):
        try:
            hit = None
            for query in dict.fromkeys([addr, simplify(addr)]):
                hit = geocode(query)
                time.sleep(1.1)
                if hit:
                    break
            cache[addr] = hit
        except Exception as e:  # network hiccup: leave uncached, retry next run
            print(f"  error on {addr!r}: {e}")
            continue
        print(f"  {i}/{len(todo)} {addr} -> {cache[addr]}")
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    found = sum(1 for v in cache.values() if v)
    print(f"cache: {found}/{len(cache)} addresses located")


if __name__ == "__main__":
    main()
