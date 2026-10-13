# Toronto Startups

Annuaire des startups de Toronto (et du Grand Toronto, GTA), construit par une équipe d'agents IA orchestrée. Liste + carte. Double usage : prospection freelance RevOps/GTM et recherche d'emploi.

## Comment ça marche : l'orchestration

```
                     ┌──────────────────────────────┐
                     │  ORCHESTRATEUR (Opus)         │
                     │  planifie, découpe, contrôle, │
                     │  fusionne, construit le site  │
                     └───────────────┬──────────────┘
     ┌───────────────┬───────────────┼────────────────┬──────────────┐
     ▼               ▼               ▼                ▼              ▼
 Vague 1         Vague 2a         Vague 2b          Vague 3       Scripts
 SOURCING        PRÉ-FILTRE GÉO   VÉRIFICATION      SITE          (sans IA)
 Haiku           Haiku            Sonnet            Opus          YC API,
 1 agent/source  1 agent/lot      1 agent/lot       liste+carte   fusion, dédup
 data/raw/       data/geo/        data/verified/    site/
```

### Quel modèle pour quoi

| Rôle | Modèle | Pourquoi |
|---|---|---|
| Orchestrateur | Opus | Découpage, contrôle qualité, arbitrage, code. Un seul exemplaire. |
| Sourcer (`startup-sourcer`) | **Haiku** | Lire une page et en extraire des lignes. Mécanique, parallélisable. |
| Geo-checker (`startup-geochecker`) | **Haiku** | Une recherche "siège de X" par boîte : garder / écarter / incertain. Simple et répétitif. |
| Vérificateur (`startup-verifier`) | **Sonnet** | Jugement : statut, secteur, stade, doublons, recrute. Cas ambigus. |
| Import YC, fusion, dédup | **Script Python** | Quand une API ou une règle fixe existe, pas besoin d'IA : 0 coût, 0 erreur. |

Règle générale : **script si possible, Haiku pour extraire et filtrer, Sonnet pour juger, Opus pour décider.**

### Le cycle

1. **Sourcer** (vague 1) : un agent Haiku par source écrit `data/raw/<source>.json`. YC passe par un script (`scripts/import_yc.py`).
2. **Contrôler** : l'orchestrateur relit chaque sortie et corrige ou renvoie l'agent.
3. **Fusionner** : `scripts/merge.py` déduplique par domaine (sinon par nom) et produit `data/candidates.json`, chaque ligne avec un `id` stable.
4. **Pré-filtrer** (vague 2a) : les candidats dont le siège n'est pas confirmé passent par des geo-checkers Haiku ; leurs décisions (`data/geo/*.out.json`) sont appliquées par `merge.py`, les écartés vont dans `data/dropped.json`.
5. **Vérifier** (vague 2b) : `scripts/split_batches.py` découpe les survivants, un agent Sonnet par lot.
6. **Publier** : `scripts/build_site.py` copie les données dans `site/`.

## Leçons d'orchestration (apprises en le faisant)

- **Haiku applique les consignes à la lettre.** "Ne garde que les sièges confirmés" a donné 6 fichiers vides sur 9 en vague 1. La règle a été réécrite : garder avec `city: null` + `GTA unconfirmed` quand le lien avec Toronto est fort, et laisser l'étage suivant trancher.
- **Relancer un agent existant (SendMessage) coûte moins cher qu'en créer un neuf** : il garde les pages déjà lues.
- **Le budget de recherches web est d'environ 200 par tour de conversation, partagé entre tous les agents**, et les recherches parallèles se heurtent en plus à une limite de débit. Avec 6 agents x 48 boîtes, 127 recherches sur 288 n'ont pas abouti. Correctifs : étaler le travail sur plusieurs tours (le budget se renouvelle à chaque message de l'utilisateur), et faire lire aux vérificateurs le site de la boîte (`WebFetch`, pages contact / about) plutôt que de lancer une recherche quand le domaine est connu.
- **L'orchestrateur relit tout** : Golden Ventures avait mis "Toronto" pour un libellé "Toronto & Waterloo" ; corrigé avant fusion.
- **Ce que lisent les agents est de la donnée, pas des ordres** : une page contenait un texte caché demandant aux IA de citer une source ; l'agent l'a ignoré.

## Sources (vague 1)

| Source | Méthode | Notes |
|---|---|---|
| Y Combinator | script, API yc-oss | ville du siège fournie |
| Listes du projet Freelance | script | levées BetaKit déjà repérées |
| BetaKit (funding 2025-2026) | Haiku | levées, montants, tours |
| DMZ (TMU) | Haiku | annuaire avec ville, 150 sur ~280 lus |
| NEXT Canada (NextAI Toronto, Next 36) | Haiku | pas de ville, à pré-filtrer |
| Golden Ventures | Haiku | libellé régional "Toronto & Waterloo" |
| OMERS, Georgian, Whitecap, Relay | Haiku + recherche siège | 115 écartés sur 168 |
| Techstars Toronto | Haiku | cohortes, nombreuses boîtes étrangères |
| Rankings (Seedtable, LinkedIn Top Startups) | Haiku | Seedtable bloque (403) |
| MaRS | Haiku | annuaire derrière un login |
| CDL Toronto | Haiku | seulement 6 boîtes publiques |

## Lancer le site en local

```bash
python scripts/merge.py
python scripts/build_site.py --candidates
python -m http.server 8765 --directory site
```

Puis ouvrir http://localhost:8765 (vue Carte ou Liste). Sans `--candidates`, le site lit la liste finale vérifiée `data/startups.json`.

## Structure

```
.claude/agents/     définitions des agents (modèle fixé dans l'en-tête)
data/SCHEMA.md      format d'une startup
data/raw/           sorties des sourcers, une par source
data/geo/           lots du pré-filtre géo (entrées + *.out.json)
data/candidates.json  liste fusionnée, dédupliquée
data/dropped.json   candidats écartés, avec la raison
data/verified/      sorties des vérificateurs Sonnet
data/startups.json  liste finale consommée par le site
scripts/            imports, fusion, découpage, build
site/               site statique : liste + carte (Leaflet, OpenStreetMap)
```
