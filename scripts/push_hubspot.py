"""Push the directory to HubSpot as Company records.

Dry run by default: builds the payloads and writes data/cache/hubspot_preview.json.
With --push it creates the custom properties (group "Toronto startups") if missing,
updates companies that already exist in HubSpot (matched on domain) and upserts
the rest on the unique property ts_id, so running it twice creates no duplicates.

Token: a HubSpot private app token with scopes crm.objects.companies.read/write
and crm.schemas.companies.read/write, in HUBSPOT_TOKEN (env or .env at the root).

    python scripts/push_hubspot.py            # dry run, final list (data/startups.json)
    python scripts/push_hubspot.py --all      # dry run, every candidate incl. unconfirmed
    python scripts/push_hubspot.py --push     # send
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

from common import ROOT, write_json

API = "https://api.hubapi.com"
GROUP = "toronto_startups"

SECTORS = ["Fintech", "AI/ML", "Healthtech", "B2B SaaS", "E-commerce/Retail", "Proptech",
           "Edtech", "Climate/Energy", "Cybersecurity", "Marketplace", "Consumer",
           "Hardware/Robotics", "Biotech", "Insurtech", "HR/Future of work",
           "Media/Entertainment", "Logistics", "Other"]
STAGES = ["Pre-seed", "Seed", "Series A", "Series B", "Growth", "Late stage", "Acquired", "Unknown"]
STATUSES = ["active", "acquired", "closed", "unknown"]


def enum(values):
    return [{"label": v, "value": v, "displayOrder": i} for i, v in enumerate(values)]


BOOL_OPTIONS = [{"label": "Yes", "value": "true", "displayOrder": 0},
                {"label": "No", "value": "false", "displayOrder": 1}]

# name -> (label, type, fieldType, extra)
PROPERTIES = {
    "ts_id": ("Toronto startups ID", "string", "text", {"hasUniqueValue": True}),
    "ts_sector": ("Startup sector", "enumeration", "select", {"options": enum(SECTORS)}),
    "ts_stage": ("Startup stage", "enumeration", "select", {"options": enum(STAGES)}),
    "ts_status": ("Startup status", "enumeration", "select", {"options": enum(STATUSES)}),
    "ts_employees_range": ("Employees (range)", "string", "text", {}),
    "ts_last_round": ("Last funding round", "string", "text", {}),
    "ts_last_round_date": ("Last round date", "date", "date", {}),
    "ts_last_round_amount": ("Last round amount", "string", "text", {}),
    "ts_hiring": ("Hiring", "enumeration", "booleancheckbox", {"options": BOOL_OPTIONS}),
    "ts_verified": ("Verified (directory)", "enumeration", "booleancheckbox", {"options": BOOL_OPTIONS}),
    "ts_city_confirmed": ("HQ city confirmed", "enumeration", "booleancheckbox", {"options": BOOL_OPTIONS}),
    "ts_found_in": ("Found in (directory sources)", "string", "text", {}),
    "ts_sources": ("Source URLs", "string", "textarea", {}),
    "ts_notes": ("Directory notes", "string", "textarea", {}),
}


def to_properties(r):
    """Directory record -> HubSpot properties. Unknown values are left out, never blanked."""
    b = lambda v: None if v is None else ("true" if v else "false")
    p = {
        "name": r["name"],
        "domain": r.get("domain"),
        "website": r.get("website"),
        "description": r.get("description"),
        "city": r.get("city"),
        "state": "Ontario",
        "country": "Canada",
        "address": r.get("address"),
        "founded_year": str(r["founded"]) if r.get("founded") else None,
        "linkedin_company_page": r.get("linkedin"),
        "ts_sector": r.get("sector") if r.get("sector") in SECTORS else None,
        "ts_stage": r.get("stage") if r.get("stage") in STAGES else None,
        "ts_status": r.get("status") if r.get("status") in STATUSES else None,
        "ts_employees_range": r.get("employees"),
        "ts_last_round": r.get("last_round"),
        "ts_last_round_date": r.get("last_round_date"),
        "ts_last_round_amount": r.get("last_round_amount"),
        "ts_hiring": b(r.get("hiring")),
        "ts_verified": b(r.get("verified")),
        "ts_city_confirmed": b(bool(r.get("city"))),
        "ts_found_in": ", ".join(r.get("found_in") or []) or None,
        "ts_sources": "\n".join(r.get("sources") or []) or None,
        "ts_notes": r.get("notes") or None,
    }
    return {k: v for k, v in p.items() if v not in (None, "")}


def load_token():
    token = os.environ.get("HUBSPOT_TOKEN")
    env = ROOT / ".env"
    if not token and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("HUBSPOT_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not token:
        sys.exit("HUBSPOT_TOKEN missing: set it in the environment or in .env")
    return token


class HubSpot:
    def __init__(self, token):
        self.token = token

    def call(self, method, path, body=None, retries=5):
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(retries):
            req = urllib.request.Request(API + path, data=data, method=method, headers={
                "Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    raw = resp.read()
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    time.sleep(2 ** attempt)
                    continue
                sys.exit(f"{method} {path} -> {e.code}: {e.read().decode(errors='replace')}")
        sys.exit(f"{method} {path}: gave up after {retries} retries")

    def ensure_properties(self):
        existing = {p["name"] for p in self.call("GET", "/crm/v3/properties/companies")["results"]}
        groups = {g["name"] for g in self.call("GET", "/crm/v3/properties/companies/groups")["results"]}
        if GROUP not in groups:
            self.call("POST", "/crm/v3/properties/companies/groups",
                      {"name": GROUP, "label": "Toronto startups", "displayOrder": -1})
        created = []
        for name, (label, typ, field, extra) in PROPERTIES.items():
            if name in existing:
                continue
            self.call("POST", "/crm/v3/properties/companies", {
                "name": name, "label": label, "type": typ, "fieldType": field,
                "groupName": GROUP, **extra})
            created.append(name)
        return created

    def ids_by_domain(self, domains):
        """domain -> HubSpot company id, for companies already in the portal."""
        found = {}
        for i in range(0, len(domains), 100):
            chunk = domains[i:i + 100]
            after = None
            while True:
                body = {"filterGroups": [{"filters": [
                    {"propertyName": "domain", "operator": "IN", "values": chunk}]}],
                    "properties": ["domain"], "limit": 100}
                if after:
                    body["after"] = after
                res = self.call("POST", "/crm/v3/objects/companies/search", body)
                for c in res["results"]:
                    d = (c["properties"].get("domain") or "").lower()
                    found.setdefault(d, c["id"])
                after = res.get("paging", {}).get("next", {}).get("after")
                time.sleep(0.25)  # search API: 5 requests / second
                if not after:
                    break
        return found

    def batch(self, path, inputs):
        for i in range(0, len(inputs), 100):
            self.call("POST", path, {"inputs": inputs[i:i + 100]})
            time.sleep(0.15)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="push every candidate (data/candidates.json) instead of the final list")
    ap.add_argument("--push", action="store_true", help="actually send to HubSpot")
    args = ap.parse_args()

    src = ROOT / "data" / ("candidates.json" if args.all else "startups.json")
    rows = json.loads(src.read_text(encoding="utf-8"))
    payloads = [{"ts_id": r["id"], "domain": r.get("domain"), "properties": to_properties(r)}
                for r in rows]

    if not args.push:
        (ROOT / "data" / "cache").mkdir(parents=True, exist_ok=True)
        write_json(ROOT / "data" / "cache" / "hubspot_preview.json", payloads)
        print(f"Dry run: {len(payloads)} companies from {src.name}, "
              f"{sum(1 for p in payloads if p['domain'])} with a domain. "
              f"Preview: data/cache/hubspot_preview.json. Add --push to send.")
        return

    hs = HubSpot(load_token())
    created = hs.ensure_properties()
    print(f"Custom properties created: {len(created)}")

    existing = hs.ids_by_domain(sorted({p["domain"] for p in payloads if p["domain"]}))
    updates, upserts = [], []
    for p in payloads:
        hid = existing.get(p["domain"]) if p["domain"] else None
        if hid:
            updates.append({"id": hid, "properties": {**p["properties"], "ts_id": p["ts_id"]}})
        else:
            upserts.append({"id": p["ts_id"], "idProperty": "ts_id", "properties": p["properties"]})

    hs.batch("/crm/v3/objects/companies/batch/update", updates)
    hs.batch("/crm/v3/objects/companies/batch/upsert", upserts)
    print(f"Done: {len(updates)} existing companies updated (matched on domain), "
          f"{len(upserts)} created or updated on ts_id.")


if __name__ == "__main__":
    main()
