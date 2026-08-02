"""
test_collectors_phase_d.py — tests §9.9 Phase D.

Couvre :
  §9.9a — social.plateformes_mentionnees dérivé de website.social_links,
           aucun appel réseau (collecteur passif)
  §9.9b — website.derniere_maj renseigné depuis Last-Modified HTTP et/ou sitemap.xml
  §9.9c — website.fraicheur_mois calculé correctement
  §9.9d — reviews.repond_aux_avis déduit des réponses propriétaire dans les avis
  §9.9e — gbp._parse_place : verified et has_photos selon la réponse Places
  §9.9f — seo.local_keywords détecte les mots de la région dans le texte
  §9.9g — pipeline injecte _website_signals dans SeoCollector et SocialCollector

Aucun réseau réel, aucune clé API.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from diagnostic.collectors.gbp import GbpCollector
from diagnostic.collectors.reviews import ReviewsCollector
from diagnostic.collectors.seo import SeoCollector
from diagnostic.collectors.social import SocialCollector
from diagnostic.collectors.website import WebsiteCollector
from diagnostic.models import Company


# ---------------------------------------------------------------------------
# §9.9a — SocialCollector passif
# ---------------------------------------------------------------------------

class TestSocialPassif:
    def test_plateformes_depuis_website_signals(self):
        c = SocialCollector()
        c._website_signals = {"social_links": ["facebook", "linkedin"], "reachable": True}
        result = c.collect(Company(nom="Test", url=""))
        assert result["plateformes_mentionnees"] == ["facebook", "linkedin"]

    def test_sans_website_signals_retourne_none_pas_liste_vide(self):
        """Site non consulté → None (inconnu), jamais [] (observation négative).

        Ce test assertait auparavant `== []`. Il verrouillait un défaut : une
        liste vide signifie « j'ai regardé le site, il ne mentionne aucun
        réseau social » — une observation. Or quand `_website_signals` est
        absent, le site n'a JAMAIS pu être consulté. Confondre les deux faisait
        émettre la faille « Aucune présence sociale reliée depuis le site »
        contre une entreprise dont le site était simplement hors ligne.
        """
        c = SocialCollector()
        result = c.collect(Company(nom="Test", url=""))
        assert result["plateformes_mentionnees"] is None

    def test_site_consulte_sans_lien_social_reste_une_liste_vide(self):
        """Contre-épreuve : [] doit rester une observation négative légitime."""
        c = SocialCollector()
        c._website_signals = {"social_links": []}
        result = c.collect(Company(nom="Test", url=""))
        assert result["plateformes_mentionnees"] == []

    def test_social_links_vide_retourne_liste_vide(self):
        c = SocialCollector()
        c._website_signals = {"social_links": [], "reachable": True}
        result = c.collect(Company(nom="Test", url=""))
        assert result["plateformes_mentionnees"] == []

    def test_aucun_appel_reseau(self):
        """SocialCollector n'utilise pas requests, même si on lui passe une company avec URL."""
        c = SocialCollector()
        c._website_signals = {"social_links": ["instagram"]}
        with patch("requests.get") as mock_get:
            c.collect(Company(nom="Test", url="https://exemple.com"))
        mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# §9.9b — WebsiteCollector : derniere_maj depuis Last-Modified / sitemap / time
# ---------------------------------------------------------------------------

class TestDerniereMaj:
    def _collector(self) -> WebsiteCollector:
        return WebsiteCollector(use_cache=False)

    def test_last_modified_http_utilise(self):
        c = self._collector()
        resp = MagicMock()
        resp.text = "<html><body>no dates</body></html>"
        resp.url = "https://exemple.ca"
        resp.status_code = 200
        resp.headers.get = lambda k, default=None: "Mon, 01 Jan 2024 10:00:00 GMT" if k == "Last-Modified" else default
        with patch("requests.get", return_value=resp):
            result = c.collect(Company(nom="Test", url="https://exemple.ca"))
        assert result["derniere_maj"] is not None
        assert "2024" in result["derniere_maj"]

    def test_sitemap_lastmod_extrait(self):
        c = self._collector()
        sitemap_xml = """<?xml version="1.0"?>
<urlset>
  <url><loc>https://exemple.ca/</loc><lastmod>2025-03-15</lastmod></url>
  <url><loc>https://exemple.ca/a</loc><lastmod>2024-06-01</lastmod></url>
</urlset>"""
        html = "<html><body></body></html>"

        call_count = {"n": 0}
        def fake_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            call_count["n"] += 1
            if "sitemap" in url:
                resp.text = sitemap_xml
            else:
                resp.text = html
            resp.url = url
            resp.headers.get = lambda k, default=None: None
            return resp

        with patch("requests.get", side_effect=fake_get):
            result = c.collect(Company(nom="Test", url="https://exemple.ca"))
        assert result["derniere_maj"] == "2025-03-15"

    def test_time_tag_extrait(self):
        c = self._collector()
        html = '<html><body><time datetime="2025-05-20">20 mai 2025</time></body></html>'
        resp = MagicMock()
        resp.text = html
        resp.url = "https://exemple.ca"
        resp.status_code = 200
        resp.headers.get = lambda k, default=None: None
        with patch("requests.get", return_value=resp):
            result = c.collect(Company(nom="Test", url="https://exemple.ca"))
        assert result["derniere_maj"] == "2025-05-20"

    def test_copyright_year_fallback(self):
        c = self._collector()
        html = "<html><body><p>© 2023 Test Inc.</p></body></html>"
        resp = MagicMock()
        resp.text = html
        resp.url = "https://exemple.ca"
        resp.status_code = 200
        resp.headers.get = lambda k, default=None: None
        with patch("requests.get", return_value=resp):
            result = c.collect(Company(nom="Test", url="https://exemple.ca"))
        assert result["derniere_maj"] == "2023"

    def test_aucune_date_retourne_none(self):
        c = self._collector()
        html = "<html><body><p>Aucune date ici</p></body></html>"
        resp = MagicMock()
        resp.text = html
        resp.url = "https://exemple.ca"
        resp.status_code = 200
        resp.headers.get = lambda k, default=None: None
        with patch("requests.get", return_value=resp):
            result = c.collect(Company(nom="Test", url="https://exemple.ca"))
        assert result["derniere_maj"] is None

    def test_date_la_plus_recente_gagne(self):
        """Si plusieurs sources, la plus récente est retenue."""
        c = self._collector()
        # copyright 2022, time tag 2024 → 2024 gagne
        html = '<html><body><p>© 2022</p><time datetime="2024-08-01">aout 2024</time></body></html>'
        resp = MagicMock()
        resp.text = html
        resp.url = "https://exemple.ca"
        resp.status_code = 200
        resp.headers.get = lambda k, default=None: None
        with patch("requests.get", return_value=resp):
            result = c.collect(Company(nom="Test", url="https://exemple.ca"))
        assert result["derniere_maj"] == "2024-08-01"


# ---------------------------------------------------------------------------
# §9.9c — fraicheur_mois
# ---------------------------------------------------------------------------

class TestFraicheurMois:
    def test_fraicheur_calculee_depuis_date_iso(self):
        import datetime
        today = datetime.date.today()
        # une date d'il y a 6 mois
        d = today.replace(month=today.month) - datetime.timedelta(days=180)
        c = WebsiteCollector(use_cache=False)
        mois = WebsiteCollector._fraicheur_mois(d.isoformat())
        assert isinstance(mois, int)
        assert mois >= 5  # environ 6 mois, tolérance ±1

    def test_fraicheur_depuis_annee_seule(self):
        import datetime
        c = WebsiteCollector(use_cache=False)
        mois = WebsiteCollector._fraicheur_mois("2020")
        today = datetime.date.today()
        attendu = (today.year - 2020) * 12 + today.month - 1
        assert mois == attendu

    def test_sans_date_retourne_none(self):
        assert WebsiteCollector._fraicheur_mois(None) is None

    def test_fraicheur_dans_signaux_website(self):
        c = WebsiteCollector(use_cache=False)
        html = "<html><body>© 2022</body></html>"
        resp = MagicMock()
        resp.text = html
        resp.url = "https://exemple.ca"
        resp.status_code = 200
        resp.headers.get = lambda k, default=None: None
        with patch("requests.get", return_value=resp):
            result = c.collect(Company(nom="Test", url="https://exemple.ca"))
        assert result["fraicheur_mois"] is not None
        assert isinstance(result["fraicheur_mois"], int)


# ---------------------------------------------------------------------------
# §9.9d — reviews.repond_aux_avis
# ---------------------------------------------------------------------------

class TestRepond:
    def _io(self, tmp_path: Path):
        from diagnostic.api_io import ApiIO
        pricing = {
            "devise": "USD",
            "fournisseurs": {
                "google_places": {
                    "unite": "requete",
                    "endpoints": {
                        "text_search": {"prix_par_unite": {"requetes": 0.0}},
                        "place_details": {"prix_par_unite": {"requetes": 0.0}},
                    },
                }
            },
        }
        return ApiIO(pricing, tmp_path / "api_usage.log", cache_dir=tmp_path / "cache")

    def test_repond_aux_avis_true_si_owner_answer(self, tmp_path):
        io = self._io(tmp_path)
        c = ReviewsCollector(api_io=io)

        def fake_api_call(fournisseur, endpoint, fn, **kwargs):
            if endpoint == "text_search":
                return {"status": "OK", "results": [{"place_id": "abc", "rating": 4.5, "user_ratings_total": 20, "business_status": "OPERATIONAL"}]}
            if endpoint == "place_details":
                return {"result": {"reviews": [
                    {"rating": 5, "text": "Super", "time": 1700000000, "owner_answer": {"text": "Merci !"}},
                    {"rating": 3, "text": "Correct", "time": 1699000000},
                ]}}
            return fn()

        io.call = fake_api_call
        result = c.collect(Company(nom="Test HVAC", url="", region="Québec"))
        assert result["repond_aux_avis"] is True

    def test_repond_aux_avis_false_si_aucune_reponse(self, tmp_path):
        io = self._io(tmp_path)
        c = ReviewsCollector(api_io=io)

        def fake_api_call(fournisseur, endpoint, fn, **kwargs):
            if endpoint == "text_search":
                return {"status": "OK", "results": [{"place_id": "abc", "rating": 3.8, "user_ratings_total": 5}]}
            if endpoint == "place_details":
                return {"result": {"reviews": [
                    {"rating": 4, "text": "Bien", "time": 1700000000},
                ]}}
            return fn()

        io.call = fake_api_call
        result = c.collect(Company(nom="Test", url="", region="Genève"))
        assert result["repond_aux_avis"] is False

    def test_stub_sans_api_io(self):
        c = ReviewsCollector()
        result = c.collect(Company(nom="Test", url=""))
        assert result["count"] is None
        assert result["avg"] is None

    def test_count_et_avg_depuis_text_search(self, tmp_path):
        io = self._io(tmp_path)
        c = ReviewsCollector(api_io=io)

        def fake_api_call(fournisseur, endpoint, fn, **kwargs):
            if endpoint == "text_search":
                return {"status": "OK", "results": [{"place_id": "xyz", "rating": 4.2, "user_ratings_total": 87}]}
            if endpoint == "place_details":
                return {"result": {"reviews": []}}
            return fn()

        io.call = fake_api_call
        result = c.collect(Company(nom="Test", url="", region="Montréal"))
        assert result["count"] == 87
        assert result["avg"] == 4.2

    def test_aucun_resultat_places_retourne_zero(self, tmp_path):
        io = self._io(tmp_path)
        c = ReviewsCollector(api_io=io)

        def fake_api_call(fournisseur, endpoint, fn, **kwargs):
            return {"status": "ZERO_RESULTS", "results": []}

        io.call = fake_api_call
        result = c.collect(Company(nom="Inconnue", url=""))
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# §9.9e — GbpCollector._parse_place
# ---------------------------------------------------------------------------

class TestGbpParse:
    def test_verified_true_si_operational(self):
        data = {"status": "OK", "results": [{"business_status": "OPERATIONAL", "photos": [{"photo_reference": "abc"}]}]}
        assert GbpCollector._parse_place(data) == {"verified": True, "has_photos": True}

    def test_verified_false_si_closed(self):
        data = {"status": "OK", "results": [{"business_status": "CLOSED_PERMANENTLY", "photos": []}]}
        r = GbpCollector._parse_place(data)
        assert r["verified"] is False
        assert r["has_photos"] is False

    def test_aucun_resultat_retourne_false(self):
        assert GbpCollector._parse_place({"status": "ZERO_RESULTS", "results": []}) == {"verified": False, "has_photos": False}

    def test_stub_sans_api_io(self):
        c = GbpCollector()
        result = c.collect(Company(nom="Test", url=""))
        assert result["verified"] is None
        assert result["has_photos"] is None


# ---------------------------------------------------------------------------
# §9.9f — SeoCollector._detect_local_keywords
# ---------------------------------------------------------------------------

class TestSeoKeywords:
    def test_region_dans_texte(self):
        assert SeoCollector._detect_local_keywords("chauffage québec installation", "Québec, QC") is True

    def test_region_absente(self):
        assert SeoCollector._detect_local_keywords("chauffage installation", "Genève, CH") is False

    def test_region_none_retourne_false(self):
        assert SeoCollector._detect_local_keywords("québec chauffage", None) is False

    def test_region_vide_retourne_false(self):
        assert SeoCollector._detect_local_keywords("québec chauffage", "") is False

    def test_mots_courts_ignores(self):
        # "QC" fait 2 chars → filtré. Seule ville longue compte.
        assert SeoCollector._detect_local_keywords("chauffage QC installation", "Montréal, QC") is False

    def test_stub_sans_website_signals(self):
        c = SeoCollector()
        result = c.collect(Company(nom="Test", url="", region="Québec, QC"))
        assert result["local_keywords"] is None

    def test_avec_website_signals_injectes(self):
        c = SeoCollector()
        c._website_signals = {"_seo_text": "chauffage climatisation québec"}
        result = c.collect(Company(nom="Test", url="", region="Québec, QC"))
        assert result["local_keywords"] is True


# ---------------------------------------------------------------------------
# §9.9g — Pipeline injecte _website_signals après collecte website
# ---------------------------------------------------------------------------

class TestPipelineInjection:
    def test_seo_recoit_website_signals(self):
        from diagnostic.config import load_rubrique
        from diagnostic.pipeline import DiagnosticPipeline

        seo = SeoCollector()
        social = SocialCollector()
        website = WebsiteCollector(use_cache=False)

        pipeline = DiagnosticPipeline(
            collectors=[website, seo, social],
            rubrique=load_rubrique(),
        )

        html = "<html><head><title>Climatisation Québec</title></head><body></body></html>"
        resp = MagicMock()
        resp.text = html
        resp.url = "https://exemple.ca"
        resp.status_code = 200
        resp.headers.get = lambda k, default=None: None

        with patch("requests.get", return_value=resp):
            diag = pipeline.run(Company(nom="Test HVAC", url="https://exemple.ca", region="Québec, QC"))

        # SeoCollector a bien reçu les signaux website et analysé le texte
        assert diag.signaux["seo"]["local_keywords"] is not None
        # SocialCollector a bien reçu les signaux
        assert "plateformes_mentionnees" in diag.signaux["social"]

    def test_seo_et_social_sans_website_dans_pipeline(self):
        """Si WebsiteCollector absent, _website_signals reste None → stub."""
        from diagnostic.config import load_rubrique
        from diagnostic.pipeline import DiagnosticPipeline

        seo = SeoCollector()
        social = SocialCollector()

        pipeline = DiagnosticPipeline(
            collectors=[seo, social],
            rubrique=load_rubrique(),
        )
        diag = pipeline.run(Company(nom="Test", url=""))
        assert diag.signaux["seo"]["local_keywords"] is None
        # None = non observé : sans WebsiteCollector, le site n'a jamais été
        # consulté, donc rien ne peut être affirmé de sa présence sociale.
        assert diag.signaux["social"]["plateformes_mentionnees"] is None

    def test_seo_local_keywords_true_avec_region_dans_titre(self):
        """Intégration : company.region présente dans le titre → local_keywords=True."""
        from diagnostic.config import load_rubrique
        from diagnostic.pipeline import DiagnosticPipeline

        pipeline = DiagnosticPipeline(
            collectors=[WebsiteCollector(use_cache=False), SeoCollector()],
            rubrique=load_rubrique(),
        )
        html = "<html><head><title>HVAC Montréal — Installation</title></head><body></body></html>"
        resp = MagicMock()
        resp.text = html
        resp.url = "https://exemple.ca"
        resp.status_code = 200
        resp.headers.get = lambda k, default=None: None
        with patch("requests.get", return_value=resp):
            diag = pipeline.run(Company(nom="Test", url="https://exemple.ca", region="Montréal, QC"))
        assert diag.signaux["seo"]["local_keywords"] is True


# ---------------------------------------------------------------------------
# RÉGRESSION — échec technique Places ≠ observation
#
# L'API Google Places répond HTTP 200 avec `results: []` quand la clé est
# absente (REQUEST_DENIED), le quota dépassé, ou la requête invalide. Ces
# réponses étaient interprétées comme « aucune fiche d'établissement », ce qui
# fabriquait deux failles de gravité HAUTE pour toute entreprise diagnostiquée
# dans l'état actuel du dépôt (aucune clé disponible) — dont celle qui
# alimentait l'accroche commerciale.
#
# Ces tests exercent le CHEMIN DE PRODUCTION RÉEL (api_io construit et injecté),
# pas des collecteurs isolés : c'est là que le défaut vivait, et les tests
# unitaires précédents ne le voyaient pas.
# ---------------------------------------------------------------------------

class TestPlacesEchecTechniqueNestPasUneObservation:
    def test_reponse_exploitable_distingue_les_statuts(self):
        from diagnostic.collectors._places import reponse_exploitable

        assert reponse_exploitable({"status": "OK", "results": [{}]}) is True
        assert reponse_exploitable({"status": "ZERO_RESULTS", "results": []}) is True
        for statut in ("REQUEST_DENIED", "OVER_QUERY_LIMIT", "INVALID_REQUEST",
                       "UNKNOWN_ERROR"):
            assert reponse_exploitable({"status": statut, "results": []}) is False, statut
        # Réponse malformée ou sans statut : on s'abstient.
        assert reponse_exploitable({"results": []}) is False
        assert reponse_exploitable(None) is False

    def test_gbp_request_denied_donne_none_pas_false(self):
        deny = {"status": "REQUEST_DENIED", "results": [],
                "error_message": "The provided API key is invalid."}
        assert GbpCollector._parse_place(deny) == {"verified": None, "has_photos": None}

    def test_zero_results_reste_une_observation_negative(self):
        """Contre-épreuve : une vraie absence de fiche doit rester un échec."""
        vide = {"status": "ZERO_RESULTS", "results": []}
        assert GbpCollector._parse_place(vide) == {"verified": False, "has_photos": False}

    def test_chemin_de_production_sans_cle_ne_fabrique_aucune_faille(self):
        """Assemblage réel : _build_pipeline(api_io) + Places qui refuse la clé.

        C'est le test qui manquait. Les précédents construisaient les
        collecteurs sans api_io (donc stub None) ou fabriquaient les signaux à
        la main — ils ne pouvaient pas voir le défaut, qui n'existait que
        lorsqu'un api_io était réellement injecté et que l'appel réseau partait.
        """
        import run_diagnostic
        from diagnostic.api_io import ApiIO

        deny = MagicMock()
        deny.json.return_value = {"status": "REQUEST_DENIED", "results": []}
        deny.status_code = 200
        deny.text = ""
        deny.url = "https://maps.googleapis.com/"
        deny.headers.get = lambda k, default=None: default

        with patch("requests.get", return_value=deny):
            api_io = ApiIO({"fournisseurs": {}}, Path("/tmp/_ledger_test.jsonl"))
            pipeline = run_diagnostic._build_pipeline(api_io=api_io)
            diag = pipeline.run(Company(nom="Test HVAC", url="https://exemple.test"))

        assert diag.signaux["gbp"]["verified"] is None
        assert diag.signaux["reviews"]["count"] is None
        assert diag.scores["presence_locale"] is None
        assert diag.scores["avis"] is None

        preuves = " | ".join(f.preuve for f in diag.failles)
        assert "établissement" not in preuves.lower(), (
            f"faille fabriquée depuis un refus d'authentification : {preuves}"
        )
        assert "avis" not in preuves.lower(), (
            f"faille fabriquée depuis un refus d'authentification : {preuves}"
        )
