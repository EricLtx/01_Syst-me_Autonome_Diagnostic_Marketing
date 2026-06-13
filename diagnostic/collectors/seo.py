"""
seo.py — collecteur SEO local (palier 0, §8.5).

Analyse le texte déjà récupéré par WebsiteCollector (via _seo_text injecté
par DiagnosticPipeline). Aucun appel réseau supplémentaire.

Signal produit :
  - local_keywords (bool) : True si des mots-clés géolocalisés (ville/région
    extraits de company.region) sont présents dans le titre, la meta-desc ou
    les 2 000 premiers caractères du corps de page.
  - Retourne None si _website_signals n'a pas encore été injecté (mode stub).

DiagnosticPipeline injecte _website_signals après la collecte website.
"""

from __future__ import annotations

from typing import Any

from diagnostic.collectors.base import Collector
from diagnostic.models import Company


class SeoCollector(Collector):
    name = "seo"

    def __init__(self):
        self._website_signals: dict | None = None

    def collect(self, company: Company) -> dict[str, Any]:
        if not self._website_signals or "_seo_text" not in self._website_signals:
            return {"local_keywords": None}
        seo_text = self._website_signals["_seo_text"]
        return {"local_keywords": self._detect_local_keywords(seo_text, company.region)}

    @staticmethod
    def _detect_local_keywords(text: str, region: str | None) -> bool:
        """Vérifie si des mots de la région (>2 chars) apparaissent dans le texte."""
        if not region or not text:
            return False
        parts = [p.strip().lower() for p in region.replace(",", " ").split() if len(p.strip()) > 2]
        return any(part in text.lower() for part in parts)
