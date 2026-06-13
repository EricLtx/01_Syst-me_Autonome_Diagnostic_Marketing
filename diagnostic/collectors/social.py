"""
social.py — collecteur réseaux sociaux (palier 0, §8.2).

Collecteur PASSIF : aucun appel réseau, aucune API.
Dérive son signal depuis website.social_links (liens sortants déjà extraits
par WebsiteCollector). La présence d'un lien vers Facebook/LinkedIn/Instagram
est suffisante pour diagnostiquer la maturité sociale de la marque.

DiagnosticPipeline injecte _website_signals après la collecte website.
"""

from __future__ import annotations

from typing import Any

from diagnostic.collectors.base import Collector
from diagnostic.models import Company


class SocialCollector(Collector):
    name = "social"

    def __init__(self):
        self._website_signals: dict | None = None

    def collect(self, company: Company) -> dict[str, Any]:
        if self._website_signals and "social_links" in self._website_signals:
            plateformes = list(self._website_signals["social_links"])
            return {"plateformes_mentionnees": plateformes}
        return {"plateformes_mentionnees": []}
