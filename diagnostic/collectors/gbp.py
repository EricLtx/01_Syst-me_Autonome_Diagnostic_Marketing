"""
gbp.py — collecteur Google Business Profile (palier 1, §8.3).

Sans api_io injecté : mode stub (valeurs None), rétrocompatibilité J1/J2.
Avec api_io injecté : appel Google Places text_search (fiche vérifiée = présente
dans Places + statut OPERATIONAL, photos = liste photos non vide).

La clé API est lue depuis la variable d'environnement GOOGLE_PLACES_API_KEY.
Si elle est absente, l'appel échouera → safe_collect isole l'erreur.

cache_key = "places:{nom} {région}" pour partager le cache avec ReviewsCollector.
"""

from __future__ import annotations

import os
from typing import Any

from diagnostic.collectors._places import reponse_exploitable
from diagnostic.collectors.base import Collector
from diagnostic.models import Company


class GbpCollector(Collector):
    name = "gbp"

    def __init__(self, api_io=None):
        self._api_io = api_io

    def collect(self, company: Company) -> dict[str, Any]:
        if self._api_io is None:
            return {"verified": None, "has_photos": None}

        query = f"{company.nom} {company.region or ''}".strip()
        try:
            data = self._api_io.call(
                "google_places", "text_search",
                lambda: self._places_text_search(query),
                fiche=company.nom,
                cache_key=f"places:{query}",
            )
            return self._parse_place(data)
        except Exception:
            return {"verified": None, "has_photos": None}

    def _places_text_search(self, query: str) -> dict:
        import requests as _req  # lazy : appel toujours via api_io bus
        # Base surchargeable : le défaut EST la production (zéro changement de
        # comportement). PLACES_BASE_URL n'est posée qu'en test d'intégration.
        base = os.getenv("PLACES_BASE_URL", "https://maps.googleapis.com").rstrip("/")
        resp = _req.get(
            f"{base}/maps/api/place/textsearch/json",
            params={"query": query, "key": os.getenv("GOOGLE_PLACES_API_KEY", "")},
            timeout=10,
        )
        return resp.json()

    @staticmethod
    def _parse_place(data: dict) -> dict:
        # Une réponse non exploitable (REQUEST_DENIED sans clé, quota, erreur)
        # arrive en HTTP 200 avec `results: []`. La compter comme « pas de
        # fiche » fabriquerait une faille de gravité haute à partir d'un échec
        # d'authentification. On s'abstient : cf. collectors/_places.py.
        if not reponse_exploitable(data):
            return {"verified": None, "has_photos": None}
        results = data.get("results", [])
        if not results:
            return {"verified": False, "has_photos": False}
        place = results[0]
        return {
            "verified": place.get("business_status") == "OPERATIONAL",
            "has_photos": bool(place.get("photos")),
        }
