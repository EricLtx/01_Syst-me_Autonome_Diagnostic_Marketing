# Module `diagnostic` — J1 + J2

Deux livrables regroupés dans ce module :

- **J1 — pipeline diagnostic** : prend une entreprise en entrée, produit un
  **diagnostic de marque scoré** + un **mini-audit lisible**. Autonome,
  testable hors-ligne.
- **J2 — bus vault** : couche de persistance Obsidian. Le pipeline J1 écrit
  ses résultats dans un vault structuré ; un opérateur humain valide via
  Obsidian. Audit de marque traçable, versionné, pilotable en lot.

Cible actuelle : persona 1 — installateur / détaillant HVAC, séquence Québec → Suisse.

---

## Arborescence

```
01_Module_Diagnostic/
├─ CLAUDE.md                      ← contexte projet pour Claude Code
├─ README.md                      ← ce fichier
├─ requirements.txt
├─ SPEC-J2-bus-vault.md           ← spécification du livrable J2
│
├─ run_diagnostic.py              ← CLI (mode standard + mode vault)
├─ init_vault.py                  ← CLI initialisation du vault Obsidian
│
├─ knowledge/
│  └─ rubric_persona1.yaml        ← rubrique métier (jugement en données, pas en code)
│
├─ diagnostic/                    ← package principal
│  ├─ models.py                   ← contrat J1 : Diagnostic, Company, Gap (dataclasses)
│  ├─ config.py                   ← charge rubrique + base de connaissances
│  ├─ pipeline.py                 ← orchestre la chaîne J1 (collecte → score → synthèse)
│  ├─ scoring.py                  ← moteur de scoring générique (piloté par la rubrique)
│  ├─ synthesis.py                ← rédaction LLM + contrôle qualité + repli déterministe
│  ├─ serializers.py              ← Diagnostic → FicheProspect / Rapport Markdown (J2)
│  ├─ vault_schema.py             ← FicheProspect Pydantic, enums, machine à états (J2)
│  ├─ vault_io.py                 ← bus controller : seul module à lire/écrire le vault (J2)
│  ├─ vault_init.py               ← scaffold idempotent du vault Obsidian (J2)
│  ├─ vault_runner.py             ← orchestrateur mode --out vault (J2)
│  └─ collectors/
│     ├─ base.py                  ← interface Collector (enfichable, anti-crash)
│     ├─ website.py               ← scraping site web (implémenté)
│     ├─ gbp.py                   ← Google Business Profile (stub — J3)
│     ├─ reviews.py               ← avis en ligne (stub — J3)
│     ├─ seo.py                   ← SEO (stub — J3)
│     └─ social.py                ← réseaux sociaux (stub — J3)
│
├─ tests/
│  ├─ test_j1_smoke.py            ← smoke tests pipeline J1 (6)
│  ├─ test_vault_schema.py        ← schéma Pydantic, enums, transitions (15)
│  ├─ test_vault_io.py            ← bus controller : atomicité, journal, query… (30)
│  ├─ test_vault_init.py          ← scaffold idempotent, dashboard, git… (25)
│  ├─ test_serializers.py         ← Diagnostic → Fiche / Rapport Markdown (18)
│  └─ test_integration_vault.py   ← pipeline complet §8.6 (7)
│
└─ vault/                         ← créé par init_vault.py (non versionné)
   ├─ 00-Dashboard.md             ← tableau de bord Dataview (pipeline + gaps + relance)
   ├─ 10-Prospects/               ← fiches prospect par persona/marché
   ├─ 20-Rubrics/                 ← copies des rubrics YAML
   ├─ 30-Diagnostics/             ← rapports générés par le pipeline
   ├─ 90-Systeme/                 ← memory-map + journal de décisions
   └─ _templates/                 ← gabarit fiche-prospect.md
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

### Ouvrir le vault dans Obsidian

Pointer Obsidian vers le dossier `vault/` (Open folder as vault). Activer le
plugin **Dataview** pour que `00-Dashboard.md` affiche les tableaux de bord.

---

## Tests

```bash
pytest tests/ -v                    # suite complète (101 tests)
pytest tests/ -v -k "vault"         # seulement les tests vault
pytest tests/ -v -k "integration"   # test end-to-end §8.6
```

---

## Architecture en bref

Le système suit le modèle d'un **micro-ordinateur** :

| Rôle | Composant |
|------|-----------|
| RAM | `vault/` — notes Markdown + frontmatter YAML |
| Bus controller | `vault_io.py` — seul module à lire/écrire dans `vault/` |
| CPU | agents (pipeline J1 aujourd'hui, découverte J3 et outreach J4 à venir) |
| ROM | rubrics YAML + templates (lecture seule) |
| Disque | cache de scraping brut, toujours hors du vault |
| Console | opérateur humain via Obsidian |

**Invariants de sécurité :**
- Toute écriture dans le vault est atomique (`tmp` + `os.replace()`).
- Tout appel d'agent passe par `VaultIO` et est journalisé dans `runs.log`.
- La machine à états (`decouvert → diagnostique → valide → contacte`) est
  validée à chaque transition. Un agent ne peut que passer `decouvert → diagnostique`.

---

## Prochaine étape (J3)

Agent de découverte : alimentation automatique du vault en fiches `decouvert`
depuis une source (Apollo, LinkedIn, annuaire sectoriel). Les collecteurs stubs
(GBP, avis, SEO, social) seront activés avec leurs vraies API.

---

## Construire et étendre ce module avec Claude Code

Claude Code est l'agent de codage en terminal : il lit le dépôt, édite les
fichiers, exécute les commandes et gère git.

**Mise en place (5 min) :**
```bash
# Installeur natif :
curl -fsSL https://claude.ai/install.sh | bash
# — ou via npm (Node.js 18+) :
npm install -g @anthropic-ai/claude-code

cd 01_Module_Diagnostic
claude
```

**Le réflexe à prendre : `/init`.** Régénère `CLAUDE.md` avec la structure
actuelle du projet. Un `CLAUDE.md` est déjà fourni — il garde les règles
d'architecture à portée de l'agent à chaque session.

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

Le scraping est volontairement poli (User-Agent, timeout, cache, une requête
par cible). Pour l'outreach à venir (J3+), CASL (Québec) et la nLPD + art. 3
LCD (Suisse) encadrent l'email à froid : ciblage B2B, identification claire,
désinscription. À faire valider par un juriste avant envoi.
