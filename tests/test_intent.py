"""
test_intent.py — diagnostic/intent.py (ADR 0004, axe intention).

Aucune I/O : tout est en mémoire, sur des rubriques d'intention synthétiques.
"""

from __future__ import annotations

from datetime import date, timedelta

from diagnostic.intent import evaluer_intention
from diagnostic.models import EvenementIntention

HIER = (date.today() - timedelta(days=1)).isoformat()
IL_Y_A_10J = (date.today() - timedelta(days=10)).isoformat()
IL_Y_A_200J = (date.today() - timedelta(days=200)).isoformat()


def _rubrique(**overrides) -> dict:
    check = {
        "signal": "website.offre_detectee",
        "op": "is_true",
        "nature": "evenement",
        "date_signal": "website.offre_detectee_date",
        "fenetre_jours": 90,
        "intensite": "haute",
        "citable": True,
        "fiabilite": "B_site_officiel",
        "preuve": "Recrute (offre il y a {jours} j)",
    }
    check.update(overrides)
    return {"dimensions": {"recrutement": {"checks": [check]}}}


class TestEvaluerIntentionCasNominal:
    def test_check_passant_et_date_produit_un_evenement(self):
        signaux = {"website": {"offre_detectee": True, "offre_detectee_date": IL_Y_A_10J}}
        evenements = evaluer_intention(_rubrique(), signaux)
        assert len(evenements) == 1
        assert isinstance(evenements[0], EvenementIntention)
        assert evenements[0].dimension == "recrutement"
        assert "10 j" in evenements[0].preuve
        assert evenements[0].date_evenement == date.fromisoformat(IL_Y_A_10J)

    def test_expire_le_egale_date_plus_fenetre(self):
        signaux = {"website": {"offre_detectee": True, "offre_detectee_date": IL_Y_A_10J}}
        evenements = evaluer_intention(_rubrique(fenetre_jours=90), signaux)
        attendu = date.fromisoformat(IL_Y_A_10J) + timedelta(days=90)
        assert evenements[0].expire_le == attendu

    def test_repli_demi_vie_x3_si_fenetre_absente(self):
        signaux = {"website": {"offre_detectee": True, "offre_detectee_date": IL_Y_A_10J}}
        check = {
            "signal": "website.offre_detectee", "op": "is_true", "nature": "evenement",
            "date_signal": "website.offre_detectee_date", "demi_vie_jours": 20,
            "preuve": "x",
        }
        evenements = evaluer_intention({"dimensions": {"d": {"checks": [check]}}}, signaux)
        attendu = date.fromisoformat(IL_Y_A_10J) + timedelta(days=60)
        assert evenements[0].expire_le == attendu

    def test_intensite_et_fiabilite_reprises_du_yaml(self):
        signaux = {"website": {"offre_detectee": True, "offre_detectee_date": IL_Y_A_10J}}
        evenements = evaluer_intention(
            _rubrique(intensite="basse", fiabilite="C_api_commerciale"), signaux,
        )
        assert evenements[0].intensite == "basse"
        assert evenements[0].fiabilite == "C_api_commerciale"

    def test_tri_du_plus_recent_au_plus_ancien(self):
        rubrique = {"dimensions": {
            "a": {"checks": [{
                "signal": "website.a", "op": "is_true", "nature": "evenement",
                "date_signal": "website.date_a", "fenetre_jours": 90, "preuve": "a",
            }]},
            "b": {"checks": [{
                "signal": "website.b", "op": "is_true", "nature": "evenement",
                "date_signal": "website.date_b", "fenetre_jours": 90, "preuve": "b",
            }]},
        }}
        signaux = {"website": {
            "a": True, "date_a": IL_Y_A_200J,
            "b": True, "date_b": IL_Y_A_10J,
        }}
        evenements = evaluer_intention(rubrique, signaux)
        assert [e.dimension for e in evenements] == ["b", "a"]


class TestTroisEtatsPreserves:
    """Miroir de test_pipeline_stubs_ne_fabriquent_aucune_faille (besoin)."""

    def test_signal_none_ne_fabrique_aucun_evenement(self):
        signaux = {"website": {"offre_detectee": None, "offre_detectee_date": None}}
        assert evaluer_intention(_rubrique(), signaux) == []

    def test_signal_false_ne_fabrique_aucun_evenement(self):
        """False = observation négative (pas de recrutement) : toujours pas
        d'événement — un événement n'est jamais un "gap inversé"."""
        signaux = {"website": {"offre_detectee": False, "offre_detectee_date": None}}
        assert evaluer_intention(_rubrique(), signaux) == []

    def test_check_passant_sans_date_est_ecarte(self):
        """D2 : un événement non daté est ÉCARTÉ, jamais dégradé en état permanent."""
        signaux = {"website": {"offre_detectee": True, "offre_detectee_date": None}}
        assert evaluer_intention(_rubrique(), signaux) == []

    def test_date_non_parsable_est_ecartee(self):
        signaux = {"website": {"offre_detectee": True, "offre_detectee_date": "n'importe quoi"}}
        assert evaluer_intention(_rubrique(), signaux) == []


class TestTypologieEvenementEtat:
    def test_check_nature_etat_est_ignore(self):
        """D12.6 : un check déclaré nature: etat n'est JAMAIS transformé en
        événement, même s'il passerait le test is_true/date."""
        signaux = {"website": {"offre_detectee": True, "offre_detectee_date": IL_Y_A_10J}}
        evenements = evaluer_intention(_rubrique(nature="etat"), signaux)
        assert evenements == []

    def test_absence_de_nature_defaut_etat_est_ignoree(self):
        """Défaut rétro-compatible : un check sans `nature` du tout vaut `etat`."""
        check = {
            "signal": "website.offre_detectee", "op": "is_true",
            "date_signal": "website.offre_detectee_date", "preuve": "x",
        }
        signaux = {"website": {"offre_detectee": True, "offre_detectee_date": IL_Y_A_10J}}
        evenements = evaluer_intention({"dimensions": {"d": {"checks": [check]}}}, signaux)
        assert evenements == []


class TestCitabiliteDefaut:
    def test_citable_defaut_false_si_absent_du_yaml(self):
        """D6 : sécurité par défaut — jamais citable sans déclaration explicite."""
        check = {
            "signal": "website.offre_detectee", "op": "is_true", "nature": "evenement",
            "date_signal": "website.offre_detectee_date", "fenetre_jours": 90, "preuve": "x",
        }
        signaux = {"website": {"offre_detectee": True, "offre_detectee_date": IL_Y_A_10J}}
        evenements = evaluer_intention({"dimensions": {"d": {"checks": [check]}}}, signaux)
        assert evenements[0].citable is False

    def test_citable_false_explicite_est_respecte(self):
        signaux = {"website": {"offre_detectee": True, "offre_detectee_date": IL_Y_A_10J}}
        evenements = evaluer_intention(_rubrique(citable=False), signaux)
        assert evenements[0].citable is False


class TestOperateurGte:
    """Preuve ADR 0004 §D4 : `gte` (déjà existant, non modifié) fonctionne
    sans aucun nouvel opérateur pour l'axe intention."""

    def test_gte_sur_valeur_numerique(self):
        check = {
            "signal": "website.metrique", "op": "gte", "value": 0.5,
            "nature": "evenement", "date_signal": "website.metrique_date",
            "fenetre_jours": 30, "preuve": "x",
        }
        signaux = {"website": {"metrique": 0.8, "metrique_date": IL_Y_A_10J}}
        evenements = evaluer_intention({"dimensions": {"d": {"checks": [check]}}}, signaux)
        assert len(evenements) == 1

        signaux_faible = {"website": {"metrique": 0.2, "metrique_date": IL_Y_A_10J}}
        assert evaluer_intention({"dimensions": {"d": {"checks": [check]}}}, signaux_faible) == []
