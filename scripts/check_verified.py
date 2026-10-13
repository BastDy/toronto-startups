"""Check every verifier output against its input batch (the output contract).

For each data/verified/<name>.json with a matching data/batches/<name>.json:
  - the file parses as JSON
  - every input id appears exactly once, and no unknown id appears
  - stage and sector use schema values
Usage: python scripts/check_verified.py   (exit code 1 if any problem)
"""
import json
import sys
from collections import Counter

from common import ROOT

STAGES = {"Pre-seed", "Seed", "Series A", "Series B", "Growth", "Late stage", "Acquired", "Unknown", None}
SECTORS = {"Fintech", "AI/ML", "Healthtech", "B2B SaaS", "E-commerce/Retail", "Proptech", "Edtech",
           "Climate/Energy", "Cybersecurity", "Marketplace", "Consumer", "Hardware/Robotics", "Biotech",
           "Insurtech", "HR/Future of work", "Media/Entertainment", "Logistics", "Other", None}

problems = 0
for out_path in sorted((ROOT / "data" / "verified").glob("*.json")):
    in_path = ROOT / "data" / "batches" / out_path.name
    try:
        out = json.loads(out_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"{out_path.name}: INVALID JSON ({e})")
        problems += 1
        continue
    issues = []
    if in_path.exists():
        want = [r["id"] for r in json.loads(in_path.read_text(encoding="utf-8"))]
        got = Counter(o.get("id") for o in out)
        missing = [i for i in want if i not in got]
        extra = [i for i in got if i not in want]
        twice = [i for i, n in got.items() if n > 1]
        if missing:
            issues.append(f"missing ids {missing}")
        if extra:
            issues.append(f"unknown ids {extra}")
        if twice:
            issues.append(f"repeated ids {twice}")
    kept = [o for o in out if not o.get("drop") and not o.get("skip")]
    bad_stage = sorted({o.get("stage") for o in kept} - STAGES, key=str)
    bad_sector = sorted({o.get("sector") for o in kept} - SECTORS, key=str)
    if bad_stage:
        issues.append(f"stage values {bad_stage} (normalized by merge.py)")
    if bad_sector:
        issues.append(f"sector values {bad_sector}")
    status = "; ".join(issues) if issues else "ok"
    print(f"{out_path.name}: {len(out)} rows, {len(out) - len(kept)} dropped - {status}")
    problems += any("ids" in i or "sector" in i for i in issues)

sys.exit(1 if problems else 0)
