# Cockpit opérateur — application web (backend + frontend)

Complément web d'Obsidian pour le Système Autonome de Diagnostic Marketing.
Deux moitiés, lancées ensemble par un seul script :

| Dossier | Rôle | Techno |
|---|---|---|
| `backend/` | Façade HTTP **strictement en lecture seule** au-dessus du vault et du grand livre | FastAPI |
| `frontend/` | SPA de pilotage (6 écrans) | React 18 + Vite + TypeScript |

Le cockpit **ne modifie jamais rien** : aucune écriture vault, aucune transition
d'état, aucun appel d'API externe, aucun `api_io`. Il lit, il agrège, il affiche.

---

## Lancement conjoint (recommandé)

```bash
# 1. dépendances (une fois)
pip install -r webapp/backend/requirements.txt
cd webapp/frontend && npm install && cd ../..

# 2. tout démarrer, front déjà branché sur le vrai backend
./webapp/start-dev.sh
```

- API : <http://localhost:8000> — documentation interactive sur `/docs`
- Front : <http://localhost:5173> — écran GreenIT sur `/greenit`
- `Ctrl-C` arrête **les deux** processus (trap sur les groupes de processus :
  pas d'uvicorn orphelin qui garde le port occupé).

### Options

```bash
./webapp/start-dev.sh --help
./webapp/start-dev.sh --vault /data/vault-prod          # autre vault
./webapp/start-dev.sh --api-port 8010 --web-port 5180   # autres ports
./webapp/start-dev.sh --ledger /data/api_usage.log      # autre grand livre
./webapp/start-dev.sh --mocks                           # front en fixtures locales
VAULT_PATH=/data/vault ./webapp/start-dev.sh            # équivalent par l'env
```

Le script charge `webapp/.env` s'il existe (voir `webapp/.env.example`), résout
les chemins relatifs depuis la racine du dépôt, vérifie que FastAPI/uvicorn et
npm sont présents, installe les dépendances npm manquantes, et prévient (sans
bloquer) si le vault ou le grand livre sont absents.

### Configuration

```bash
cp webapp/.env.example webapp/.env
```

| Variable | Rôle | Défaut |
|---|---|---|
| `VAULT_PATH` | racine du vault Obsidian lu par l'API | `<repo>/vault` |
| `API_USAGE_LOG` | grand livre d'usage (JSONL) — source de `/api/usage`, `/api/greenit` et du flux temps réel | `<repo>/api_usage.log` |
| `RUNS_LOG` | journal d'écritures vault (`/api/runs`) | `<repo>/runs.log` |
| `PREFLIGHT_ROOT_DIR` | racine du contrôle `tests_verts` du préflight (le pointer sur un dossier vide évite de relancer `pytest tests/` à chaque appel) | `<repo>` |
| `API_PORT` / `WEB_PORT` | ports d'uvicorn et de Vite | `8000` / `5173` |
| `VITE_USE_MOCKS` | `false` = front branché sur le backend ; `true` = fixtures locales | `false` via `start-dev.sh`, `true` en `npm run dev` seul |
| `VITE_API_TARGET` | cible du proxy Vite pour `/api` | `http://localhost:8000` |

---

## Lancement séparé

```bash
# Backend seul
VAULT_PATH=vault uvicorn webapp.backend.app:app --reload --port 8000

# Front seul, branché sur le backend ci-dessus
cd webapp/frontend && VITE_USE_MOCKS=false npm run dev

# Front seul, hors-ligne (fixtures)
cd webapp/frontend && npm run dev
```

---

## Écrans

| Route | Contenu |
|---|---|
| `/` | verdict GO/NO-GO, entonnoir du pipeline, tuiles de coûts |
| `/prospects` | table filtrable (statut / persona / marché), tri par score |
| `/prospects/:slug` | fiche complète + rendu Markdown sûr du rapport |
| `/usage` | coûts API par fournisseur, top fiches, taux de cache |
| **`/greenit`** | **efficience en temps réel** : coût, énergie, CO₂e, octets, flux SSE des appels, ventilation par modèle et fournisseur, économies du cache |
| `/preflight` | les 9 contrôles GO/NO-GO avec niveau et pastille |

---

## Observabilité GreenIT

L'écran `/greenit` et les routes `/api/greenit*` lisent les champs d'empreinte
optionnels du grand livre (`octets_entrants`, `octets_sortants`, `duree_ms`,
`energie_wh`, `co2e_g`, `modele`, `profil`). La lecture est **défensive** : une
ligne écrite avant l'instrumentation, sans aucun de ces champs, compte pour zéro
en empreinte et ne fait tomber ni l'API ni l'écran.

> ⚠️ **Énergie et CO₂e sont des ESTIMATIONS.** Elles proviennent des facteurs
> paramétrables de `knowledge/greenit.yaml` : des ordres de grandeur destinés à
> comparer des scénarios entre eux (avec ou sans cache, petit ou gros modèle).
> Ce ne sont pas des mesures certifiées, et elles ne constituent pas un bilan
> carbone opposable. L'API le déclare (`estimation`, `note_estimation`,
> `couverture_greenit`) et l'écran affiche un bandeau permanent qui le rappelle.
> Le **coût**, lui, est calculé depuis `knowledge/api_pricing.yaml`.

---

## Tests

```bash
python -m pytest webapp/backend/tests -q     # 45 tests
cd webapp/frontend && npm run test           # 34 tests (Vitest)
cd webapp/frontend && npm run build          # typecheck + bundle
```
