"""
test_api_schema.py — tests unitaires de diagnostic/api_schema.py.

Couvre §9.1 (LedgerEntry : sérialisation JSONL, champs) et §9.2 (compute_cout
depuis api_pricing.yaml de test). Aucune I/O réseau.

Note : le test §9.1 complet (une ligne produite par api_io.call) est en Phase B,
quand api_io.py existe. Ici on teste le schéma et la fonction de calcul en isolation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from diagnostic.api_schema import LedgerEntry, compute_cout

# ---------------------------------------------------------------------------
# Grille tarifaire de test (valeurs non nulles pour vérifier les calculs)
# ---------------------------------------------------------------------------

PRICING_TEST = {
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

# ---------------------------------------------------------------------------
# Fixture de base
# ---------------------------------------------------------------------------

def _entry(**kwargs) -> LedgerEntry:
    defaults = dict(
        fournisseur="http",
        endpoint="get",
        unites={"requetes": 1},
        cout_estime=0.0,
        devise="USD",
        resultat="ok",
    )
    return LedgerEntry.maintenant(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# §9.1 — LedgerEntry : modèle, sérialisation JSONL, round-trip
# ---------------------------------------------------------------------------

class TestLedgerEntry:
    def test_creation_avec_ts_utc(self):
        e = _entry()
        assert e.ts.tzinfo is not None
        assert e.ts.tzinfo == timezone.utc

    def test_champs_obligatoires_presents(self):
        e = _entry()
        assert e.fournisseur == "http"
        assert e.endpoint == "get"
        assert e.unites == {"requetes": 1}
        assert e.cout_estime == 0.0
        assert e.devise == "USD"
        assert e.resultat == "ok"

    def test_defaults(self):
        e = _entry()
        assert e.fiche is None
        assert e.cache_hit is False
        assert e.detail == ""

    def test_fiche_optionnelle(self):
        e = _entry(fiche="chauffage-tremblay.md")
        assert e.fiche == "chauffage-tremblay.md"

    def test_cache_hit(self):
        e = _entry(cache_hit=True, cout_estime=0.0)
        assert e.cache_hit is True

    def test_resultat_erreur(self):
        e = _entry(resultat="erreur", detail="timeout")
        assert e.resultat == "erreur"
        assert e.detail == "timeout"

    def test_resultat_budget_depasse(self):
        e = _entry(resultat="budget_depasse")
        assert e.resultat == "budget_depasse"

    def test_resultat_invalide_leve_erreur(self):
        with pytest.raises(Exception):
            _entry(resultat="inconnu")

    def test_to_jsonl_produit_une_ligne(self):
        ligne = _entry().to_jsonl()
        assert "\n" not in ligne
        parsed = json.loads(ligne)
        assert parsed["fournisseur"] == "http"
        assert parsed["resultat"] == "ok"

    def test_round_trip_jsonl(self):
        original = _entry(fiche="test.md", detail="info")
        ligne = original.to_jsonl()
        restaure = LedgerEntry.from_jsonl(ligne)
        assert restaure.fournisseur == original.fournisseur
        assert restaure.endpoint == original.endpoint
        assert restaure.unites == original.unites
        assert restaure.cout_estime == original.cout_estime
        assert restaure.fiche == original.fiche
        assert restaure.cache_hit == original.cache_hit
        assert restaure.resultat == original.resultat

    def test_ts_serialise_en_iso(self):
        ligne = _entry().to_jsonl()
        parsed = json.loads(ligne)
        # Le champ ts doit être une chaîne ISO parseable
        dt = datetime.fromisoformat(parsed["ts"])
        assert dt.tzinfo is not None

    def test_champ_extra_interdit(self):
        """extra='forbid' : un champ inconnu doit lever une erreur."""
        with pytest.raises(Exception):
            LedgerEntry.maintenant(
                fournisseur="http", endpoint="get",
                unites={"requetes": 1}, cout_estime=0.0,
                devise="USD", resultat="ok",
                champ_inconnu="valeur",
            )


# ---------------------------------------------------------------------------
# §9.2 — compute_cout : calcul depuis la grille tarifaire
# ---------------------------------------------------------------------------

class TestComputeCout:
    def test_anthropic_tokens(self):
        """1 200 tokens entrée + 350 tokens sortie."""
        cout = compute_cout(
            PRICING_TEST, "anthropic", "messages",
            {"input_tokens": 1200.0, "output_tokens": 350.0},
        )
        attendu = 1200 * 0.000003 + 350 * 0.000015
        assert abs(cout - attendu) < 1e-10

    def test_serp_une_requete(self):
        cout = compute_cout(PRICING_TEST, "serp", "search", {"requetes": 1.0})
        assert abs(cout - 0.01) < 1e-10

    def test_http_cout_nul(self):
        cout = compute_cout(PRICING_TEST, "http", "get", {"requetes": 1.0})
        assert cout == 0.0

    def test_fournisseur_inconnu_retourne_zero(self):
        cout = compute_cout(PRICING_TEST, "inconnu", "messages", {"input_tokens": 1000.0})
        assert cout == 0.0

    def test_endpoint_inconnu_retourne_zero(self):
        cout = compute_cout(PRICING_TEST, "anthropic", "inexistant", {"input_tokens": 1000.0})
        assert cout == 0.0

    def test_unites_supplementaires_ignorees(self):
        """Des unités hors grille ne font pas planter le calcul."""
        cout = compute_cout(
            PRICING_TEST, "serp", "search",
            {"requetes": 1.0, "cache_tokens": 500.0},
        )
        assert abs(cout - 0.01) < 1e-10

    def test_unites_vides(self):
        cout = compute_cout(PRICING_TEST, "serp", "search", {})
        assert cout == 0.0

    def test_plusieurs_serp_requetes(self):
        cout = compute_cout(PRICING_TEST, "serp", "search", {"requetes": 10.0})
        assert abs(cout - 0.10) < 1e-10
