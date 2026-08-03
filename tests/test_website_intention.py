"""
test_website_intention.py — extension de WebsiteCollector pour l'axe intention
(ADR 0004, Lots 1 et 2).

Couvre :
  - offre_detectee : trois états (True/False/None), même discipline anti-fuite
    que mentions_offre (ADR 0003, anti-fuite B5).
  - Escalade Lot 2 : UN SEUL appel réseau de plus vers la page carrières,
    déclenché uniquement quand offre_detectee est vrai ET qu'un lien
    carrières est visible sur la page d'accueil — jamais systématique.
  - Extraction de date (balise <time>, repli Last-Modified) ou None si rien
    n'est extractible (un événement non daté est écarté en amont, D2).

Aucun réseau réel. Le chemin `api_io` est exercé via un double minimal
(pas de mock du bus complet) pour vérifier le nombre d'appels et le cache_key.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from diagnostic.collectors.website import WebsiteCollector
from diagnostic.models import Company

HOMEPAGE_AVEC_RECRUTEMENT = """
<html><head><title>Chauffage Test</title></head>
<body>
<h1>Chauffage Test</h1>
<p>Installation de thermopompe et climatisation.</p>
<p><a href="/carrieres">Carrières</a> : nous recrutons ! Rejoignez notre équipe.</p>
<p>© 2024 Chauffage Test</p>
</body></html>
"""

HOMEPAGE_SANS_RECRUTEMENT = """
<html><head><title>Chauffage Test</title></head>
<body>
<h1>Chauffage Test</h1>
<p>Installation de thermopompe et climatisation.</p>
<p>© 2024 Chauffage Test</p>
</body></html>
"""

CARRIERES_AVEC_DATE = '<html><body><time datetime="2026-07-20">Offre publiée</time></body></html>'
CARRIERES_SANS_DATE = "<html><body><p>Rejoignez notre équipe.</p></body></html>"

VOCABULAIRE = ["nous recrutons", "offre d'emploi"]


def _resp(text: str, url: str = "https://exemple.test/") -> MagicMock:
    resp = MagicMock()
    resp.text = text
    resp.url = url
    resp.status_code = 200
    resp.headers = {}
    return resp


class _FakeApiIO:
    """Double minimal : exécute la fonction, journalise les cache_key demandées."""

    def __init__(self):
        self.appels: list[str | None] = []

    def call(self, fournisseur, endpoint, fn, cache_key=None, **kw):
        self.appels.append(cache_key)
        return fn()


# ---------------------------------------------------------------------------
# offre_detectee : trois états
# ---------------------------------------------------------------------------

class TestOffreDetecteeTroisEtats:
    def test_vocabulaire_non_configure_donne_none(self):
        """Anti-fuite B5 : pas de vocabulaire injecté ⇒ None, jamais False."""
        with patch("requests.get", return_value=_resp(HOMEPAGE_AVEC_RECRUTEMENT)):
            c = WebsiteCollector(use_cache=False)  # vocabulaire_intention=None (défaut)
            result = c.collect(Company(nom="Test", url="https://exemple.test/"))
        assert result["offre_detectee"] is None

    def test_vocabulaire_configure_et_present_donne_true(self):
        with patch("requests.get", return_value=_resp(HOMEPAGE_AVEC_RECRUTEMENT)):
            c = WebsiteCollector(use_cache=False, vocabulaire_intention=VOCABULAIRE)
            result = c.collect(Company(nom="Test", url="https://exemple.test/"))
        assert result["offre_detectee"] is True

    def test_vocabulaire_configure_et_absent_donne_false(self):
        """Observation NÉGATIVE réelle : le site a été lu, aucun mot ne matche."""
        with patch("requests.get", return_value=_resp(HOMEPAGE_SANS_RECRUTEMENT)):
            c = WebsiteCollector(use_cache=False, vocabulaire_intention=VOCABULAIRE)
            result = c.collect(Company(nom="Test", url="https://exemple.test/"))
        assert result["offre_detectee"] is False

    def test_site_injoignable_ne_produit_pas_la_cle(self):
        """Échec technique : pas de clé du tout ⇒ _resolve() renverra None
        automatiquement, jamais une valeur fabriquée."""
        with patch("requests.get", side_effect=Exception("boom")):
            c = WebsiteCollector(use_cache=False, vocabulaire_intention=VOCABULAIRE)
            result = c.collect(Company(nom="Test", url="https://exemple.test/"))
        assert "offre_detectee" not in result
        assert result["reachable"] is False


# ---------------------------------------------------------------------------
# Escalade Lot 2 : un seul appel de plus, jamais systématique
# ---------------------------------------------------------------------------

class TestEscaladeCarrieres:
    def test_aucune_escalade_si_pas_de_recrutement_detecte(self):
        """offre_detectee=False ⇒ aucun appel vers une page carrières."""
        api_io = _FakeApiIO()
        with patch("requests.get", return_value=_resp(HOMEPAGE_SANS_RECRUTEMENT)):
            c = WebsiteCollector(use_cache=True, api_io=api_io, vocabulaire_intention=VOCABULAIRE)
            result = c.collect(Company(nom="Test", url="https://exemple.test/"))
        assert result["offre_detectee_date"] is None
        # Homepage + sitemap.xml (déjà existant, indépendant de l'intention) :
        # aucun appel de plus pour la page carrières.
        assert len(api_io.appels) == 2
        assert not any(k and "carrieres" in k for k in api_io.appels)

    def test_aucune_escalade_si_pas_de_lien_carrieres(self):
        """Recrutement détecté mais aucun lien carrières visible ⇒ pas d'escalade."""
        homepage_sans_lien = HOMEPAGE_AVEC_RECRUTEMENT.replace(
            '<a href="/carrieres">Carrières</a> : ', ""
        )
        api_io = _FakeApiIO()
        with patch("requests.get", return_value=_resp(homepage_sans_lien)):
            c = WebsiteCollector(use_cache=True, api_io=api_io, vocabulaire_intention=VOCABULAIRE)
            result = c.collect(Company(nom="Test", url="https://exemple.test/"))
        assert result["offre_detectee"] is True
        assert result["offre_detectee_date"] is None
        assert len(api_io.appels) == 2  # homepage + sitemap, jamais de page carrières
        assert not any(k and "carrieres" in k for k in api_io.appels)

    def test_escalade_unique_extrait_la_date_de_la_page_carrieres(self):
        """Un lien carrières + recrutement détecté ⇒ UN appel de plus, date extraite."""
        api_io = _FakeApiIO()

        def fake_get(url, **kw):
            return _resp(CARRIERES_AVEC_DATE, url) if "carrieres" in url else _resp(
                HOMEPAGE_AVEC_RECRUTEMENT, url
            )

        with patch("requests.get", side_effect=fake_get):
            c = WebsiteCollector(use_cache=True, api_io=api_io, vocabulaire_intention=VOCABULAIRE)
            result = c.collect(Company(nom="Test", url="https://exemple.test/"))

        assert result["offre_detectee"] is True
        assert result["offre_detectee_date"] == "2026-07-20"
        # Homepage + sitemap + UNE SEULE page carrières : jamais plus.
        assert len(api_io.appels) == 3
        assert sum(1 for k in api_io.appels if k and "carrieres" in k) == 1

    def test_page_carrieres_sans_date_donne_none(self):
        """Page carrières fetchée mais aucune date extractible ⇒ événement
        écarté en amont (D2), pas de date fabriquée."""
        api_io = _FakeApiIO()

        def fake_get(url, **kw):
            return _resp(CARRIERES_SANS_DATE, url) if "carrieres" in url else _resp(
                HOMEPAGE_AVEC_RECRUTEMENT, url
            )

        with patch("requests.get", side_effect=fake_get):
            c = WebsiteCollector(use_cache=True, api_io=api_io, vocabulaire_intention=VOCABULAIRE)
            result = c.collect(Company(nom="Test", url="https://exemple.test/"))
        assert result["offre_detectee_date"] is None

    def test_echec_reseau_sur_la_page_carrieres_donne_none(self):
        """Échec technique du SEUL appel supplémentaire ⇒ None, pas de plantage."""
        api_io = _FakeApiIO()

        def fake_get(url, **kw):
            if "carrieres" in url:
                raise Exception("boom")
            return _resp(HOMEPAGE_AVEC_RECRUTEMENT, url)

        with patch("requests.get", side_effect=fake_get):
            c = WebsiteCollector(use_cache=True, api_io=api_io, vocabulaire_intention=VOCABULAIRE)
            result = c.collect(Company(nom="Test", url="https://exemple.test/"))
        assert result["offre_detectee"] is True
        assert result["offre_detectee_date"] is None

    def test_cache_key_de_la_page_carrieres_est_son_url(self):
        """Politesse : le fetch supplémentaire passe par le bus avec cache_key
        (même convention que _try_sitemap)."""
        api_io = _FakeApiIO()

        def fake_get(url, **kw):
            return _resp(CARRIERES_AVEC_DATE, url) if "carrieres" in url else _resp(
                HOMEPAGE_AVEC_RECRUTEMENT, url
            )

        with patch("requests.get", side_effect=fake_get):
            c = WebsiteCollector(use_cache=True, api_io=api_io, vocabulaire_intention=VOCABULAIRE)
            c.collect(Company(nom="Test", url="https://exemple.test/"))

        cache_keys_avec_carrieres = [k for k in api_io.appels if k and "carrieres" in k]
        assert len(cache_keys_avec_carrieres) == 1
        assert cache_keys_avec_carrieres[0].startswith("https://exemple.test/carrieres")
