"""Write CSV copies of the directory (Excel / HubSpot import friendly).

    python scripts/export_csv.py
    -> data/startups.csv    final list (what the site shows)
    -> data/candidates.csv  every candidate, incl. unconfirmed city and closed
    -> data/youspot_companies.csv  final list with readable headers, for a YouSpot company import
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


# YouSpot import: readable headers, one company per row, final list only
YOUSPOT = [
    ("Company name", "name"), ("Domain", "domain"), ("Website", "website"),
    ("Description", "description"), ("LinkedIn", "linkedin"), ("City", "city"),
    ("Address", "address"), ("Industry", "sector"), ("Funding stage", "stage"),
    ("Founded", "founded"), ("Employees", "employees"), ("Last round", "last_round"),
    ("Last round date", "last_round_date"), ("Last round amount", "last_round_amount"),
    ("Hiring", "hiring"), ("Status", "status"), ("Notes", "notes"),
]


def export_youspot():
    rows = json.loads((ROOT / "data" / "startups.json").read_text(encoding="utf-8"))
    out = ROOT / "data" / "youspot_companies.csv"
    yes_no = {True: "Yes", False: "No", None: ""}
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([h for h, _ in YOUSPOT])
        for r in rows:
            w.writerow([yes_no[r.get(k)] if k == "hiring" else
                        ("" if r.get(k) is None else r[k]) for _, k in YOUSPOT])
    print(f"{out.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    export("startups")
    export("candidates")
    export_youspot()
