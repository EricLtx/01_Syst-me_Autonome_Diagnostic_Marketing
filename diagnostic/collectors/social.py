"""
social.py — collecteur réseaux sociaux (stub J1).

Retourne des signaux vides. L'implémentation réelle en J3 vérifiera
la présence et l'activité sur les plateformes détectées par website.py.
"""

from __future__ import annotations

from typing import Any

from diagnostic.collectors.base import Collector
from diagnostic.models import Company


class SocialCollector(Collector):
    name = "social"

    def collect(self, company: Company) -> dict[str, Any]:
        # Stub — implémentation réelle en J3
        return {"active": None, "platforms": []}
