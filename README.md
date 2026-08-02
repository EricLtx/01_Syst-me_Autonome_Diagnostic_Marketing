# Système Autonome de Diagnostic Marketing — « Kemana-Flow »

Écosystème d'agents de prospection pour une consultante en marketing / branding.
Entrée : un profil de client idéal. Sortie : une liste de prospects qualifiés,
chacun accompagné d'un diagnostic de marque scoré et d'un mini-audit rédigé.

> **Documentation** — `docs/architecture/` (vue d'ensemble, invariants, flux de
> données) · `docs/adr/` (décisions structurantes) · `docs/CHANGELOG.md`
> (avancement réel) · `docs/agents/ECOSYSTEME.md` (les agents de construction).

---

## ⚠️ État réel du système (vérifié le 2026-08-01)

Ces limites sont **structurelles et voulues** — ce sont les garde-fous qui
fonctionnent, pas des défauts :

| Constat | Conséquence |
|---|---|
| **Aucune clé API dans l'environnement** (`SERP_API_KEY`, `APOLLO_API_KEY`, `GOOGLE_PLACES_API_KEY`, `ANTHROPIC_API_KEY`) | aucun run réel possible ; tout tourne **hors ligne** (stubs + repli déterministe), y compris l'intégralité de la suite de tests |
| **`knowledge/api_pricing.yaml` à `0`**, `releve_le: null`, budgets à `0` | **`run_preflight.py` renvoie NO-GO structurel** ; tout coût affiché vaut 0,00 et n'est pas engageant |
| **Vault non initialisé** (`vault/` vide) | lancer `python init_vault.py` |
| **J6 outreach non activable** | `enabled: false` dans `dag_pipeline.yaml` **et** runner qui refuse ; validation juridique CASL / nLPD + art. 3 LCD / RGPD / AI Act requise |

Lever les trois premiers points relève de la **Phase D** (paramétrage par
l'opératrice : variables d'environnement + YAML), pas du développement.

---

## Les livrables

Cinq livrables métier, une couche d'ordonnancement, une console d'observation :

- **J1 — pipeline diagnostic** : prend une entreprise en entrée, produit un
  **diagnostic de marque scoré** + un **mini-audit lisible**. Autonome,
  testable hors-ligne.
- **J2 — bus vault** : couche de persistance Obsidian. Le pipeline J1 écrit
  ses résultats dans un vault structuré ; un opérateur humain valide via
  Obsidian. Audit de marque traçable, versionné, pilotable en lot.
- **J3 — bus I/O + collecteurs réels** : `api_io.py` orchestre tous les appels
  externes (cache, budget, journal). Collecteurs Google Places, SEO, social.
- **J4 — agent découverte** : `run_discovery.py` (SERP → candidates → fiches
  `decouvert`) + enrichissement Apollo. ICP = données YAML dans `icp/`.
- **J5 — sortie + préflight** : `run_export.py` (fiches `valide` → liste Kemana
  CSV/JSONL, opt_out absolu), `run_usage.py` (agrégat usage API), `run_preflight.py`
  (9 contrôles GO/NO-GO, code de sortie 0/1).
- **CORE — orchestrateur DAG « Kemana-Flow »** : `run_pipeline.py` +
  `diagnostic/orchestrator.py` + `dag_pipeline.yaml`. Ordonnancement déterministe
  de toute la chaîne, instance `ApiIO` **unique**, verrou de run, reprise
  idempotente. Décision : `docs/adr/0001-orchestrateur-dag-deterministe.md`.
- **Cockpit opérateur** : `webapp/backend` (FastAPI, 10 routes `GET`, dont un
  flux SSE d'observabilité GreenIT temps réel) + `webapp/frontend` (React 18 +
  Vite + TypeScript, 6 écrans). **Lecture seule stricte** — complément
  d'Obsidian, jamais un substitut à la porte humaine.
- **GreenIT — efficience et observabilité** : routage de modèle **déterministe**
  piloté par `knowledge/greenit.yaml` (`diagnostic/greenit.py`), bornes de
  frugalité, empreinte **estimée** tracée au grand livre.
  Décision : `docs/adr/0002-greenit-efficience-et-observabilite.md`.
- **J6 — outreach** : **non implémenté, non activable** (voir ci-dessus).

Cible actuelle : persona 1 — installateur / détaillant HVAC, séquence Québec → Suisse.

---

## Arborescence

```
01_Systeme_Autonome_Diagnostic_Marketing/
├─ CLAUDE.md                      ← contexte projet pour Claude Code (mémoire de session)
├─ README.md                      ← ce fichier
├─ requirements.txt
├─ SPEC-J2…J5-*.md                ← spécifications des livrables
│
├─ run_pipeline.py                ← CLI de l'orchestrateur DAG (chaîne complète)
├─ dag_pipeline.yaml              ← LE GRAPHE EST UNE DONNÉE
├─ run_diagnostic.py              ← CLI J1 (mode standard + mode vault)
├─ run_discovery.py               ← CLI J4 (découverte SERP + Apollo)
├─ run_export.py                  ← CLI J5 (liste Kemana, lecture seule)
├─ run_usage.py                   ← CLI J5 (agrégat api_usage.log)
├─ run_preflight.py               ← CLI J5 (GO / NO-GO, code de sortie 0/1)
├─ init_vault.py                  ← CLI initialisation du vault Obsidian
│
├─ knowledge/                     ← ROM : la connaissance métier est une DONNÉE
│  ├─ rubric_persona1.yaml        ← rubrique de scoring
│  ├─ api_pricing.yaml            ← grille tarifaire + budgets de garde-fou
│  ├─ export_kemana.yaml          ← colonnes de la liste de sortie
│  └─ greenit.yaml                ← stratégie d'efficience  [EN COURS]
├─ icp/
│  └─ persona1-quebec.yaml        ← profil de client idéal (validé par IcpConfig)
│
├─ diagnostic/                    ← package principal
│  ├─ orchestrator.py             ← CORE : ordonnancement DAG, ZÉRO logique métier
│  ├─ models.py                   ← contrat J1 : Diagnostic, Company, Gap
│  ├─ config.py                   ← charge rubrique, ICP, grille tarifaire
│  ├─ pipeline.py                 ← chaîne J1 (collecte → score → synthèse)
│  ├─ scoring.py                  ← moteur générique piloté par la rubrique
│  ├─ synthesis.py                ← rédaction LLM + QA + repli déterministe
│  ├─ serializers.py              ← Diagnostic → FicheProspect / Rapport Markdown
│  ├─ vault_schema.py             ← FicheProspect Pydantic, enums, machine à états
│  ├─ vault_io.py                 ← BUS STOCKAGE : seul module à lire/écrire le vault
│  ├─ vault_init.py               ← scaffold idempotent du vault
│  ├─ vault_runner.py             ← mode --out vault
│  ├─ api_io.py                   ← BUS RÉSEAU : seul module à toucher le réseau
│  ├─ api_schema.py               ← LedgerEntry, calcul de coût
│  ├─ discovery.py                ← J4 : SERP → Candidate
│  ├─ enrichment.py               ← J4 : Apollo → Contact (6 champs, minimisation RGPD)
│  ├─ icp_schema.py               ← IcpConfig
│  ├─ export.py                   ← J5 : sélection + mapping Kemana (lecture seule)
│  ├─ usage.py                    ← J5 : agrégation du grand livre
│  ├─ preflight.py                ← J5 : 9 contrôles GO/NO-GO + garde-fous AST
│  └─ collectors/
│     ├─ base.py                  ← interface Collector (enfichable, anti-crash)
│     ├─ website.py               ← palier 0 — fetch via api_io
│     ├─ seo.py                   ← palier 0 — dérivé de _website_signals
│     ├─ social.py                ← palier 0 — dérivé de _website_signals
│     ├─ gbp.py                   ← palier 1 — Google Places
│     └─ reviews.py               ← palier 1 — Google Places
│
├─ webapp/                        ← cockpit opérateur — LECTURE SEULE STRICTE
│  ├─ backend/                    ← FastAPI : 10 routes GET, services.py, greenit.py (SSE)
│  └─ frontend/                   ← React + Vite + TS : 6 écrans, thème clair/sombre
│
├─ tests/                         ← suite Python (J1→J5 + CORE)
├─ .claude/agents/                ← sous-agents Claude Code persistants
├─ docs/
│  ├─ architecture/               ← vue d'ensemble, invariants, flux de données
│  ├─ adr/                        ← décisions structurantes
│  ├─ agents/ECOSYSTEME.md        ← cartographie des agents
│  ├─ CHANGELOG.md
│  └─ strategie/                  ← analyses + gouvernance (chef de projet)
│
├─ vault/                         ← créé par init_vault.py (non versionné)
│  ├─ 00-Dashboard.md             ← tableau de bord Dataview
│  ├─ 10-Prospects/               ← fiches par persona/marché
│  ├─ 20-Rubrics/ 30-Diagnostics/ 90-Systeme/ _templates/
│
└─ (hors versionnement)
   ├─ exports/                    ← listes Kemana générées
   ├─ .cache/                     ← cache api_io + manifestes de run
   ├─ api_usage.log               ← grand livre des coûts (JSONL append-only)
   ├─ runs.log                    ← journal des écritures vault (JSONL)
   └─ .run.lock                   ← verrou d'exécution de l'orchestrateur
```

---

## Installation

```bash
python -m venv .venv
# Windows :
.venv\Scripts\activate
# macOS / Linux :
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Utilisation

### Mode standard — diagnostic d'une entreprise (J1)

```bash
# Sortie lisible
python run_diagnostic.py --nom "Climatisation Tremblay" \
    --url "https://exemple-hvac.ca" --region "Québec, QC"

# Sortie JSON complète
python run_diagnostic.py --nom "Climatisation Tremblay" \
    --url "https://exemple-hvac.ca" --json
```

Sans `ANTHROPIC_API_KEY`, la synthèse utilise un **repli déterministe** : le
module fonctionne entièrement hors-ligne.

### Mode vault — traitement en lot (J2)

```bash
# 1. Initialiser le vault (une seule fois ; idempotent si relancé)
python init_vault.py
python init_vault.py --vault chemin/vers/vault    # ou variable $VAULT_PATH

# 2. Créer une fiche manuellement
#    Copier vault/_templates/fiche-prospect.md dans le bon sous-dossier
#    Renseigner nom, site_web, marche, persona — laisser statut: decouvert

# 3. Lancer le diagnostic sur toutes les fiches 'decouvert'
python run_diagnostic.py --out vault
python run_diagnostic.py --out vault --vault chemin/vers/vault
```

Le pipeline :
1. Lit toutes les fiches `statut: decouvert` dans `10-Prospects/`
2. Exécute le diagnostic J1 sur chacune
3. Écrit un rapport Markdown dans `30-Diagnostics/`
4. Met à jour le frontmatter (score, gaps, date, wikilink rapport)
5. Passe la fiche en `statut: diagnostique`
6. Journalise chaque opération dans `runs.log`

En cas d'erreur sur une fiche, l'erreur est journalisée et les autres fiches
continuent d'être traitées.

### Mode orchestré — la chaîne complète (CORE)

```bash
python run_pipeline.py --icp persona1-quebec              # chaîne complète
python run_pipeline.py --icp persona1-quebec --dry-run    # n'écrit RIEN
python run_pipeline.py --icp persona1-quebec --depuis diagnostic
python run_pipeline.py --icp persona1-quebec --jusqu-a discovery
```

Chaîne exécutée :
`preflight_gate → discovery → diagnostic → [PORTE HUMAINE] → export → usage_snapshot`.

Code de sortie : `0` = chaîne OK, `1` = arrêt (NO-GO préflight, budget dépassé,
nœud bloquant). Les `run_*.py` continuent de fonctionner **seuls** : l'orchestrateur
ne les remplace pas, il les ordonne.

### Ouvrir le vault dans Obsidian

Pointer Obsidian vers le dossier `vault/` (*Open folder as vault*). Activer le
plugin **Dataview** pour que `00-Dashboard.md` affiche les tableaux de bord.

C'est ici que se joue la **porte humaine** : l'opératrice lit les rapports de
`30-Diagnostics/` et fait passer les fiches retenues en `statut: valide`.
**Aucun agent ne peut franchir cette porte.**

### Cockpit opérateur (lecture seule)

```bash
pip install -r webapp/backend/requirements.txt
uvicorn webapp.backend.app:app --reload --port 8000   # API + doc sur /docs
cd webapp/frontend && npm install && npm run dev      # front sur :5173
```

Cinq écrans : Dashboard, Prospects, Détail prospect, Usage, Préflight.
Thème clair et sombre. Un mode mock permet de démontrer l'application
**hors ligne**, sans backend.

---

## Tests

```bash
pytest tests/ -v                            # suite complète (560 tests — J1 à J5, CORE, GreenIT, e2e)
pytest tests/integration -v                 # tests d'intégration e2e (faux serveur d'API local)
pytest tests/ -v -k "vault"                 # tests vault
pytest tests/ -v -k "integration"           # test end-to-end
pytest tests/ -v -k "export or usage or preflight"   # tests J5
pytest tests/ -v -k "orchestrator or pipeline_cli"   # tests CORE
pytest tests/integration -q                 # flux e2e réels contre un faux serveur local (46)
pytest tests/test_greenit.py -q             # routage, frugalité, empreinte (78)
pytest webapp/backend/tests -q              # backend cockpit (45 tests)
cd webapp/frontend && npm run build && npm run test   # front (tsc + vite + vitest, 34)
```

**Toute la suite tourne sans aucune clé API** — c'est la preuve permanente que
le repli déterministe et les stubs fonctionnent.

---

## Architecture en bref

Le système suit le modèle d'un **micro-ordinateur** : chaque ressource partagée a
**un seul contrôleur de bus**, et tout le monde passe par lui. C'est l'unique
raison pour laquelle les coûts et les écritures sont intégralement traçables.

| Rôle | Composant |
|------|-----------|
| Stockage persistant | `vault/` — notes Markdown + frontmatter YAML, source de vérité |
| **Bus stockage** | `diagnostic/vault_io.py` — **seul** module à lire/écrire `vault/` |
| **Bus réseau** | `diagnostic/api_io.py` — **seul** module dont les fn touchent le réseau |
| CPU | agents : pipeline J1, découverte J4, export J5 |
| Séquenceur | `diagnostic/orchestrator.py` + `dag_pipeline.yaml` |
| ROM | rubrics, ICP, tarifs, colonnes d'export, graphe du DAG — tous en YAML |
| Disque | `.cache/` — **toujours hors du vault** |
| Console | Obsidian (décision) + `webapp/` (observation, lecture seule) |
| Grand livre | `api_usage.log` (coûts) · `runs.log` (écritures vault) |

**Invariants de sécurité** — détail et preuves dans
`docs/architecture/invariants.md` (21 invariants, chacun avec sa commande de
contrôle) :

- Toute écriture dans le vault est **atomique** (`tmp` + `os.replace()`) et
  **journalisée** dans `runs.log`. `os.replace()` est **exclusif à `vault_io.py`**.
- Tout appel réseau passe par `ApiIO` : cache, **budget bloquant avant l'appel**,
  ligne au grand livre. Aucun import `requests`/`anthropic` au niveau module dans
  les modules surveillés par le garde-fou AST du préflight.
- La machine à états (`decouvert → diagnostique → valide → contacte`, `* → rejete`)
  est validée à chaque transition. **Un agent ne peut faire que
  `decouvert → diagnostique`** — le reste est humain.
- Le graphe du pipeline, les rubriques, les ICP et les tarifs sont des **données**,
  jamais du code.
- Le cockpit web est **strictement en lecture seule**.
- Le LLM **rédige à partir de faits déjà établis** ; il ne collecte jamais. Sans
  clé, un repli déterministe prend le relais.

---

## Construire ce projet — écosystème d'agents

Le projet est développé par **orchestration d'agents spécialisés**, définis de
façon **persistante** dans `.claude/agents/` — ils survivent aux sessions.

| Agent | Rôle |
|---|---|
| `agent-documentation` | lancé à **chaque** itération : changelog, ADR, architecture, `CLAUDE.md` |
| `agent-revue` | garde-fou anti-hallucination, **sans droit d'écriture** |
| `agent-architecte` | conception, invariants de bus, ADR |
| `agent-dev-python` | implémentation du socle |
| `agent-frontend` | cockpit React/TS |
| `agent-greenit` | efficience des appels IA, frugalité, coûts |
| `agent-produit` | roadmap, priorisation |

**Porte de cohérence 97 %** : après chaque itération, l'agent de revue
ré-exécute 10 à 14 assertions vérifiables (tests, build, AST, `git diff`) et
calcule un taux. Sous le seuil, le **même** agent d'implémentation est relancé,
contexte conservé, avec les assertions échouées comme backlog.
Protocole : `docs/strategie/GOUVERNANCE-revue-iterative.md` ·
cartographie : `docs/agents/ECOSYSTEME.md`.

---

## Prochaine étape — Paramétrage réel (Phase D)

Avant le premier run réel, l'opératrice doit — **aucun code à écrire** :

1. Renseigner `SERP_API_KEY` et `APOLLO_API_KEY` dans l'environnement.
2. Saisir les vrais tarifs + `releve_le` dans `knowledge/api_pricing.yaml`.
3. Configurer `budgets.serp` et `budgets.apollo` dans `api_pricing.yaml`.
4. Initialiser le vault : `python init_vault.py`.
5. Lancer `python run_preflight.py` → vérifier **GO** (code de sortie 0).
6. Tester : `python run_discovery.py --icp persona1-quebec --dry-run`, puis
   `python run_pipeline.py --icp persona1-quebec --dry-run`.

**J6 — Outreach : non activable.** Séquence d'emails depuis le vault
(`valide → contacte`). Validation par un **juriste** obligatoire avant tout
envoi : CASL (QC), nLPD + art. 3 LCD (CH), RGPD (FR), transparence AI Act.
Ce n'est pas une tâche de développement.

---

## Mise en place de Claude Code

Claude Code est l'agent de codage en terminal : il lit le dépôt, édite les
fichiers, exécute les commandes et gère git.

```bash
# Installeur natif :
curl -fsSL https://claude.ai/install.sh | bash
# — ou via npm (Node.js 18+) :
npm install -g @anthropic-ai/claude-code

cd 01_Systeme_Autonome_Diagnostic_Marketing
claude
```

`CLAUDE.md` est lu automatiquement à chaque session : c'est la mémoire du
projet, et elle est déjà remplie. **Ne pas la régénérer avec `/init`** — cela
écraserait les invariants d'architecture accumulés. On la **complète**.

Les sous-agents de `.claude/agents/` sont disponibles immédiatement : décrire la
tâche suffit à déclencher le bon (« documente ce qui a changé », « vérifie que
ce chantier tient ses promesses », « où doit vivre ce nouveau module ? »).

**Comment piloter :**
1. *Donner le cap, pas la solution.* Pointe l'architecture, laisse-le proposer
   un plan avant de coder.
2. *Relire le diff, pas le réécrire.* Ta valeur est dans la direction et la revue.
3. *Capitaliser.* Quand une convention émerge, demande-lui de l'inscrire dans
   `CLAUDE.md`. Le projet s'auto-documente.

Ton historique C++/VHDL joue ici : la pensée système — pipelines, états,
contraintes — est exactement ce qu'une architecture d'agents réclame.

---

## Conformité

**Par construction :**
- **Scraping poli** — User-Agent honnête, timeout, cache disque, une requête par
  cible.
- **Aucun scraping LinkedIn ni Facebook.** Les données « personnes » proviennent
  exclusivement de l'API Apollo.
- **Minimisation** — le modèle `Contact` est limité à 6 champs
  (`extra="forbid"`) : la minimisation RGPD est garantie par le schéma, pas par
  la discipline. `contact_email_source` est toujours renseigné quand un email est
  présent (piste d'audit).
- **`opt_out: true` exclut une fiche de tout export, sans exception.**
- **Porte humaine obligatoire** — aucune fiche ne sort du système sans qu'une
  personne l'ait validée dans Obsidian. Aucun agent, aucune interface web ne peut
  la contourner.
- **Traçabilité** — chaque écriture du vault est journalisée (`runs.log`), chaque
  appel externe est comptabilisé (`api_usage.log`).

**Avant tout envoi d'email (J6) — pré-condition dure :**
validation par un **juriste** du cadre CASL (Québec), nLPD + art. 3 LCD (Suisse),
RGPD (France) et des obligations de transparence de l'AI Act. Le ciblage B2B,
l'identification claire de l'expéditeur et le mécanisme de désinscription sont
nécessaires mais **pas suffisants** pour se dispenser de cette validation.
J6 est verrouillé à double tour tant qu'elle n'a pas eu lieu.

**Sur les chiffres de coût et d'empreinte :** tant que
`knowledge/api_pricing.yaml` est à `0`, aucun coût affiché n'est engageant. Les
estimations d'énergie et de CO₂e sont des **ordres de grandeur paramétrables**,
jamais des mesures certifiées — un chiffrage opposable exigerait une ACV réalisée
par un tiers.
