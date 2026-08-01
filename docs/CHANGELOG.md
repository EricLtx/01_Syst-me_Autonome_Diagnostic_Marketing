# Changelog

Toutes les évolutions notables de ce projet sont consignées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
avec les rubriques rendues en français : **Ajouté**, **Modifié**, **Corrigé**,
**Déprécié**, **Retiré**, **Sécurité**.

**Règle de ce fichier : on ne documente que ce qui est vérifiable dans le
dépôt.** Une intention se marque `[EN COURS]` ou `[PLANIFIÉ]`, jamais au présent
de l'indicatif. Chaque entrée cite son commit ou son fichier.

---

## [Itération 2] — 2026-08-01 — GreenIT, intégration e2e, cockpit connecté

Quatre chantiers menés en parallèle, tous commités et audités.
Revue : **29 assertions ré-exécutées** — GREENIT 100 %, INTÉGRATION 100 %,
WEBAPP 100 % → CLEARED ; **DOCUMENTATION 5/6 = 83,3 % → RELANCE** (assertion D4 :
chiffres périmés dans `CLAUDE.md`/`README.md`, corrigés depuis).
Ancrage de la revue : `04059f6`. Correctifs post-revue : `611eb74`.

**Comptes vérifiés par exécution** (le 2026-08-01, commit de tête `611eb74`) :
`tests/` **527** (dont **46** e2e et **78** GreenIT) · backend **45** ·
frontend **34**.

**Commits de l'itération :** `6055e14` (GreenIT) · `d5b14d1` (cockpit connecté) ·
`0234af3` (intégration e2e) · `4585a10` (agents + documentation) ·
`04059f6` (ancrage revue) · `611eb74` (correctifs post-revue).

### Ajouté

- **GreenIT — efficience des appels IA et empreinte tracée** (`6055e14`) —
  décision : `docs/adr/0002-greenit-efficience-et-observabilite.md`.
  - `diagnostic/greenit.py` — `charger_config`, `evaluer_escalade`,
    `choisir_modele`, `max_tokens_du_profil`, `tronquer_contexte`,
    `intensite_carbone`, `estimer_empreinte`.
  - `knowledge/greenit.yaml` — **la stratégie d'efficience est une donnée** :
    3 profils (`frugal` haiku/400, `standard` haiku/600, `qualite` sonnet/900),
    routage `standard` par défaut avec escalade en mode `ou` sur
    `quality_check_echoue == true`, `nb_failles >= 6`, `score_global >= 75` ;
    bornes de frugalité (contexte 4 000 car., prompt 8 000 car.,
    `max_tokens_sortie` 600, TTL cache 30 j, prompt caching désactivé) ;
    facteurs d'empreinte avec intensité carbone **par région**.
  - **Routage déterministe** — mêmes entrées, même profil. **Aucun LLM ne décide
    du routage** : le superviseur-planificateur LLM reste refusé (ADR 0001).
  - **7 champs ajoutés à `LedgerEntry`** : `octets_entrants`, `octets_sortants`,
    `duree_ms`, `energie_wh`, `co2e_g`, `modele`, `profil` — tous optionnels avec
    défaut, donc **les lignes antérieures se relisent sans migration**.
  - `diagnostic/synthesis.py` consomme le routage ; **le modèle n'est plus en
    dur**. Le repli déterministe sans clé est préservé.
  - `tests/test_greenit.py` — **78 tests** (le message de commit annonçait 77 ;
    écart relevé par la revue).
- **Tests d'intégration end-to-end réels** (`0234af3`) — `tests/integration/` :
  **46 tests** exécutés contre un **faux serveur HTTP local**
  (`faux_api.py`), **sans aucune clé API**. Cinq flux :
  `test_e2e_bus.py` (cache, budgets, garde-fous vault),
  `test_e2e_decouverte.py`, `test_e2e_diagnostic.py`, `test_e2e_export.py`,
  `test_e2e_orchestrateur.py`.
  Les invariants ne sont plus seulement prouvés par mock mais **par le réseau** :
  deux appels identiques ne produisent **qu'une seule** requête ; le budget
  interrompt **avant** l'appel ; la machine à états est inviolable ; le cache et
  les exports refusent de s'installer dans le vault.
- **Observabilité GreenIT temps réel dans le cockpit** (`d5b14d1`) —
  `webapp/backend/greenit.py` (lecture/agrégation du grand livre + tail par
  offset), routes **`/api/greenit`** et **`/api/greenit/stream`** (SSE), écran
  **`/greenit`** côté front. Le cockpit passe de **8 à 10 routes** et de
  **5 à 6 écrans**. Connexion réelle back ↔ front.
  **Lecture seule stricte préservée.**
- **Écosystème d'agents persistant + documentation technique** (`4585a10`) —
  `.claude/agents/` : sept sous-agents Claude Code réutilisables d'une session à
  l'autre, chacun portant les invariants d'architecture dans son prompt système
  (`agent-documentation`, `agent-revue`, `agent-architecte`, `agent-dev-python`,
  `agent-frontend`, `agent-greenit`, `agent-produit`).
  `docs/architecture/` (vue d'ensemble + Mermaid, **21 invariants** avec leur
  preuve exécutable, flux de bout en bout), `docs/adr/` (ADR 0001 et 0002),
  `docs/agents/ECOSYSTEME.md`, `docs/CHANGELOG.md`.

### Modifié

- `CLAUDE.md`, `README.md` — orchestrateur DAG, cockpit, écosystème d'agents,
  gouvernance 97 %, section GreenIT, état réel du système, comptes de tests.
- `docs/architecture/invariants.md` — deux invariants ajoutés : **I20** (routage
  déterministe piloté par la donnée) et **I21** (bornes de frugalité appliquées
  avant émission). Colonnes « comment c'est testé » de I5, I6, I7 et I15
  enrichies des preuves e2e.

### Corrigé

- **Chiffres périmés dans la documentation** (assertion D4 de la revue) :
  routes cockpit 8 → **10**, écrans 5 → **6**, tests backend 18 → **45**,
  suite 403 → **527**. Cause : documentation d'un instantané pris **avant**
  l'atterrissage du chantier WEBAPP de la même itération.
  Règle qui en découle, inscrite dans le prompt de `agent-documentation` :
  **re-vérifier chaque chiffre par une commande juste avant de rendre**, jamais
  au moment où on le relève.
- **`tests/test_greenit.py` : 77 → 78** — le compte annoncé par le message de
  commit ne correspondait pas au compte réel.
- **Justification erronée du parsing défensif du cockpit** (`611eb74`).
  L'argument avancé par `d5b14d1` — « `extra="forbid"` rejetterait les lignes
  enrichies » — est **faux** : `LedgerEntry` relit parfaitement les lignes
  enrichies depuis `6055e14` (vérifié par exécution). Le bon argument est la
  **tolérance au schéma futur et aux lignes corrompues** : `LedgerEntry` est un
  schéma d'*écriture*, strict par construction, tandis qu'une vue de
  *consultation* ne doit jamais tomber sur ce qu'elle lit (champ futur, `ts`
  malformé, `unites: null`, ligne lue à chaud pendant une écriture).
  Docstring du module et ADR 0002 corrigés.

### Sécurité / fiabilité

- **Test de non-régression croisé socle ⇄ cockpit** (`611eb74`) —
  `webapp/backend/tests/test_greenit_usage_convergence.py`, **7 tests** :
  coût total, comptages, par fournisseur, filtre `depuis`, ledger vide,
  endpoints HTTP (avec et sans filtre). Il compare `diagnostic/usage.py::agreger`
  et `webapp/backend/greenit.py::agreger` sur un ledger panaché et **échoue si
  elles divergent**. Le backend passe de 38 à **45 tests**.
  Ce test a été créé après que la passe documentaire a signalé que le docstring
  l'annonçait sans qu'il existe — un filet de sécurité documenté mais absent est
  plus dangereux qu'un manque assumé.

### Dette technique inscrite (non bloquante)

1. ~~**Duplication de la logique de coût** sans test de convergence.~~
   **Fermée par `611eb74`** (voir ci-dessus). Il subsiste une duplication de
   *code* — refactor souhaitable à terme (une seule fonction de calcul, deux
   vues), mais **plus de risque de divergence silencieuse**.
2. **`diagnostic/greenit.py` absent de la liste `_check_garde_fous_bus`** alors
   que l'invariant I4 l'impose. **Toujours ouvert** — vérifié :
   `sed -n '/modules_j5 = \[/,/\]/p' diagnostic/preflight.py | grep -c greenit`
   → `0`. L'invariant tient *de fait* via le test générique en `rglob` sur
   `diagnostic/**`, mais pas par le mécanisme annoncé, et le préflight ne le
   signale pas. → L'ajouter à `diagnostic/preflight.py`.

### Ce qui reste NON mesurable

Le mécanisme GreenIT est livré ; **l'économie ne l'est pas**. `api_pricing.yaml`
est toujours à `0.0` (tous les coûts valent 0,00), les facteurs d'empreinte n'ont
jamais été étalonnés (`releve_le: null`), et aucun run réel n'a eu lieu.
**Aucun pourcentage de gain n'est calculable** — l'avancer serait une invention.
Le préflight reste en **NO-GO structurel**, le vault reste non initialisé, et
**J6 reste non activable**.

---

## [Itération 1] — 2026-08-01 — Palier 1 « Kemana-Flow »

Trois chantiers livrés et audités indépendamment. Protocole
`docs/strategie/GOUVERNANCE-revue-iterative.md` : **CORE 12/12, BACKEND 7/7,
FRONTEND 8/8 — 100 %, verdict CLEARED sur les trois, aucune relance nécessaire,
aucune hallucination détectée** (commit `2ed8d93`).

### Ajouté

- **Orchestrateur DAG déterministe « Kemana-Flow »** (`36380c8`) —
  décision : `docs/adr/0001-orchestrateur-dag-deterministe.md`.
  - `diagnostic/orchestrator.py` — couche mince d'ordonnancement au-dessus de
    J1-J5, **zéro logique métier**. Chargement et validation du DAG
    (`DagInvalide`, `CycleDetecte`), tri topologique de Kahn avec **départage
    alphabétique** (ordre reproductible), verrou de run exclusif
    (`RunLock`, `os.open` avec `O_CREAT|O_EXCL`), reprise idempotente,
    arrêt propre sur `BudgetExceeded`, manifeste de run sous
    `.cache/orchestrator/<run_id>.json`.
  - `run_pipeline.py` — CLI unique : `--icp`, `--dry-run`, `--depuis`,
    `--jusqu-a`, `--vault`, `--dag`. Code de sortie `0` = OK, `1` = arrêt.
  - `dag_pipeline.yaml` — **le graphe est une donnée** :
    `preflight_gate → discovery → diagnostic → [porte humaine] → export →
    usage_snapshot`, plus `outreach` en `enabled: false`.
  - **Une seule instance `ApiIO`** créée en tête de chaîne et **injectée** dans
    les nœuds réseau — un seul grand livre, un seul garde-fou budgétaire pour
    toute la chaîne.
  - Les `run_*.py` historiques continuent de fonctionner seuls
    (rétro-compatibilité préservée).
- **API cockpit FastAPI en lecture seule** (`b5430d1`) — `webapp/backend/` :
  huit routes `GET` (`/api/health`, `/api/preflight`, `/api/pipeline/funnel`,
  `/api/prospects`, `/api/prospects/{slug}`, `/api/usage`, `/api/icp`,
  `/api/runs`), logique d'accès concentrée dans `services.py`, CORS restreint
  aux origines Vite de développement avec `allow_methods=["GET"]`.
  **Aucune écriture vault, aucune transition d'état, aucun appel `api_io`,
  aucune dépendance `requests`/`anthropic`.** Dégradation propre sur vault vide.
- **Cockpit opérateur React** (`25ea9d0`) — `webapp/frontend/` :
  React 18 + Vite 5 + TypeScript 5, cinq écrans (Dashboard, Prospects, Détail
  prospect, Usage, Préflight), thème clair **et** sombre, mode mock hors ligne
  (`src/mocks/fixtures.ts`), tests Vitest + Testing Library. Aucune librairie de
  graphiques ni UI kit : composants écrits à la main (`FunnelBars`, `StatTile`,
  `StatusPill`, `VerdictBanner`, `AsyncState`).
- **Protocole de revue itérative avec porte de cohérence 97 %** (`4beea7e`,
  ancrage `2ed8d93`) — `docs/strategie/GOUVERNANCE-revue-iterative.md` :
  assertions vérifiables **par exécution**, taux de cohérence chiffré, relance
  du **même** agent d'implémentation (contexte conservé) sous le seuil, journal
  d'ancrage horodaté par itération.
- **Livrables stratégiques consolidés** (`6c83a68`) — `docs/strategie/` :
  analyse comparative des trois scénarios, matrice de décision pondérée, SWOT,
  PESTEL, plan d'implémentation, tableau de bord HTML.

### Modifié

- **Garde-fou AST de bus étendu** — `diagnostic/preflight.py::_check_garde_fous_bus`
  surveille désormais aussi `orchestrator.py` et `run_pipeline.py` : aucun import
  `requests` ni `anthropic` au niveau module (`36380c8`).
- **`run_discovery.py`** — passe désormais `budgets=` à `ApiIO` et accepte une
  instance `api_io` injectée (`36380c8`).
- **`run_diagnostic.py`** — instancie un `ApiIO` unique et l'injecte au pipeline ;
  expose `_build_pipeline(api_io=…)` réutilisé par l'orchestrateur (`36380c8`).
- **`.gitignore`** — artefacts webapp (`node_modules/`, `dist/`, `.vite/`,
  `coverage/`, `.env`), grand livre `api_usage.log`, exports, verrou de run
  `.run.lock` (`71484a9`), puis `*.tsbuildinfo` (`2ed8d93`).

### Corrigé

- **Défaut AS-IS : `ApiIO` multiple.** Chaque `run_*.py` fabriquait sa propre
  instance → budgets non partagés, garde-fou budgétaire inopérant à l'échelle
  d'une campagne. Corrigé par l'instance unique injectée (`36380c8`).
- **Caches `*.tsbuildinfo` committés par inadvertance** — ajoutés au
  `.gitignore` et dé-suivis. Trouvaille de l'audit d'itération 1, sévérité
  basse (`2ed8d93`).

### Sécurité / conformité

- **J6 outreach verrouillé à double tour** : `enabled: false` dans
  `dag_pipeline.yaml` **et** `Orchestrateur._run_outreach()` qui renvoie
  systématiquement `bloque` même si le drapeau est forcé. Activation conditionnée
  à une validation juridique — CASL (Québec), nLPD + art. 3 LCD (Suisse), RGPD
  (France), transparence AI Act.
- **Porte humaine préservée** : l'orchestrateur ne déclenche que la transition
  agent `decouvert → diagnostique`. Vérifié par un test qui exécute la chaîne
  **complète** et constate qu'aucune fiche ne passe en `valide`.
- **Cockpit strictement en lecture seule** : aucune interface web ne peut
  contourner la porte humaine d'Obsidian.

### État connu à la fin de l'itération 1

Ces limites sont **structurelles et voulues** — ce sont les garde-fous qui
fonctionnent, pas des défauts :

- **Aucune clé API dans l'environnement** (`SERP_API_KEY`, `APOLLO_API_KEY`,
  `GOOGLE_PLACES_API_KEY`, `ANTHROPIC_API_KEY`) → aucun run réel possible ;
  tout tourne hors ligne (stubs + repli déterministe).
- **`knowledge/api_pricing.yaml` intégralement à `0.0`**, `releve_le: null`,
  budgets `serp` et `apollo` à `0` → **préflight NO-GO structurel**, et aucun
  coût affiché n'est engageant.
- **Vault non initialisé** : `vault/` est vide, `init_vault.py` n'a pas été
  exécuté.
- Lever ces trois points relève de la **Phase D** (paramétrage par l'opératrice :
  variables d'environnement + YAML), pas du développement.

---

## Avant l'itération 1 — socle J1 à J5

Historique antérieur à la mise en place de ce changelog, reconstitué depuis
`git log`. Les livrables sont décrits dans les spécifications à la racine
(`SPEC-J2-bus-vault.md`, `SPEC-J3-api-io.md`, `SPEC-J4-decouverte.md`,
`SPEC-J5-sortie-preflight.md`).

| Date | Commit | Contenu |
|---|---|---|
| 2026-06-13 | `531a50b` | **J5** — export Kemana, agrégat d'usage, préflight GO/NO-GO |
| — | `cb4e3c6` | **J4** — agent de découverte (SERP → candidats → fiches), enrichissement Apollo, ICP en donnée |
| — | `c038008` | Documentation fonctionnelle — README + CLAUDE.md |
| — | `4d64691` | **Phase D** — serializers, vault runner, `vault_io`, diagnostic terminé |
| — | `0d8f327` | **Phase A** — `vault_schema.py`, modèle Pydantic `FicheProspect` |
| — | `4a84150` | **Phase 0** — scaffold du package `diagnostic/`, smoke tests |
| — | `63f5a4d` | Baseline J1 avant refactor du package J2 |
| — | `e8946cd` | État initial — architecture J1 |
