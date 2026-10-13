# Schéma d'une startup

Chaque fichier de `data/raw/` et `data/verified/` est un tableau JSON d'objets :

```json
{
  "name": "Wealthsimple",
  "website": "https://www.wealthsimple.com",
  "domain": "wealthsimple.com",
  "description": "Online investing and money management platform.",
  "sector": "Fintech",
  "city": "Toronto",
  "founded": 2014,
  "stage": "Late stage",
  "employees": "1001-5000",
  "last_round": "Series E",
  "last_round_date": "2025-10-01",
  "last_round_amount": "CAD 750M",
  "linkedin": "https://www.linkedin.com/company/wealthsimple",
  "hiring": true,
  "sources": ["https://www.ycombinator.com/companies/wealthsimple"],
  "status": "active",
  "verified": false,
  "notes": ""
}
```

## Règles

- `domain` : clé de déduplication, en minuscules, sans `www.` ni chemin.
- `name`, `sources` : obligatoires. Les autres champs : `null` si inconnu, **jamais inventés**.
- `city` : ville du siège dans le Grand Toronto (Toronto, Mississauga, Markham, Vaughan, Oakville, Richmond Hill...). Hors GTA = exclu. En sourcing, `null` autorisé si la source rattache fortement la boîte à Toronto sans préciser le siège (cohorte torontoise, portfolio local) : `notes` commence alors par `GTA unconfirmed:` et le vérificateur tranche.
- `sector` : une valeur parmi `Fintech`, `AI/ML`, `Healthtech`, `B2B SaaS`, `E-commerce/Retail`, `Proptech`, `Edtech`, `Climate/Energy`, `Cybersecurity`, `Marketplace`, `Consumer`, `Hardware/Robotics`, `Biotech`, `Insurtech`, `HR/Future of work`, `Media/Entertainment`, `Logistics`, `Other`.
- `stage` : `Pre-seed`, `Seed`, `Series A`, `Series B`, `Growth`, `Late stage`, `Acquired`, `Unknown`.
- `status` : `active`, `acquired`, `closed`, `unknown`.
- `verified` : `false` en sortie de sourcing, `true` après passage d'un vérificateur Sonnet.
