"""
legitimite.py — collecteur légitimité/conformité (palier 0, ADR 0004 D8).

Dérivé du HTML déjà téléchargé par `WebsiteCollector` (même patron que
`seo.py`/`social.py` : `_website_signals` injecté par `DiagnosticPipeline`
après la collecte website, AUCUN appel réseau propre à ce collecteur).

Apporte à l'axe BESOIN (pas intention) : une certification affichée sur son
propre site est un ÉTAT (elle reste vraie tant qu'elle n'est pas retirée),
jamais un événement daté — cohérent avec la règle B1 de l'ADR 0004
(la décroissance ne s'applique qu'aux événements).

Trois états, pas deux
----------------------
`self.motifs` (injecté, jamais lu depuis le disque par ce module — cf.
`vault_runner.py`) est un dict `{categorie: [motifs...]}` pour LE marché de
l'entreprise diagnostiquée. Par catégorie :
  - `None` si le motif n'est pas configuré pour ce marché/secteur (anti-fuite
    B5, même discipline que `website.mentions_offre`) ;
  - `None` aussi si le site est injoignable : un ÉCHEC TECHNIQUE n'est pas
    une observation négative (même règle que `_places.py`) ;
  - sinon `True`/`False` selon la présence effective du motif dans le texte.
"""

from __future__ import annotations

from typing import Any

from diagnostic.collectors.base import Collector
from diagnostic.models import Company


class LegitimiteCollector(Collector):
    name = "legitimite"

    def __init__(self, motifs: dict[str, list[str]] | None = None):
        # None = aucun motif configuré pour ce marché/secteur → tous les
        # checks restent `None` (inconnu), jamais `False` (anti-fuite B5).
        self.motifs = motifs
        # Injecté par DiagnosticPipeline après la collecte website (même
        # mécanisme que SeoCollector/SocialCollector) — ce collecteur ne
        # fait jamais son propre fetch.
        self._website_signals: dict | None = None

    def collect(self, company: Company) -> dict[str, Any]:
        categories = self.motifs or {}
        if not categories:
            return {}

        if not self._website_signals or not self._website_signals.get("reachable"):
            # Échec technique (site injoignable, ou pas encore injecté) :
            # on n'a RIEN pu observer — pas "aucune mention détectée".
            return {categorie: None for categorie in categories}

        texte = (self._website_signals.get("_seo_text") or "").lower()
        return {
            categorie: self._detecte(texte, mots)
            for categorie, mots in categories.items()
        }

    @staticmethod
    def _detecte(texte: str, mots: list[str] | None) -> bool | None:
        """True/False si des motifs sont configurés pour cette catégorie,
        None sinon (catégorie déclarée mais vide — anti-fuite B5)."""
        if not mots:
            return None
        return any(m.lower() in texte for m in mots)
