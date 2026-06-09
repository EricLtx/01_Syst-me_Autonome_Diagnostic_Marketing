"""
models.py — le contrat de données du module.

C'est la pièce la plus importante : tant que la forme de `Diagnostic` ne
bouge pas, tout ce qui est en aval (qualification, rédaction, CRM) peut s'y
brancher sans rien casser. On code "autour" de ce contrat, pas l'inverse.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass
class Company:
    """L'entrée du module : le strict minimum pour démarrer."""
    nom: str
    url: str
    region: str = ""


@dataclass
class Gap:
    """Une faille exploitable : la matière première de l'accroche d'outreach."""
    dimension: str
    gravite: str          # "haute" | "moyenne" | "basse"
    preuve: str           # phrase lisible, factuelle


@dataclass
class Diagnostic:
    """La sortie. Double usage : machine (scores, failles) + humain (mini_audit)."""
    entreprise: Company
    signaux: dict[str, Any] = field(default_factory=dict)     # bruts, par collecteur
    scores: dict[str, float] = field(default_factory=dict)    # 0–100 par dimension + "global"
    failles: list[Gap] = field(default_factory=list)
    accroche: str = ""
    mini_audit: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
