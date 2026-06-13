"""
test_preflight.py — tests 9-12, 14 de la spec J5 §7.

Test  9 : NO-GO — clés absentes / tarifs placeholder / budget nul → bloquant(s) → NO-GO
Test 10 : GO simulé — env complet + budgets + tarifs → verdict GO
Test 11 : GOOGLE_PLACES_API_KEY et ANTHROPIC_API_KEY absents = warn (pas bloquant)
Test 12 : garde_fous_bus — modules J5 sans import requests ni anthropic au niveau module
Test 14 : régression — les tests J1–J4 existants continuent de passer (vérification AST imports)
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from diagnostic.preflight import (
    Check,
    _ast_module_importe,
    _check_budgets,
    _check_cles_api,
    _check_garde_fous_bus,
    _check_schema_export,
    _check_tarifs_reels,
    _check_vault_initialise,
    _check_cache_hors_vault,
    verdict_global,
    formater_rapport,
)

# ---------------------------------------------------------------------------
# Fixtures helpers
# ---------------------------------------------------------------------------

def _pricing_yaml(tmp_path: Path, releve="2025-01-01", serp=0.01, apollo=0.02,
                  budget_serp=500, budget_apollo=50) -> Path:
    pricing = {
        "devise": "USD",
        "releve_le": releve,
        "fournisseurs": {
            "serp": {"unite": "requete", "endpoints": {
                "search": {"prix_par_unite": {"requetes": serp}},
            }},
            "apollo": {"unite": "credit", "endpoints": {
                "people_enrichment": {"prix_par_unite": {"credits": apollo}},
            }},
        },
        "budgets": {
            "serp": {"unites_max": {"requetes": budget_serp}},
            "apollo": {"unites_max": {"credits": budget_apollo}},
        },
    }
    p = tmp_path / "api_pricing.yaml"
    p.write_text(yaml.dump(pricing, allow_unicode=True), encoding="utf-8")
    return p


def _vault_init(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    for d in ["10-Prospects", "20-Rubrics", "30-Diagnostics", "90-Systeme"]:
        (vault / d).mkdir(parents=True)
    return vault


# ---------------------------------------------------------------------------
# Test 9 — NO-GO : clés absentes / tarifs placeholder / budget nul
# ---------------------------------------------------------------------------

class TestNoGo:
    def test_cles_obligatoires_absentes_bloquant(self):
        with patch.dict("os.environ", {}, clear=True):
            # Supprimer les clés si présentes
            env_sans_cles = {k: v for k, v in __import__("os").environ.items()
                             if k not in ("SERP_API_KEY", "APOLLO_API_KEY")}
            with patch("os.environ", env_sans_cles):
                checks = _check_cles_api()
        bloquants_ko = [c for c in checks if c.niveau == "bloquant" and not c.ok]
        assert len(bloquants_ko) >= 1

    def test_tarifs_placeholder_bloquant(self, tmp_path):
        pricing = _pricing_yaml(tmp_path, serp=0.0)  # 0.0 = placeholder
        checks = _check_tarifs_reels(pricing)
        assert any(not c.ok and c.niveau == "bloquant" for c in checks)

    def test_releve_le_absent_bloquant(self, tmp_path):
        pricing = _pricing_yaml(tmp_path, releve=None)
        checks = _check_tarifs_reels(pricing)
        releve_check = [c for c in checks if "releve_le" in c.message]
        assert any(not c.ok for c in releve_check)

    def test_budget_zero_bloquant(self, tmp_path):
        pricing = _pricing_yaml(tmp_path, budget_serp=0, budget_apollo=0)
        checks = _check_budgets(pricing)
        assert any(not c.ok and c.niveau == "bloquant" for c in checks)

    def test_verdict_no_go_si_un_bloquant_ko(self):
        checks = [
            Check("cles_api", "bloquant", False, "SERP_API_KEY absente"),
            Check("budgets", "warn", False, "warn seulement"),
        ]
        assert verdict_global(checks) is False

    def test_vault_non_initialise_bloquant(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()  # sans sous-dossiers
        checks = _check_vault_initialise(vault)
        assert any(not c.ok for c in checks)


# ---------------------------------------------------------------------------
# Test 10 — GO simulé : tout OK → verdict GO
# ---------------------------------------------------------------------------

class TestGo:
    def test_verdict_go_si_tous_bloquants_ok(self):
        checks = [
            Check("cles_api", "bloquant", True, "OK"),
            Check("tarifs_reels", "bloquant", True, "OK"),
            Check("budgets", "bloquant", True, "OK"),
            Check("tests_verts", "warn", False, "warn ko — pas bloquant"),
        ]
        assert verdict_global(checks) is True

    def test_tarifs_ok(self, tmp_path):
        pricing = _pricing_yaml(tmp_path, releve="2025-01-01", serp=0.005, apollo=0.01)
        checks = _check_tarifs_reels(pricing)
        assert all(c.ok for c in checks)

    def test_budgets_ok(self, tmp_path):
        pricing = _pricing_yaml(tmp_path, budget_serp=500, budget_apollo=50)
        checks = _check_budgets(pricing)
        assert all(c.ok for c in checks)

    def test_vault_initialise_ok(self, tmp_path):
        vault = _vault_init(tmp_path)
        checks = _check_vault_initialise(vault)
        assert all(c.ok for c in checks)

    def test_cache_hors_vault_ok(self, tmp_path):
        vault = tmp_path / "vault"
        cache = tmp_path / ".cache"
        check = _check_cache_hors_vault(vault, cache)
        assert check.ok

    def test_schema_export_ok(self):
        check = _check_schema_export()
        assert check.ok, f"Schéma Kemana invalide : {check.message}"

    def test_warn_ne_bloque_pas_go(self):
        checks = [
            Check("tests_verts", "warn", False, "tests ko"),
            Check("cles_api", "bloquant", True, "OK"),
        ]
        assert verdict_global(checks) is True


# ---------------------------------------------------------------------------
# Test 11 — GOOGLE_PLACES et ANTHROPIC absents = warn uniquement
# ---------------------------------------------------------------------------

class TestWarnSeulement:
    def test_google_places_absent_warn(self):
        with patch.dict("os.environ", {
            "SERP_API_KEY": "x",
            "APOLLO_API_KEY": "x",
        }, clear=True):
            checks = _check_cles_api()
        google_check = next(
            (c for c in checks if "GOOGLE_PLACES_API_KEY" in c.message), None
        )
        assert google_check is not None
        assert google_check.niveau == "warn"
        assert not google_check.ok

    def test_anthropic_absent_warn(self):
        with patch.dict("os.environ", {
            "SERP_API_KEY": "x",
            "APOLLO_API_KEY": "x",
        }, clear=True):
            checks = _check_cles_api()
        anthropic_check = next(
            (c for c in checks if "ANTHROPIC_API_KEY" in c.message), None
        )
        assert anthropic_check is not None
        assert anthropic_check.niveau == "warn"

    def test_warn_absent_ne_cause_pas_no_go(self):
        with patch.dict("os.environ", {
            "SERP_API_KEY": "x",
            "APOLLO_API_KEY": "x",
        }, clear=True):
            checks = _check_cles_api()
        # Vérifier que les bloquants sont OK (SERP et APOLLO présents)
        bloquants = [c for c in checks if c.niveau == "bloquant"]
        assert all(c.ok for c in bloquants)

    def test_serp_absent_bloquant(self):
        with patch.dict("os.environ", {"APOLLO_API_KEY": "x"}, clear=True):
            checks = _check_cles_api()
        serp_check = next(c for c in checks if "SERP_API_KEY" in c.message)
        assert serp_check.niveau == "bloquant"
        assert not serp_check.ok


# ---------------------------------------------------------------------------
# Test 12 — garde_fous_bus : modules J5 sans imports réseau au niveau module
# ---------------------------------------------------------------------------

class TestGardeFousBus:
    def test_modules_j5_sans_import_requests(self):
        checks = _check_garde_fous_bus()
        for c in checks:
            if not c.ok:
                pytest.fail(f"Garde-fou bus VIOLATION dans {c.message}")

    def test_ast_detect_import_requests_module(self, tmp_path):
        source = textwrap.dedent("""\
            import requests
            def foo():
                pass
        """)
        violations = _ast_module_importe(source, {"requests"})
        assert "requests" in violations

    def test_ast_lazy_import_non_detecte(self, tmp_path):
        source = textwrap.dedent("""\
            def foo():
                import requests   # lazy — à l'intérieur d'une fonction
                return requests.get("http://example.com")
        """)
        violations = _ast_module_importe(source, {"requests"})
        assert violations == []

    def test_ast_import_anthropic_module_detecte(self):
        source = "import anthropic\n"
        violations = _ast_module_importe(source, {"anthropic"})
        assert "anthropic" in violations

    def test_ast_source_propre_ok(self):
        source = textwrap.dedent("""\
            from __future__ import annotations
            import json
            from pathlib import Path
        """)
        violations = _ast_module_importe(source, {"requests", "anthropic"})
        assert violations == []

    def test_cache_hors_vault_dans_vault_bloquant(self, tmp_path):
        vault = tmp_path / "vault"
        cache_dans_vault = vault / ".cache"
        check = _check_cache_hors_vault(vault, cache_dans_vault)
        assert not check.ok
        assert check.niveau == "bloquant"


# ---------------------------------------------------------------------------
# Test 14 — Régression : format rapport + garde-fous cohérents
# ---------------------------------------------------------------------------

class TestRegression:
    def test_formater_rapport_contient_tous_les_noms(self):
        checks = [
            Check("cles_api", "bloquant", True, "OK"),
            Check("budgets", "bloquant", False, "nul"),
            Check("tests_verts", "warn", False, "échec"),
        ]
        rapport = formater_rapport(checks)
        assert "cles_api" in rapport
        assert "budgets" in rapport
        assert "tests_verts" in rapport

    def test_formater_rapport_distingue_go_no_go(self):
        checks_go = [Check("cles_api", "bloquant", True, "OK")]
        checks_nogo = [Check("cles_api", "bloquant", False, "ABSENT")]
        rapport_go = formater_rapport(checks_go)
        rapport_nogo = formater_rapport(checks_nogo)
        assert "✅" in rapport_go
        assert "❌" in rapport_nogo

    def test_vault_initialise_dossiers_obligatoires(self, tmp_path):
        vault = _vault_init(tmp_path)
        checks = _check_vault_initialise(vault)
        dossiers = [c.message for c in checks]
        assert any("10-Prospects" in d for d in dossiers)
        assert any("90-Systeme" in d for d in dossiers)

    def test_ast_check_ne_plante_pas_sur_syntaxe_invalide(self):
        violations = _ast_module_importe("def foo(:\n    pass", {"requests"})
        assert violations == []

    def test_modules_j5_pas_d_appel_os_replace_direct(self):
        """os.replace() doit rester exclusif à vault_io.py (§8.7 existant)."""
        from diagnostic import export, usage, preflight as pf
        import inspect
        for module in (export, usage, pf):
            source = inspect.getsource(module)
            assert "os.replace(" not in source, (
                f"{module.__name__} appelle os.replace() directement — réservé à vault_io.py"
            )
