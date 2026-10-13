"""Copy the final dataset into the site folder.

Usage:
  python scripts/build_site.py               # data/startups.json -> site/startups.json
  python scripts/build_site.py --candidates  # preview with unverified data/candidates.json
"""
import json
import sys

from common import ROOT, write_json

src = ROOT / "data" / ("candidates.json" if "--candidates" in sys.argv else "startups.json")
rows = json.loads(src.read_text(encoding="utf-8"))
write_json(ROOT / "site" / "startups.json", rows)
print(f"site/startups.json <- {src.name}: {len(rows)} startups")
