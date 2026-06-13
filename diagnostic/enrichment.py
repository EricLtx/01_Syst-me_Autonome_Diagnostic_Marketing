"""
enrichment.py — PersonEnrichment (phase 1b, §5.3 de la spec J4).

Apollo people_enrichment → meilleur contact selon titres_cibles de l'ICP.
Minimisation RGPD stricte : seuls les 6 champs Contact sont persistés.
  - extra="forbid" sur Contact : aucun champ Apollo non autorisé ne peut passer.
  - cache_key par domaine : un seul appel Apollo par entreprise, même si
    plusieurs runs touchent la même candidate.
Tout le réseau passe par api_io.call() — jamais d'import requests au niveau module.
"""

from __future__ import annotations

import os
from datetime import date
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict

from diagnostic.api_io import ApiIO, BudgetExceeded
from diagnostic.icp_schema import Candidate, IcpConfig


class Contact(BaseModel):
    """Données de contact minimales conformes RGPD.

    extra="forbid" garantit la minimisation : aucun champ Apollo non listé
    ne peut être instancié, même accidentellement.
    contact_email_source est la provenance déclarée par Apollo (audit RGPD).
    """

    model_config = ConfigDict(extra="forbid")

    nom_personne: str
    titre: str
    email: str | None = None
    email_source: str | None = None   # "verified", "guessed", "likely"… (Apollo)
    linkedin_url: str | None = None   # référence uniquement, jamais scrapée
    date_enrichissement: date


class PersonEnrichment:
    """Enrichit une candidate via Apollo ; respecte le plafond max_enrichissements.

    Le compteur est par instance (= par run de run_discovery.py).
    Une candidate sans contact éligible est quand même écrite dans le vault.
    """

    def __init__(self, api_io: ApiIO, icp: IcpConfig) -> None:
        self._api_io = api_io
        self.icp = icp
        self._nb_enrichissements = 0

    def enrich(self, candidate: Candidate) -> Contact | None:
        """Retourne le contact le plus pertinent selon titres_cibles, ou None.

        None = aucun contact éligible OU plafond atteint.
        Propage BudgetExceeded si api_io dépasse son budget de run.
        Retourne None (sans lever) pour toute autre erreur réseau.
        """
        if self._nb_enrichissements >= self.icp.enrichissement.max_enrichissements:
            return None

        domaine = urlparse(candidate.site_web).netloc.removeprefix("www.")
        try:
            data = self._api_io.call(
                "apollo",
                "people_enrichment",
                lambda d=domaine: self._apollo_people_search(d),
                fiche=candidate.nom,
                cache_key=f"apollo:{domaine}",
            )
        except BudgetExceeded:
            raise
        except Exception:
            return None

        contact = self._extraire_contact(data)
        if contact is not None:
            self._nb_enrichissements += 1
        return contact

    # --- I/O réseau (via bus api_io uniquement) ----------------------------

    def _apollo_people_search(self, domaine: str) -> dict:
        import requests as _req  # lazy : toujours via api_io bus (§9.6)

        resp = _req.post(
            "https://api.apollo.io/v1/people/search",
            json={
                "organization_domains": [domaine],
                "person_titles": self.icp.enrichissement.titres_cibles,
                "per_page": 5,
            },
            headers={
                "X-Api-Key": os.getenv("APOLLO_API_KEY", ""),
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        return resp.json()

    # --- Extraction (minimisation RGPD) ------------------------------------

    def _extraire_contact(self, data: dict) -> Contact | None:
        """Sélectionne le premier contact dont le titre correspond à titres_cibles.

        Minimisation stricte : seuls les 6 champs Contact sont lus depuis Apollo.
        Tous les autres champs de la réponse sont ignorés.
        """
        personnes = data.get("people") or data.get("contacts") or []
        titres_lower = [t.lower() for t in self.icp.enrichissement.titres_cibles]

        for personne in personnes:
            titre = personne.get("title", "") or ""
            if any(t in titre.lower() for t in titres_lower):
                prenom = personne.get("first_name", "") or ""
                nom = personne.get("last_name", "") or ""
                return Contact(
                    nom_personne=f"{prenom} {nom}".strip(),
                    titre=titre,
                    email=personne.get("email"),
                    email_source=personne.get("email_status"),
                    linkedin_url=personne.get("linkedin_url"),
                    date_enrichissement=date.today(),
                )
        return None
