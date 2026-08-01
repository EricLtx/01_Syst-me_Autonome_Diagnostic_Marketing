# Gouvernance de revue itérative — écosystème d'agents

> Journal d'ancrage des revues anti-hallucination. Tenu par l'agent chef de
> projet (autorité ultime). L'écosystème d'agents est **conservé** d'une
> itération à l'autre : on relance les mêmes agents (contexte préservé) avec un
> backlog de correctifs, on ne re-spawne pas d'agents neufs.

## Principe

Chaque **chantier** (CORE, BACKEND, FRONTEND, …) est livré par itérations. Après
chaque itération, l'**agent de revue** :

1. **Vérifie** un jeu d'assertions *checkables par exécution* (tests, build, AST,
   `git diff`, conformité de contrat) — jamais une simple opinion.
2. **Ancre** ses trouvailles dans ce journal (une entrée horodatée par itération).
3. Calcule le **taux de cohérence** = `assertions vérifiées / assertions totales`.
4. **Porte 97 %** : si `taux < 97 %`, le chef de projet **relance** l'agent
   d'implémentation concerné (même agent, contexte conservé) avec la liste des
   assertions échouées comme backlog, puis **re-revue**. Boucle jusqu'à ≥ 97 %.

> Le taux est ancré dans des faits reproductibles : une assertion n'est comptée
> « vérifiée » que si sa commande de contrôle passe réellement. Avec ~10–14
> assertions par chantier, le seuil de 97 % impose de facto **zéro échec dur**
> (une seule assertion ratée fait tomber sous le seuil) — exigence appropriée
> pour du code.

## Assertions de contrôle — Chantier CORE (orchestration DAG)

| # | Assertion | Contrôle |
|---|-----------|----------|
| C1 | Suite complète verte (365 + nouveaux) | `python -m pytest tests/ -q` |
| C2 | `orchestrator.py`, `run_pipeline.py`, `dag_pipeline.yaml` créés et non triviaux | inspection |
| C3 | `orchestrator.py` + `run_pipeline.py` sans import `requests`/`anthropic` au niveau module | AST / grep |
| C4 | `_check_garde_fous_bus` étendu aux 2 nouveaux modules | grep + exécution du check |
| C5 | `run_discovery.py` passe `budgets=` à `ApiIO` | grep |
| C6 | `run_diagnostic.py` instancie un `ApiIO` unique et l'injecte au pipeline | grep / inspection |
| C7 | `dag_pipeline.yaml` valide, tri topologique sain, `outreach` en `enabled:false` | chargement |
| C8 | Verrou de run (refus de démarrage concurrent) | test dédié |
| C9 | Machine à états : orchestrateur limité à `decouvert→diagnostique` | test / inspection |
| C10 | Aucun fichier hors périmètre modifié | `git diff --name-only` |
| C11 | `python run_pipeline.py --help` fonctionne | exécution |
| C12 | Rétro-compat : les `run_*.py` existants tournent toujours seuls | smoke |

## Assertions de contrôle — Chantier BACKEND (FastAPI read-only)

| # | Assertion | Contrôle |
|---|-----------|----------|
| B1 | Tests backend verts | `python -m pytest webapp/backend/tests -q` |
| B2 | 8 endpoints du contrat présents | inspection routes |
| B3 | Lecture seule stricte (aucun `.write_*`/`.transition`/`api_io`) | grep |
| B4 | Import propre + démarrage uvicorn | exécution |
| B5 | Dégradation propre vault vide | test |
| B6 | `Check.message` renvoyé tel quel (pas `detail`) | inspection |
| B7 | Aucun fichier hors `webapp/backend/` | `git diff --name-only` |

## Assertions de contrôle — Chantier FRONTEND (React + Vite + TS)

| # | Assertion | Contrôle |
|---|-----------|----------|
| F1 | `npm run build` (tsc + vite) réussit | exécution |
| F2 | `npm run test` (vitest) passe | exécution |
| F3 | 5 écrans/routes présents (Dashboard, Prospects, Détail, Usage, Préflight) | inspection |
| F4 | Mode mock : app buildée/démontrable hors-ligne | exécution |
| F5 | Tokens thème clair **et** sombre | inspection `theme.css` |
| F6 | Types alignés sur le contrat d'API | inspection `types.ts` |
| F7 | Accessibilité de base (focus visible, aria sur graphiques, reduced-motion) | inspection |
| F8 | Aucun fichier hors `webapp/frontend/` | `git diff --name-only` |

## Journal des itérations (ancrage)

> Entrées ajoutées par le chef de projet après chaque revue. Format :
> `AAAA-MM-JJ · chantier · itération n · taux · verdict · backlog relancé`.

### Itération 1 — Palier 1 / J+30 (2026-08-01)

Vérification factuelle par le chef de projet + audit indépendant de l'agent de
revue anti-hallucination (re-exécution réelle de chaque contrôle, aucun rapport
d'agent pris pour argent comptant).

| Chantier | Assertions | Taux | Verdict | Backlog relancé |
|----------|:----------:|:----:|---------|-----------------|
| CORE (orchestrateur DAG, `36380c8`) | 12/12 | **100 %** | CLEARED | — |
| BACKEND (API FastAPI read-only, `b5430d1`) | 7/7 | **100 %** | CLEARED | — |
| FRONTEND (cockpit React, `25ea9d0`) | 8/8 | **100 %** | CLEARED | — |

**Preuves clés (exécutées) :** `pytest tests/` → 403 passed (365 intacts + 38
nouveaux) ; `pytest webapp/backend/tests` → 18 passed ; `npm run build` OK +
`npm run test` → 17 passed. Garde-fou AST étendu et vert ; ApiIO unique injectée
**par identité** (test `... is api`) ; orchestrateur borné à
`decouvert→diagnostique` (porte humaine jamais franchie) ; backend strictement
lecture seule (aucune écriture vault, aucun `api_io`).

**Hallucinations détectées : aucune.** Toutes les affirmations des messages de
commit confirmées par exécution. Invariants d'architecture tenus (vault_io seul
écrivain, api_io seul réseau sortant).

**Trouvaille corrigée (hygiène, basse) :** caches `*.tsbuildinfo` committés par
inadvertance → ajoutés au `.gitignore` et dé-suivis.

Porte 97 % franchie sur les trois chantiers, aucune relance nécessaire.

### Itération 2 — GreenIT / WebApp / Intégration / Documentation (2026-08-01)

Audit indépendant de l'agent de revue — **29 assertions ré-exécutées**, aucun
rapport d'agent pris pour argent comptant.

| Chantier | Assertions | Taux | Verdict | Backlog relancé |
|----------|:----------:|:----:|---------|-----------------|
| GREENIT (`6055e14`) | 9/9 | **100 %** | CLEARED | — |
| INTÉGRATION (`0234af3`) | 7/7 | **100 %** | CLEARED | — |
| WEBAPP (`d5b14d1`) | 7/7 | **100 %** | CLEARED | — |
| DOCUMENTATION (`4585a10`) | 5/6 | **83,3 %** | **RELANCE** | D4 — chiffres cockpit périmés |

**Preuves clés (exécutées) :** `pytest tests/` → 527 passed (dont 46 e2e) ;
`pytest webapp/backend/tests` → 38 ; `npm run build` OK + 34 tests front ;
`tests/test_greenit.py` → 78. Routage GreenIT déterministe et sans LLM (haiku
par défaut, escalade sonnet sur règle YAML) ; cache-hit → coût ET empreinte à 0
vérifiés sur ledger réel ; `synthesize()` sans clé avec `socket.connect` bloqué →
repli déterministe, `anthropic` jamais importé ; `/api/greenit` répond 200 sur
ledger absent / ancien / panaché+corrompu ; SSE clos en 2,0 s ; backend lecture
seule prouvé par AST ; `run_preflight.py` → code 1 (NO-GO structurel confirmé).

**Hallucinations détectées : 4.**
1. `d5b14d1` justifiait la séparation de l'agrégat par un `extra="forbid"` qui
   rejetterait les lignes enrichies — **faux**, `6055e14` avait déjà étendu
   `LedgerEntry` (ligne enrichie ACCEPTÉE en test). *Relayée par le chef de
   projet dans son message de commit — la revue l'a rattrapée.*
2. `4585a10` décrit « 8 routes / 5 écrans » alors que le chantier WEBAPP de la
   **même itération** en a livré 10 et 6 (instantané périmé).
3. `README.md:248` annonçait 18 tests backend pour une commande qui en rend 38.
4. `6055e14` annonçait 77 tests GreenIT — il y en a **78**. *Également relayée
   par le chef de projet.*

**Arbitrage — duplication socle/cockpit :** le risque invoqué n'existe pas. Les
deux agrégats (`diagnostic/usage.py` et `webapp/backend/greenit.py`) convergent
aujourd'hui **au centime** sur un ledger panaché (coût, appels, cache-hits, taux
identiques). Mais rien ne teste cette convergence → **risque de divergence
silencieuse**. Verdict : refactor recommandé, **non bloquant** ; un test de
non-régression croisé est demandé au chantier WEBAPP.

**Invariants d'architecture : tous tenus** (vault_io seul écrivain, api_io seul
réseau sortant, cockpit lecture seule, machine à états bornée, DAG = donnée,
outreach désactivé).

**Enseignement de méthode :** en orchestration parallèle, l'agent de
documentation doit re-vérifier ses chiffres **juste avant de rendre**, pas au
moment où il les relève — sinon il fige un instantané que ses pairs ont déjà
périmé. Consigne intégrée à la relance.

**Relances lancées** (écosystème conservé, agents repris avec leur contexte) :
documentation (backlog D4 + seconde passe), webapp (justification erronée +
test croisé).
