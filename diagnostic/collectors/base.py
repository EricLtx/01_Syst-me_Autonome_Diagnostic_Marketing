"""
collectors/base.py — contrat commun de tous les collecteurs.

Principe #2 (CLAUDE.md) : chaque collecteur hérite de Collector et échoue
de façon isolée via safe_collect. Le pipeline ne s'arrête jamais pour un
collecteur défaillant.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from diagnostic.models import Company


class Collector(ABC):
    name: str = ""

    @abstractmethod
    def collect(self, company: Company) -> dict[str, Any]: ...

    def safe_collect(self, company: Company) -> dict[str, Any]:
        """Isole l'échec : retourne un dict d'erreur sans propager l'exception."""
        try:
            return self.collect(company)
        except Exception as exc:
            return {"_erreur": str(exc), "_collecteur": self.name}
