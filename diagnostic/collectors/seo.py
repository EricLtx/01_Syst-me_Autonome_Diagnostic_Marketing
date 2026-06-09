"""
seo.py — collecteur SEO local (stub J1).

Retourne des signaux vides : la rubrique les notera comme failles avec
le suffixe "(à confirmer en J3)". L'implémentation réelle analysera
les mots-clés géolocalisés dans le contenu du site.
"""

from __future__ import annotations

from typing import Any

from diagnostic.collectors.base import Collector
from diagnostic.models import Company


class SeoCollector(Collector):
    name = "seo"

    def collect(self, company: Company) -> dict[str, Any]:
        # Stub — implémentation réelle en J3
        return {"local_keywords": None}
