"""
test_audit_dossier.py — ADR 0005 : le livrable est un dossier d'audit.

Ce que ces tests verrouillent, et pourquoi
------------------------------------------
Le changement de paradigme de l'ADR 0005 tient dans quatre règles, dont trois
sont des règles d'HONNÊTETÉ. Sans test, elles s'érodent à la première
retouche cosmétique du gabarit :

1. « complet » est vérifiable, pas décoratif — un audit sous le seuil de
   couverture se déclare PARTIEL de lui-même.
2. Une dimension non observée devient une QUESTION D'ENTRETIEN, jamais un
   zéro, jamais un point fort, jamais un écart. C'est la règle des trois
   états (I22) appliquée au livrable.
3. Le score global est un instrument interne NON COMPARABLE d'une entreprise
   à l'autre — chaque score étant renormalisé sur les seules dimensions
   observées, deux entreprises couvertes différemment ne passent pas le même
   examen. Le document doit le dire.
4. La priorisation est déterministe : gravité, puis faiblesse de la
   dimension. Aucun LLM ne réordonne le plan d'action.

Aucune I/O : tout est en mémoire.
"""
from __future__ import annotations

from diagnostic.models import Company, Diagnostic, Gap
from diagnostic.serializers import (
    SEUIL_AUDIT_COMPLET,
    SEUIL_POINT_FORT,
    diagnostic_to_rapport_md,
)


def _diag(scores: dict, failles: list[Gap] | None = None) -> Diagnostic:
    return Diagnostic(
        entreprise=Company(nom="Chauffage ABC inc.", url="https://chauffage-abc.ca"),
        scores=scores,
        failles=[] if failles is None else failles,
        mini_audit="Audit de test.",
        accroche="Accroche de test.",
        meta={"collecteurs": ["website"], "rubrique": 1},
    )


class TestCompletude:
    """« Audit complet » est une promesse — elle doit être auditable."""

    def test_couverture_haute_declare_complet(self):
        md = diagnostic_to_rapport_md(
            _diag({"global": 50.0, "site_web": 50.0, "_couverture": 0.95})
        )
        assert "audit complet" in md
        assert "PARTIEL" not in md

    def test_couverture_basse_declare_partiel(self):
        md = diagnostic_to_rapport_md(
            _diag({"global": 50.0, "site_web": 50.0, "_couverture": 0.65})
        )
        assert "PARTIEL" in md

    def test_seuil_est_la_frontiere_exacte(self):
        """Juste au seuil ⇒ complet ; juste en dessous ⇒ partiel."""
        au_seuil = diagnostic_to_rapport_md(
            _diag({"global": 50.0, "site_web": 50.0, "_couverture": SEUIL_AUDIT_COMPLET})
        )
        sous_seuil = diagnostic_to_rapport_md(
            _diag({"global": 50.0, "site_web": 50.0,
                   "_couverture": SEUIL_AUDIT_COMPLET - 0.01})
        )
        assert "audit complet" in au_seuil
        assert "PARTIEL" in sous_seuil

    def test_couverture_absente_ne_ment_pas(self):
        """Sans couverture connue, on ne déclare NI complet NI partiel."""
        md = diagnostic_to_rapport_md(_diag({"global": 50.0, "site_web": 50.0}))
        assert "complétude inconnue" in md
        assert "audit complet" not in md


class TestDimensionNonObservee:
    """I22 appliqué au livrable : non observé ⇒ question, jamais verdict."""

    def _md(self) -> str:
        return diagnostic_to_rapport_md(
            _diag({"global": 50.0, "site_web": 80.0, "avis": None, "_couverture": 0.5})
        )

    def test_devient_une_question_d_entretien(self):
        md = self._md()
        section = md.split("## À vérifier en entretien")[1]
        assert "`avis`" in section

    def test_n_est_jamais_un_point_fort(self):
        """Une dimension non observée ne peut pas être un point d'appui."""
        md = self._md()
        forts = md.split("## Points forts")[1].split("## À vérifier")[0]
        assert "`avis`" not in forts

    def test_n_est_pas_transformee_en_zero(self):
        md = self._md()
        assert "non observé" in md
        # Un 0 fabriqué se lirait comme un constat d'échec jamais établi.
        assert "| `avis` | 0 |" not in md

    def test_toutes_observees_le_dit_explicitement(self):
        md = diagnostic_to_rapport_md(
            _diag({"global": 50.0, "site_web": 80.0, "_couverture": 1.0})
        )
        section = md.split("## À vérifier en entretien")[1]
        assert "Toutes les dimensions" in section


class TestPointsForts:
    def test_dimension_au_dessus_du_seuil_est_listee(self):
        md = diagnostic_to_rapport_md(
            _diag({"global": 80.0, "site_web": SEUIL_POINT_FORT + 5, "_couverture": 1.0})
        )
        forts = md.split("## Points forts")[1].split("## À vérifier")[0]
        assert "`site_web`" in forts

    def test_dimension_sous_le_seuil_est_absente(self):
        md = diagnostic_to_rapport_md(
            _diag({"global": 30.0, "site_web": SEUIL_POINT_FORT - 5, "_couverture": 1.0})
        )
        forts = md.split("## Points forts")[1].split("## À vérifier")[0]
        assert "`site_web`" not in forts

    def test_aucun_point_fort_ne_laisse_pas_un_tableau_vide(self):
        md = diagnostic_to_rapport_md(
            _diag({"global": 10.0, "site_web": 10.0, "_couverture": 1.0})
        )
        forts = md.split("## Points forts")[1].split("## À vérifier")[0]
        assert "Aucune dimension observée" in forts


class TestPlanActionDeterministe:
    def test_gravite_haute_avant_moyenne(self):
        md = diagnostic_to_rapport_md(_diag(
            {"global": 30.0, "site_web": 50.0, "avis": 50.0, "_couverture": 1.0},
            [Gap(dimension="site_web", gravite="moyenne", preuve="Écart moyen"),
             Gap(dimension="avis", gravite="haute", preuve="Écart grave")],
        ))
        plan = md.split("## Écarts détectés")[1].split("## Points forts")[0]
        assert plan.index("Écart grave") < plan.index("Écart moyen")

    def test_a_gravite_egale_la_dimension_la_plus_faible_dabord(self):
        md = diagnostic_to_rapport_md(_diag(
            {"global": 30.0, "site_web": 60.0, "avis": 10.0, "_couverture": 1.0},
            [Gap(dimension="site_web", gravite="haute", preuve="Écart site"),
             Gap(dimension="avis", gravite="haute", preuve="Écart avis")],
        ))
        plan = md.split("## Écarts détectés")[1].split("## Points forts")[0]
        # `avis` est à 10, `site_web` à 60 : le plus faible passe en premier.
        assert plan.index("Écart avis") < plan.index("Écart site")

    def test_gravite_inconnue_passe_en_dernier(self):
        """On ne fait pas remonter en tête ce qu'on n'a pas su qualifier."""
        md = diagnostic_to_rapport_md(_diag(
            {"global": 30.0, "site_web": 50.0, "avis": 50.0, "_couverture": 1.0},
            [Gap(dimension="site_web", gravite="fantaisie", preuve="Écart non qualifié"),
             Gap(dimension="avis", gravite="basse", preuve="Écart mineur")],
        ))
        plan = md.split("## Écarts détectés")[1].split("## Points forts")[0]
        assert plan.index("Écart mineur") < plan.index("Écart non qualifié")

    def test_ordre_reproductible(self):
        """Deux générations du même Diagnostic donnent le même plan."""
        d = _diag(
            {"global": 30.0, "site_web": 60.0, "avis": 10.0, "_couverture": 1.0},
            [Gap(dimension="site_web", gravite="haute", preuve="Écart site"),
             Gap(dimension="avis", gravite="haute", preuve="Écart avis")],
        )
        assert diagnostic_to_rapport_md(d) == diagnostic_to_rapport_md(d)

    def test_aucun_ecart_ne_laisse_pas_un_tableau_vide(self):
        md = diagnostic_to_rapport_md(
            _diag({"global": 90.0, "site_web": 90.0, "_couverture": 1.0})
        )
        plan = md.split("## Écarts détectés")[1].split("## Points forts")[0]
        assert "Aucun écart majeur" in plan


class TestHonnetetesDuDocument:
    def test_le_score_est_declare_non_comparable(self):
        """Le cœur de l'ADR 0005 : un score renormalisé ne classe pas."""
        md = diagnostic_to_rapport_md(
            _diag({"global": 36.9, "site_web": 36.9, "_couverture": 0.65})
        )
        assert "non comparable d'une entreprise à l'autre" in md

    def test_document_declare_son_usage_interne(self):
        md = diagnostic_to_rapport_md(
            _diag({"global": 50.0, "site_web": 50.0, "_couverture": 1.0})
        )
        assert "Document de travail interne" in md

    def test_le_plan_daction_precede_les_scores(self):
        """L'ordre des sections encode le paradigme : l'action avant l'instrument."""
        md = diagnostic_to_rapport_md(
            _diag({"global": 50.0, "site_web": 50.0, "_couverture": 1.0})
        )
        assert md.index("## Écarts détectés") < md.index("## Scores par dimension")
