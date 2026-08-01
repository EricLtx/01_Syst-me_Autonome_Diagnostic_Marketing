# Changelog

Toutes les évolutions notables de ce projet sont consignées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
avec les rubriques rendues en français : **Ajouté**, **Modifié**, **Corrigé**,
**Déprécié**, **Retiré**, **Sécurité**.

**Règle de ce fichier : on ne documente que ce qui est vérifiable dans le
dépôt.** Une intention se marque `[EN COURS]` ou `[PLANIFIÉ]`, jamais au présent
de l'indicatif. Chaque entrée cite son commit ou son fichier.

---

## [Non publié] — Itération 2 `[EN COURS]`

> Trois chantiers étaient actifs en parallèle au moment de la rédaction de cette
> section. **Elle sera complétée en seconde passe**, une fois leur contenu
> réellement vérifiable. Rien ci-dessous ne doit être considéré comme livré.

### Ajouté

- **Écosystème d'agents persistant** — `.claude/agents/` : sept sous-agents
  Claude Code réutilisables d'une session à l'autre, chacun portant les
  invariants d'architecture du projet dans son prompt système
  (`agent-documentation`, `agent-revue`, `agent-architecte`, `agent-dev-python`,
  `agent-frontend`, `agent-greenit`, `agent-produit`).
  Cartographie : `docs/agents/ECOSYSTEME.md`.
- **Documentation d'architecture** — `docs/architecture/` :
  `README.md` (vue d'ensemble + diagrammes Mermaid), `invariants.md`
  (19 invariants avec leur preuve exécutable), `flux-donnees.md` (chaîne de bout
  en bout).
- **Registre de décisions** — `docs/adr/` :
  ADR 0001 (orchestrateur DAG déterministe, décision du Palier 1),
  ADR 0002 (GreenIT, **en cours d'implémentation**), index et format.
- **Ce changelog** — `docs/CHANGELOG.md`.
- **`knowledge/greenit.yaml`** `[EN COURS]` — stratégie d'efficience en donnée :
  profils de modèle, règles de routage déterministes, bornes de frugalité,
  facteurs d'estimation d'empreinte régionalisés. Présent dans l'arbre de
  travail, non commité à la date de rédaction. Le module Python associé n'était
  pas encore présent.

### À compléter en seconde passe

| Chantier | Périmètre annoncé | Ce qu'il faudra vérifier |
|---|---|---|
| **GreenIT** | `knowledge/greenit.yaml`, module(s) d'efficience (emplacement à confirmer), effets sur `api_io.py` / `api_schema.py` / `synthesis.py` | emplacement et API réels des modules, valeurs finales du YAML, champs ajoutés au grand livre, colonnes du rapport d'usage, tests de déterminisme du routage, étiquetage « estimation » effectif |
| **Intégration e2e** | `tests/integration/**`, `scripts/**` | scénarios couverts, compte de tests, intégration au protocole de revue |
| **Collecteurs / découverte** | `diagnostic/discovery.py`, `diagnostic/enrichment.py`, `diagnostic/collectors/*` | tableau des collecteurs et de leurs paliers dans `flux-donnees.md` §4 |
| **Cockpit** | `webapp/**` (backend, frontend, écran GreenIT) | écrans, routes et contrat d'API dans `docs/architecture/README.md` §5 ; **vérifier que la lecture seule stricte (I14) est préservée** |

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
