"""
config.py — chargement de la rubrique et de la base de connaissance.

Les fichiers YAML vivent dans knowledge/ (à la racine du projet),
jamais dans le code. Principe #3 : la rubrique est une donnée.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Résolu depuis l'emplacement de ce fichier : diagnostic/ -> racine -> knowledge/
KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def load_rubrique(persona: int = 1) -> dict[str, Any]:
    path = KNOWLEDGE_DIR / f"rubric_persona{persona}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_knowledge(persona: int = 1) -> dict[str, Any]:
    """Retourne {} si le fichier optionnel n'existe pas encore."""
    path = KNOWLEDGE_DIR / f"knowledge_persona{persona}.yaml"
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
