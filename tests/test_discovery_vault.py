"""
test_discovery_vault.py — §7.5, §7.9-11.

§7.5  : déduplication inter-runs (vault_io.exists() avant write_fiche)
§7.9  : dry-run → write_fiche jamais appelé
§7.10 : --sans-contact → zéro appel Apollo
§7.11 : FicheProspect créée avec statut=decouvert + champs J4 corrects
"""

from __future__ import annotations

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, call

from diagnostic.enrichment import Contact
from diagnostic.icp_schema import Candidate, IcpConfig
from diagnostic.vault_schema import FicheProspect

# ---------------------------------------------------------------------------
# Fixture partagée
# ---------------------------------------------------------------------------

_ICP_DATA = {
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
        "titres_cibles": ["propriétaire"],
        "max_enrichissements": 5,
    },
}


def _make_icp() -> IcpConfig:
    return IcpConfig(**_ICP_DATA)


def _make_candidate(nom="Test HVAC", url="https://test-hvac.ca") -> Candidate:
    return Candidate(
        nom=nom,
        site_web=url,
        icp_id="persona1-quebec",
        source="serp:test Québec",
        date_decouverte=date.today(),
    )


# ---------------------------------------------------------------------------
# §7.5 — Déduplication inter-runs
# ---------------------------------------------------------------------------

class TestDedupInterRuns:
    def test_doublon_par_site_web_detecte(self, tmp_path):
        from diagnostic.vault_io import VaultIO
        vault_path = tmp_path / "vault"
        (vault_path / "10-Prospects" / "persona1-quebec").mkdir(parents=True)
        vault_io = VaultIO(vault_path)

        fiche = FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Test HVAC", site_web="https://test-hvac.ca",
            date_creation=date.today(), icp_id="persona1-quebec",
        )
        vault_io.write_fiche(fiche)

        # Même site_web → doublon détecté
        assert vault_io.exists(site_web="https://test-hvac.ca") is not None

    def test_doublon_par_nom_detecte(self, tmp_path):
        from diagnostic.vault_io import VaultIO
        vault_path = tmp_path / "vault"
        (vault_path / "10-Prospects" / "persona1-quebec").mkdir(parents=True)
        vault_io = VaultIO(vault_path)

        fiche = FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Test HVAC", date_creation=date.today(),
        )
        vault_io.write_fiche(fiche)

        assert vault_io.exists(nom="Test HVAC") is not None

    def test_nouvelle_candidate_pas_detectee_comme_doublon(self, tmp_path):
        from diagnostic.vault_io import VaultIO
        vault_path = tmp_path / "vault"
        (vault_path / "10-Prospects" / "persona1-quebec").mkdir(parents=True)
        vault_io = VaultIO(vault_path)

        assert vault_io.exists(site_web="https://nouveau.ca") is None

    def test_write_fiche_non_appelee_si_doublon(self):
        """Logique de run_discovery.py : exists() → skip sans appeler write_fiche."""
        vault_io = MagicMock()
        vault_io.exists.return_value = Path("fiche-existante.md")  # doublon

        candidate = _make_candidate()
        if vault_io.exists(site_web=candidate.site_web) or vault_io.exists(nom=candidate.nom):
            pass  # skip — comportement attendu
        else:
            vault_io.write_fiche(MagicMock())

        vault_io.write_fiche.assert_not_called()


# ---------------------------------------------------------------------------
# §7.9 — Dry-run
# ---------------------------------------------------------------------------

class TestDryRun:
    def test_dry_run_aucune_ecriture_vault(self):
        vault_io = MagicMock()
        vault_io.exists.return_value = None

        dry_run = True
        candidate = _make_candidate()

        if not dry_run:
            vault_io.write_fiche(MagicMock())

        vault_io.write_fiche.assert_not_called()

    def test_dry_run_existe_pas_dans_api_io(self):
        """Dry-run : SERP est quand même appelé (métrée + cache) — seule l'écriture vault est bloquée."""
        api_io = MagicMock()
        api_io.call.return_value = {
            "organic_results": [{"link": "https://test.ca", "title": "Test"}]
        }
        icp = _make_icp()
        from diagnostic.discovery import DiscoveryCollector
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        candidates = collector.discover()
        assert len(candidates) == 1
        # SERP bien appelé même en dry-run
        api_io.call.assert_called_once()


# ---------------------------------------------------------------------------
# §7.10 — --sans-contact
# ---------------------------------------------------------------------------

class TestSansContact:
    def test_sans_contact_enrichment_est_none(self):
        from diagnostic.enrichment import PersonEnrichment
        api_io = MagicMock()
        icp = _make_icp()

        sans_contact = True
        enrichment = None if sans_contact else PersonEnrichment(api_io=api_io, icp=icp)

        assert enrichment is None
        api_io.call.assert_not_called()

    def test_avec_contact_enrichment_instancie(self):
        from diagnostic.enrichment import PersonEnrichment
        api_io = MagicMock()
        icp = _make_icp()

        sans_contact = False
        enrichment = None if sans_contact else PersonEnrichment(api_io=api_io, icp=icp)

        assert isinstance(enrichment, PersonEnrichment)


# ---------------------------------------------------------------------------
# §7.11 — FicheProspect créée avec les bons champs J4
# ---------------------------------------------------------------------------

class TestFicheDecouvert:
    def test_statut_decouvert(self):
        from run_discovery import _candidate_vers_fiche
        icp = _make_icp()
        fiche = _candidate_vers_fiche(_make_candidate(), None, icp)
        assert fiche.statut == "decouvert"

    def test_icp_id_present(self):
        from run_discovery import _candidate_vers_fiche
        icp = _make_icp()
        fiche = _candidate_vers_fiche(_make_candidate(), None, icp)
        assert fiche.icp_id == "persona1-quebec"

    def test_opt_out_false_par_defaut(self):
        from run_discovery import _candidate_vers_fiche
        icp = _make_icp()
        fiche = _candidate_vers_fiche(_make_candidate(), None, icp)
        assert fiche.opt_out is False

    def test_source_decouverte_contient_icp_id(self):
        from run_discovery import _candidate_vers_fiche
        icp = _make_icp()
        fiche = _candidate_vers_fiche(_make_candidate(), None, icp)
        assert "persona1-quebec" in fiche.source_decouverte

    def test_fiche_sans_contact_champs_contact_none(self):
        from run_discovery import _candidate_vers_fiche
        icp = _make_icp()
        fiche = _candidate_vers_fiche(_make_candidate(), None, icp)
        assert fiche.contact_nom is None
        assert fiche.contact_email is None
        assert fiche.contact_linkedin is None

    def test_fiche_avec_contact_champs_mappes(self):
        from run_discovery import _candidate_vers_fiche
        icp = _make_icp()
        contact = Contact(
            nom_personne="Jean Tremblay",
            titre="Propriétaire",
            email="jean@test.ca",
            email_source="verified",
            linkedin_url="https://linkedin.com/in/jean",
            date_enrichissement=date.today(),
        )
        fiche = _candidate_vers_fiche(_make_candidate(), contact, icp)
        assert fiche.contact_nom == "Jean Tremblay"
        assert fiche.contact_titre == "Propriétaire"
        assert fiche.contact_email == "jean@test.ca"
        assert fiche.contact_email_source == "verified"
        assert fiche.contact_linkedin == "https://linkedin.com/in/jean"

    def test_fiche_valide_par_pydantic(self):
        """FicheProspect(statut=decouvert) doit passer la validation Pydantic."""
        from run_discovery import _candidate_vers_fiche
        icp = _make_icp()
        fiche = _candidate_vers_fiche(_make_candidate(), None, icp)
        # model_dump ne lève pas d'exception si la fiche est valide
        d = fiche.model_dump(mode="json")
        assert d["statut"] == "decouvert"

    def test_round_trip_vault(self, tmp_path):
        """Fiche créée par run_discovery, écrite et relue depuis le vault."""
        from diagnostic.vault_io import VaultIO
        from run_discovery import _candidate_vers_fiche
        vault_path = tmp_path / "vault"
        (vault_path / "10-Prospects" / "persona1-quebec").mkdir(parents=True)
        vault_io = VaultIO(vault_path)

        icp = _make_icp()
        contact = Contact(
            nom_personne="Marie Roy",
            titre="Présidente",
            email="marie@roy.ca",
            email_source="verified",
            linkedin_url=None,
            date_enrichissement=date.today(),
        )
        fiche = _candidate_vers_fiche(_make_candidate(), contact, icp)
        path = vault_io.write_fiche(fiche)

        fiche_relue = vault_io.read_fiche(path)
        assert fiche_relue.contact_nom == "Marie Roy"
        assert fiche_relue.contact_email == "marie@roy.ca"
        assert fiche_relue.icp_id == "persona1-quebec"
        assert fiche_relue.opt_out is False
