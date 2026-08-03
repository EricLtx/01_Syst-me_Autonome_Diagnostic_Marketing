"""
test_serializers_intention.py — dérivation de l'axe intention côté vault
(ADR 0004, D6/D12.5).

Aucune I/O : tout est en mémoire.
"""

from __future__ import annotations

from datetime import date, timedelta

from diagnostic.models import Company, Diagnostic, EvenementIntention
from diagnostic.serializers import diagnostic_to_fiche, diagnostic_to_rapport_md
from diagnostic.vault_schema import FicheProspect

FICHE_BASE = dict(
    persona=1, marche="quebec", statut="decouvert",
    nom="Chauffage ABC inc.", date_creation="2026-06-09",
)


def _fiche(**extra) -> FicheProspect:
    return FicheProspect(**{**FICHE_BASE, **extra})


def _evenement(citable: bool, jours_passes: int = 10, **extra) -> EvenementIntention:
    d = date.today() - timedelta(days=jours_passes)
    base = dict(
        dimension="recrutement_production",
        preuve=f"Recrute (offre il y a {jours_passes} j)",
        date_evenement=d,
        expire_le=d + timedelta(days=90),
        intensite="haute",
        citable=citable,
        fiabilite="B_site_officiel",
    )
    base.update(extra)
    return EvenementIntention(**base)


def _diag(evenements: list[EvenementIntention] | None = None) -> Diagnostic:
    return Diagnostic(
        entreprise=Company(nom="Chauffage ABC inc.", url="https://chauffage-abc.ca"),
        scores={"global": 40.0},
        failles=[],
        mini_audit="Audit.",
        accroche="Accroche.",
        evenements_intention=evenements or [],
    )


class TestDerivationSignalIntention:
    def test_aucun_evenement_donne_champs_none(self):
        fiche = diagnostic_to_fiche(_diag(), _fiche())
        assert fiche.signal_intention is None
        assert fiche.date_intention is None
        assert fiche.intention_expire_le is None

    def test_evenement_citable_est_derive(self):
        evt = _evenement(citable=True)
        fiche = diagnostic_to_fiche(_diag([evt]), _fiche())
        assert fiche.signal_intention == evt.preuve
        assert fiche.date_intention == evt.date_evenement
        assert fiche.intention_expire_le == evt.expire_le

    def test_evenement_non_citable_ne_produit_jamais_signal_intention(self):
        """D6/D12.5 : contrainte dure — un événement non citable ne peut
        JAMAIS apparaître dans FicheProspect.signal_intention."""
        evt = _evenement(citable=False)
        fiche = diagnostic_to_fiche(_diag([evt]), _fiche())
        assert fiche.signal_intention is None
        assert fiche.date_intention is None
        assert fiche.intention_expire_le is None

    def test_evenement_non_citable_parmi_plusieurs_est_saute(self):
        """Un événement non citable suivi d'un citable : c'est le citable qui gagne."""
        non_citable = _evenement(citable=False, jours_passes=1, dimension="a")
        citable = _evenement(citable=True, jours_passes=20, dimension="b")
        fiche = diagnostic_to_fiche(_diag([non_citable, citable]), _fiche())
        assert fiche.signal_intention == citable.preuve

    def test_champs_existants_non_perturbes(self):
        """Ajout strictement additif : le reste de la projection est intact."""
        fiche = diagnostic_to_fiche(_diag(), _fiche())
        assert fiche.date_diagnostic == date.today()
        assert fiche.gaps_majeurs == []


class TestRapportMarkdownIntention:
    def test_section_absente_si_aucun_evenement(self):
        rapport = diagnostic_to_rapport_md(_diag())
        assert "Signaux d'intention" not in rapport

    def test_section_presente_si_evenement(self):
        evt = _evenement(citable=True)
        rapport = diagnostic_to_rapport_md(_diag([evt]))
        assert "Signaux d'intention" in rapport
        assert evt.preuve in rapport
        assert evt.dimension in rapport

    def test_evenement_non_citable_visible_dans_rapport_interne(self):
        """Le rapport (pilotage humain interne) peut montrer un événement non
        citable — la contrainte dure ne s'applique qu'à signal_intention."""
        evt = _evenement(citable=False)
        rapport = diagnostic_to_rapport_md(_diag([evt]))
        assert evt.preuve in rapport
        assert "| non |" in rapport or "non |" in rapport


class TestRetrocompatibiliteFicheProspect:
    def test_fiche_sans_champs_intention_reste_valide(self):
        """Une fiche vault écrite AVANT l'ADR 0004 (sans ces 3 clés) se relit
        sans erreur de validation Pydantic (D12.10)."""
        raw = {
            "type": "prospect", "persona": 1, "marche": "quebec",
            "statut": "valide", "nom": "Vieille Fiche HVAC",
            "date_creation": date.today().isoformat(),
        }
        fiche = FicheProspect.model_validate(raw)
        assert fiche.signal_intention is None
        assert fiche.date_intention is None
        assert fiche.intention_expire_le is None

    def test_model_fields_contient_les_trois_nouveaux_champs(self):
        assert "signal_intention" in FicheProspect.model_fields
        assert "date_intention" in FicheProspect.model_fields
        assert "intention_expire_le" in FicheProspect.model_fields
