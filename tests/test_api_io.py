"""
test_api_io.py — tests unitaires de diagnostic/api_io.py.

Couvre :
  §9.1  — un appel via call() produit exactement une ligne JSONL dans api_usage.log
  §9.3  — cache idempotent : même cache_key → un seul appel réseau
  §9.4  — budget / interruption : BudgetExceeded levée avant fn(), ligne budget_depasse
  §9.5  — mesureur anthropic : tokens extraits et coût calculé correctement
  §9.6  — garde-fou imports : requests et anthropic au niveau module uniquement dans api_io.py
  §9.7  — cache hors vault : cache_dir sous vault_path → erreur fatale au démarrage
  §9.8  — câblage : website.py passe par api_io.call (HTTP journalisé dans le ledger)

Aucun réseau réel, aucune clé API.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from diagnostic.api_io import ApiIO, BudgetExceeded, MESUREURS_DEFAUT

# ---------------------------------------------------------------------------
# Grille tarifaire de test (prix non nuls pour vérifier les calculs)
# ---------------------------------------------------------------------------

PRICING = {
    "devise": "USD",
    "fournisseurs": {
        "anthropic": {
            "unite": "token",
            "endpoints": {
                "messages": {
                    "prix_par_unite": {
                        "input_tokens":  0.000003,
                        "output_tokens": 0.000015,
                    }
                }
            },
        },
        "serp": {
            "unite": "requete",
            "endpoints": {
                "search": {"prix_par_unite": {"requetes": 0.01}},
            },
        },
        "http": {
            "unite": "requete",
            "endpoints": {
                "get": {"prix_par_unite": {"requetes": 0.0}},
            },
        },
    },
}


def _io(tmp_path: Path, budgets=None, with_cache=True) -> tuple[ApiIO, Path]:
    ledger = tmp_path / "api_usage.log"
    cache = tmp_path / "cache" if with_cache else None
    return ApiIO(PRICING, ledger, cache_dir=cache, budgets=budgets), ledger


def _lignes(ledger: Path) -> list[dict]:
    return [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# §9.1 — call() produit une ligne JSONL correcte
# ---------------------------------------------------------------------------

class TestCallLedger:
    def test_une_ligne_par_appel(self, tmp_path):
        io, ledger = _io(tmp_path)
        io.call("http", "get", lambda: {"ok": True})
        assert len(_lignes(ledger)) == 1

    def test_champs_obligatoires_presents(self, tmp_path):
        io, ledger = _io(tmp_path)
        io.call("http", "get", lambda: {}, fiche="test.md")
        e = _lignes(ledger)[0]
        assert e["fournisseur"] == "http"
        assert e["endpoint"] == "get"
        assert e["resultat"] == "ok"
        assert e["cache_hit"] is False
        assert e["fiche"] == "test.md"
        assert "ts" in e
        assert "unites" in e
        assert "cout_estime" in e

    def test_retourne_reponse_brute(self, tmp_path):
        io, _ = _io(tmp_path)
        reponse = io.call("serp", "search", lambda: {"hits": 42})
        assert reponse == {"hits": 42}

    def test_deux_appels_deux_lignes(self, tmp_path):
        io, ledger = _io(tmp_path)
        io.call("http", "get", lambda: {})
        io.call("http", "get", lambda: {})
        assert len(_lignes(ledger)) == 2

    def test_erreur_fn_journalisee_et_propagee(self, tmp_path):
        io, ledger = _io(tmp_path)
        def fn_echoue():
            raise ValueError("timeout")
        with pytest.raises(ValueError, match="timeout"):
            io.call("http", "get", fn_echoue)
        e = _lignes(ledger)[0]
        assert e["resultat"] == "erreur"
        assert "timeout" in e["detail"]


# ---------------------------------------------------------------------------
# §9.3 — Cache idempotent
# ---------------------------------------------------------------------------

class TestCacheIdempotent:
    def test_meme_cache_key_un_seul_appel_reseau(self, tmp_path):
        io, _ = _io(tmp_path)
        compteur = {"n": 0}
        def fn():
            compteur["n"] += 1
            return {"data": 1}
        io.call("serp", "search", fn, cache_key="q1")
        io.call("serp", "search", fn, cache_key="q1")
        assert compteur["n"] == 1

    def test_deuxieme_ligne_cache_hit_true(self, tmp_path):
        io, ledger = _io(tmp_path)
        io.call("serp", "search", lambda: {"r": 1}, cache_key="q1")
        io.call("serp", "search", lambda: {"r": 1}, cache_key="q1")
        lignes = _lignes(ledger)
        assert len(lignes) == 2
        assert lignes[1]["cache_hit"] is True
        assert lignes[1]["cout_estime"] == 0.0

    def test_deuxieme_appel_retourne_valeur_cachee(self, tmp_path):
        io, _ = _io(tmp_path)
        io.call("serp", "search", lambda: {"v": "premier"}, cache_key="q1")
        result = io.call("serp", "search", lambda: {"v": "second"}, cache_key="q1")
        assert result == {"v": "premier"}

    def test_cache_keys_differentes_deux_appels_reseau(self, tmp_path):
        io, _ = _io(tmp_path)
        compteur = {"n": 0}
        def fn():
            compteur["n"] += 1
            return {}
        io.call("serp", "search", fn, cache_key="q1")
        io.call("serp", "search", fn, cache_key="q2")
        assert compteur["n"] == 2

    def test_sans_cache_key_toujours_appelle_fn(self, tmp_path):
        io, _ = _io(tmp_path)
        compteur = {"n": 0}
        def fn():
            compteur["n"] += 1
            return {}
        io.call("http", "get", fn)
        io.call("http", "get", fn)
        assert compteur["n"] == 2

    def test_sans_cache_dir_pas_de_mise_en_cache(self, tmp_path):
        io, _ = _io(tmp_path, with_cache=False)
        compteur = {"n": 0}
        def fn():
            compteur["n"] += 1
            return {}
        io.call("http", "get", fn, cache_key="url")
        io.call("http", "get", fn, cache_key="url")
        assert compteur["n"] == 2  # cache désactivé → 2 appels


# ---------------------------------------------------------------------------
# §9.4 — Budget et interruption
# ---------------------------------------------------------------------------

class TestBudget:
    def test_budget_depasse_leve_avant_appel(self, tmp_path):
        """BudgetExceeded levée AVANT que fn() soit appelée."""
        # Budget 0.015 : permet 1 appel à 0.01 $, bloque le 2ème
        io, _ = _io(tmp_path, budgets={"serp": {"cout_max": 0.015}})
        io.call("serp", "search", lambda: {})  # premier appel OK
        compteur = {"n": 0}
        def fn():
            compteur["n"] += 1
            return {}
        with pytest.raises(BudgetExceeded):
            io.call("serp", "search", fn)
        assert compteur["n"] == 0  # fn() jamais appelée

    def test_budget_depasse_journalise_budget_depasse(self, tmp_path):
        io, ledger = _io(tmp_path, budgets={"serp": {"cout_max": 0.015}})
        io.call("serp", "search", lambda: {})
        with pytest.raises(BudgetExceeded):
            io.call("serp", "search", lambda: {})
        lignes = _lignes(ledger)
        assert lignes[-1]["resultat"] == "budget_depasse"

    def test_budget_unites_max(self, tmp_path):
        """unites_max sur les requêtes (pas sur le coût)."""
        io, _ = _io(tmp_path, budgets={"serp": {"unites_max": {"requetes": 1}}})
        io.call("serp", "search", lambda: {})  # 1 requête consommée
        with pytest.raises(BudgetExceeded):
            io.call("serp", "search", lambda: {})

    def test_budget_non_depasse_appels_continues(self, tmp_path):
        io, _ = _io(tmp_path, budgets={"serp": {"cout_max": 1.0}})
        for _ in range(5):
            io.call("serp", "search", lambda: {})  # 5 × 0.01 = 0.05 < 1.0

    def test_sans_budget_aucune_interruption(self, tmp_path):
        io, _ = _io(tmp_path)
        for _ in range(10):
            io.call("serp", "search", lambda: {})

    def test_budget_fournisseur_different_non_affecte(self, tmp_path):
        """Le budget serp n'affecte pas les appels http."""
        io, _ = _io(tmp_path, budgets={"serp": {"cout_max": 0.005}})
        # http non limité → passe toujours
        for _ in range(3):
            io.call("http", "get", lambda: {})

    def test_registres_recalcules_depuis_ledger(self, tmp_path):
        """Une nouvelle instance ApiIO recharge les totaux depuis le ledger existant."""
        ledger = tmp_path / "api_usage.log"
        cache = tmp_path / "cache"
        io1 = ApiIO(PRICING, ledger, cache_dir=cache)
        io1.call("serp", "search", lambda: {})  # 0.01 USD journalisé

        # Nouvelle instance, même ledger
        io2 = ApiIO(PRICING, ledger, cache_dir=cache, budgets={"serp": {"cout_max": 0.015}})
        # Registre rechargé : 0.01 USD déjà consommé → le 2ème appel passerait (0.01+0.01=0.02>0.015)
        with pytest.raises(BudgetExceeded):
            io2.call("serp", "search", lambda: {})


# ---------------------------------------------------------------------------
# §9.5 — Mesureur Anthropic
# ---------------------------------------------------------------------------

class TestMesureurAnthropic:
    def _reponse_mock(self, input_tokens=1200, output_tokens=350,
                      cache_read=None, cache_create=None):
        usage = MagicMock()
        usage.input_tokens = input_tokens
        usage.output_tokens = output_tokens
        usage.cache_read_input_tokens = cache_read
        usage.cache_creation_input_tokens = cache_create
        reponse = MagicMock()
        reponse.usage = usage
        return reponse

    def test_tokens_extraits_correctement(self, tmp_path):
        io, ledger = _io(tmp_path)
        reponse = self._reponse_mock(1200, 350)
        io.call("anthropic", "messages", lambda: reponse)
        e = _lignes(ledger)[0]
        assert e["unites"]["input_tokens"] == 1200.0
        assert e["unites"]["output_tokens"] == 350.0

    def test_cout_anthropic_calcule(self, tmp_path):
        io, ledger = _io(tmp_path)
        reponse = self._reponse_mock(1000, 200)
        io.call("anthropic", "messages", lambda: reponse)
        e = _lignes(ledger)[0]
        attendu = 1000 * 0.000003 + 200 * 0.000015
        assert abs(e["cout_estime"] - attendu) < 1e-10

    def test_cache_tokens_inclus_si_presents(self, tmp_path):
        io, ledger = _io(tmp_path)
        reponse = self._reponse_mock(500, 100, cache_read=800, cache_create=0)
        io.call("anthropic", "messages", lambda: reponse)
        e = _lignes(ledger)[0]
        assert "cache_read_input_tokens" in e["unites"]
        assert e["unites"]["cache_read_input_tokens"] == 800.0
        # cache_create = 0 → falsy → absent
        assert "cache_creation_input_tokens" not in e["unites"]

    def test_mesureur_via_mesureurs_defaut(self):
        """MESUREURS_DEFAUT est exporté et contient le mesureur anthropic."""
        assert "anthropic" in MESUREURS_DEFAUT
        reponse = self._reponse_mock(100, 50)
        unites = MESUREURS_DEFAUT["anthropic"](reponse)
        assert unites["input_tokens"] == 100.0
        assert unites["output_tokens"] == 50.0

    def test_measure_custom_remplace_defaut(self, tmp_path):
        """Un mesureur custom passé à call() prend le dessus sur le défaut."""
        io, ledger = _io(tmp_path)
        reponse = self._reponse_mock(100, 50)
        custom_measure = lambda r: {"tokens_custom": 999.0}
        io.call("anthropic", "messages", lambda: reponse, measure=custom_measure)
        e = _lignes(ledger)[0]
        assert "tokens_custom" in e["unites"]
        assert "input_tokens" not in e["unites"]


# ---------------------------------------------------------------------------
# §9.7 — Cache hors vault
# ---------------------------------------------------------------------------

class TestCacheHorsVault:
    def test_cache_dans_vault_erreur_fatale(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        cache_dans_vault = vault / "cache"
        with pytest.raises(RuntimeError, match="DANS le vault"):
            ApiIO(PRICING, tmp_path / "api_usage.log",
                  cache_dir=cache_dans_vault, vault_path=vault)

    def test_cache_hors_vault_ok(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        cache_hors = tmp_path / "cache"
        api = ApiIO(PRICING, tmp_path / "api_usage.log",
                    cache_dir=cache_hors, vault_path=vault)
        assert api._cache_dir == cache_hors

    def test_sans_vault_path_pas_de_verification(self, tmp_path):
        """Pas de vault_path → aucune vérification de localisation."""
        ApiIO(PRICING, tmp_path / "api_usage.log",
              cache_dir=tmp_path / "cache")  # ne lève pas

    def test_sans_cache_dir_pas_de_verification(self, tmp_path):
        """Pas de cache_dir → aucune vérification non plus."""
        vault = tmp_path / "vault"
        vault.mkdir()
        ApiIO(PRICING, tmp_path / "api_usage.log",
              vault_path=vault)  # ne lève pas


# ---------------------------------------------------------------------------
# §9.6 — Garde-fou imports (module-level)
# ---------------------------------------------------------------------------

class TestGardefouImports:
    """Transposition de §8.7 (os.replace) : requests et anthropic ne doivent
    pas être importés au niveau module dans des fichiers autres que api_io.py.

    Les imports paresseux (lazy) à l'intérieur des fonctions sont autorisés
    pour la rétrocompatibilité en mode autonome (sans bus injecté).
    """

    def _imports_module_level(self, py_file):
        """Retourne les noms importés au niveau module (directs enfants de ast.Module)."""
        import ast as _ast
        source = py_file.read_text(encoding="utf-8")
        try:
            tree = _ast.parse(source, filename=str(py_file))
        except SyntaxError:
            return []
        violations = []
        for node in tree.body:  # uniquement le niveau module
            if isinstance(node, _ast.Import):
                for alias in node.names:
                    violations.append((py_file.name, node.lineno, alias.name))
            elif isinstance(node, _ast.ImportFrom):
                module = node.module or ""
                top = module.split(".")[0]
                violations.append((py_file.name, node.lineno, top))
        return violations

    def test_requests_pas_importe_niveau_module_hors_api_io(self):
        diagnostic_dir = Path(__file__).resolve().parent.parent / "diagnostic"
        violations = []
        for py_file in sorted(diagnostic_dir.rglob("*.py")):
            if py_file.name == "api_io.py":
                continue
            for fname, lineno, name in self._imports_module_level(py_file):
                if name == "requests":
                    violations.append(f"{fname}:{lineno} — import requests")
        assert not violations, (
            "import requests trouvé au niveau module hors api_io.py "
            "(utiliser un import lazy à l'intérieur de la fonction) :\n"
            + "\n".join(violations)
        )

    def test_anthropic_pas_importe_niveau_module_hors_api_io(self):
        diagnostic_dir = Path(__file__).resolve().parent.parent / "diagnostic"
        violations = []
        for py_file in sorted(diagnostic_dir.rglob("*.py")):
            if py_file.name == "api_io.py":
                continue
            for fname, lineno, name in self._imports_module_level(py_file):
                if name == "anthropic":
                    violations.append(f"{fname}:{lineno} — import anthropic")
        assert not violations, (
            "import anthropic trouvé au niveau module hors api_io.py :\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# §9.8 — Câblage website.py via api_io
# ---------------------------------------------------------------------------

class TestCablage:
    def test_fetch_http_journalise_dans_ledger(self, tmp_path):
        """Avec api_io injecté, le fetch HTTP de website.py apparaît dans le ledger."""
        from unittest.mock import MagicMock, patch

        from diagnostic.collectors.website import WebsiteCollector
        from diagnostic.config import load_rubrique
        from diagnostic.models import Company
        from diagnostic.pipeline import DiagnosticPipeline

        io, ledger = _io(tmp_path)
        pipeline = DiagnosticPipeline(
            collectors=[WebsiteCollector(use_cache=False)],
            rubrique=load_rubrique(),
            api_io=io,
        )

        fake_resp = MagicMock()
        fake_resp.text = "<html><title>Test</title></html>"
        fake_resp.url = "https://exemple.ca"
        fake_resp.status_code = 200

        with patch("requests.get", return_value=fake_resp):
            pipeline.run(Company(nom="Test HVAC", url="https://exemple.ca"))

        assert ledger.exists()
        lignes = _lignes(ledger)
        ops_http = [l for l in lignes if l["fournisseur"] == "http" and l["endpoint"] == "get"]
        assert len(ops_http) >= 1, "Aucune entrée http/get dans le ledger"

    def test_api_io_injecte_dans_website_collector(self, tmp_path):
        """Pipeline injecte _api_io dans WebsiteCollector au moment de __init__."""
        from diagnostic.collectors.website import WebsiteCollector
        from diagnostic.config import load_rubrique
        from diagnostic.pipeline import DiagnosticPipeline

        io, _ = _io(tmp_path)
        collector = WebsiteCollector(use_cache=False)
        assert collector._api_io is None  # avant injection

        DiagnosticPipeline(
            collectors=[collector],
            rubrique=load_rubrique(),
            api_io=io,
        )
        assert collector._api_io is io  # après injection via pipeline
