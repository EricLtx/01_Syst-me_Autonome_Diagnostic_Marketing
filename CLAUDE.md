# CLAUDE.md — contexte projet pour Claude Code

> Ce fichier est lu automatiquement par Claude Code à chaque session. C'est
> sa mémoire du projet. Le tenir à jour est l'étape la plus rentable et la plus
> souvent oubliée — c'est le rôle de `agent-documentation`, à chaque itération.
>
> ⚠️ **Ne pas régénérer ce fichier avec `/init`** : cela écraserait les
> invariants d'architecture accumulés. On le **complète**, on ne le refond pas.
> Règle d'écriture : ne consigner que ce qui est **vérifiable dans le code**.
> Une intention se marque `[EN COURS]` ou `[PLANIFIÉ]`, jamais au présent.

> **Documentation détaillée** — ce fichier est le résumé opérationnel.
> Voir `docs/architecture/` (vue d'ensemble, invariants, flux de données),
> `docs/adr/` (décisions structurantes), `docs/CHANGELOG.md` (avancement réel),
> `docs/agents/ECOSYSTEME.md` (les agents et comment les invoquer).

## Ce qu'est ce projet

Écosystème d'agents de prospection pour une consultante en marketing / branding.
Cinq livrables métier (J1–J5), une couche d'ordonnancement (CORE) et une console
d'observation (cockpit) :

- **J1 — pipeline diagnostic** : entrée = une entreprise ; sortie = score + mini-audit
  de marque. Cible : persona 1 (installateur HVAC), séquence Québec → Suisse.
- **J2 — bus vault** : couche de persistance Obsidian. Le pipeline J1 écrit dans
  un vault structuré ; un opérateur humain valide et pilote via Obsidian. Audit de
  marque complet, traçable, versionné.
- **J3 — bus I/O + collecteurs réels** : contrôleur unique pour tous les appels
  API externes (`api_io.py`). Collecteurs palier 0 enrichis, palier 1 (Google Places),
  tokens Claude métrés dans `api_usage.log`.
- **J4 — agent découverte** : `run_discovery.py` (SERP → candidates → fiches
  `decouvert`) + enrichissement Apollo (`PersonEnrichment`). ICP = données YAML
  dans `icp/*.yaml`. Zéro LLM, zéro scraping LinkedIn.
- **J5 — sortie + préflight** : `run_export.py` (fiches `valide` → liste Kemana
  CSV/JSONL, lecture seule, opt_out absolu), `run_usage.py` (agrégat `api_usage.log`,
  snapshot vault), `run_preflight.py` (9 contrôles GO/NO-GO, pré-condition cron J7).
- **CORE — orchestrateur DAG « Kemana-Flow »** : `run_pipeline.py` +
  `diagnostic/orchestrator.py` + `dag_pipeline.yaml`. Ordonnancement déterministe
  de toute la chaîne, instance `ApiIO` **unique** injectée, verrou de run.
  Décision : `docs/adr/0001-orchestrateur-dag-deterministe.md`.
- **Cockpit opérateur** : `webapp/backend` (FastAPI, 10 routes `GET`) +
  `webapp/frontend` (React 18 + Vite + TS, 6 écrans). **Lecture seule stricte** —
  complément d'Obsidian, jamais un substitut à la porte humaine.
- **J6 — outreach** : **non implémenté, non activable** (validation juridique
  CASL / nLPD + art. 3 LCD / RGPD / AI Act requise au préalable).

## ⚠️ État réel du système (vérifié le 2026-08-01)

Ces limites sont **structurelles et voulues** : ce sont les garde-fous qui
fonctionnent, pas des défauts à contourner. Ne les masque jamais dans une
documentation ou un rapport.

- **Aucune clé API n'est disponible dans l'environnement** (`SERP_API_KEY`,
  `APOLLO_API_KEY`, `GOOGLE_PLACES_API_KEY`, `ANTHROPIC_API_KEY`). Tout tourne
  hors ligne : stubs des collecteurs palier 1 + repli déterministe de la synthèse.
  **La suite de tests s'exécute intégralement sans aucune clé.**
- **`knowledge/api_pricing.yaml` a tous ses prix et budgets à `0`**, avec
  `releve_le: null` → **`run_preflight.py` renvoie NO-GO structurel** (code de
  sortie 1). Tout coût affiché vaut 0,00 et **n'est pas engageant**.
- **Le vault n'est pas initialisé** : `vault/` est vide, `init_vault.py` n'a pas
  été exécuté.
- **J6 outreach non activable** : `enabled: false` dans `dag_pipeline.yaml` **et**
  runner qui renvoie `bloque` même si le drapeau est forcé.
- Lever les trois premiers points relève de la **Phase D** (paramétrage par
  l'opératrice : variables d'environnement + YAML), pas du développement.

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
| Contrôleur de bus stockage | `diagnostic/vault_io.py` — *seul* module autorisé à lire/écrire |
| Contrôleur de bus I/O réseau | `diagnostic/api_io.py` — *seul* module dont les fn peuvent toucher le réseau |
| CPU | agents (pipeline J1, découverte J4, export J5 ; outreach J6 à venir) |
| Séquenceur / horloge | `diagnostic/orchestrator.py` + `dag_pipeline.yaml` (CORE) |
| ROM | rubrics YAML + ICP + templates (lecture seule pour les agents) |
| Disque | cache de scraping brut, **toujours hors du vault** (contraintes G9 + api_io) |
| Console | opérateur humain via Obsidian (validation, manage-by-exception) + cockpit `webapp/` (observation, lecture seule) |

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

### J3 — Bus I/O périphérique

Règles non négociables J3 :
- **Bus unique réseau** : `api_io.py` orchestre TOUS les appels API externes
  (cache, budget, journalisation). Aucun `import requests` ni `import anthropic`
  au niveau module hors `api_io.py` (testé via AST walk §9.6).
- **Grand livre `api_usage.log`** : JSONL append-only à la racine, une ligne par
  appel via `LedgerEntry`. Source de vérité pour les coûts (tokens Claude,
  crédits Places, requêtes SERP).
- **Grille tarifaire = donnée** : `knowledge/api_pricing.yaml`. Changer un tarif =
  éditer le YAML, pas le code.
- **Registres recalculés** depuis le ledger au démarrage (pas de double état).
- **Injection de dépendance** : `DiagnosticPipeline` reçoit `api_io` optionnel ;
  l'injecte dans les collecteurs (`_api_io`) et dans `synthesize()`.
- **Injection `_website_signals`** : après collecte website, le pipeline injecte
  les signaux bruts dans `SeoCollector` et `SocialCollector` (collecteurs dérivés,
  sans accès réseau propre).

### J5 — Sortie + préflight

Règles non négociables J5 :
- **Export lecture seule** : `run_export.py` ne fait aucune transition d'état, aucun appel
  réseau. Seule la lecture du vault est autorisée. Les fiches `opt_out: true` sont exclues
  sans exception (RGPD/CASL/nLPD).
- **`signal_chaud` dérivé, pas dans Diagnostic** : calculé dans `serializers.py` depuis
  `diag.failles` (contrat JSON Diagnostic préservé → test_j1_smoke intact).
- **Exports hors vault** : dossier `exports/` hors vault, dans `.gitignore`. Écriture
  refusée si `--out` pointe sous `vault/` (erreur fatale).
- **Snapshot usage via bus vault** : `run_usage.py --snapshot` écrit dans `90-Systeme/`
  via `vault_io.write_system_note()` (pas d'open() direct).
- **Préflight GO/NO-GO** : 9 contrôles, code de sortie 0=GO / 1=NO-GO. Pré-condition du
  cron J7. Les checks `tests_verts` et warnings clés optionnelles ne bloquent pas.
- **Garde-fous bus étendus** : l'AST walk de `_check_garde_fous_bus` vérifie que
  **8 modules** n'importent ni `requests` ni `anthropic` au niveau module —
  `export.py`, `usage.py`, `preflight.py`, `run_export.py`, `run_usage.py`,
  `run_preflight.py`, et depuis l'itération 1 `orchestrator.py` + `run_pipeline.py`.
  **Tout nouveau module de ce type doit être ajouté à cette liste.**
- **Config = données** : colonnes Kemana dans `knowledge/export_kemana.yaml`, budgets
  dans `budgets:` de `api_pricing.yaml`. Modifier = éditer le YAML, pas le code.

### CORE — Orchestrateur DAG « Kemana-Flow »

Chaîne : `preflight_gate → discovery → diagnostic → [PORTE HUMAINE] → export →
usage_snapshot`. `outreach` déclaré mais `enabled: false`.

Règles non négociables CORE :
- **Le graphe est une DONNÉE** (`dag_pipeline.yaml`). Ajouter, désactiver ou
  réordonner une étape = éditer ce YAML, **jamais** `orchestrator.py`.
- **Zéro logique métier dans l'orchestrateur** : chaque nœud est un adaptateur
  MINCE autour d'un entrypoint existant (`run_discovery.run`,
  `run_diagnostic._build_pipeline` + `vault_runner.run_vault_mode`,
  `diagnostic.export`, `diagnostic.usage`, `diagnostic.preflight`).
- **Tri topologique déterministe** : Kahn + départage **alphabétique**. Deux
  exécutions du même DAG → exactement la même séquence.
- **Exécution strictement séquentielle** — aucun parallélisme (l'ambiguïté
  « export ∥ outreach » a été tranchée en faveur du séquentiel).
- **Instance `ApiIO` UNIQUE** créée en tête de chaîne (budgets depuis
  `api_pricing.yaml`) et **injectée** dans les nœuds réseau. Un seul grand livre,
  un seul garde-fou budgétaire. C'est le geste qui corrige le défaut AS-IS
  « chaque `run_*.py` fabriquait son propre `ApiIO` ».
- **Verrou de run exclusif** : `os.open(..., O_CREAT|O_EXCL)` — délibérément
  **pas** `os.replace()`, qui reste l'exclusivité de `vault_io.py`. Libéré en
  `try/finally`. Un second run lève `VerrouExiste`.
- **Reprise idempotente** : le nœud `diagnostic` est sauté s'il ne reste aucune
  fiche `decouvert`. Arrêt propre sur `BudgetExceeded` — ce qui est écrit reste valide.
- **Machine à états respectée** : l'orchestrateur ne déclenche QUE
  `decouvert → diagnostique`. Les transitions `valide`/`contacte`/`rejete` restent
  humaines (Obsidian). Testé sur une exécution complète de la chaîne.
- **`outreach` non activable** : double verrou — `enabled: false` dans le YAML
  **et** `_run_outreach()` qui renvoie `bloque` si on force le drapeau.
- **Traçabilité** : manifeste `.cache/orchestrator/<run_id>.json` (run_id, fenêtre
  temporelle, statut des nœuds). Corrèle `runs.log` ⇄ `api_usage.log` **par
  intervalle temporel**, sans modifier le schéma de ces journaux.
- Les `run_*.py` historiques **continuent de fonctionner seuls** : l'orchestrateur
  ne les remplace pas, il les ordonne.

### Cockpit opérateur (`webapp/`) — lecture seule stricte

- **Backend** `webapp/backend/` (FastAPI) : **10 routes `GET`** — `/api/health`,
  `/api/preflight`, `/api/pipeline/funnel`, `/api/prospects`,
  `/api/prospects/{slug}`, `/api/usage`, **`/api/greenit`**,
  **`/api/greenit/stream`** (SSE, observabilité temps réel), `/api/icp`,
  `/api/runs`. Logique d'accès dans `services.py` ; lecture/agrégation du grand
  livre pour GreenIT dans `webapp/backend/greenit.py`.
  CORS restreint (`allow_methods=["GET"]`).
  Variables d'environnement : `VAULT_PATH`, `API_USAGE_LOG`, `RUNS_LOG`,
  `PREFLIGHT_ROOT_DIR`.
- **Frontend** `webapp/frontend/` (React 18 + Vite 5 + TS 5) : **6 écrans** —
  Dashboard `/`, Prospects `/prospects`, Détail `/prospects/:slug`,
  Usage `/usage`, **GreenIT `/greenit`**, Préflight `/preflight`. Thème clair
  **et** sombre (`src/theme.css`), mode mock hors ligne
  (`src/mocks/fixtures.ts`), tests Vitest.
- **AUCUNE écriture vault, AUCUNE transition d'état, AUCUN appel `api_io`,
  AUCUN réseau sortant.** Un bouton « Valider » dans cette interface
  contournerait la porte humaine : c'est interdit par construction.
- Frugalité assumée : aucune librairie de graphiques ni UI kit, composants écrits
  à la main.

### GreenIT — efficience des appels IA et observabilité

`diagnostic/greenit.py` + `knowledge/greenit.yaml`. ADR :
`docs/adr/0002-greenit-efficience-et-observabilite.md`.

Règles non négociables GreenIT :
- **Routage de modèle DÉTERMINISTE piloté par YAML.** `choisir_modele(contexte,
  config)` évalue des comparaisons explicites — mêmes entrées, même sortie.
  **Aucun LLM ne décide du routage** (le superviseur-planificateur LLM est
  refusé par l'ADR 0001 : ne pas le réintroduire par cette porte).
  Profil par défaut `standard` (haiku, 600 tokens) ; escalade vers `qualite`
  (sonnet, 900) en mode `ou` sur trois règles : `quality_check_echoue == true`,
  `nb_failles >= 6`, `score_global >= 75`.
- **Le modèle n'est jamais en dur** : changer de modèle = éditer le YAML.
- **Bornes de frugalité appliquées avant émission** : troncature du contexte
  (4 000 car.), plafond du prompt assemblé (8 000 car.), `max_tokens_sortie`
  (600) qui écrase le profil s'il est plus permissif, TTL de cache (30 j).
  `activer_prompt_caching: false` — non rentable tant qu'aucun préfixe long
  n'est réutilisé (un prompt par prospect).
- **7 champs ajoutés à `LedgerEntry`** : `octets_entrants`, `octets_sortants`,
  `duree_ms`, `energie_wh`, `co2e_g`, `modele`, `profil`. Tous optionnels avec
  défaut → **les anciennes lignes se relisent sans migration**
  (`extra="forbid"` interdit les champs inconnus, pas les champs manquants).
- **Empreinte régionalisée** : `intensite_carbone(region, config)` en g CO₂e/kWh.
  L'écart entre un mix hydroélectrique et la moyenne mondiale est de **deux
  ordres de grandeur** — ignorer la région produirait un chiffre sans sens.
- ⚠️ **`energie_wh` et `co2e_g` sont des ESTIMATIONS**, jamais des mesures
  certifiées. Facteurs = ordres de grandeur paramétrables, `releve_le: null`
  tant qu'aucun réétalonnage n'a eu lieu. Usage **comparatif** uniquement
  (avec/sans cache, frugal vs qualité). Toute valeur affichée porte la mention
  « estimation ». Un chiffrage opposable exigerait une ACV par un tiers.
- ⚠️ **Aucun pourcentage d'économie n'est mesurable aujourd'hui** :
  `knowledge/api_pricing.yaml` est à `0`, donc tous les coûts valent 0,00.
  Ne jamais avancer de gain chiffré avant la Phase D.

### J4 — Agent de découverte

Règles non négociables J4 :
- **ICP = donnée** : `icp/*.yaml` validés par `IcpConfig` (Pydantic). Nouveau marché =
  nouveau fichier YAML, zéro code. Cohérence `icp_id = "persona{persona}-{marche}"`.
- **Candidate en mémoire** : `Candidate` (Pydantic, extra="forbid") entre SERP et vault.
  Jamais persistée directement — `run_discovery.py` la mappe vers `FicheProspect`.
- **Dédup intra-lot** : domaine normalisé (minuscule, sans www., sans trailing slash).
- **Dédup inter-runs** : `vault_io.exists(site_web=..., nom=...)` avant chaque `write_fiche`.
- **Contact = 6 champs** : `Contact` (extra="forbid") — minimisation RGPD garantie.
  `contact_email_source` toujours renseigné si email présent (audit RGPD).
- **BudgetExceeded** : arrêt propre, fiches déjà écrites restent valides, ré-exécution idempotente.
- **Dry-run** : SERP exécuté et métrée (cache utile), aucune écriture vault.
- **Aucun LLM en J4** : zéro import anthropic dans discovery/enrichment/run_discovery.
- **Aucun scraping LinkedIn/Facebook** : données « personnes » exclusivement via Apollo API.

### Collecteurs et leurs paliers

| Collecteur | Palier | Source réseau | Mode dégradé (sans api_io) |
|---|---|---|---|
| `website.py` | 0 | `requests.get` via api_io | lazy import requests |
| `seo.py` | 0 | aucun — dérivé de `_website_signals._seo_text` | stub `local_keywords=None` |
| `social.py` | 0 | aucun — dérivé de `_website_signals.social_links` | `plateformes_mentionnees=[]` |
| `gbp.py` | 1 | Google Places `text_search` via api_io | stub `verified=None` |
| `reviews.py` | 1 | Google Places `text_search` + `place_details` via api_io | stub `count=None` |

### Schéma vault + exports

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
│  ├─ journal-decisions.md      ← log humain des décisions (éditable)
│  └─ usage-AAAA-MM-JJ.md      ← snapshots d'usage API (J5, via run_usage --snapshot)
├─ _templates/
│  └─ fiche-prospect.md         ← gabarit de nouvelle fiche
└─ 00-Dashboard.md              ← 3 requêtes Dataview (pipeline, top gaps, relance)

exports/                        ← HORS vault, dans .gitignore (artefacts J5)
├─ kemana_tous_AAAA-MM-JJ.csv  ← liste Kemana (utf-8-sig pour Excel FR)
└─ kemana_tous_AAAA-MM-JJ.anomalies.txt  ← rapport anomalies (email manquant, etc.)

.cache/                         ← HORS vault, gitignoré
├─ api_io/                      ← cache disque des appels API
└─ orchestrator/<run_id>.json   ← manifestes de run (CORE)

.run.lock                       ← verrou d'exécution de l'orchestrateur (gitignoré)
api_usage.log                   ← grand livre des coûts, JSONL append-only (gitignoré)
runs.log                        ← journal des écritures vault, JSONL (gitignoré)
```

### Documentation et écosystème d'agents

```
.claude/agents/                 ← sous-agents Claude Code PERSISTANTS
├─ agent-documentation.md       ← lancé à CHAQUE itération (le plus important)
├─ agent-revue.md               ← garde-fou anti-hallucination, porte 97 %
├─ agent-architecte.md          ← conception + invariants de bus + ADR
├─ agent-dev-python.md          ← implémentation Python
├─ agent-frontend.md            ← cockpit React/TS
├─ agent-greenit.md             ← efficience IA, frugalité, coûts
└─ agent-produit.md             ← roadmap, priorisation

docs/
├─ architecture/                ← README (vue + Mermaid), invariants, flux-donnees
├─ adr/                         ← décisions structurantes (0001 DAG, 0002 GreenIT)
├─ agents/ECOSYSTEME.md         ← cartographie des agents, invocation, amélioration
├─ CHANGELOG.md                 ← Keep a Changelog, une section par itération
└─ strategie/                   ← PROPRIÉTÉ DU CHEF DE PROJET — lecture seule
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

# Découverte J4
python run_discovery.py --icp persona1-quebec                    # SERP + Apollo
python run_discovery.py --icp persona1-quebec --sans-contact     # SERP uniquement
python run_discovery.py --icp persona1-quebec --dry-run          # aperçu, aucune écriture
python run_discovery.py --icp persona1-quebec --enrichir-existants  # rejeu phase 1b

# Export J5 — couche de sortie Kemana (lecture seule, aucune transition d'état)
python run_export.py                                  # CSV toutes fiches valide/non opt_out
python run_export.py --icp persona1-quebec            # filtré par ICP
python run_export.py --format jsonl                   # JSONL au lieu de CSV
python run_export.py --dry-run                        # aperçu sans écriture

# Usage J5 — agrégat api_usage.log
python run_usage.py                                   # rapport console
python run_usage.py --depuis 2025-01-01               # filtré par date
python run_usage.py --snapshot                        # rapport + snapshot vault/90-Systeme/

# Préflight J5 — vérification GO / NO-GO (code de sortie 0=GO / 1=NO-GO)
python run_preflight.py                               # tous les contrôles
python run_preflight.py --icp persona1-quebec         # + vérification ICP spécifique
python run_preflight.py --strict                      # tests_verts devient bloquant

# CORE — orchestrateur DAG « Kemana-Flow » (chaîne complète J1→J5)
python run_pipeline.py --icp persona1-quebec          # chaîne complète
python run_pipeline.py --icp persona1-quebec --dry-run   # n'écrit RIEN, préflight informatif
python run_pipeline.py --icp persona1-quebec --depuis diagnostic   # démarre à ce nœud
python run_pipeline.py --icp persona1-quebec --jusqu-a discovery   # s'arrête après ce nœud
python run_pipeline.py --icp persona1-quebec --vault chemin/vers/vault
python run_pipeline.py --dag autre_graphe.yaml        # graphe alternatif
# Code de sortie : 0 = chaîne OK, 1 = arrêt (NO-GO, budget dépassé, nœud bloquant)

# Cockpit opérateur (lecture seule)
pip install -r webapp/backend/requirements.txt
uvicorn webapp.backend.app:app --reload --port 8000   # API + /docs
VAULT_PATH=/chemin/vers/vault uvicorn webapp.backend.app:app --port 8000
cd webapp/frontend && npm install && npm run dev      # front sur :5173
cd webapp/frontend && npm run build && npm run test   # tsc + vite + vitest

# Tests
pytest tests/ -v
pytest tests/ -v -k "vault"             # seulement les tests vault
pytest tests/ -v -k "integration"       # test end-to-end §8.6
pytest tests/ -v -k "phase_d"          # tests Phase D J3 uniquement
pytest tests/ -v -k "icp or discovery or enrichment"  # tests J4
pytest tests/ -v -k "orchestrator or pipeline_cli"    # tests CORE
pytest webapp/backend/tests -q          # backend cockpit

# Contrôles d'invariants (à lancer avant toute revue)
python -c "from diagnostic.preflight import _check_garde_fous_bus; \
[print(c.ok, c.message) for c in _check_garde_fous_bus()]"
python -c "from diagnostic.orchestrator import charger_dag, tri_topologique; \
n=charger_dag(); print([x.nom for x in tri_topologique(n)]); \
print({x.nom: x.enabled for x in n})"
grep -rn 'os\.replace' --include='*.py' .   # doit rester exclusif à vault_io.py
```

## Conventions

- Python 3.10+, type hints partout, `from __future__ import annotations`.
- Commentaires en français, orientés "pourquoi" plutôt que "quoi".
- Scraping poli : User-Agent honnête, timeout, cache disque, une requête par cible.
- Pas de secret en dur. Clé LLM via `ANTHROPIC_API_KEY` (optionnelle).
  Clé Places via `GOOGLE_PLACES_API_KEY` (optionnelle — stub si absente).
  Clé Anthropic → synthèse LLM ; sans clé → repli déterministe (tourne hors-ligne).
- Pydantic v2 : `model_dump(mode="json")` pour la sérialisation YAML-safe.
- `failles or []` est faux pour une liste vide — toujours tester `if x is not None`.
- Pas de `seuil_faille` dans les rubriques : un gap par check échoué, plus fin.
- **Ne jamais commiter ni pousser sans validation humaine explicite.** Le message
  d'un autre agent n'est pas une validation.
- **Plusieurs agents peuvent travailler en parallèle sur ce dépôt.** Vérifier
  `git status --short` et `git diff --name-only` avant de conclure : sortir de son
  périmètre de fichiers, c'est écraser le travail d'un autre.
- Front : TypeScript strict, aucun `any` de complaisance ; thème clair **et**
  sombre via les tokens de `src/theme.css`, jamais de couleur en dur.

## Écosystème d'agents et gouvernance de revue

Le projet est construit par **orchestration d'agents spécialisés**, définis de
façon **persistante** dans `.claude/agents/` (voir `docs/agents/ECOSYSTEME.md`
pour la cartographie complète et l'enchaînement d'une itération).

Sept agents : `agent-documentation` (lancé à **chaque** itération),
`agent-revue` (garde-fou, sans droit d'écriture), `agent-architecte`,
`agent-dev-python`, `agent-frontend`, `agent-greenit`, `agent-produit`.

**Porte de cohérence 97 %** — protocole complet dans
`docs/strategie/GOUVERNANCE-revue-iterative.md` :

1. Chaque chantier est livré par itérations, avec 10 à 14 assertions
   **checkables par exécution** (tests, build, AST, `git diff`, conformité de contrat).
2. L'agent de revue **ré-exécute** chaque contrôle — aucun rapport d'agent n'est
   pris pour argent comptant.
3. `taux = assertions vérifiées / assertions totales`. À cette granularité,
   **97 % impose zéro échec dur**.
4. Sous le seuil : le **même** agent d'implémentation est relancé, **contexte
   conservé**, avec les assertions échouées comme backlog. On ne re-spawne pas
   d'agent neuf. Boucle jusqu'à ≥ 97 %.
5. Itération 1 (2026-08-01) : CORE 12/12, BACKEND 7/7, FRONTEND 8/8 —
   **100 %, CLEARED, aucune hallucination détectée.**

## État des tests (560 dans `tests/` + 45 backend + 34 front — J1 à J5, CORE, GreenIT, intégration)

> Le compte évolue à chaque itération : **re-compte, ne recopie pas.**
> `python -m pytest tests/ --collect-only -q | tail -2`

| Fichier | Couverture | Nb |
|---------|-----------|-----|
| `test_j1_smoke.py` | Pipeline end-to-end (smoke) | 6 |
| `test_scoring.py` | Moteur : 3 états (ok/échec/inconnu), gravité déclarée, couverture, discrimination du signal_chaud | **19** |
| `test_vault_schema.py` | FicheProspect, enums, transitions | 15 |
| `test_vault_io.py` | VaultIO (écriture atomique, journal, query, transition) | 30 |
| `test_vault_init.py` | Scaffold idempotent, dashboard, template, git | 25 |
| `test_serializers.py` | diagnostic_to_fiche, diagnostic_to_rapport_md | 18 |
| `test_integration_vault.py` | Pipeline complet → fiche + rapport + journal | 7 |
| `test_api_schema.py` | LedgerEntry, compute_cout | 20 |
| `test_api_io.py` | ApiIO call/cache/budget/mesureur/garde-fou/câblage | 31 |
| `test_collectors_phase_d.py` | §9.9 social passif, derniere_maj, repond_aux_avis, seo, injection | 38 |
| `test_icp_schema.py` | §7.1 IcpConfig + §7.12 FicheProspect rétro-compat | 19 |
| `test_discovery.py` | §7.2-4 + §7.7 DiscoveryCollector (SERP, filtres, dédup) | 36 |
| `test_enrichment.py` | §7.6 + §7.8 PersonEnrichment + Contact minimisation | 16 |
| `test_discovery_vault.py` | §7.5, §7.9-11 dédup inter-runs, dry-run, fiche decouvert | 16 |
| `test_j5_phase0.py` | §13 signal_chaud/accroche, contrat JSON Diagnostic, api_pricing | 20 |
| `test_export.py` | Tests 1-6 : sélection, mapping Kemana, anomalies, garde-fous | 26 |
| `test_usage.py` | Tests 7-8 : agrégation ledger, taux cache, write_system_note | 19 |
| `test_preflight.py` | Tests 9-12, 14 : GO/NO-GO, warn, garde-fous AST, régression | 28 |
| `test_orchestrator.py` | CORE : DAG, tri topologique, verrou, ApiIO unique, machine à états, budget, tranches | 34 |
| `test_pipeline_cli.py` | CORE : CLI `run_pipeline.py` | 4 |
| `test_greenit.py` | GreenIT : config, routage déterministe, max_tokens, empreinte, troncature, ledger, rétro-compat, intégration synthesis | **78** |
| `test_doc_coherence.py` | Garde-fou : les chiffres documentés (tests, routes, écrans, invariants, agents) doivent être les chiffres réels | **9** |
| `tests/integration/` | e2e réels contre un faux serveur HTTP local, sans clé : bus, découverte, diagnostic, export, orchestrateur | **46** |
| `webapp/backend/tests/` | Cockpit : 10 routes, lecture seule, GreenIT, SSE, dégradation vault vide, **convergence socle ⇄ cockpit** | **45** |
| `webapp/frontend/src/__tests__/` | Cockpit : api, dashboard, prospects, détail, greenit (Vitest) | **34** |

**Toute la suite tourne sans aucune clé API** : c'est la preuve permanente que le
repli déterministe et les stubs fonctionnent.

## Prochaines tâches

### Dette technique identifiée (non bloquante, à traiter côté code)

1. **Duplication de la logique de coût.** `diagnostic/usage.py::agreger` et
   `webapp/backend/greenit.py::agreger` calculent tous deux le coût depuis le
   **même** grand livre. **Couvert depuis `611eb74`** par
   `webapp/backend/tests/test_greenit_usage_convergence.py` (7 tests : coût
   total, comptages, par fournisseur, filtre `depuis`, ledger vide, endpoints
   HTTP) — il échoue si les deux divergent. Le risque de divergence silencieuse
   est donc **fermé**. Reste une duplication de code : refactor recommandé à
   terme (une seule fonction de calcul, deux vues), **non urgent**.
2. **`diagnostic/greenit.py` absent de la liste `_check_garde_fous_bus`**
   (`diagnostic/preflight.py`), alors que l'invariant I4 pose la règle « tout
   nouveau module de ce type doit y être ajouté ». La couverture est assurée
   **de fait** par le test générique
   `tests/test_api_io.py::test_requests_pas_importe_niveau_module_hors_api_io`,
   qui parcourt `diagnostic/**` en `rglob` — donc l'invariant tient, mais pas
   par le mécanisme annoncé. Ajouter le module à la liste du préflight.

### Paramétrage réel (Phase D — opératrice / Cowork, pas de code à écrire)
1. Renseigner `SERP_API_KEY` et `APOLLO_API_KEY` dans l'environnement.
2. Relever les vrais tarifs et les saisir dans `knowledge/api_pricing.yaml` :
   - `releve_le: AAAA-MM-JJ` (date du relevé)
   - `prix_par_unite` de serp et apollo (non-zéro)
3. Configurer les budgets de garde-fou dans `api_pricing.yaml` :
   - `budgets.serp.unites_max.requetes` (ex. 500 pour un pilote borné)
   - `budgets.apollo.unites_max.credits` (ex. 50 pour un pilote borné)
4. Initialiser le vault : `python init_vault.py` (idempotent).
5. Lancer `python run_preflight.py` → vérifier **GO** avant tout run réel.
6. Premier run découverte : `python run_discovery.py --icp persona1-quebec --dry-run`.
7. Puis chaîne complète en dry-run :
   `python run_pipeline.py --icp persona1-quebec --dry-run`.

### Palier 2 (ADR 0001) — après le premier pilote
- **Critique de grounding déterministe** entre la synthèse et la transition
  `decouvert → diagnostique`, pour durcir « aucune affirmation non adossée ».
- **Conformité-par-donnée** : politiques `compliance/*.yaml` par marché
  (CASL-QC, nLPD + art. 3 LCD-CH, RGPD-FR, transparence AI Act) + nœud
  « Conformité » **bloquant** en amont d'export et d'outreach.
- **Routage de modèle YAML** — amorcé par le chantier GreenIT `[EN COURS]`.
- ⚠️ Le **superviseur-planificateur LLM est explicitement refusé** (ADR 0001) :
  coût, non-déterminisme, charge cognitive. Ne pas le réintroduire par la porte
  du routage.

### J6 — Outreach : NON ACTIVABLE en l'état
- Séquence d'emails déclenchée depuis le vault (`valide → contacte`).
- **Pré-condition dure** : validation par un juriste du cadre CASL (QC) /
  nLPD + art. 3 LCD (CH) / RGPD (FR) / transparence AI Act **avant tout envoi**.
  Ce n'est pas une formalité et ce n'est pas une tâche de développement.
- Double verrou actuel : `enabled: false` dans `dag_pipeline.yaml` **et**
  `_run_outreach()` qui renvoie `bloque`.
- `rubric_persona2.yaml` (second persona) — indépendant de J6.
- Cron J7 (batch planifié) — **préflight en pré-condition** (déjà premier nœud
  du DAG).

### Palier 3 (ADR 0001) — GELÉ
Fragments multi-tenant (gateway `api_io` métrée par tenant, isolation, coût par
tenant). Déclenchement conditionné à un **seuil de tenants payants défini à
l'avance**, pas à une intuition. Le vault reste la source de vérité : il n'est
**pas** un read-model.
