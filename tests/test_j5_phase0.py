"""
test_j5_phase0.py — §13 de la spec J5.

Vérifie :
- FicheProspect accepte signal_chaud et accroche (rétro-compatible)
- diagnostic_to_fiche() dérive signal_chaud depuis les failles
- Contrat JSON de Diagnostic préservé (to_dict() intact)
- vault_runner propage signal_chaud et accroche via update_frontmatter
- api_pricing.yaml contient bien releve_le et budgets:
"""

from __future__ import annotations

from datetime import date

import pytest
import yaml

from diagnostic.models import Company, Diagnostic, Gap
from diagnostic.serializers import diagnostic_to_fiche
from diagnostic.vault_schema import FicheProspect


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _fiche_base() -> FicheProspect:
    return FicheProspect(
        persona=1,
        marche="quebec",
        statut="valide",
        nom="Test HVAC",
        date_creation=date.today(),
    )


def _diag(failles: list[Gap] | None = None, accroche: str = "") -> Diagnostic:
    return Diagnostic(
        entreprise=Company(nom="Test HVAC", url="https://test.ca"),
        scores={"global": 40.0, "web": 30.0},
        failles=failles or [],
        accroche=accroche,
        mini_audit="Mini audit test.",
    )


# ---------------------------------------------------------------------------
# §13.1 — FicheProspect : nouveaux champs rétro-compatibles
# ---------------------------------------------------------------------------

class TestFicheProspectJ5Champs:
    def test_signal_chaud_optionnel(self):
        fiche = _fiche_base()
        assert fiche.signal_chaud is None

    def test_accroche_optionnel(self):
        fiche = _fiche_base()
        assert fiche.accroche is None

    def test_signal_chaud_accepte_string(self):
        fiche = FicheProspect(
            persona=1, marche="quebec", statut="valide",
            nom="X", date_creation=date.today(),
            signal_chaud="Absence totale de site web",
        )
        assert fiche.signal_chaud == "Absence totale de site web"

    def test_fiche_sans_signal_chaud_valide(self):
        """Les fiches J4 existantes (sans signal_chaud) restent valides."""
        raw = {
            "type": "prospect", "persona": 1, "marche": "quebec",
            "statut": "valide", "nom": "Old HVAC",
            "date_creation": date.today().isoformat(),
        }
        fiche = FicheProspect.model_validate(raw)
        assert fiche.signal_chaud is None
        assert fiche.accroche is None

    def test_model_fields_contient_signal_chaud_et_accroche(self):
        assert "signal_chaud" in FicheProspect.model_fields
        assert "accroche" in FicheProspect.model_fields


# ---------------------------------------------------------------------------
# §13.2 — diagnostic_to_fiche() : dérivation de signal_chaud
# ---------------------------------------------------------------------------

class TestDiagnosticToFicheJ5:
    def test_signal_chaud_depuis_faille_haute(self):
        gaps = [
            Gap(dimension="web", gravite="haute", preuve="Pas de site HTTPS"),
            Gap(dimension="seo", gravite="moyenne", preuve="Aucun mot-clé local"),
        ]
        fiche = diagnostic_to_fiche(_diag(failles=gaps, accroche="Accroche test"), _fiche_base())
        assert fiche.signal_chaud == "Pas de site HTTPS"

    def test_signal_chaud_premiere_faille_si_aucune_haute(self):
        gaps = [
            Gap(dimension="seo", gravite="moyenne", preuve="Aucun mot-clé local"),
            Gap(dimension="social", gravite="basse", preuve="Peu de présence"),
        ]
        fiche = diagnostic_to_fiche(_diag(failles=gaps, accroche="Accroche test"), _fiche_base())
        assert fiche.signal_chaud == "Aucun mot-clé local"

    def test_signal_chaud_depuis_accroche_si_aucune_faille(self):
        fiche = diagnostic_to_fiche(_diag(failles=[], accroche="Fort potentiel"), _fiche_base())
        assert fiche.signal_chaud == "Fort potentiel"

    def test_accroche_propagee(self):
        fiche = diagnostic_to_fiche(
            _diag(failles=[Gap("web", "haute", "Pas de HTTPS")], accroche="Accroche email"),
            _fiche_base(),
        )
        assert fiche.accroche == "Accroche email"

    def test_accroche_vide_devient_none(self):
        fiche = diagnostic_to_fiche(_diag(failles=[], accroche=""), _fiche_base())
        assert fiche.accroche is None

    def test_champs_existants_toujours_presents(self):
        gaps = [Gap("web", "haute", "Pas de HTTPS")]
        fiche = diagnostic_to_fiche(_diag(failles=gaps), _fiche_base())
        assert fiche.score_global is not None
        assert isinstance(fiche.gaps_majeurs, list)
        assert fiche.date_diagnostic == date.today()

    def test_signal_chaud_priorite_haute_sur_moyenne(self):
        """La faille haute doit gagner même si une faille moyenne est en premier."""
        gaps = [
            Gap(dimension="seo", gravite="moyenne", preuve="SEO moyen"),
            Gap(dimension="web", gravite="haute", preuve="HTTPS manquant"),
        ]
        fiche = diagnostic_to_fiche(_diag(failles=gaps), _fiche_base())
        assert fiche.signal_chaud == "HTTPS manquant"


# ---------------------------------------------------------------------------
# §13.3 — Contrat JSON Diagnostic préservé
# ---------------------------------------------------------------------------

class TestDiagnosticContratJSON:
    def test_to_dict_na_pas_signal_chaud(self):
        """Diagnostic.to_dict() ne contient pas signal_chaud (contrat préservé)."""
        diag = _diag(failles=[Gap("web", "haute", "Proof")])
        d = diag.to_dict()
        assert "signal_chaud" not in d

    def test_to_json_contrat_inchange(self):
        diag = _diag(failles=[Gap("web", "haute", "Proof")])
        import json
        d = json.loads(diag.to_json())
        assert set(d.keys()) == {"entreprise", "signaux", "scores", "failles", "accroche", "mini_audit", "meta"}

    def test_diagnostic_naccroche_pas_signal_chaud(self):
        diag = _diag()
        assert not hasattr(diag, "signal_chaud")


# ---------------------------------------------------------------------------
# §13.4 — api_pricing.yaml : releve_le et budgets présents
# ---------------------------------------------------------------------------

class TestApiPricingJ5:
    def test_releve_le_present(self):
        from pathlib import Path
        pricing_path = Path(__file__).resolve().parent.parent / "knowledge" / "api_pricing.yaml"
        data = yaml.safe_load(pricing_path.read_text(encoding="utf-8"))
        assert "releve_le" in data

    def test_budgets_section_presente(self):
        from pathlib import Path
        pricing_path = Path(__file__).resolve().parent.parent / "knowledge" / "api_pricing.yaml"
        data = yaml.safe_load(pricing_path.read_text(encoding="utf-8"))
        assert "budgets" in data

    def test_budgets_serp_present(self):
        from pathlib import Path
        pricing_path = Path(__file__).resolve().parent.parent / "knowledge" / "api_pricing.yaml"
        data = yaml.safe_load(pricing_path.read_text(encoding="utf-8"))
        assert "serp" in data["budgets"]
        assert "unites_max" in data["budgets"]["serp"]

    def test_budgets_apollo_present(self):
        from pathlib import Path
        pricing_path = Path(__file__).resolve().parent.parent / "knowledge" / "api_pricing.yaml"
        data = yaml.safe_load(pricing_path.read_text(encoding="utf-8"))
        assert "apollo" in data["budgets"]
        assert "unites_max" in data["budgets"]["apollo"]


# ---------------------------------------------------------------------------
# §13.5 — vault_runner propage signal_chaud et accroche
# ---------------------------------------------------------------------------

class TestVaultRunnerPropagation:
    def test_update_frontmatter_reçoit_signal_chaud_accroche(self, tmp_path):
        """vault_runner appelle update_frontmatter avec signal_chaud et accroche."""
        from unittest.mock import MagicMock, patch, call
        from pathlib import Path

        vault_path = tmp_path / "vault"
        (vault_path / "10-Prospects" / "persona1-quebec").mkdir(parents=True)

        fiche = FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="Tremblay HVAC", date_creation=date.today(),
            site_web="https://tremblay.ca",
        )

        from diagnostic.vault_io import VaultIO
        io = VaultIO(vault_path)
        fiche_path = io.write_fiche(fiche)

        # Pipeline qui retourne un diagnostic avec une faille haute
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = Diagnostic(
            entreprise=Company(nom="Tremblay HVAC", url="https://tremblay.ca"),
            scores={"global": 35.0},
            failles=[Gap("web", "haute", "Aucun site HTTPS")],
            accroche="Bonjour — j'ai noté l'absence de HTTPS.",
            mini_audit="Mini audit.",
        )

        from diagnostic.vault_runner import run_vault_mode
        result = run_vault_mode(vault_path, pipeline=mock_pipeline)

        assert result["ok"] == ["Tremblay HVAC"]
        fiche_maj = io.read_fiche(fiche_path)
        assert fiche_maj.signal_chaud == "Aucun site HTTPS"
        assert fiche_maj.accroche == "Bonjour — j'ai noté l'absence de HTTPS."
