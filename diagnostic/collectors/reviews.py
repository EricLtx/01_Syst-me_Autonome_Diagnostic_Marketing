"""
reviews.py — collecteur d'avis Google (palier 1, §8.4).

Sans api_io injecté : mode stub (valeurs None), rétrocompatibilité J1/J2.
Avec api_io injecté :
  1. text_search (partagé avec GbpCollector via même cache_key) → place_id + stats
  2. place_details → reviews avec éventuelle réponse propriétaire

Signaux produits :
  - count       : nombre total d'avis (user_ratings_total)
  - avg         : note moyenne (rating, float)
  - repond_aux_avis : True si au moins un avis a une réponse propriétaire
  - date_dernier_avis : date ISO du dernier avis (YYYY-MM-DD) ou None

La clé API est lue depuis GOOGLE_PLACES_API_KEY.
"""

from __future__ import annotations

import os
from typing import Any

from diagnostic.collectors.base import Collector
from diagnostic.models import Company


class ReviewsCollector(Collector):
    name = "reviews"

    def __init__(self, api_io=None):
        self._api_io = api_io

    def collect(self, company: Company) -> dict[str, Any]:
        if self._api_io is None:
            return {"count": None, "avg": None}

        query = f"{company.nom} {company.region or ''}".strip()
        try:
            # 1. text_search : cache partagé avec GbpCollector (même cache_key)
            search = self._api_io.call(
                "google_places", "text_search",
                lambda: self._places_text_search(query),
                fiche=company.nom,
                cache_key=f"places:{query}",
            )
            results = search.get("results", [])
            if not results:
                return {"count": 0, "avg": None, "repond_aux_avis": None, "date_dernier_avis": None}

            place = results[0]
            count = place.get("user_ratings_total", 0)
            avg = place.get("rating")
            place_id = place.get("place_id")

            # 2. place_details : récupère les avis avec réponses propriétaire
            repond: bool | None = None
            date_dernier: str | None = None
            if place_id:
                try:
                    detail = self._api_io.call(
                        "google_places", "place_details",
                        lambda: self._places_details(place_id),
                        fiche=company.nom,
                        cache_key=f"places_details:{place_id}",
                    )
                    reviews = detail.get("result", {}).get("reviews", [])
                    if reviews:
                        repond = any("owner_answer" in r for r in reviews)
                        times = [r.get("time", 0) for r in reviews if isinstance(r.get("time"), int)]
                        if times:
                            import datetime
                            date_dernier = datetime.date.fromtimestamp(max(times)).isoformat()
                except Exception:
                    pass

            return {
                "count": count,
                "avg": avg,
                "repond_aux_avis": repond,
                "date_dernier_avis": date_dernier,
            }
        except Exception:
            return {"count": None, "avg": None, "repond_aux_avis": None, "date_dernier_avis": None}

    def _places_text_search(self, query: str) -> dict:
        import requests as _req  # lazy : appel toujours via api_io bus
        resp = _req.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": query, "key": os.getenv("GOOGLE_PLACES_API_KEY", "")},
            timeout=10,
        )
        return resp.json()

    def _places_details(self, place_id: str) -> dict:
        import requests as _req  # lazy : appel toujours via api_io bus
        resp = _req.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "rating,user_ratings_total,reviews,photos",
                "key": os.getenv("GOOGLE_PLACES_API_KEY", ""),
            },
            timeout=10,
        )
        return resp.json()
