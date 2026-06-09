"""
gbp.py — collecteur Google Business Profile (stub J1).

Retourne des signaux vides : la rubrique les notera comme failles avec
le suffixe "(à confirmer en J3)". L'implémentation réelle utilisera
l'API Google Places / Business Profile.
"""

from __future__ import annotations

from typing import Any

from diagnostic.collectors.base import Collector
from diagnostic.models import Company


class GbpCollector(Collector):
    name = "gbp"

    def collect(self, company: Company) -> dict[str, Any]:
        # Stub — implémentation réelle en J3
        return {"verified": None, "has_photos": None}
