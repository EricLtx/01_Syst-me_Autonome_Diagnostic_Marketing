"""
reviews.py — collecteur d'avis Google (stub J1).

Retourne des signaux vides : la rubrique les notera comme failles avec
le suffixe "(à confirmer en J3)". L'implémentation réelle utilisera
l'API Google Places.
"""

from __future__ import annotations

from typing import Any

from diagnostic.collectors.base import Collector
from diagnostic.models import Company


class ReviewsCollector(Collector):
    name = "reviews"

    def collect(self, company: Company) -> dict[str, Any]:
        # Stub — implémentation réelle en J3
        return {"count": None, "avg": None}
