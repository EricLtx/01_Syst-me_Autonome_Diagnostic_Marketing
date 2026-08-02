"""
test_j1_smoke.py — vérifie que le câblage du pipeline J1 fonctionne end-to-end.

Aucune dépendance réseau : requests.get est mocké.
Aucune clé API requise : la synthèse tombe sur le repli déterministe.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from diagnostic.collectors.base import Collector
from diagnostic.collectors.gbp import GbpCollector
from diagnostic.collectors.reviews import ReviewsCollector
from diagnostic.collectors.seo import SeoCollector
from diagnostic.collectors.social import SocialCollector
from diagnostic.collectors.website import WebsiteCollector
from diagnostic.config import load_rubrique
from diagnostic.models import Company, Diagnostic
from diagnostic.pipeline import DiagnosticPipeline

# HTML minimal qui satisfait plusieurs checks de la rubrique
FAKE_HTML = """
<html>
<head>
  <title>Chauffage Tremblay — Climatisation Québec</title>
  <meta name="description" content="Installation pompe à chaleur Québec">
  <meta name="viewport" content="width=device-width">
</head>
<body>
  <img src="logo.png" alt="logo Tremblay">
  <img src="img1.jpg"><img src="img2.jpg"><img src="img3.jpg">
  <a href="tel:5141234567">Appelez-nous</a>
  <p>Installation de thermopompes, chauffage et climatisation HVAC.</p>
  <p>© 2024 Chauffage Tremblay</p>
</body>
</html>
"""


def _fake_response(url: str = "https://exemple-hvac.ca") -> MagicMock:
    resp = MagicMock()
    resp.text = FAKE_HTML
    resp.url = url
    resp.status_code = 200
    return resp


def _make_pipeline() -> DiagnosticPipeline:
    return DiagnosticPipeline(
        collectors=[
            WebsiteCollector(use_cache=False),
            GbpCollector(),
            ReviewsCollector(),
            SeoCollector(),
            SocialCollector(),
        ],
        rubrique=load_rubrique(),
    )


def test_pipeline_retourne_diagnostic():
    """Le pipeline produit un Diagnostic complet avec tous les champs attendus."""
    company = Company(nom="Chauffage Tremblay", url="https://exemple-hvac.ca", region="Québec, QC")
    with patch("requests.get", return_value=_fake_response()):
        diag = _make_pipeline().run(company)

    assert isinstance(diag, Diagnostic)
    assert diag.entreprise.nom == "Chauffage Tremblay"
    assert "global" in diag.scores
    assert 0 <= diag.scores["global"] <= 100
    assert isinstance(diag.failles, list)
    assert diag.mini_audit
    assert diag.accroche
    assert diag.meta["collecteurs"] == ["website", "gbp", "reviews", "seo", "social"]


def test_pipeline_score_coherent_avec_html():
    """Les signaux website bien remplis donnent un score site_web > 0."""
    company = Company(nom="Chauffage Tremblay", url="https://exemple-hvac.ca")
    with patch("requests.get", return_value=_fake_response()):
        diag = _make_pipeline().run(company)

    assert diag.scores["site_web"] > 0, "Le site HTTPS avec titre et contact doit scorer"


def test_pipeline_stubs_ne_fabriquent_aucune_faille():
    """Un signal NON OBSERVÉ ne produit ni faille ni score (invariant J1 n°4).

    Ce test assertait auparavant l'inverse : « le stub GBP DOIT produire une
    faille presence_locale ». Il verrouillait un défaut, pas un comportement.
    Sans clé Google Places, gbp/reviews renvoient None ; le moteur émettait
    alors des failles dont le libellé avouait « à confirmer en J3 », et les
    dimensions presence_locale + avis (45 % de la pondération) valaient 0/100
    pour tous les prospects. Mesuré : trois entreprises radicalement
    différentes recevaient la MÊME accroche, et une entreprise au site
    irréprochable plafonnait à 27,5/100.

    « Je n'ai pas regardé » n'est pas « c'est mauvais » : c'est la règle que
    ce test protège désormais.
    """
    company = Company(nom="Test HVAC", url="https://exemple-hvac.ca")
    with patch("requests.get", return_value=_fake_response()):
        diag = _make_pipeline().run(company)

    dims_failles = {f.dimension for f in diag.failles}
    assert "presence_locale" not in dims_failles, (
        "gbp est en mode stub (None) : aucune faille ne doit être affirmée"
    )
    assert "avis" not in dims_failles, (
        "reviews est en mode stub (None) : aucune faille ne doit être affirmée"
    )

    # Une dimension non observée n'a pas de score — elle ne vaut pas 0.
    assert diag.scores["presence_locale"] is None
    assert diag.scores["avis"] is None

    # ... et elle sort du calcul global au lieu de le tirer vers le bas.
    assert diag.scores["_couverture"] < 1.0
    assert diag.scores["global"] is not None

    # Aucune faille émise ne peut porter une mention d'incertitude : une
    # faille est une affirmation adossée à un fait observé.
    for f in diag.failles:
        assert "confirmer" not in f.preuve.lower(), (
            f"Faille non adossée à un fait observé : {f.preuve!r}"
        )


def test_collecteur_echec_isole():
    """Un collecteur qui plante ne fait pas planter le pipeline (principe #2)."""

    class CollecteurBrise(Collector):
        name = "brise"

        def collect(self, company: Company) -> dict[str, Any]:
            raise RuntimeError("Simuler une panne réseau")

    company = Company(nom="Test", url="https://exemple-hvac.ca")
    with patch("requests.get", return_value=_fake_response()):
        pipeline = DiagnosticPipeline(
            collectors=[WebsiteCollector(use_cache=False), CollecteurBrise()],
            rubrique=load_rubrique(),
        )
        diag = pipeline.run(company)

    assert "_erreur" in diag.signaux["brise"]
    assert "Simuler une panne réseau" in diag.signaux["brise"]["_erreur"]
    assert isinstance(diag, Diagnostic)


def test_pipeline_sans_url():
    """Une entreprise sans URL ne fait pas crasher le pipeline."""
    company = Company(nom="Sans Site", url="")
    diag = _make_pipeline().run(company)

    assert isinstance(diag, Diagnostic)
    assert diag.signaux["website"]["reachable"] is False


def test_load_rubrique_charge_persona1():
    """load_rubrique() trouve le fichier YAML dans knowledge/."""
    rubrique = load_rubrique(persona=1)
    assert "dimensions" in rubrique
    assert "site_web" in rubrique["dimensions"]
    assert "seuil_faille" not in rubrique  # supprimé : un gap par check échoué, pas de seuil par dimension
