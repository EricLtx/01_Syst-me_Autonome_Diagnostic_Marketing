# Cockpit opérateur — API backend (lecture seule)

Façade HTTP **strictement en lecture seule** au-dessus du système de diagnostic
marketing. Elle alimente le front-end React (cockpit opérateur, complément
d'Obsidian). Elle lit le vault via le bus `vault_io` et les agrégats via les
modules existants (`usage`, `preflight`, `icp_schema`).

Ce qu'elle **ne fait jamais** : aucune écriture vault, aucun appel réseau
sortant, aucune transition d'état, aucun appel à `api_io.call`. Pas de
dépendance `requests` ni `anthropic`.

## Installation

```bash
pip install -r webapp/backend/requirements.txt
```

## Lancement

Depuis la racine du dépôt :

```bash
# Vault par défaut : <racine_repo>/vault
uvicorn webapp.backend.app:app --reload --port 8000

# Vault explicite via VAULT_PATH
VAULT_PATH=/chemin/vers/vault uvicorn webapp.backend.app:app --port 8000
```

API sur `http://localhost:8000`, documentation interactive sur
`http://localhost:8000/docs`.

### Variables d'environnement

| Variable | Rôle | Défaut |
|---|---|---|
| `VAULT_PATH` | racine du vault Obsidian | `<repo>/vault` |
| `API_USAGE_LOG` | grand livre d'usage API | `<repo>/api_usage.log` |
| `RUNS_LOG` | journal d'écritures vault | `<repo>/runs.log` |
| `PREFLIGHT_ROOT_DIR` | racine du contrôle `tests_verts` du préflight (permet d'éviter de relancer `pytest tests/` en sous-processus) | `<repo>` |

Toutes les routes dégradent proprement quand le vault est vide/absent (listes
vides, funnel à zéro, préflight souvent NO-GO en AS-IS).

## CORS

Origines autorisées (front de dev Vite) : `http://localhost:5173` et
`http://127.0.0.1:5173`.

## Endpoints (base `http://localhost:8000`, tout sous `/api`, JSON)

| Méthode | Route | Réponse |
|---|---|---|
| GET | `/api/health` | `{status, vault_path, vault_initialise}` |
| GET | `/api/preflight?icp=<id?>` | `{verdict:"GO"\|"NO-GO", checks:[{nom, niveau, ok, message}]}` |
| GET | `/api/pipeline/funnel` | `{total, etats:{decouvert, diagnostique, valide, contacte, rejete}}` |
| GET | `/api/prospects?statut&persona&marche` | `[{slug, nom, site_web, statut, persona, marche, score_global, signal_chaud, gaps_majeurs, date_creation, date_diagnostic, icp_id, opt_out, contact_nom, contact_email}]` |
| GET | `/api/prospects/{slug}` | `{fiche:{…}, rapport_md:str\|null}` |
| GET | `/api/usage?depuis=<YYYY-MM-DD?>` | `{cout_total_usd, devise, nb_appels, nb_cache_hits, taux_cache, par_fournisseur:[…], top_fiches:[…]}` |
| GET | `/api/icp` | `[{icp_id, persona, marche, description}]` |
| GET | `/api/runs?limit=50` | `[ objets JSONL de runs.log ]` (best-effort, `[]` si absent) |

## Tests

```bash
python -m pytest webapp/backend/tests -q
```

## Architecture interne

- `app.py` : application FastAPI + routes (minces) + CORS.
- `services.py` : adaptateurs au-dessus de `diagnostic/*` — **seul** endroit qui
  touche `VaultIO`, `usage`, `preflight`, `icp_schema`. Read-only strict.
- `schemas.py` : modèles de réponse Pydantic (contrat de sortie stable).
```
