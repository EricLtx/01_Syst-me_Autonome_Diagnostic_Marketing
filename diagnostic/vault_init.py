"""
vault_init.py — scaffolding idempotent du vault Obsidian (§5 de la spec J2).

Règle d'or : ne jamais modifier un fichier existant.
Un fichier absent → créé. Un fichier présent → ignoré silencieusement.
Ainsi, les annotations humaines et les fiches existantes survivent à toute
ré-exécution (relance après mise à jour, crash, migration).
"""
from __future__ import annotations

import shutil
import subprocess
from datetime import date
from pathlib import Path

from diagnostic.vault_schema import Marche, Statut, TRANSITIONS_AGENT, TRANSITIONS_LEGALES

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"

VAULT_DIRS = [
    "10-Prospects/persona1-quebec",
    "10-Prospects/persona1-romandie",
    "10-Prospects/persona2-france",
    "10-Prospects/persona2-suisse",
    "10-Prospects/persona2-espagne",
    "20-Rubrics",
    "30-Diagnostics",
    "90-Systeme",
    "_templates",
]

_GITIGNORE = """.obsidian/workspace*
.obsidian/cache
.trash/
.DS_Store
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_if_absent(path: Path, content: str) -> bool:
    """Écrit uniquement si absent. Retourne True si le fichier a été créé."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _dashboard_md() -> str:
    return """\
# 00 — Dashboard prospects

> Tableau de bord opérationnel. Requiert le plugin [Dataview](https://blacksmithgu.github.io/obsidian-dataview/).
> Rafraîchir : rouvrir la note ou activer *Live Preview*.

---

## En attente de ma validation

<!-- Fiches diagnostiquées, triées par score croissant.
     Les moins bien notées d'abord : plus de gaps = argument de vente plus fort. -->

```dataview
TABLE nom AS "Entreprise", score_global AS "Score /100", gaps_majeurs AS "Gaps détectés"
FROM "10-Prospects"
WHERE statut = "diagnostique"
SORT score_global ASC NULLS LAST
```

---

## Pipeline par persona / marché

<!-- Vue d'ensemble du pipeline complet, hors fiches rejetées.
     Permet de surveiller la densité par segment et d'équilibrer l'effort de prospection. -->

```dataview
TABLE rows.file.link AS "Fiches", rows.statut AS "Statut", rows.score_global AS "Score"
FROM "10-Prospects"
WHERE type = "prospect" AND statut != "rejete"
GROUP BY (persona + " — " + marche)
SORT file.name ASC
```

---

## Meilleures cibles validées

<!-- Fiches validées avec score < 50 : beaucoup de gaps = fort potentiel d'amélioration
     = argument de vente concret et chiffré à présenter lors du premier contact. -->

```dataview
TABLE nom AS "Entreprise", score_global AS "Score /100", gaps_majeurs AS "Axes à travailler"
FROM "10-Prospects"
WHERE statut = "valide" AND score_global < 50
SORT score_global ASC
```
"""


def _template_fiche_md() -> str:
    today = date.today().isoformat()
    return f"""\
---
type: prospect
persona: 1
marche: quebec
statut: decouvert
nom:
site_web:
score_global: null
gaps_majeurs: []
source_decouverte: manuel
date_creation: {today}
date_diagnostic: null
rapport: null
---

<!-- Notes personnelles sur cette entreprise.
     Tous les champs supplémentaires que vous ajoutez ici sont préservés automatiquement. -->
"""


def _memory_map_md() -> str:
    """Génère la datasheet du système depuis vault_schema.py (source de vérité)."""
    statuts = " | ".join(f"`{s.value}`" for s in Statut)
    marches = " | ".join(f"`{m.value}`" for m in Marche)

    transitions_rows = []
    for depart, cibles in sorted(TRANSITIONS_LEGALES.items(), key=lambda x: x[0].value):
        for cible in sorted(cibles, key=lambda x: x.value):
            cibles_agent = TRANSITIONS_AGENT.get(depart, set())
            acteur = "agent + humain" if cible in cibles_agent else "**humain uniquement**"
            transitions_rows.append(f"| `{depart.value}` → `{cible.value}` | {acteur} |")
    transitions_table = "\n".join(transitions_rows)

    return f"""\
# memory-map — Datasheet du système

> Généré automatiquement depuis `diagnostic/vault_schema.py`.
> Relancer `python init_vault.py` pour mettre à jour après une modification du schéma.

---

## Frontmatter d'une fiche prospect

| Champ | Type | Valeurs légales | Écrit par | Description |
|---|---|---|---|---|
| `type` | `str` | `prospect` | système | Discriminant, toujours `prospect` |
| `persona` | `int` | `1` \\| `2` | humain / agent | 1 = HVAC Québec–Romandie · 2 = France–Suisse–Espagne |
| `marche` | `str` | {marches} | humain / agent | Marché géographique ciblé |
| `statut` | `str` | {statuts} | machine à états | Workflow — transitions contrôlées par `vault_io` |
| `nom` | `str` | — | humain | Nom officiel de l'entreprise |
| `date_creation` | `date` | `AAAA-MM-JJ` | humain | Date d'entrée dans le vault |
| `site_web` | `str \\| null` | URL | humain / agent | Site principal de l'entreprise |
| `score_global` | `int \\| null` | `0`–`100` | **agent** | Score calculé par le pipeline de diagnostic |
| `gaps_majeurs` | `list[str]` | identifiants rubrique | **agent** | Gaps détectés lors du diagnostic |
| `source_decouverte` | `str` | `manuel`, `apollo`… | humain | Origine de la cible |
| `date_diagnostic` | `date \\| null` | `AAAA-MM-JJ` | **agent** | Date du dernier diagnostic automatique |
| `rapport` | `str \\| null` | wikilink | **agent** | `[[30-Diagnostics/nom-entreprise]]` |

> **Annotations libres** : tout champ non listé ci-dessus est toléré et préservé
> en round-trip (`extra = "allow"`). Exemples : `note_humaine`, `priorite`, `relance_prevue`.
> Vous pouvez annoter librement vos fiches sans risque de perte.

---

## Machine à états (`statut`)

```
decouvert ──→ diagnostique ──→ valide ──→ contacte
    │               │              │          │
    └───────────────┴──────────────┴──────────┴──→ rejete
                                              (humain uniquement, depuis tout état)
```

| Transition | Déclenché par |
|---|---|
{transitions_table}

---

## Plan des dossiers

| Dossier | Rôle | Accès |
|---|---|---|
| `10-Prospects/` | Fiches prospects par persona et marché | Agent (lecture/écriture via `vault_io`) + humain |
| `20-Rubrics/` | Copies YAML des rubriques de scoring (ROM) | Lecture seule — ne pas modifier |
| `30-Diagnostics/` | Rapports détaillés générés par le pipeline | Agent (création) + humain (lecture, annotation) |
| `90-Systeme/` | Datasheet système, journal de décisions | Référence humain |
| `_templates/` | Template fiche prospect pour création manuelle | Humain |

---

## Règles à respecter

- **`vault_io.py` est le seul module autorisé à lire/écrire dans ce vault.**
  Jamais d'`open()` direct depuis un agent ou un collecteur.
- **Écritures atomiques** : chaque écriture passe par `.tmp` → `os.replace()`.
  Un crash ne peut jamais corrompre une fiche partiellement écrite.
- **Commits manuels uniquement** : `make snapshot` dans le terminal.
  Jamais de commit automatique — vous restez maître de l'historique.
- **L'agent ne peut pas rejeter** : `* → rejete` est réservé à l'humain (dans Obsidian).
"""


def _journal_decisions_md() -> str:
    return """\
# Journal de décisions

> Ce fichier vous appartient. Notez ici les choix importants :
> pourquoi vous avez rejeté une cible, changé de persona, ajusté la rubrique…
>
> Format suggéré :

---

## {date} — {titre court}

**Contexte** : …

**Décision** : …

**Raison** : …
"""


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def init_vault(vault_path: Path) -> dict[str, list[str]]:
    """Initialise le vault de façon idempotente.

    Retourne {"created": [...], "skipped": [...]} pour affichage CLI.
    """
    vault = Path(vault_path).resolve()
    created: list[str] = []
    skipped: list[str] = []

    # 1. Créer les répertoires (mkdir est idempotent)
    for rel in VAULT_DIRS:
        (vault / rel).mkdir(parents=True, exist_ok=True)

    # 2. Fichiers de contenu
    files: list[tuple[str, str]] = [
        ("00-Dashboard.md",                  _dashboard_md()),
        ("_templates/fiche-prospect.md",     _template_fiche_md()),
        ("90-Systeme/memory-map.md",         _memory_map_md()),
        ("90-Systeme/journal-decisions.md",  _journal_decisions_md()),
    ]
    for rel, content in files:
        path = vault / rel
        if _write_if_absent(path, content):
            created.append(rel)
        else:
            skipped.append(rel)

    # 3. Copie des rubriques YAML dans 20-Rubrics/ (ROM)
    for src in sorted(KNOWLEDGE_DIR.glob("rubric_*.yaml")):
        dst = vault / "20-Rubrics" / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
            created.append(f"20-Rubrics/{src.name}")
        else:
            skipped.append(f"20-Rubrics/{src.name}")

    # 4. Git : init + .gitignore (G10)
    git_dir = vault / ".git"
    if not git_dir.exists():
        try:
            subprocess.run(
                ["git", "init", str(vault)],
                check=True,
                capture_output=True,
            )
            created.append(".git/")
        except (subprocess.CalledProcessError, FileNotFoundError):
            skipped.append(".git/  [git non disponible]")
    else:
        skipped.append(".git/")

    gitignore = vault / ".gitignore"
    if _write_if_absent(gitignore, _GITIGNORE):
        created.append(".gitignore")
    else:
        skipped.append(".gitignore")

    return {"created": created, "skipped": skipped}
