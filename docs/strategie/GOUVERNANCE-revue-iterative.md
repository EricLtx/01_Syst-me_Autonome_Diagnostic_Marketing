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

_(à compléter au fil des itérations)_
