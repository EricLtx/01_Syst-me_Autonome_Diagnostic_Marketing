"""
test_scoring.py — verrouille les trois défauts structurels du moteur de scoring.

Ces trois défauts ont été trouvés par lecture du code puis REPRODUITS par
exécution avant correction. Ils se renforçaient l'un l'autre :

  A1. `None` était compté comme un échec. Sans clé Google Places, les
      dimensions presence_locale et avis valaient 0/100 pour TOUS les
      prospects — 45 % de la pondération fabriquée à zéro. Une entreprise au
      site irréprochable plafonnait à 27,5/100.
  A2. La gravité était déduite du poids du check rapporté au total de sa
      dimension, donc du NOMBRE de checks voisins. « Site web inaccessible »
      ressortait en `moyenne`.
  A3. Conséquence des deux précédents : `signal_chaud` était CONSTANT.
      Trois entreprises radicalement différentes recevaient la même accroche
      — « Fiche Google Business non vérifiée (à confirmer en J3) » — une
      affirmation jamais vérifiée, en violation de l'invariant J1 n°4.

Sans ces tests, rien n'empêche le retour du défaut.
"""

from __future__ import annotations

from datetime import date

import pytest

from diagnostic.models import Company, Diagnostic
from diagnostic.scoring import ScoringEngine, _check_passes
from diagnostic.serializers import diagnostic_to_fiche
from diagnostic.vault_schema import FicheProspect

# Rubrique minimale : deux dimensions de poids égal, l'une observable,
# l'autre volontairement non observée (comme gbp/reviews sans clé API).
RUBRIQUE = {
    "persona": "test",
    "dimensions": {
        "observable": {
            "poids": 50,
            "checks": [
                {"signal": "web.a", "op": "is_true", "points": 50,
                 "gravite": "haute", "gap": "A manque"},
                {"signal": "web.b", "op": "is_true", "points": 50,
                 "gravite": "basse", "gap": "B manque"},
            ],
        },
        "non_observee": {
            "poids": 50,
            "checks": [
                {"signal": "places.x", "op": "is_true", "points": 100,
                 "gravite": "haute", "gap": "X manque"},
            ],
        },
    },
}


def _fiche(nom: str) -> FicheProspect:
    return FicheProspect(persona=1, marche="quebec", statut="decouvert",
                         nom=nom, date_creation=date.today())


class TestA1SignalInconnu:
    """Un signal non observé ne produit ni faille, ni point, ni dénominateur."""

    def test_signal_none_ne_produit_aucune_faille(self):
        scores, gaps = ScoringEngine(RUBRIQUE).score(
            {"web": {"a": True, "b": True}, "places": {"x": None}}
        )
        assert [g.dimension for g in gaps] == [], (
            "un signal None ne doit jamais être affirmé comme une faille"
        )

    def test_dimension_non_observee_vaut_none_pas_zero(self):
        scores, _ = ScoringEngine(RUBRIQUE).score(
            {"web": {"a": True, "b": True}, "places": {"x": None}}
        )
        assert scores["non_observee"] is None, "ne pas fabriquer un 0"
        assert scores["observable"] == 100.0

    def test_global_renormalise_sur_les_dimensions_observees(self):
        """Le défaut d'origine : la dimension inconnue tirait le global à 50."""
        scores, _ = ScoringEngine(RUBRIQUE).score(
            {"web": {"a": True, "b": True}, "places": {"x": None}}
        )
        assert scores["global"] == 100.0

    def test_couverture_expose_la_part_reellement_evaluee(self):
        scores, _ = ScoringEngine(RUBRIQUE).score(
            {"web": {"a": True, "b": True}, "places": {"x": None}}
        )
        assert scores["_couverture"] == 0.5

        complet, _ = ScoringEngine(RUBRIQUE).score(
            {"web": {"a": True, "b": True}, "places": {"x": True}}
        )
        assert complet["_couverture"] == 1.0

    def test_echec_observe_produit_bien_une_faille(self):
        """Contre-épreuve : False (observé) reste un échec, contrairement à None."""
        _, gaps = ScoringEngine(RUBRIQUE).score(
            {"web": {"a": False, "b": True}, "places": {"x": None}}
        )
        assert [g.preuve for g in gaps] == ["A manque"]

    def test_partiel_dans_une_dimension_renormalise_le_denominateur(self):
        """Un seul check connu sur deux : le score porte sur ce qui est connu."""
        scores, _ = ScoringEngine(RUBRIQUE).score(
            {"web": {"a": True, "b": None}, "places": {"x": None}}
        )
        assert scores["observable"] == 100.0

    def test_aucun_signal_du_tout_donne_un_global_none(self):
        scores, gaps = ScoringEngine(RUBRIQUE).score(
            {"web": {"a": None, "b": None}, "places": {"x": None}}
        )
        assert scores["global"] is None, "aucune observation => aucun score"
        assert scores["_couverture"] == 0.0
        assert gaps == []


class TestA2Gravite:
    """La gravité est un jugement déclaré, pas un artefact du nombre de checks."""

    def test_gravite_declaree_est_respectee(self):
        _, gaps = ScoringEngine(RUBRIQUE).score(
            {"web": {"a": False, "b": False}, "places": {"x": None}}
        )
        par_preuve = {g.preuve: g.gravite for g in gaps}
        # Poids identiques (50/50) : sous l'ancien calcul les deux auraient eu
        # la même gravité. Ici elles diffèrent, parce qu'elles sont déclarées.
        assert par_preuve["A manque"] == "haute"
        assert par_preuve["B manque"] == "basse"

    def test_repli_si_gravite_absente(self):
        """Rétro-compatibilité : une rubrique sans `gravite` reste exploitable."""
        rub = {"dimensions": {"d": {"poids": 100, "checks": [
            {"signal": "s.k", "op": "is_true", "points": 100, "gap": "G"},
        ]}}}
        _, gaps = ScoringEngine(rub).score({"s": {"k": False}})
        assert gaps[0].gravite == "haute"

    def test_gravite_invalide_leve_une_erreur(self):
        rub = {"dimensions": {"d": {"poids": 100, "checks": [
            {"signal": "s.k", "op": "is_true", "points": 100,
             "gravite": "critique", "gap": "G"},
        ]}}}
        with pytest.raises(ValueError, match="Gravité invalide"):
            ScoringEngine(rub).score({"s": {"k": False}})

    def test_site_inaccessible_est_haute_dans_la_vraie_rubrique(self):
        """Régression : la pire faille possible était classée `moyenne`."""
        from diagnostic.config import load_rubrique

        signaux = {"website": {"reachable": False}, "seo": {}, "social": {},
                   "gbp": {}, "reviews": {}}
        _, gaps = ScoringEngine(load_rubrique()).score(signaux)
        inaccessible = [g for g in gaps if "inaccessible" in g.preuve.lower()]
        assert inaccessible, "la faille doit être émise"
        assert inaccessible[0].gravite == "haute"

    def test_tri_place_les_hautes_en_premier(self):
        _, gaps = ScoringEngine(RUBRIQUE).score(
            {"web": {"a": False, "b": False}, "places": {"x": None}}
        )
        assert [g.gravite for g in gaps] == ["haute", "basse"]


class TestA3SignalChaudDiscrimine:
    """L'accroche envoyée doit dépendre de l'entreprise, sinon c'est du spam."""

    @staticmethod
    def _signal(signaux: dict, nom: str) -> str | None:
        from diagnostic.config import load_rubrique

        scores, failles = ScoringEngine(load_rubrique()).score(signaux)
        diag = Diagnostic(entreprise=Company(nom=nom, url="https://x.test"),
                          signaux=signaux, scores=scores, failles=failles,
                          accroche="", mini_audit="", meta={})
        return diagnostic_to_fiche(diag, _fiche(nom)).signal_chaud

    def test_entreprises_differentes_donnent_des_accroches_differentes(self):
        base = {"reachable": True, "https": True, "has_viewport": True,
                "has_meta_description": True, "has_logo": True, "has_contact": True,
                "mentions_offre": True, "has_title": True, "image_count": 8,
                "fraicheur_mois": 2}
        cas = {
            "sans_site": {"website": {"reachable": False}, "seo": {}, "social": {},
                          "gbp": {}, "reviews": {}},
            "pas_mobile": {"website": {**base, "has_viewport": False},
                           "seo": {"local_keywords": True},
                           "social": {"plateformes_mentionnees": ["fb"]},
                           "gbp": {}, "reviews": {}},
            "site_abandonne": {"website": {**base, "fraicheur_mois": 60},
                               "seo": {"local_keywords": True},
                               "social": {"plateformes_mentionnees": ["fb"]},
                               "gbp": {}, "reviews": {}},
        }
        signaux = {n: self._signal(s, n) for n, s in cas.items()}
        assert len(set(signaux.values())) == len(cas), (
            f"accroches non discriminantes : {signaux}"
        )

    def test_aucune_accroche_ne_porte_de_mention_dincertitude(self):
        from diagnostic.config import load_rubrique

        signaux = {"website": {"reachable": False}, "seo": {}, "social": {},
                   "gbp": {}, "reviews": {}}
        _, gaps = ScoringEngine(load_rubrique()).score(signaux)
        for g in gaps:
            assert "confirmer" not in g.preuve.lower()

    def test_entreprise_sans_faille_na_pas_daccroche(self):
        """Rien à reprocher => rien à vendre. C'est une disqualification."""
        parfait = {
            "website": {"reachable": True, "https": True, "has_viewport": True,
                        "has_meta_description": True, "has_logo": True,
                        "has_contact": True, "mentions_offre": True,
                        "has_title": True, "image_count": 8, "fraicheur_mois": 1},
            "seo": {"local_keywords": True},
            "social": {"plateformes_mentionnees": ["fb", "ig"]},
            "gbp": {}, "reviews": {},
        }
        assert self._signal(parfait, "parfait") is None


class TestOperateurs:
    def test_non_vide_distingue_liste_vide_et_absence(self):
        assert _check_passes(["fb"], "non_vide", None) is True
        assert _check_passes([], "non_vide", None) is False, (
            "une liste vide est une observation négative, pas une absence"
        )
        assert _check_passes(None, "non_vide", None) is None, (
            "None reste une absence d'observation"
        )

    def test_none_est_inconnu_pour_tous_les_operateurs(self):
        for op in ("is_true", "gte", "lte", "exists", "non_vide"):
            assert _check_passes(None, op, 1) is None

    def test_operateur_inconnu_leve(self):
        with pytest.raises(ValueError, match="Opérateur inconnu"):
            _check_passes(True, "peut_etre", None)


class TestClassementParBesoin:
    """Le score doit ordonner les prospects par BESOIN décroissant."""

    def test_le_score_discrimine_reellement(self):
        from diagnostic.config import load_rubrique

        eng = ScoringEngine(load_rubrique())
        bon = {"website": {"reachable": True, "https": True, "has_viewport": True,
                           "has_meta_description": True, "has_logo": True,
                           "has_contact": True, "mentions_offre": True,
                           "has_title": True, "image_count": 8, "fraicheur_mois": 1},
               "seo": {"local_keywords": True},
               "social": {"plateformes_mentionnees": ["fb"]}, "gbp": {}, "reviews": {}}
        mauvais = {"website": {"reachable": True, "https": False, "has_viewport": False,
                               "has_meta_description": False, "has_logo": False,
                               "has_contact": False, "mentions_offre": False,
                               "has_title": False, "image_count": 0, "fraicheur_mois": 80},
                   "seo": {"local_keywords": False},
                   "social": {"plateformes_mentionnees": []}, "gbp": {}, "reviews": {}}

        s_bon = eng.score(bon)[0]["global"]
        s_mauvais = eng.score(mauvais)[0]["global"]
        assert s_bon > s_mauvais, "le moteur doit séparer les deux profils"
        assert s_bon >= 90, "une entreprise saine ne doit pas être pénalisée"
        assert s_mauvais <= 25, "une entreprise en difficulté doit ressortir"
