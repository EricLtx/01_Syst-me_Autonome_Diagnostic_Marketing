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


def test_pipeline_stubs_signalent_zero_pour_gbp_avis():
    """Les stubs GBP/avis retournent None → la rubrique génère des failles."""
    company = Company(nom="Test HVAC", url="https://exemple-hvac.ca")
    with patch("requests.get", return_value=_fake_response()):
        diag = _make_pipeline().run(company)

    dims_failles = {f.dimension for f in diag.failles}
    assert "presence_locale" in dims_failles, "GBP stub doit produire une faille presence_locale"
    assert "avis" in dims_failles, "Reviews stub doit produire une faille avis"


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
