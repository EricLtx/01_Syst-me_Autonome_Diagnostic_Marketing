"""
test_integration_vault.py — test d'intégration §8.6.

Critère : init-vault + 1 fiche decouvert + pipeline --out vault
          → fiche en diagnostique, rapport créé, wikilink valide, 2 lignes dans runs.log.

HTTP mocké (requests.get). Aucune clé API (synthèse déterministe).
Aucun réseau. Aucune base de données.
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
from diagnostic.config import load_rubrique
from diagnostic.pipeline import DiagnosticPipeline
from diagnostic.vault_init import init_vault
from diagnostic.vault_io import VaultIO
from diagnostic.vault_runner import run_vault_mode
from diagnostic.vault_schema import FicheProspect

# ---------------------------------------------------------------------------
# Outillage
# ---------------------------------------------------------------------------

FAKE_HTML = """
<html>
<head>
  <title>Chauffage Tremblay — Climatisation Québec</title>
  <meta name="description" content="Installation pompe à chaleur Québec">
  <meta name="viewport" content="width=device-width">
</head>
<body>
  <a href="tel:5141234567">Appelez-nous</a>
  <img src="logo.png" alt="logo Tremblay">
  <p>Installation de thermopompes HVAC.</p>
  <p>© 2024 Chauffage Tremblay</p>
</body>
</html>
"""


def _fake_response() -> MagicMock:
    resp = MagicMock()
    resp.text = FAKE_HTML
    resp.url = "https://exemple-hvac.ca"
    resp.status_code = 200
    return resp


def _test_pipeline() -> DiagnosticPipeline:
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


# ---------------------------------------------------------------------------
# §8.6 — Test d'intégration principal
# ---------------------------------------------------------------------------

class TestIntegrationVault:
    def test_pipeline_complet_une_fiche(self, tmp_path):
        """§8.6 : une fiche decouvert → diagnostique + rapport + journal."""
        vault = tmp_path / "vault"
        init_vault(vault)

        io = VaultIO(vault)
        fiche = FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Chauffage Tremblay",
            site_web="https://exemple-hvac.ca",
            date_creation="2026-06-09",
        )
        fiche_path = io.write_fiche(fiche)

        with patch("requests.get", return_value=_fake_response()):
            result = run_vault_mode(vault, _test_pipeline())

        # Résultat de l'orchestrateur
        assert "Chauffage Tremblay" in result["ok"]
        assert result["erreurs"] == []

        # Fiche en statut diagnostique
        fiche_finale = io.read_fiche(fiche_path)
        assert fiche_finale.statut == "diagnostique"

    def test_score_et_gaps_renseignes(self, tmp_path):
        vault = tmp_path / "vault"
        init_vault(vault)
        io = VaultIO(vault)
        fiche_path = io.write_fiche(FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="HVAC Test", site_web="https://exemple-hvac.ca",
            date_creation="2026-06-09",
        ))

        with patch("requests.get", return_value=_fake_response()):
            run_vault_mode(vault, _test_pipeline())

        fiche = io.read_fiche(fiche_path)
        assert fiche.score_global is not None
        assert 0 <= fiche.score_global <= 100
        assert isinstance(fiche.gaps_majeurs, list)
        assert fiche.date_diagnostic is not None

    def test_rapport_cree_et_wikilink_valide(self, tmp_path):
        """Le rapport existe dans 30-Diagnostics/ et le wikilink pointe dessus."""
        vault = tmp_path / "vault"
        init_vault(vault)
        io = VaultIO(vault)
        fiche_path = io.write_fiche(FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Climatisation Laval",
            site_web="https://exemple-hvac.ca",
            date_creation="2026-06-09",
        ))

        with patch("requests.get", return_value=_fake_response()):
            run_vault_mode(vault, _test_pipeline())

        fiche = io.read_fiche(fiche_path)
        wikilink = fiche.rapport
        assert wikilink is not None, "Le champ rapport ne doit pas être null après diagnostic"
        assert wikilink.startswith("[[30-Diagnostics/")
        assert wikilink.endswith("]]")

        # Le fichier référencé existe réellement
        chemin_interne = wikilink[2:-2]   # "30-Diagnostics/slug"
        rapport_fichier = vault / f"{chemin_interne}.md"
        assert rapport_fichier.exists(), f"Rapport introuvable : {rapport_fichier}"

        # Le rapport contient le nom de l'entreprise
        contenu = rapport_fichier.read_text(encoding="utf-8")
        assert "Climatisation Laval" in contenu

    def test_journal_contient_write_rapport_et_transition(self, tmp_path):
        """runs.log doit contenir au moins write_rapport et transition."""
        vault = tmp_path / "vault"
        init_vault(vault)
        io = VaultIO(vault)
        io.write_fiche(FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Thermo Expert",
            site_web="https://exemple-hvac.ca",
            date_creation="2026-06-09",
        ))

        with patch("requests.get", return_value=_fake_response()):
            run_vault_mode(vault, _test_pipeline())

        log_path = tmp_path / "runs.log"
        assert log_path.exists(), "runs.log absent après exécution"
        lignes = log_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lignes) >= 2, f"Attendu ≥ 2 lignes dans runs.log, trouvé {len(lignes)}"

        ops = [json.loads(l)["op"] for l in lignes]
        assert "write_rapport" in ops, "Opération write_rapport absente du journal"
        assert "transition" in ops,    "Opération transition absente du journal"

    def test_deux_fiches_traitees_independamment(self, tmp_path):
        """Deux fiches decouvert → deux fiches diagnostique, deux rapports."""
        vault = tmp_path / "vault"
        init_vault(vault)
        io = VaultIO(vault)
        for nom in ["Entreprise Alpha", "Entreprise Beta"]:
            io.write_fiche(FicheProspect(
                persona=1, marche="quebec", statut="decouvert",
                nom=nom, site_web="https://exemple-hvac.ca",
                date_creation="2026-06-09",
            ))

        with patch("requests.get", return_value=_fake_response()):
            result = run_vault_mode(vault, _test_pipeline())

        assert len(result["ok"]) == 2
        assert result["erreurs"] == []
        # Les deux fiches sont passées à diagnostique
        for _, fiche in io.query(statut="diagnostique"):
            assert fiche.rapport is not None

    def test_fiche_sans_url_passe_diagnostique_score_nul(self, tmp_path):
        """Une fiche sans URL passe quand même à diagnostique avec un score nul.
        WebsiteCollector retourne reachable=False ; le pipeline ne lève pas."""
        vault = tmp_path / "vault"
        init_vault(vault)
        io = VaultIO(vault)
        fiche_path = io.write_fiche(FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Sans Site HVAC", site_web=None,
            date_creation="2026-06-09",
        ))

        # Pas de mock réseau — WebsiteCollector(use_cache=False) retourne reachable=False
        result = run_vault_mode(vault, _test_pipeline())

        # Pas d'erreur fatale : le pipeline gère l'absence d'URL
        assert "Sans Site HVAC" in result["ok"]
        fiche = io.read_fiche(fiche_path)
        assert fiche.statut == "diagnostique"


# ---------------------------------------------------------------------------
# §8.8 — La suite J1 n'est pas cassée (test de régression)
# ---------------------------------------------------------------------------

def test_run_diagnostic_mode_standard_non_casse():
    """Mode --out json (défaut) : --nom et --url toujours fonctionnels."""
    from diagnostic.models import Company, Diagnostic
    from diagnostic.pipeline import DiagnosticPipeline

    company = Company(nom="Test HVAC", url="https://exemple-hvac.ca")
    pipeline = _test_pipeline()

    with patch("requests.get", return_value=_fake_response()):
        diag = pipeline.run(company)

    assert isinstance(diag, Diagnostic)
    assert diag.entreprise.nom == "Test HVAC"
    assert 0 <= diag.scores["global"] <= 100
