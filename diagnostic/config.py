"""
config.py — chargement de la rubrique et de la base de connaissance.

Les fichiers YAML vivent dans knowledge/ (à la racine du projet),
jamais dans le code. Principe #3 : la rubrique est une donnée.

ADR 0003 : la clé de sélection est désormais secteur_id (str), pas persona
(int). Le paramètre s'appelle encore `persona` par compatibilité littérale
des appels existants (`load_rubrique()`, `load_rubrique(2)`…), mais son type
s'élargit à `str | int` : un int legacy est traduit en f"persona{N}", un str
(secteur_id ADR 0003, ex. "dentaire-test") est déjà la clé complète.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Résolu depuis l'emplacement de ce fichier : diagnostic/ -> racine -> knowledge/
KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def _secteur_label(persona: str | int) -> str:
    """Normalise la clé de sélection en suffixe de nom de fichier.

    Un int (legacy, ex. `load_rubrique(1)`) devient "persona1" ; un str
    (secteur_id ADR 0003, ex. "dentaire-test") est déjà la clé complète et
    n'est pas reformaté.
    """
    return f"persona{persona}" if isinstance(persona, int) else persona


def load_rubrique(persona: str | int = 1) -> dict[str, Any]:
    path = KNOWLEDGE_DIR / f"rubric_{_secteur_label(persona)}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_knowledge(persona: str | int = 1) -> dict[str, Any]:
    """Retourne {} si le fichier optionnel n'existe pas encore."""
    path = KNOWLEDGE_DIR / f"knowledge_{_secteur_label(persona)}.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {}


def load_rubrique_intention(persona: str | int = 1) -> dict[str, Any] | None:
    """Charge knowledge/intent_{secteur}.yaml (ADR 0004 — axe intention).

    Retourne `None`, PAS `{}`, si le fichier est absent : distinction
    nécessaire entre « ce secteur n'a pas d'axe intention » (repli propre,
    `pipeline.py` n'évalue rien) et « axe vide » (erreur de configuration,
    un fichier présent mais sans dimensions serait un bug à signaler, pas un
    silence poli).
    """
    path = KNOWLEDGE_DIR / f"intent_{_secteur_label(persona)}.yaml"
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_vocabulaire_intention(persona: str | int = 1) -> dict[str, Any]:
    """Vocabulaire de recrutement par secteur (ADR 0004).

    Même contrat que `load_vocabulaire` : fichier absent → {}, JAMAIS une
    exception. Un secteur sans lexique documenté dégrade vers `None` dans
    `WebsiteCollector.offre_detectee` (anti-fuite B5), pas vers un plantage.
    """
    path = KNOWLEDGE_DIR / f"vocabulaire_intention_{_secteur_label(persona)}.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {}


def load_certifications(marche: str) -> dict[str, list[str]] | None:
    """Motifs de légitimité/conformité par MARCHÉ (ADR 0004 — `legitimite.py`).

    Distinct des autres chargeurs de ce module : une licence professionnelle
    (RBQ au Québec, RGE en France, suissetec en Suisse) est propre à une
    juridiction, pas à un secteur d'activité — c'est pourquoi la clé est le
    marché, pas `secteur_id`. Retourne `None` si le fichier est absent (même
    distinction que `load_rubrique_intention` : « marché non documenté » ≠
    « aucun motif »).

    Limite assumée de ce lot : la résolution effective (quel fichier charger
    pour quelle fiche) reste câblée par défaut au marché Québec dans
    `vault_runner.py`/`run_diagnostic.py`, seul marché ayant un ICP réel dans
    ce dépôt à ce jour — même simplification déjà acceptée pour
    `vocabulaire_offre` (partagé par secteur, pas par marché). Le schéma
    (cette fonction, le fichier `certifications_{marche}.yaml`) est prêt pour
    un second marché sans aucun changement de code : il suffit d'ajouter le
    fichier et d'appeler `load_certifications("romandie")` au bon endroit.
    """
    path = KNOWLEDGE_DIR / f"certifications_{marche}.yaml"
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_vocabulaire(persona: str | int = 1) -> dict[str, Any]:
    """Vocabulaire lexical par secteur (ADR 0003 — anti-fuite B5).

    Même contrat que `load_knowledge` : fichier absent → {}, JAMAIS une
    exception. Un secteur sans vocabulaire documenté doit dégrader vers
    « inconnu » (None dans WebsiteCollector), pas planter le pipeline.
    """
    path = KNOWLEDGE_DIR / f"vocabulaire_{_secteur_label(persona)}.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {}


def load_pricing() -> dict[str, Any]:
    """Charge la grille tarifaire API depuis knowledge/api_pricing.yaml."""
    path = KNOWLEDGE_DIR / "api_pricing.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


ICP_DIR = Path(__file__).resolve().parent.parent / "icp"


def load_icp(icp_id: str) -> "IcpConfig":
    """Charge et valide un fichier ICP depuis icp/{icp_id}.yaml."""
    from diagnostic.icp_schema import IcpConfig  # import local : évite la circularité
    path = ICP_DIR / f"{icp_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"ICP introuvable : {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return IcpConfig(**raw)
