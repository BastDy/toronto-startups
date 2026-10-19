"""Write CSV copies of the directory (Excel / HubSpot import friendly).

    python scripts/export_csv.py
    -> data/startups.csv    final list (what the site shows)
    -> data/candidates.csv  every candidate, incl. unconfirmed city and closed
"""
import csv
import json

from common import FIELDS, ROOT

COLUMNS = ["id"] + FIELDS + ["found_in", "lat", "lng"]


def export(name):
    rows = json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))
    out = ROOT / "data" / f"{name}.csv"
    # utf-8-sig so Excel reads accents correctly
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r = dict(r)
            for k in ("sources", "found_in"):
                r[k] = " | ".join(r.get(k) or [])
            w.writerow({k: "" if r.get(k) is None else r[k] for k in COLUMNS})
    print(f"{out.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    export("startups")
    export("candidates")
