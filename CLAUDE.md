# CLAUDE.md — contexte projet pour Claude Code

> Ce fichier est lu automatiquement par Claude Code à chaque session. C'est
> sa mémoire du projet. `/init` peut le (re)générer ; ici il est pré-rempli.
> Le tenir à jour est l'étape la plus rentable et la plus souvent oubliée.

## Ce qu'est ce projet

Écosystème d'agents de prospection pour une consultante en marketing / branding.
Cinq livrables complets :

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
| CPU | agents (pipeline J1, découverte J4, outreach J4) |
| ROM | rubrics YAML + templates (lecture seule pour les agents) |
| Disque | cache de scraping brut, **toujours hors du vault** (contraintes G9 + api_io) |
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
- **Garde-fous bus étendus** : AST walk vérifie que les 5 modules J5 (export, usage,
  preflight, run_export, run_usage) n'importent ni `requests` ni `anthropic` au niveau module.
- **Config = données** : colonnes Kemana dans `knowledge/export_kemana.yaml`, budgets
  dans `budgets:` de `api_pricing.yaml`. Modifier = éditer le YAML, pas le code.

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

# Tests
pytest tests/ -v
pytest tests/ -v -k "vault"             # seulement les tests vault
pytest tests/ -v -k "integration"       # test end-to-end §8.6
pytest tests/ -v -k "phase_d"          # tests Phase D J3 uniquement
pytest tests/ -v -k "icp or discovery or enrichment"  # tests J4
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

## État des tests (365 au total — J1 à J5)

| Fichier | Couverture | Nb |
|---------|-----------|-----|
| `test_j1_smoke.py` | Pipeline end-to-end (smoke) | 6 |
| `test_vault_schema.py` | FicheProspect, enums, transitions | 15 |
| `test_vault_io.py` | VaultIO (écriture atomique, journal, query, transition) | 30 |
| `test_vault_init.py` | Scaffold idempotent, dashboard, template, git | 25 |
| `test_serializers.py` | diagnostic_to_fiche, diagnostic_to_rapport_md | 18 |
| `test_integration_vault.py` | Pipeline complet → fiche + rapport + journal | 7 |
| `test_api_schema.py` | LedgerEntry, compute_cout | 20 |
| `test_api_io.py` | ApiIO call/cache/budget/mesureur/garde-fou/câblage | 31 |
| `test_collectors_phase_d.py` | §9.9 social passif, derniere_maj, repond_aux_avis, seo, injection | 33 |
| `test_icp_schema.py` | §7.1 IcpConfig + §7.12 FicheProspect rétro-compat | ~20 |
| `test_discovery.py` | §7.2-4 + §7.7 DiscoveryCollector (SERP, filtres, dédup) | ~30 |
| `test_enrichment.py` | §7.6 + §7.8 PersonEnrichment + Contact minimisation | ~20 |
| `test_discovery_vault.py` | §7.5, §7.9-11 dédup inter-runs, dry-run, fiche decouvert | ~20 |
| `test_j5_phase0.py` | §13 signal_chaud/accroche, contrat JSON Diagnostic, api_pricing | 20 |
| `test_export.py` | Tests 1-6 : sélection, mapping Kemana, anomalies, garde-fous | 22 |
| `test_usage.py` | Tests 7-8 : agrégation ledger, taux cache, write_system_note | 20 |
| `test_preflight.py` | Tests 9-12, 14 : GO/NO-GO, warn, garde-fous AST, régression | 27 |

## Prochaines tâches — Paramétrage réel (Phase D / Cowork)

### Paramétrage J4 + J5 (opératrice / Cowork — pas de code à écrire)
1. Renseigner `SERP_API_KEY` et `APOLLO_API_KEY` dans l'environnement.
2. Relever les vrais tarifs et les saisir dans `knowledge/api_pricing.yaml` :
   - `releve_le: AAAA-MM-JJ` (date du relevé)
   - `prix_par_unite` de serp et apollo (non-zéro)
3. Configurer les budgets de garde-fou dans `api_pricing.yaml` :
   - `budgets.serp.unites_max.requetes` (ex. 500 pour un pilote borné)
   - `budgets.apollo.unites_max.credits` (ex. 50 pour un pilote borné)
4. Lancer `python run_preflight.py` → vérifier GO avant tout run réel.
5. Premier run découverte : `python run_discovery.py --icp persona1-quebec --dry-run`.

### J6 — Outreach (session suivante)
- Séquence d'emails déclenchée depuis le vault (statut `valide → contacte`).
- Faire valider par un juriste le cadre CASL (QC) / nLPD + art. 3 LCD (CH) / RGPD (FR)
  **avant tout envoi**.
- `rubric_persona2.yaml` (second persona).
- Orchestrateur cron (traitement batch planifié) — préflight en pré-condition.
