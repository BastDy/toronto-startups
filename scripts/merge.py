"""Merge every data/raw/*.json into data/candidates.json, deduplicated.

Dedup key: normalized domain, else normalized name.
Field conflicts: first non-null value wins, sources are unioned.
Prints a per-source report (rows, kept, outside GTA, overlap with other sources).
"""
import json
import re
from collections import defaultdict

from common import FIELDS, RAW, ROOT, city_in_gta, normalize_domain, write_json


def name_key(name):
    n = re.sub(r"[^a-z0-9]", "", (name or "").lower())
    return re.sub(r"(inc|ltd|corp|technologies|technology|labs|ai|hq)$", "", n) or n


def apply_geo(merged):
    """Apply wave-2a geo-check results (data/geo/*.out.json), keyed by candidate id.

    keep   -> set city (+ website/domain if missing), note the evidence
    drop   -> remove from candidates, kept in data/dropped.json for audit
    unclear-> leave as is
    """
    dropped = []
    for path in sorted((ROOT / "data" / "geo").glob("*.out.json")):
        for g in json.loads(path.read_text(encoding="utf-8")):
            r = merged.get(g.get("id"))
            if r is None:
                continue
            if g.get("decision") == "drop":
                r["notes"] = f"Dropped: {g.get('evidence')}"
                dropped.append(merged.pop(g["id"]))
            elif g.get("decision") == "keep" and city_in_gta(g.get("city")):
                r["city"] = g["city"]
                if not r.get("website") and g.get("website"):
                    r["website"] = g["website"]
                    r["domain"] = normalize_domain(g["website"])
                r["notes"] = f"GTA confirmed: {g.get('evidence')}"
    if dropped:
        print(f"geo-check: {len(dropped)} dropped")
    return dropped


def main():
    merged = {}
    name_index = {}
    seen_by = defaultdict(set)
    report = []

    for path in sorted(RAW.glob("*.json")):
        source = path.stem
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            report.append((source, "INVALID JSON", str(e)))
            continue
        kept = outside = 0
        for r in rows:
            if not r.get("name"):
                continue
            if r.get("city") and not city_in_gta(r["city"]):
                outside += 1
                continue
            dom = normalize_domain(r.get("domain") or r.get("website"))
            nk = name_key(r["name"])
            key = dom or name_index.get(nk) or f"name:{nk}"
            if not dom and key == f"name:{nk}":
                # a domain-less row may match an existing domain row by name
                key = name_index.get(nk, key)
            cur = merged.get(key)
            if cur is None:
                cur = {f: None for f in FIELDS}
                cur["sources"] = []
                merged[key] = cur
            for f in FIELDS:
                if f == "sources":
                    for s in r.get("sources") or []:
                        if s and s not in cur["sources"]:
                            cur["sources"].append(s)
                elif cur.get(f) in (None, "", "Unknown", "unknown") and r.get(f) not in (None, ""):
                    cur[f] = r[f]
            cur["domain"] = cur.get("domain") and normalize_domain(cur["domain"]) or dom
            cur["verified"] = False
            name_index.setdefault(nk, key)
            seen_by[key].add(source)
            kept += 1
        report.append((source, len(rows), kept, outside))

    for key, r in merged.items():
        r["id"] = key
        r["found_in"] = sorted(seen_by[key])

    dropped = apply_geo(merged)
    out = sorted(merged.values(), key=lambda r: r["name"].lower())
    write_json(ROOT / "data" / "candidates.json", out)
    write_json(ROOT / "data" / "dropped.json", sorted(dropped, key=lambda r: r["name"].lower()))

    print(f"{'source':28} {'rows':>5} {'kept':>5} {'outGTA':>6}")
    for line in report:
        print(f"{line[0]:28} " + " ".join(f"{x:>5}" if isinstance(x, int) else str(x) for x in line[1:]))
    multi = sum(1 for r in out if len(r["found_in"]) > 1)
    no_domain = sum(1 for r in out if not r["domain"])
    print(f"\nunique companies: {len(out)} | in 2+ sources: {multi} | without domain: {no_domain}")


if __name__ == "__main__":
    main()
