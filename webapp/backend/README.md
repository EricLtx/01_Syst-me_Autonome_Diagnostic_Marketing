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
| GET | `/api/greenit?depuis=<YYYY-MM-DD?>` | agrégat d'efficience (voir ci-dessous) |
| GET | `/api/greenit/stream` | flux **SSE** temps réel du grand livre (voir ci-dessous) |

## Observabilité GreenIT

### `GET /api/greenit`

Agrège `api_usage.log` sur l'axe **efficience** (coût + empreinte + volume),
là où `/api/usage` ne regarde que le coût.

```jsonc
{
  "cout_total_usd": 12.47, "devise": "USD",
  "energie_wh_total": 41.8,        // ⚠ ESTIMATION
  "co2e_g_total": 6.94,            // ⚠ ESTIMATION
  "octets_total": 27918336,
  "duree_ms_totale": 186420.0,
  "nb_appels": 214, "nb_cache_hits": 96, "nb_erreurs": 3,
  "nb_lignes_illisibles": 0, "taux_cache": 0.3097,
  "economies": {                   // déduites des cache-hits (1 hit = 1 appel évité)
    "appels_evites": 96, "cout_evite_usd": 5.59,
    "energie_wh_evitee": 18.75, "co2e_evite_g": 3.11,
    "methode": "ESTIMATION — chaque cache-hit est valorisé à la moyenne des appels réels de même (fournisseur, endpoint)…"
  },
  "par_modele":      [{"modele": "claude-haiku-4-5", "nb_appels": 34, "tokens": 98400, "cout": 4.62, "energie_wh": 22.1, "co2e_g": 3.66, "octets": 4812800, "duree_ms": 91200}],
  "par_fournisseur": [{"fournisseur": "anthropic",   "nb_appels": 41, "tokens": 128400, "cout": 7.83, "energie_wh": 34.5, "co2e_g": 5.72, "octets": 6811648, "duree_ms": 130100}],
  "estimation": true,
  "note_estimation": "energie_wh et co2e_g sont des ESTIMATIONS…",
  "source_facteurs": "knowledge/greenit.yaml",
  "couverture_greenit": 0.87,      // part des appels réels portant des champs d'empreinte
  "ledger_present": true, "ledger_path": "/…/api_usage.log"
}
```

Conventions (identiques à `diagnostic.usage.agreger`, contrat cohérent entre les
deux vues) : un **cache-hit n'est pas un appel** (il alimente `nb_cache_hits`) ;
un appel `budget_depasse` compte dans `nb_appels` mais n'a **rien** dépensé,
donc ni coût ni empreinte.

> ⚠️ **`energie_wh` et `co2e_g` sont des ESTIMATIONS**, calculées à partir des
> facteurs paramétrables de `knowledge/greenit.yaml` (ordres de grandeur pour
> comparer des scénarios). Ce ne sont pas des mesures certifiées et elles ne
> constituent pas un bilan carbone opposable. Les champs `estimation`,
> `note_estimation` et `couverture_greenit` portent cet avertissement dans la
> réponse elle-même. Les « économies » sont doublement estimées : un appel qui
> n'a pas eu lieu n'a pas de coût connu, on l'approche par la **moyenne des
> appels réels de même (fournisseur, endpoint)** ; sans jumeau, l'économie vaut
> 0 plutôt qu'une extrapolation.

### `GET /api/greenit/stream` — Server-Sent Events

Suit `api_usage.log` en direct (tail incrémental par offset d'octets) et pousse
une trame par nouvelle ligne. `Content-Type: text/event-stream`.

| Paramètre | Défaut | Rôle |
|---|---|---|
| `historique` | `0` | rejoue les N dernières lignes déjà journalisées à l'ouverture (0-200) |
| `limite` | `0` | nombre max d'événements `appel` avant fermeture (0 = illimité) |
| `duree_max_s` | `300` | durée de vie maximale du flux |
| `intervalle_s` | `1.0` | période de scrutation du fichier |
| `heartbeat_s` | `15` | période des trames `heartbeat` (garde la connexion vivante) |
| `depuis_debut` | `false` | suit depuis l'octet 0 au lieu de la fin du fichier |

Événements : `init` (offset, présence du ledger, avertissement d'estimation),
`appel` (une ligne normalisée : champs GreenIT toujours présents, à 0/`null`
s'ils manquent dans le ledger), `heartbeat`, `fin` (`raison` :
`limite` | `duree_max` | `deconnexion`).

```bash
curl -N "http://localhost:8000/api/greenit/stream?historique=10&heartbeat_s=5"
```

Robustesse du tail : une ligne en cours d'écriture (sans `\n` final) est mise en
tampon et publiée seulement une fois complète ; une troncature ou rotation du
fichier fait repartir la lecture de zéro ; un fichier absent ne produit ni
erreur ni événement.

**Bornage obligatoire en test** : ouvrir le flux avec `limite` et/ou un
`duree_max_s` court, sinon la requête tourne jusqu'à `duree_max_s` (300 s).

## Tests

```bash
python -m pytest webapp/backend/tests -q
```

## Architecture interne

- `app.py` : application FastAPI + routes (minces) + CORS + générateur SSE.
- `services.py` : adaptateurs au-dessus de `diagnostic/*` — **seul** endroit qui
  touche `VaultIO`, `usage`, `preflight`, `icp_schema`. Read-only strict.
- `schemas.py` : modèles de réponse Pydantic (contrat de sortie stable).
- `greenit.py` : lecture **défensive** du grand livre + agrégation d'efficience
  + tail incrémental pour le SSE. Volontairement séparé de `services.py`.
  `LedgerEntry` sait relire les lignes enrichies (les 7 champs GreenIT y sont
  déclarés) — la raison n'est pas la compatibilité amont, mais la **nature du
  schéma** : `LedgerEntry` est un contrat d'**écriture**, strict par
  construction (`extra="forbid"`, `ts: datetime`, `resultat` en `Literal`).
  Une vue de consultation a le devoir inverse — ne jamais tomber sur ce qu'elle
  lit. La validation stricte lève (vérifié par exécution) sur un **champ
  futur** (`pue`, `region_datacenter`… → 500 tant que webapp n'a pas rattrapé
  le schéma, pour un champ qui ne la concerne pas) et sur une **ligne
  dégradée** (`ts` malformé, `unites: null`, `resultat` hors énumération —
  cas normaux d'un journal append-only lu pendant qu'un autre processus écrit).
  On parse donc le JSONL brut avec des défauts (0 / `None`) et on compte
  l'illisible (`nb_lignes_illisibles`) : ledger absent, ancien, enrichi, en
  avance sur nous ou panaché, la réponse reste 200.
```
