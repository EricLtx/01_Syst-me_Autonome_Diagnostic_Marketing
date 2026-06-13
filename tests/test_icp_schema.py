"""
test_icp_schema.py — §7.1 + §7.12.

§7.1 : validation IcpConfig (YAML accepté / erreurs icp_id / gabarit / champ manquant)
§7.12 : rétro-compatibilité FicheProspect — fiches antérieures toujours valides
"""
from __future__ import annotations

import pytest
from datetime import date
from pydantic import ValidationError

from diagnostic.icp_schema import IcpConfig, Candidate

# ---------------------------------------------------------------------------
# Fixture de base
# ---------------------------------------------------------------------------

VALID_ICP = {
    "icp_id": "persona1-quebec",
    "persona": 1,
    "marche": "quebec",
    "description": "Test ICP",
    "requetes": {
        "gabarits": ["installateur thermopompe {localite}"],
        "localites": ["Québec", "Montréal"],
        "max_resultats_par_requete": 10,
    },
    "filtres": {
        "domaines_exclus": ["yelp."],
        "exiger_domaine_propre": True,
    },
    "enrichissement": {
        "titres_cibles": ["propriétaire", "président"],
        "max_enrichissements": 25,
    },
}


# ---------------------------------------------------------------------------
# §7.1 — IcpConfig validation
# ---------------------------------------------------------------------------

class TestIcpConfigValidation:
    def test_yaml_valide_accepte(self):
        icp = IcpConfig(**VALID_ICP)
        assert icp.icp_id == "persona1-quebec"
        assert icp.persona == 1
        assert icp.marche == "quebec"

    def test_icp_id_incoherent_leve_erreur(self):
        data = dict(VALID_ICP, icp_id="persona1-romandie")
        with pytest.raises(ValidationError, match="incohérent"):
            IcpConfig(**data)

    def test_icp_id_persona_incorrect_leve_erreur(self):
        data = dict(VALID_ICP, icp_id="persona2-quebec")  # persona=1 ≠ persona2
        with pytest.raises(ValidationError, match="incohérent"):
            IcpConfig(**data)

    def test_gabarit_sans_localite_leve_erreur(self):
        data = {
            **VALID_ICP,
            "requetes": {
                "gabarits": ["installateur thermopompe sans variable"],
                "localites": ["Québec"],
            },
        }
        with pytest.raises(ValidationError, match="localite"):
            IcpConfig(**data)

    def test_champ_manquant_leve_erreur(self):
        data = {k: v for k, v in VALID_ICP.items() if k != "enrichissement"}
        with pytest.raises(ValidationError):
            IcpConfig(**data)

    def test_champ_inconnu_leve_erreur(self):
        data = dict(VALID_ICP, champ_extra="interdit")
        with pytest.raises(ValidationError):
            IcpConfig(**data)

    def test_plusieurs_gabarits_valides(self):
        data = {
            **VALID_ICP,
            "requetes": {
                "gabarits": ["test {localite}", "autre {localite}"],
                "localites": ["Québec"],
            },
        }
        icp = IcpConfig(**data)
        assert len(icp.requetes.gabarits) == 2


class TestGenererRequetes:
    def test_produit_cartesien_1_gabarit_2_localites(self):
        icp = IcpConfig(**VALID_ICP)
        requetes = icp.generer_requetes()
        assert len(requetes) == 2
        assert "installateur thermopompe Québec" in requetes
        assert "installateur thermopompe Montréal" in requetes

    def test_produit_cartesien_2_gabarits_3_localites(self):
        data = {
            **VALID_ICP,
            "requetes": {
                "gabarits": ["chauf {localite}", "clim {localite}"],
                "localites": ["A", "B", "C"],
            },
        }
        icp = IcpConfig(**data)
        assert len(icp.generer_requetes()) == 6

    def test_localite_interpolee_correctement(self):
        icp = IcpConfig(**VALID_ICP)
        requetes = icp.generer_requetes()
        for r in requetes:
            assert "{localite}" not in r


class TestCandidate:
    def test_candidate_valide(self):
        c = Candidate(
            nom="Tremblay HVAC",
            site_web="https://tremblay-hvac.ca",
            icp_id="persona1-quebec",
            source="serp:installateur thermopompe Québec",
            date_decouverte=date(2026, 6, 1),
        )
        assert c.nom == "Tremblay HVAC"
        assert c.icp_id == "persona1-quebec"

    def test_candidate_extra_interdit(self):
        with pytest.raises(ValidationError):
            Candidate(
                nom="X",
                site_web="https://x.ca",
                icp_id="test",
                source="s",
                date_decouverte=date.today(),
                champ_inconnu="oops",
            )


# ---------------------------------------------------------------------------
# §7.12 — Rétro-compatibilité FicheProspect
# ---------------------------------------------------------------------------

class TestFicheProspectRetroCompat:
    """Fiches créées avant J4 (sans contact_nom, icp_id, opt_out) restent valides."""

    def test_fiche_sans_champs_j4_est_valide(self):
        from diagnostic.vault_schema import FicheProspect
        fiche = FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Ancien Prospect", date_creation="2025-01-01",
        )
        assert fiche.contact_nom is None
        assert fiche.contact_email is None
        assert fiche.icp_id is None
        assert fiche.opt_out is False

    def test_fiche_avec_contact_complet(self):
        from diagnostic.vault_schema import FicheProspect
        fiche = FicheProspect(
            persona=1,
            marche="quebec",
            statut="decouvert",
            nom="Nouveau Prospect",
            date_creation="2026-06-01",
            contact_nom="Jean Tremblay",
            contact_titre="Propriétaire",
            contact_email="jean@tremblay.ca",
            contact_email_source="verified",
            contact_linkedin="https://linkedin.com/in/jean",
            icp_id="persona1-quebec",
            opt_out=False,
        )
        assert fiche.contact_nom == "Jean Tremblay"
        assert fiche.icp_id == "persona1-quebec"
        assert fiche.opt_out is False

    def test_opt_out_defaut_false(self):
        from diagnostic.vault_schema import FicheProspect
        fiche = FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Test", date_creation="2026-06-01",
        )
        assert fiche.opt_out is False

    def test_opt_out_true_persiste(self):
        from diagnostic.vault_schema import FicheProspect
        fiche = FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Test Opt-Out", date_creation="2026-06-01",
            opt_out=True,
        )
        assert fiche.opt_out is True

    def test_champs_j4_dans_model_dump(self):
        from diagnostic.vault_schema import FicheProspect
        fiche = FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Test", date_creation="2026-06-01",
            icp_id="persona1-quebec",
        )
        d = fiche.model_dump(mode="json")
        assert "icp_id" in d
        assert d["icp_id"] == "persona1-quebec"
        assert "opt_out" in d
        assert d["opt_out"] is False

    def test_load_icp_persona1_quebec(self):
        """Smoke test : le fichier icp/persona1-quebec.yaml se charge et valide."""
        from diagnostic.config import load_icp
        icp = load_icp("persona1-quebec")
        assert icp.icp_id == "persona1-quebec"
        assert icp.persona == 1
        assert len(icp.requetes.gabarits) >= 1
        assert len(icp.requetes.localites) >= 1

    def test_load_icp_fichier_absent_leve_erreur(self):
        from diagnostic.config import load_icp
        with pytest.raises(FileNotFoundError):
            load_icp("persona99-inconnu")
