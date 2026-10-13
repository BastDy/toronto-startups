"""Shared helpers: domain normalization, GTA cities, record template."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

GTA_CITIES = {
    "toronto", "north york", "scarborough", "etobicoke", "york", "east york",
    "mississauga", "brampton", "markham", "vaughan", "richmond hill", "oakville",
    "burlington", "milton", "pickering", "ajax", "whitby", "oshawa", "newmarket",
    "aurora", "concord", "thornhill", "woodbridge", "maple", "caledon",
}

FIELDS = [
    "name", "website", "domain", "description", "sector", "city", "founded",
    "stage", "employees", "last_round", "last_round_date", "last_round_amount",
    "linkedin", "hiring", "sources", "status", "verified", "notes", "address",
]


def normalize_domain(value):
    """'https://www.Foo.com/about' -> 'foo.com'. Returns None if not a domain."""
    if not value or not isinstance(value, str):
        return None
    v = value.strip().lower()
    v = re.sub(r"^[a-z]+://", "", v)
    v = v.split("/")[0].split("?")[0].split("#")[0]
    v = re.sub(r"^www\d?\.", "", v)
    if "." not in v or " " in v:
        return None
    return v


def city_in_gta(city):
    if not city:
        return False
    return city.strip().lower().split(",")[0].strip() in GTA_CITIES


def employees_range(n):
    if not isinstance(n, int) or n <= 0:
        return None
    for hi, label in [(10, "1-10"), (50, "11-50"), (200, "51-200"),
                      (500, "201-500"), (1000, "501-1000"), (5000, "1001-5000")]:
        if n <= hi:
            return label
    return "5001+"


def record(**kw):
    r = {f: None for f in FIELDS}
    r.update(kw)
    r["sources"] = r.get("sources") or []
    r["verified"] = bool(r.get("verified"))
    r["domain"] = normalize_domain(r.get("domain") or r.get("website"))
    return r


def write_json(path, rows):
    Path(path).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
