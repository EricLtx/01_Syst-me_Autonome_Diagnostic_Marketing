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
