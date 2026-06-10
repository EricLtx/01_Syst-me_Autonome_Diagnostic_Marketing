# CLAUDE.md — contexte projet pour Claude Code

> Ce fichier est lu automatiquement par Claude Code à chaque session. C'est
> sa mémoire du projet. `/init` peut le (re)générer ; ici il est pré-rempli.
> Le tenir à jour est l'étape la plus rentable et la plus souvent oubliée.

## Ce qu'est ce projet

Écosystème d'agents de prospection pour une consultante en marketing / branding.
Deux livrables complets :

- **J1 — pipeline diagnostic** : entrée = une entreprise ; sortie = score + mini-audit
  de marque. Cible : persona 1 (installateur HVAC), séquence Québec → Suisse.
- **J2 — bus vault** : couche de persistance Obsidian. Le pipeline J1 écrit dans
  un vault structuré ; un opérateur humain valide et pilote via Obsidian. Audit de
  marque complet, traçable, versionné.

## Architecture (à respecter)

### J1 — Pipeline diagnostic

Chaîne : `entrée → collecteurs → signaux → scoring → synthèse+QA → sortie`.

1. **Collecte déterministe ≠ raisonnement LLM.** Les collecteurs vont chercher
   des faits ; le LLM (`synthesis.py`) rédige à partir de faits déjà établis.
   Le LLM ne fetch jamais.
2. **Collecteurs isolés et enfichables** (héritent de `Collector`, échec via
   `safe_collect`). On en ajoute un sans toucher aux autres.
3. **La rubrique est une donnée** (`knowledge/rubric_*.yaml`), jamais du code.
   Nouveau persona = nouvelle rubrique, `scoring.py` ne bouge pas.
4. **QA avant sortie** : aucune affirmation non adossée aux failles réelles.

### J2 — Bus vault (architecture micro-ordinateur)

| Rôle | Composant |
|------|-----------|
| RAM / stockage persistant | `vault/` — fichiers Markdown + frontmatter YAML |
| Contrôleur de bus | `diagnostic/vault_io.py` — *seul* module autorisé à lire/écrire |
| CPU | agents (pipeline J1, découverte J3, outreach J4) |
| ROM | rubrics YAML + templates (lecture seule pour les agents) |
| Disque | cache de scraping brut, **toujours hors du vault** (contrainte G9) |
| Console | opérateur humain via Obsidian (validation, manage-by-exception) |

Règles non négociables J2 :
- **Écriture atomique uniquement** : tmp dans le même répertoire + `os.replace()`.
  Aucun autre module ne doit appeler `os.replace()` (testé via AST walk).
- **Journal append-only** : `runs.log` JSONL, une ligne par opération d'écriture.
  Jamais écrit directement par les agents — uniquement via `VaultIO._journal()`.
- **Schéma validé à l'écriture** : `FicheProspect` (Pydantic v2) valide chaque
  frontmatter avant persistance.
- **Machine à états respectée** : `decouvert → diagnostique → valide → contacte`,
  `* → rejete` (humain seulement). Agent autorisé : `decouvert → diagnostique`
  uniquement. Transitions en dehors de ce registre → `ValueError`.

### Schéma vault

```
vault/
├─ 10-Prospects/
│  ├─ persona1-quebec/          ← fiches Markdown (frontmatter YAML)
│  ├─ persona1-romandie/
│  ├─ persona2-france/
│  └─ …
├─ 20-Rubrics/                  ← copies des rubric_*.yaml (lecture seule)
├─ 30-Diagnostics/              ← rapports générés (un par fiche diagnostiquée)
├─ 90-Systeme/
│  ├─ memory-map.md             ← plan d'adressage (généré, ne pas éditer)
│  └─ journal-decisions.md      ← log humain des décisions (éditable)
├─ _templates/
│  └─ fiche-prospect.md         ← gabarit de nouvelle fiche
└─ 00-Dashboard.md              ← 3 requêtes Dataview (pipeline, top gaps, relance)
```

## Commandes

```bash
# Installation
pip install -r requirements.txt

# Initialiser le vault (idempotent — peut être relancé sans risque)
python init_vault.py
python init_vault.py --vault chemin/vers/vault   # ou $VAULT_PATH

# Diagnostic d'une entreprise (mode standard — sortie console/JSON)
python run_diagnostic.py --nom "Climatisation Tremblay" --url "https://..." --region "Québec, QC"
python run_diagnostic.py --nom "..." --url "..." --json   # sortie JSON complète

# Traiter toutes les fiches 'decouvert' dans le vault
python run_diagnostic.py --out vault
python run_diagnostic.py --out vault --vault chemin/vers/vault

# Tests
pytest tests/ -v
pytest tests/ -v -k "vault"       # seulement les tests vault
pytest tests/ -v -k "integration" # test end-to-end §8.6
```

## Conventions

- Python 3.10+, type hints partout, `from __future__ import annotations`.
- Commentaires en français, orientés "pourquoi" plutôt que "quoi".
- Scraping poli : User-Agent honnête, timeout, cache disque, une requête par cible.
- Pas de secret en dur. Clé LLM via `ANTHROPIC_API_KEY` (optionnelle).
  Clé Anthropic → synthèse LLM ; sans clé → repli déterministe (tourne hors-ligne).
- Pydantic v2 : `model_dump(mode="json")` pour la sérialisation YAML-safe.
- `failles or []` est faux pour une liste vide — toujours tester `if x is not None`.

## État des tests (101 au total)

| Fichier | Couverture | Nb |
|---------|-----------|-----|
| `test_j1_smoke.py` | Pipeline end-to-end (smoke) | 6 |
| `test_vault_schema.py` | FicheProspect, enums, transitions | 15 |
| `test_vault_io.py` | VaultIO (écriture atomique, journal, query, transition) | 30 |
| `test_vault_init.py` | Scaffold idempotent, dashboard, template, git | 25 |
| `test_serializers.py` | diagnostic_to_fiche, diagnostic_to_rapport_md | 18 |
| `test_integration_vault.py` | Pipeline complet → fiche + rapport + journal | 7 |

## Prochaines tâches (J3)

- Agent découverte : collector Apollo (ou enrichissement LinkedIn) → fiches `decouvert`
  créées automatiquement dans le vault.
- Activation des 4 stubs collecteurs (GBP, avis, SEO, social) avec vraies API.
- `rubric_persona2.yaml` (cabinet d'avocats ou autre persona 2).
- Orchestrateur cron (traitement batch planifié).
