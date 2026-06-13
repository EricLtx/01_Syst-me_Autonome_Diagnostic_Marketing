"""
test_discovery.py — §7.2-4 + §7.7.

§7.2 : produit cartésien gabarits × localités → nombre correct d'appels SERP
§7.3 : filtres (domaines_exclus, exiger_domaine_propre)
§7.4 : déduplication intra-lot (même domaine, URLs différentes → 1 Candidate)
§7.7 : BudgetExceeded propagé proprement
"""

from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import MagicMock

from diagnostic.discovery import (
    DiscoveryCollector,
    _est_heberge,
    _extraire_nom,
    _normaliser_domaine,
    _normaliser_url,
)
from diagnostic.icp_schema import IcpConfig

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ICP_BASE = {
    "icp_id": "persona1-quebec",
    "persona": 1,
    "marche": "quebec",
    "description": "Test",
    "requetes": {
        "gabarits": ["chauffage {localite}", "clim {localite}"],
        "localites": ["Québec", "Lévis"],
        "max_resultats_par_requete": 5,
    },
    "filtres": {
        "domaines_exclus": ["yelp."],
        "exiger_domaine_propre": True,
    },
    "enrichissement": {
        "titres_cibles": ["propriétaire"],
        "max_enrichissements": 10,
    },
}


def _make_icp(**overrides) -> IcpConfig:
    d = {**_ICP_BASE, **overrides}
    return IcpConfig(**d)


def _make_api_io(return_value: dict | None = None) -> MagicMock:
    api_io = MagicMock()
    api_io.call.return_value = return_value or {"organic_results": []}
    return api_io


# ---------------------------------------------------------------------------
# Tests de normalisation — fonctions pures
# ---------------------------------------------------------------------------

class TestNormalisationDomaine:
    def test_retire_www(self):
        assert _normaliser_domaine("https://www.exemple.ca") == "exemple.ca"

    def test_minuscule(self):
        assert _normaliser_domaine("https://EXEMPLE.CA/page") == "exemple.ca"

    def test_url_sans_www(self):
        assert _normaliser_domaine("https://exemple.ca/") == "exemple.ca"

    def test_url_invalide_retourne_vide(self):
        assert _normaliser_domaine("pas-une-url") == ""


class TestNormalisationUrl:
    def test_http_vers_https(self):
        assert _normaliser_url("http://exemple.ca") == "https://exemple.ca"

    def test_supprime_www(self):
        assert _normaliser_url("https://www.tremblay.ca/") == "https://tremblay.ca"

    def test_supprime_trailing_slash(self):
        assert _normaliser_url("https://exemple.ca/") == "https://exemple.ca"

    def test_preserve_chemin(self):
        assert _normaliser_url("https://exemple.ca/about") == "https://exemple.ca/about"

    def test_http_www_slash_vers_https_propre(self):
        assert _normaliser_url("http://www.tremblay-hvac.ca/") == "https://tremblay-hvac.ca"


class TestExtraireNom:
    def test_pipe(self):
        assert _extraire_nom("Chauffage Tremblay | Services HVAC") == "Chauffage Tremblay"

    def test_tiret_court(self):
        assert _extraire_nom("Climatisation Roy - Québec") == "Climatisation Roy"

    def test_tiret_long(self):
        assert _extraire_nom("Entreprise ABC — Plomberie") == "Entreprise ABC"

    def test_sans_separateur(self):
        assert _extraire_nom("Chauffage Tremblay") == "Chauffage Tremblay"

    def test_titre_vide(self):
        assert _extraire_nom("") == ""


class TestEstHeberge:
    def test_wixsite_heberge(self):
        assert _est_heberge("tremblay.wixsite.com") is True

    def test_squarespace_heberge(self):
        assert _est_heberge("tremblay.squarespace.com") is True

    def test_wordpress_heberge(self):
        assert _est_heberge("tremblay.wordpress.com") is True

    def test_domaine_propre_non_heberge(self):
        assert _est_heberge("tremblay-hvac.ca") is False

    def test_www_domaine_propre_non_heberge(self):
        assert _est_heberge("www.exemple.ca") is False

    def test_domaine_deux_parties_non_heberge(self):
        assert _est_heberge("exemple.ca") is False


# ---------------------------------------------------------------------------
# §7.2 — Produit cartésien → nombre d'appels SERP
# ---------------------------------------------------------------------------

class TestProduitCartesien:
    def test_2_gabarits_2_localites_4_appels(self):
        icp = _make_icp()  # 2 gabarits × 2 localités
        api_io = _make_api_io()
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        collector.discover()
        assert api_io.call.call_count == 4

    def test_1_gabarit_3_localites_3_appels(self):
        icp = _make_icp(requetes={
            "gabarits": ["test {localite}"],
            "localites": ["A", "B", "C"],
            "max_resultats_par_requete": 5,
        })
        api_io = _make_api_io()
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        collector.discover()
        assert api_io.call.call_count == 3

    def test_cache_key_contient_la_requete(self):
        icp = _make_icp(requetes={
            "gabarits": ["test {localite}"],
            "localites": ["Québec"],
            "max_resultats_par_requete": 5,
        })
        api_io = _make_api_io()
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        collector.discover()
        _, kwargs = api_io.call.call_args
        assert kwargs.get("cache_key") == "test Québec"


# ---------------------------------------------------------------------------
# §7.3 — Filtres
# ---------------------------------------------------------------------------

class TestFiltres:
    def test_domaine_exclu_rejete(self):
        icp = _make_icp()
        collector = DiscoveryCollector(api_io=_make_api_io(), icp=icp)
        assert collector._passe_filtres("https://yelp.ca/biz/test") is False

    def test_heberge_rejete_quand_filtre_actif(self):
        icp = _make_icp()
        collector = DiscoveryCollector(api_io=_make_api_io(), icp=icp)
        assert collector._passe_filtres("https://tremblay.wixsite.com/accueil") is False

    def test_domaine_propre_accepte(self):
        icp = _make_icp()
        collector = DiscoveryCollector(api_io=_make_api_io(), icp=icp)
        assert collector._passe_filtres("https://tremblay-hvac.ca") is True

    def test_heberge_accepte_si_filtre_desactive(self):
        icp = _make_icp(filtres={"domaines_exclus": [], "exiger_domaine_propre": False})
        collector = DiscoveryCollector(api_io=_make_api_io(), icp=icp)
        assert collector._passe_filtres("https://tremblay.wixsite.com/accueil") is True

    def test_url_vide_rejetee(self):
        icp = _make_icp()
        collector = DiscoveryCollector(api_io=_make_api_io(), icp=icp)
        assert collector._passe_filtres("") is False


# ---------------------------------------------------------------------------
# §7.4 — Déduplication intra-lot
# ---------------------------------------------------------------------------

class TestDedupIntraBatch:
    def test_meme_domaine_deux_urls_une_candidate(self):
        icp = _make_icp(requetes={
            "gabarits": ["test {localite}"],
            "localites": ["Québec"],
            "max_resultats_par_requete": 10,
        })
        api_io = _make_api_io({
            "organic_results": [
                {"link": "https://www.exemple.ca/page1", "title": "Exemple | HVAC"},
                {"link": "http://exemple.ca/page2", "title": "Exemple - Services"},
            ]
        })
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        candidates = collector.discover()
        assert len(candidates) == 1

    def test_deux_domaines_deux_candidates(self):
        icp = _make_icp(requetes={
            "gabarits": ["test {localite}"],
            "localites": ["Québec"],
            "max_resultats_par_requete": 10,
        })
        api_io = _make_api_io({
            "organic_results": [
                {"link": "https://exemple-a.ca", "title": "Exemple A"},
                {"link": "https://exemple-b.ca", "title": "Exemple B"},
            ]
        })
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        candidates = collector.discover()
        assert len(candidates) == 2

    def test_dedup_inter_requetes(self):
        """Même domaine apparaissant dans deux requêtes différentes → 1 Candidate."""
        icp = _make_icp(requetes={
            "gabarits": ["test1 {localite}", "test2 {localite}"],
            "localites": ["Québec"],
            "max_resultats_par_requete": 5,
        })
        api_io = _make_api_io({
            "organic_results": [
                {"link": "https://doublon.ca", "title": "Doublon HVAC"},
            ]
        })
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        candidates = collector.discover()
        assert len(candidates) == 1

    def test_nom_extrait_depuis_titre(self):
        icp = _make_icp(requetes={
            "gabarits": ["test {localite}"],
            "localites": ["Québec"],
            "max_resultats_par_requete": 5,
        })
        api_io = _make_api_io({
            "organic_results": [
                {"link": "https://tremblay.ca", "title": "Tremblay HVAC | Climatisation Québec"},
            ]
        })
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        candidates = collector.discover()
        assert candidates[0].nom == "Tremblay HVAC"

    def test_url_canonique_dans_candidate(self):
        icp = _make_icp(requetes={
            "gabarits": ["test {localite}"],
            "localites": ["Québec"],
            "max_resultats_par_requete": 5,
        })
        api_io = _make_api_io({
            "organic_results": [
                {"link": "http://www.tremblay.ca/", "title": "Tremblay"},
            ]
        })
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        candidates = collector.discover()
        assert candidates[0].site_web == "https://tremblay.ca"

    def test_icp_id_dans_candidate(self):
        icp = _make_icp(requetes={
            "gabarits": ["test {localite}"],
            "localites": ["Québec"],
            "max_resultats_par_requete": 5,
        })
        api_io = _make_api_io({
            "organic_results": [{"link": "https://test.ca", "title": "Test"}]
        })
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        candidates = collector.discover()
        assert candidates[0].icp_id == "persona1-quebec"


# ---------------------------------------------------------------------------
# §7.7 — BudgetExceeded propagé
# ---------------------------------------------------------------------------

class TestBudgetExceeded:
    def test_budget_exceeded_propage(self):
        from diagnostic.api_io import BudgetExceeded
        icp = _make_icp()
        api_io = MagicMock()
        api_io.call.side_effect = BudgetExceeded("budget dépassé")
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        with pytest.raises(BudgetExceeded):
            collector.discover()

    def test_erreur_reseau_isolee_par_requete(self):
        """Une ConnectionError sur une requête n'interrompt pas les suivantes."""
        icp = _make_icp(requetes={
            "gabarits": ["test {localite}"],
            "localites": ["A", "B"],
            "max_resultats_par_requete": 5,
        })
        api_io = MagicMock()
        # Première requête échoue, deuxième réussit
        api_io.call.side_effect = [
            ConnectionError("timeout"),
            {"organic_results": [{"link": "https://ok.ca", "title": "OK"}]},
        ]
        collector = DiscoveryCollector(api_io=api_io, icp=icp)
        candidates = collector.discover()
        assert len(candidates) == 1
