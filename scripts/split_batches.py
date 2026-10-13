"""Split data/candidates.json into verification batches for the Sonnet verifiers.

Usage: python scripts/split_batches.py [batch_size]   (default 40)
Writes data/batches/batch-01.json, batch-02.json, ...
Rows already verified are skipped, so the script can be re-run after a partial wave.
"""
import json
import sys

from common import ROOT, write_json

size = int(sys.argv[1]) if len(sys.argv) > 1 else 40
rows = json.loads((ROOT / "data" / "candidates.json").read_text(encoding="utf-8"))
todo = [r for r in rows if not r.get("verified")]

out = ROOT / "data" / "batches"
out.mkdir(exist_ok=True)
for old in out.glob("batch-*.json"):
    old.unlink()
for i in range(0, len(todo), size):
    write_json(out / f"batch-{i // size + 1:02d}.json", todo[i:i + size])
print(f"{len(todo)} candidates -> {-(-len(todo) // size)} batches of {size}")
