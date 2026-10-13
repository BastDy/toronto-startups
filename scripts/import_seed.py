"""Import the GTA startups already found in the Freelance project's funding list.

Usage: python scripts/import_seed.py [path/to/startups-canada-levees.csv]
Writes data/raw/seed-freelance.json
"""
import csv
import sys
from pathlib import Path

from common import RAW, city_in_gta, normalize_domain, record, write_json

DEFAULT = Path(__file__).resolve().parents[2] / "Freelance" / "02-prospection" / "listes" / "startups-canada-levees.csv"


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            city = (r.get("Company City") or "").strip()
            if not city_in_gta(city):
                continue
            amount = " ".join(x for x in [r.get("Devise"), r.get("Montant")] if x) or None
            rows.append(record(
                name=r.get("Company"),
                website=r.get("Website") if normalize_domain(r.get("Website")) else None,
                city=city,
                last_round=r.get("Tour") or None,
                last_round_date=r.get("Last Raised At") or None,
                last_round_amount=amount,
                sources=[r["Source"]] if r.get("Source") else [],
                status="active",
            ))
    write_json(RAW / "seed-freelance.json", rows)
    print(f"seed-freelance: {len(rows)} GTA companies written")


if __name__ == "__main__":
    main()
