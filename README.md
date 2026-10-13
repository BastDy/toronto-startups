# Toronto Startups

Annuaire des startups de Toronto (et du Grand Toronto, GTA), construit par une équipe d'agents IA orchestrée. Double usage : prospection freelance RevOps/GTM et recherche d'emploi.

## Comment ça marche : l'orchestration

```
                 ┌─────────────────────────────┐
                 │  ORCHESTRATEUR (Opus)        │
                 │  planifie, découpe, vérifie, │
                 │  fusionne, construit le site │
                 └──────────────┬──────────────┘
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
  Vague 1 : SOURCING     Vague 2 : VÉRIFICATION   Vague 3 : SITE
  N agents Haiku         M agents Sonnet          orchestrateur
  1 agent = 1 source     1 agent = 1 lot          data/startups.json
  -> data/raw/*.json     -> data/verified/*.json  -> site/
```

### Pourquoi deux modèles différents

| Rôle | Modèle | Pourquoi |
|---|---|---|
| Orchestrateur | Opus | Décisions : découpage du travail, contrôle qualité, arbitrage des doublons, code du site. Un seul exemplaire, donc le coût reste maîtrisé. |
| Sourcer (`startup-sourcer`) | **Haiku** | Tâche mécanique et répétitive : lire une page (portfolio, annuaire YC, article BetaKit) et en extraire des lignes structurées. Rapide, peu cher, parallélisable sur 8 à 10 sources. |
| Vérificateur (`startup-verifier`) | **Sonnet** | Tâche de jugement : la boîte est-elle vraiment basée à Toronto ? Toujours active ? Quel secteur ? Est-ce un doublon ? Haiku se trompe plus souvent sur ces cas ambigus. |

Règle générale : **Haiku pour extraire, Sonnet pour juger, Opus pour décider.**

### Le cycle

1. **Planifier** : l'orchestrateur liste les sources (voir ci-dessous) et attribue une source par agent sourcer.
2. **Sourcer (parallèle)** : chaque agent Haiku écrit `data/raw/<source>.json` au format du schéma.
3. **Contrôler** : l'orchestrateur relit chaque fichier (volume, champs vides, hors-Toronto évidents) et relance un agent si la sortie est mauvaise.
4. **Fusionner** : `scripts/merge.py` déduplique par domaine web et produit une liste unique.
5. **Vérifier (parallèle)** : la liste est coupée en lots de ~40 ; chaque agent Sonnet vérifie ville, statut, secteur, stade, et écrit `data/verified/<lot>.json`.
6. **Publier** : fusion finale dans `data/startups.json`, puis le site statique `site/` lit ce fichier (recherche, filtres secteur / stade / ville / recrute).

Les définitions des agents sont dans [.claude/agents/](.claude/agents/) : un fichier par rôle, avec le modèle fixé dans l'en-tête (`model: haiku` / `model: sonnet`).

## Sources prévues (vague 1)

| # | Source | Ce qu'on y trouve |
|---|---|---|
| 1 | Y Combinator directory (région Toronto) | Startups YC basées à Toronto |
| 2 | BetaKit (rubrique funding) | Levées récentes, montants, tours |
| 3 | MaRS Discovery District | Startups accompagnées / IAF |
| 4 | DMZ (Toronto Metropolitan University) | Portfolio incubateur |
| 5 | Creative Destruction Lab Toronto | Startups deep tech / IA |
| 6 | Techstars Toronto | Portfolio accélérateur |
| 7 | VC torontois : Golden Ventures, OMERS Ventures, Georgian, Radical Ventures, Inovia (bureau Toronto) | Portfolios |
| 8 | NEXT Canada (Next 36 / NextAI) | Startups fondées par les cohortes |
| 9 | Listes existantes du projet Freelance (`02-prospection/listes/`) | ~48 startups torontoises déjà repérées |

## Schéma d'une startup

Voir [data/SCHEMA.md](data/SCHEMA.md).

## Structure

```
.claude/agents/   définitions des agents (sourcer = Haiku, verifier = Sonnet)
data/raw/         sorties brutes des sourcers, une par source
data/verified/    sorties des vérificateurs, une par lot
data/startups.json  liste finale consommée par le site
scripts/          fusion, déduplication, contrôles
site/             site statique (HTML/CSS/JS, sans build)
```
