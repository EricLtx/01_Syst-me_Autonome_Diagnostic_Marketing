"""
test_enrichment.py — §7.6 + §7.8.

§7.6 : Contact = minimisation stricte (extra="forbid", 6 champs uniquement)
§7.8 : max_enrichissements respecté — au-delà du plafond, enrich() retourne None
"""

from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import MagicMock

from pydantic import ValidationError

from diagnostic.enrichment import Contact, PersonEnrichment
from diagnostic.icp_schema import Candidate, IcpConfig

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ICP_BASE = {
    "icp_id": "persona1-quebec",
    "persona": 1,
    "marche": "quebec",
    "description": "Test",
    "requetes": {
        "gabarits": ["test {localite}"],
        "localites": ["Québec"],
        "max_resultats_par_requete": 5,
    },
    "filtres": {"domaines_exclus": [], "exiger_domaine_propre": False},
    "enrichissement": {
        "titres_cibles": ["propriétaire", "président"],
        "max_enrichissements": 2,
    },
}

_APOLLO_RESPONSE = {
    "people": [
        {
            "first_name": "Jean",
            "last_name": "Tremblay",
            "title": "Propriétaire",
            "email": "jean@tremblay-hvac.ca",
            "email_status": "verified",
            "linkedin_url": "https://linkedin.com/in/jean-tremblay",
            "phone_numbers": ["514-555-0001"],    # champ Apollo non autorisé
            "organization": {"name": "Tremblay HVAC"},  # champ Apollo non autorisé
        }
    ]
}


def _make_icp(**overrides) -> IcpConfig:
    d = {**_ICP_BASE, **overrides}
    return IcpConfig(**d)


def _make_candidate(nom="Tremblay HVAC", url="https://tremblay-hvac.ca") -> Candidate:
    return Candidate(
        nom=nom,
        site_web=url,
        icp_id="persona1-quebec",
        source="serp:test",
        date_decouverte=date.today(),
    )


# ---------------------------------------------------------------------------
# §7.6 — Minimisation Contact
# ---------------------------------------------------------------------------

class TestContactMinimisation:
    def test_contact_6_champs_valide(self):
        c = Contact(
            nom_personne="Jean Tremblay",
            titre="Propriétaire",
            email="jean@test.ca",
            email_source="verified",
            linkedin_url=None,
            date_enrichissement=date.today(),
        )
        assert c.nom_personne == "Jean Tremblay"
        assert c.email_source == "verified"

    def test_extra_champ_leve_erreur(self):
        with pytest.raises(ValidationError):
            Contact(
                nom_personne="Jean",
                titre="Propriétaire",
                date_enrichissement=date.today(),
                champ_inconnu="interdit",  # extra="forbid"
            )

    def test_email_et_linkedin_optionnels(self):
        c = Contact(
            nom_personne="Marie Roy",
            titre="Présidente",
            date_enrichissement=date.today(),
        )
        assert c.email is None
        assert c.linkedin_url is None

    def test_email_source_optionnel(self):
        c = Contact(
            nom_personne="X", titre="Y",
            email="x@y.ca",
            date_enrichissement=date.today(),
        )
        assert c.email_source is None


class TestPersonEnrichment:
    def test_contact_extrait_depuis_apollo(self):
        icp = _make_icp()
        api_io = MagicMock()
        api_io.call.return_value = _APOLLO_RESPONSE
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)
        contact = enrichment.enrich(_make_candidate())
        assert contact is not None
        assert contact.nom_personne == "Jean Tremblay"
        assert contact.titre == "Propriétaire"
        assert contact.email == "jean@tremblay-hvac.ca"
        assert contact.email_source == "verified"
        assert contact.linkedin_url == "https://linkedin.com/in/jean-tremblay"

    def test_contact_ne_contient_pas_champs_apollo_non_autorises(self):
        icp = _make_icp()
        api_io = MagicMock()
        api_io.call.return_value = _APOLLO_RESPONSE
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)
        contact = enrichment.enrich(_make_candidate())
        # phone_numbers et organization ne doivent PAS apparaître
        assert not hasattr(contact, "phone_numbers")
        assert not hasattr(contact, "organization")

    def test_titre_non_cible_retourne_none(self):
        icp = _make_icp()
        api_io = MagicMock()
        api_io.call.return_value = {
            "people": [
                {"first_name": "X", "last_name": "Y", "title": "Comptable"}
            ]
        }
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)
        contact = enrichment.enrich(_make_candidate())
        assert contact is None

    def test_liste_vide_retourne_none(self):
        icp = _make_icp()
        api_io = MagicMock()
        api_io.call.return_value = {"people": []}
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)
        assert enrichment.enrich(_make_candidate()) is None

    def test_cle_contacts_aussi_acceptee(self):
        """Apollo peut retourner 'contacts' au lieu de 'people'."""
        icp = _make_icp()
        api_io = MagicMock()
        api_io.call.return_value = {
            "contacts": [
                {
                    "first_name": "Marie",
                    "last_name": "Roy",
                    "title": "Présidente",
                    "email": "marie@roy.ca",
                    "email_status": "likely",
                }
            ]
        }
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)
        contact = enrichment.enrich(_make_candidate())
        assert contact is not None
        assert contact.nom_personne == "Marie Roy"

    def test_cache_key_est_domaine_sans_www(self):
        icp = _make_icp()
        api_io = MagicMock()
        api_io.call.return_value = {"people": []}
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)
        enrichment.enrich(_make_candidate(url="https://www.tremblay-hvac.ca"))
        _, kwargs = api_io.call.call_args
        assert kwargs.get("cache_key") == "apollo:tremblay-hvac.ca"

    def test_titre_cible_partiel(self):
        """'directeur général' dans le titre → match sur 'directeur'."""
        icp = _make_icp(enrichissement={
            "titres_cibles": ["directeur"],
            "max_enrichissements": 5,
        })
        api_io = MagicMock()
        api_io.call.return_value = {
            "people": [
                {"first_name": "A", "last_name": "B", "title": "Directeur Général"}
            ]
        }
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)
        contact = enrichment.enrich(_make_candidate())
        assert contact is not None


# ---------------------------------------------------------------------------
# §7.8 — Plafond max_enrichissements
# ---------------------------------------------------------------------------

class TestMaxEnrichissements:
    def test_plafond_respecte(self):
        icp = _make_icp()  # max_enrichissements = 2
        api_io = MagicMock()
        api_io.call.return_value = _APOLLO_RESPONSE
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)

        c1 = enrichment.enrich(_make_candidate("A", "https://a.ca"))
        c2 = enrichment.enrich(_make_candidate("B", "https://b.ca"))
        c3 = enrichment.enrich(_make_candidate("C", "https://c.ca"))  # plafond atteint

        assert c1 is not None
        assert c2 is not None
        assert c3 is None  # plafond → None, pas d'appel Apollo

    def test_plafond_stoppe_les_appels_api(self):
        icp = _make_icp()  # max_enrichissements = 2
        api_io = MagicMock()
        api_io.call.return_value = _APOLLO_RESPONSE
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)

        enrichment.enrich(_make_candidate("A", "https://a.ca"))
        enrichment.enrich(_make_candidate("B", "https://b.ca"))
        enrichment.enrich(_make_candidate("C", "https://c.ca"))  # plafond

        assert api_io.call.call_count == 2  # seuls 2 appels réels


# ---------------------------------------------------------------------------
# Gestion des erreurs
# ---------------------------------------------------------------------------

class TestGestionErreurs:
    def test_budget_exceeded_propage(self):
        from diagnostic.api_io import BudgetExceeded
        icp = _make_icp()
        api_io = MagicMock()
        api_io.call.side_effect = BudgetExceeded("budget dépassé")
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)
        with pytest.raises(BudgetExceeded):
            enrichment.enrich(_make_candidate())

    def test_erreur_reseau_retourne_none(self):
        icp = _make_icp()
        api_io = MagicMock()
        api_io.call.side_effect = ConnectionError("timeout Apollo")
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)
        contact = enrichment.enrich(_make_candidate())
        assert contact is None

    def test_compteur_non_incremente_si_none(self):
        """Si aucun contact trouvé, le compteur ne doit pas augmenter."""
        icp = _make_icp(enrichissement={
            "titres_cibles": ["propriétaire"],
            "max_enrichissements": 1,
        })
        api_io = MagicMock()
        api_io.call.return_value = {"people": []}  # aucun contact éligible
        enrichment = PersonEnrichment(api_io=api_io, icp=icp)

        c1 = enrichment.enrich(_make_candidate("A", "https://a.ca"))  # none → pas compté
        c2 = enrichment.enrich(_make_candidate("B", "https://b.ca"))  # none → pas compté

        assert c1 is None
        assert c2 is None
        assert enrichment._nb_enrichissements == 0
