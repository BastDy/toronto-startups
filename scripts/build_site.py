"""Build site/startups.json from the dataset.

Usage:
  python scripts/build_site.py               # verified startups only (data/candidates.json, verified: true)
  python scripts/build_site.py --candidates  # everything, including unverified candidates

Closed companies are left out. Coordinates come from data/geocode.json (scripts/geocode.py).
"""
import json
import sys

from common import ROOT, write_json

rows = json.loads((ROOT / "data" / "candidates.json").read_text(encoding="utf-8"))
if "--candidates" not in sys.argv:
    rows = [r for r in rows if r.get("verified")]
rows = [r for r in rows if r.get("status") != "closed"]

cache_path = ROOT / "data" / "geocode.json"
cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
located = 0
for r in rows:
    hit = cache.get((r.get("address") or "").strip())
    if hit:
        r["lat"], r["lng"] = hit
        located += 1

write_json(ROOT / "data" / "startups.json", [r for r in rows if r.get("verified")])
write_json(ROOT / "site" / "startups.json", rows)
print(f"site/startups.json: {len(rows)} startups, {located} with exact map position")
