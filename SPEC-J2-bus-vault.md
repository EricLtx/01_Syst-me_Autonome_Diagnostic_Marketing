# SPEC — Module « J2-bus » : contrôleur de bus vault_io + intégration Obsidian

> Document destiné à Claude Code. À placer à la racine du repo existant (à côté de `CLAUDE.md`).
> Démarrer la session par : « Lis SPEC-J2-bus-vault.md et CLAUDE.md, puis propose un plan d'implémentation phase par phase avant d'écrire du code. »

---

## 1. Contexte et objectif

Le système est conçu sur le modèle d'une architecture micro-ordinateur :

- **RAM / stockage persistant** : un vault Obsidian (fichiers Markdown + frontmatter YAML)
- **Contrôleur de bus** : `vault_io.py` — *seul* module autorisé à lire/écrire dans le vault
- **CPU** : les agents (diagnostic J1 existant, découverte à venir, outreach futur)
- **ROM** : rubrics YAML et templates, en lecture seule pour les agents
- **Disque** : cache de scraping brut, hors du vault
- **Console** : l'opérateur humain, via l'interface Obsidian (validation, « manage by exception »)

Objectif de ce livrable : construire le contrôleur de bus et brancher le pipeline
diagnostic J1 existant dessus, sans rien casser de J1.

## 2. État existant (livrable J1 — 18 fichiers)

Déjà produit et testé end-to-end :

- Collector site web implémenté + 4 collectors stubs (GBP, avis, SEO, social)
- Moteur de scoring générique piloté par rubric
- Synthèse LLM avec fallback déterministe
- Contrat de données : dataclasses `Diagnostic`, `Company`, `Gap`
- `rubric_persona1.yaml` (CVC/HVAC)
- Point d'entrée CLI
- `CLAUDE.md` pré-rempli, README pédagogique
- Cache idempotent pour scraping poli (principe n°5)

**Claude Code : commencer par inventorier le repo réel et confirmer cette liste.
Toute divergence entre cette spec et le code existant doit être signalée avant
implémentation.**

## 3. Écarts à combler (gap analysis explicite)

Ce que J1 ne fait PAS aujourd'hui et que ce livrable doit ajouter :

| # | Manque constaté dans J1 | Réponse dans ce livrable |
|---|---|---|
| G1 | Aucune couche de persistance partagée : le diagnostic sort en JSON/console, pas dans un vault | `vault_io.py` (§4) |
| G2 | Pas de sérialisation `Diagnostic`/`Company` → note Markdown + frontmatter | `serializers.py` (§6) |
| G3 | Le contrat de données existe en dataclasses mais **aucune validation à l'écriture** | Modèles pydantic dans `vault_schema.py` (§4.2) |
| G4 | Aucune machine à états : pas de champ `statut`, pas de notion de pipeline | Registre `statut` + transitions (§5.2) |
| G5 | Pas de structure de vault, ni templates, ni dashboard | Scaffold `vault/` + `00-Dashboard.md` Dataview (§5) |
| G6 | Pas d'écritures atomiques : un crash peut laisser un fichier corrompu | tmp + `os.replace` dans `vault_io.py` (§4.3) |
| G7 | Pas de journal d'exécution : aucune traçabilité ni reprise après crash | `runs.log` append-only JSONL (§7) |
| G8 | Pas de plan d'adressage documenté | `vault/90-Systeme/memory-map.md` généré (§5.3) |
| G9 | Le cache existe mais sa localisation par rapport au vault n'est pas contrainte | Contrainte : cache TOUJOURS hors du vault (§4.4) |
| G10 | Pas de versioning de l'état système | `git init` sur le vault + `.gitignore` (§5.4) |

**Hors périmètre de ce livrable** (J3) : agent découverte, collector Apollo,
activation des 4 stubs, `rubric_persona2.yaml`, orchestrateur cron.

## 4. Spécification `vault_io.py` (contrôleur de bus)

### 4.1 Principe

- ~150–250 lignes, dépendances : stdlib + `pydantic` + `PyYAML` uniquement.
- Aucun autre module du projet n'a le droit d'ouvrir un fichier du vault.
  Faire respecter par convention + un test qui greppe les imports.
- Chemin du vault injecté par config (`VAULT_PATH` env var ou `config.yaml`),
  jamais codé en dur.

### 4.2 Schéma du frontmatter (registres) — `vault_schema.py`

Modèle pydantic `FicheProspect` :

```yaml
---
type: prospect                  # discriminant, obligatoire
persona: 1                      # int, 1 | 2
marche: quebec                  # enum: quebec, romandie, france, suisse, espagne
statut: decouvert               # enum, voir machine à états §5.2
nom: Chauffage ABC inc.
site_web: https://...           # optionnel
score_global: null              # int 0-100, null tant que non diagnostiqué
gaps_majeurs: []                # list[str], identifiants de gaps de la rubric
source_decouverte: manuel       # str
date_creation: 2026-06-09       # date ISO
date_diagnostic: null           # date ISO ou null
rapport: null                   # wikilink vers 30-Diagnostics/..., ou null
---
```

Règles :
- Validation pydantic **à l'écriture ET à la lecture** (une fiche éditée à la
  main dans Obsidian peut être invalide → lever une erreur explicite, ne jamais
  écraser silencieusement).
- Champs inconnus : tolérés en lecture (l'humain peut annoter), préservés à la
  réécriture (round-trip sans perte).
- Le corps Markdown sous le frontmatter appartient à l'humain : `vault_io` ne
  modifie QUE le frontmatter, jamais le corps, sauf à la création (template).

### 4.3 API publique

```python
class VaultIO:
    def __init__(self, vault_path: Path): ...

    # Écriture atomique : écrit .tmp dans le même dossier puis os.replace()
    def write_fiche(self, fiche: FicheProspect) -> Path: ...
    def update_frontmatter(self, fiche_path: Path, **champs) -> FicheProspect: ...

    # Lecture / requête (l'API de requête du bus)
    def read_fiche(self, fiche_path: Path) -> FicheProspect: ...
    def query(self, *, statut=None, persona=None, marche=None) -> list[FicheProspect]: ...

    # Transitions d'état contrôlées (G4)
    def transition(self, fiche_path: Path, nouveau_statut: str) -> FicheProspect:
        """Vérifie que la transition est légale (§5.2), sinon ValueError."""

    # Rapports de diagnostic
    def write_rapport(self, fiche: FicheProspect, contenu_md: str) -> Path: ...

    # Déduplication (préparation J3)
    def exists(self, *, nom: str = None, site_web: str = None) -> Path | None: ...
```

Contraintes :
- `write_fiche` et `write_rapport` : atomiques (G6), idempotentes (réécrire la
  même fiche ne change rien), et journalisées (§7).
- `query` : scan du dossier `10-Prospects/`, parse frontmatter seul (pas le
  corps) pour rester rapide. Pas d'index, pas de base : à l'échelle visée
  (centaines de fiches), le filesystem suffit. Noter ce choix en commentaire.
- Nommage de fichier : slug du nom d'entreprise (`chauffage-abc-inc.md`),
  collision résolue par suffixe `-2`.

### 4.4 Contrainte cache (G9)

Le cache de scraping reste à son emplacement actuel, HORS de `vault/`.
Ajouter une assertion au démarrage : si `CACHE_PATH` est sous `VAULT_PATH`,
erreur fatale avec message explicite.

## 5. Structure du vault à générer

### 5.1 Scaffold (commande `python -m <pkg> init-vault`)

```
vault/
├── 00-Dashboard.md
├── 10-Prospects/
│   ├── persona1-quebec/
│   ├── persona1-romandie/
│   ├── persona2-france/
│   ├── persona2-suisse/
│   └── persona2-espagne/
├── 20-Rubrics/                  # copies en lecture seule des YAML (ROM)
├── 30-Diagnostics/
├── 90-Systeme/
│   ├── memory-map.md
│   └── journal-decisions.md     # vide, appartient à l'humain
└── _templates/
    └── fiche-prospect.md
```

`init-vault` est idempotent : ne touche jamais un fichier existant.

### 5.2 Machine à états (registre `statut`)

```
decouvert → diagnostique → valide → contacte
                ↓
            rejete  (transition possible depuis n'importe quel état, humain seulement)
```

- Les agents ont le droit : `decouvert → diagnostique`.
- Les transitions `diagnostique → valide` et `* → rejete` sont réservées à
  l'humain (dans Obsidian). `vault_io.transition()` les accepte quand même
  (c'est l'humain qui éditera le YAML à la main ; le module doit relire sans
  broncher), mais les agents ne doivent jamais les appeler — l'imposer par un
  paramètre `acteur: Literal["agent","humain"]` vérifié dans `transition()`.

### 5.3 `memory-map.md` (G8)

Générer ce document à partir du schéma pydantic (source unique de vérité) :
table des champs du frontmatter, valeurs légales, qui a le droit d'écrire quoi
(agent vs humain), plan des dossiers. C'est la datasheet du système.

### 5.4 Git (G10)

`init-vault` exécute `git init` dans `vault/` si absent, crée un `.gitignore`
(`.obsidian/workspace*`, `.trash/`). Ne JAMAIS commiter automatiquement :
proposer un `make snapshot` qui fait `git add -A && git commit -m "snapshot <date>"`.

### 5.5 `00-Dashboard.md`

Requêtes Dataview (plugin Obsidian) :
1. « En attente de ma validation » : `statut = diagnostique`, tri par score croissant
2. « Pipeline par persona/marché » : table groupée
3. « Meilleures cibles » : `statut = valide`, score < 50, gaps majeurs affichés

Écrire les requêtes en bloc ```dataview``` avec un commentaire HTML expliquant
chaque requête (dimension pédagogique du projet).

## 6. Adaptation du pipeline J1 (`serializers.py` + writer)

- Nouveau module `serializers.py` : `diagnostic_to_fiche(d: Diagnostic) -> FicheProspect`
  et `diagnostic_to_rapport_md(d: Diagnostic) -> str` (rapport lisible : synthèse
  LLM, tableau des scores par critère, gaps détectés, wikilinks vers la rubric).
- Nouveau flag CLI : `--out vault` (défaut : comportement actuel inchangé —
  **ne pas casser la sortie JSON existante**, c'est le harnais de test de J1).
- Workflow `--out vault` : lire les fiches `statut: decouvert` via
  `vault_io.query()`, exécuter le pipeline J1 par fiche, `write_rapport()`,
  `update_frontmatter(score_global=..., gaps_majeurs=..., rapport=...)`,
  `transition(..., "diagnostique", acteur="agent")`.
- Échec d'un diagnostic : la fiche reste en `decouvert`, l'erreur va dans
  `runs.log`, le pipeline continue (principe n°2 : échec gracieux, isolé).

## 7. Journal `runs.log` (G7)

- JSONL append-only à la racine du repo (PAS dans le vault).
- Une ligne par opération d'écriture du bus :
  `{"ts": ..., "agent": "diagnostic", "op": "write_rapport", "fiche": "...", "resultat": "ok|erreur", "detail": ...}`
- Écrit par `vault_io` lui-même (pas par les agents) : le bus journalise tout
  trafic, les CPU n'ont pas à y penser.

## 8. Tests et critères d'acceptation

1. Round-trip : write_fiche → read_fiche → write_fiche ⇒ fichier identique octet
   pour octet (champs inconnus et corps préservés).
2. Atomicité : tuer le process pendant `write_fiche` (simulé) ⇒ jamais de fichier
   partiel dans le vault.
3. Validation : frontmatter invalide (statut inconnu, persona=3) ⇒ erreur
   explicite, fichier intact.
4. Machine à états : `transition("decouvert","contacte")` ⇒ ValueError ;
   `transition(..., "valide", acteur="agent")` ⇒ ValueError.
5. Query : 3 fiches de statuts/personas différents ⇒ filtres corrects.
6. Intégration : `init-vault` + 1 fiche `decouvert` + pipeline `--out vault` sur
   un site de test ⇒ fiche en `diagnostique`, rapport créé, wikilink valide,
   2 lignes dans `runs.log`.
7. Garde-fou imports : aucun module hors `vault_io.py` n'ouvre de fichier sous
   `vault/` (test par grep/AST).
8. La suite de tests J1 existante passe toujours sans modification.

## 9. Ordre d'implémentation (phases — une session Claude Code par phase)

1. **Phase A** : `vault_schema.py` (pydantic) + tests de validation. Petit, fonde tout.
2. **Phase B** : `vault_io.py` (écriture atomique, lecture, query, transition,
   journal) + tests 1–5, 7.
3. **Phase C** : `init-vault` (scaffold, templates, dashboard, memory-map, git).
4. **Phase D** : `serializers.py` + flag `--out vault` + test d'intégration 6, 8.

Après chaque phase : revue de diff par l'opérateur avant de continuer.
Mettre à jour `CLAUDE.md` (section architecture + commandes) en fin de Phase D.

## 10. Tâches délégables à Claude Cowork (hors code)

À exécuter dans Cowork, pas dans Claude Code :

- **C1 — Jeu d'essai** : rédiger 5–10 fiches prospects réalistes (frontmatter
  conforme §4.2, entreprises CVC québécoises plausibles) servant de fixtures de
  démo après la Phase C.
- **C2 — Relecture du memory-map.md** : vérifier que la datasheet générée est
  compréhensible par un non-développeur ; reformuler si besoin.
- **C3 — Affinage du dashboard** : itérer sur les requêtes Dataview et le
  template de fiche (lisibilité, champs affichés) — c'est de la configuration,
  pas du code.
- **C4 — Revue par lot post-intégration** : après le premier run réel, passer en
  revue les rapports générés dans `30-Diagnostics/` et noter les défauts
  récurrents de la synthèse → retours pour ajuster la rubric (boucle de
  gouvernance humaine).
