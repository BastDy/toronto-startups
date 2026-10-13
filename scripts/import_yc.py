"""Import Y Combinator companies headquartered in the GTA.

Source: yc-oss public API (mirror of the YC directory), no agent needed.
Usage: python scripts/import_yc.py [path/to/all.json]
Writes data/raw/yc.json
"""
import json
import sys
import urllib.request

from common import RAW, city_in_gta, employees_range, record, write_json

API = "https://yc-oss.github.io/api/companies/all.json"

INDUSTRY_TO_SECTOR = {
    "Fintech": "Fintech",
    "Healthcare": "Healthtech",
    "B2B": "B2B SaaS",
    "Consumer": "Consumer",
    "Education": "Edtech",
    "Real Estate and Construction": "Proptech",
    "Industrials": "Hardware/Robotics",
    "Government": "Other",
}
STATUS = {"Active": "active", "Acquired": "acquired", "Inactive": "closed", "Public": "active"}


def gta_city(locations):
    for loc in (locations or "").split(";"):
        city = loc.split(",")[0].strip()
        if city_in_gta(city):
            return city
    return None


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            data = json.load(f)
    else:
        with urllib.request.urlopen(API, timeout=60) as resp:
            data = json.load(resp)

    rows = []
    for c in data:
        city = gta_city(c.get("all_locations"))
        if not city:
            continue
        tags = [t.lower() for t in c.get("tags") or []]
        sector = INDUSTRY_TO_SECTOR.get(c.get("industry"), "Other")
        if any("artificial intelligence" in t or t in ("ai", "generative ai", "machine learning") for t in tags):
            sector = "AI/ML" if sector in ("B2B SaaS", "Other") else sector
        status = STATUS.get(c.get("status"), "unknown")
        stage = {"acquired": "Acquired"}.get(status, "Growth" if c.get("stage") == "Growth" else "Unknown")
        rows.append(record(
            name=c.get("name"),
            website=c.get("website"),
            description=c.get("one_liner"),
            sector=sector,
            city=city,
            stage=stage,
            employees=employees_range(c.get("team_size")),
            hiring=bool(c.get("isHiring")),
            sources=[c.get("url")] if c.get("url") else [],
            status=status,
            notes=f"YC {c.get('batch')}" if c.get("batch") else None,
        ))

    write_json(RAW / "yc.json", rows)
    print(f"yc: {len(rows)} GTA companies written")


if __name__ == "__main__":
    main()
