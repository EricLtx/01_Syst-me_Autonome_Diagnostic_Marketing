"""
test_e2e_bus.py — garde-fous du bus d'I/O et du bus vault, en conditions réelles.

Ce que ces tests prouvent, faux serveur à l'appui :
  - le cache d'`api_io` évite RÉELLEMENT le second aller-retour réseau
    (le serveur ne voit qu'une requête pour deux appels identiques) ;
  - un budget volontairement bas interrompt AVANT l'appel réseau, laisse le
    grand livre cohérent et ne corrompt jamais le vault ;
  - la machine à états du vault n'est jamais franchie par un agent ;
  - le cache disque refuse de s'installer dans le vault (contrainte G9).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from diagnostic.api_io import ApiIO, BudgetExceeded
from diagnostic.vault_io import VaultIO
from tests.integration.conftest import lignes_ledger, lignes_pour
from tests.integration.dataset import ICP_TEST


def _bus(chemins, pricing, budgets=None) -> ApiIO:
    return ApiIO(
        pricing,
        chemins["ledger"],
        cache_dir=chemins["cache"],
        budgets=budgets if budgets is not None else pricing.get("budgets"),
        vault_path=chemins["vault"],
    )


def _get_serp(serveur, requete: str):
    """Appel réseau réel, tel que le fait `discovery._serp_search`."""
    import requests
    return requests.get(f"{serveur.base_http}/search",
                        params={"q": requete, "num": 6}, timeout=10).json()


# ---------------------------------------------------------------------------
# 1. Cache
# ---------------------------------------------------------------------------

class TestCacheDuBus:

    def test_deux_appels_identiques_une_seule_requete_reseau(
        self, env_faux_api, journal_vierge, chemins, pricing_test
    ):
        serveur = journal_vierge
        bus = _bus(chemins, pricing_test)

        a = bus.call("serp", "search", lambda: _get_serp(serveur, "chauffagiste Québec"),
                     cache_key="chauffagiste Québec")
        b = bus.call("serp", "search", lambda: _get_serp(serveur, "chauffagiste Québec"),
                     cache_key="chauffagiste Québec")

        assert a == b
        assert serveur.compter("/search") == 1, "le second appel devait être servi par le cache"

        lignes = lignes_pour(chemins["ledger"], "serp")
        assert len(lignes) == 2
        assert lignes[0]["cache_hit"] is False and lignes[0]["cout_estime"] > 0
        assert lignes[1]["cache_hit"] is True and lignes[1]["cout_estime"] == 0

    def test_cle_de_cache_differente_declenche_un_vrai_appel(
        self, env_faux_api, journal_vierge, chemins, pricing_test
    ):
        serveur = journal_vierge
        bus = _bus(chemins, pricing_test)
        bus.call("serp", "search", lambda: _get_serp(serveur, "a"), cache_key="a")
        bus.call("serp", "search", lambda: _get_serp(serveur, "b"), cache_key="b")
        assert serveur.compter("/search") == 2

    def test_cache_refuse_de_sinstaller_dans_le_vault(self, chemins, pricing_test):
        """Contrainte G9 : le cache de scraping reste hors du vault."""
        with pytest.raises(RuntimeError, match="DANS le vault"):
            ApiIO(pricing_test, chemins["ledger"],
                  cache_dir=chemins["vault"] / ".cache",
                  vault_path=chemins["vault"])


# ---------------------------------------------------------------------------
# 2. Budgets
# ---------------------------------------------------------------------------

class TestBudgets:

    def test_budget_interrompt_avant_lappel_reseau(
        self, env_faux_api, journal_vierge, chemins, pricing_test
    ):
        serveur = journal_vierge
        bus = _bus(chemins, pricing_test, budgets={"serp": {"unites_max": {"requetes": 1}}})

        bus.call("serp", "search", lambda: _get_serp(serveur, "un"), cache_key="un")
        with pytest.raises(BudgetExceeded):
            bus.call("serp", "search", lambda: _get_serp(serveur, "deux"), cache_key="deux")

        # La preuve que l'interruption a lieu AVANT le réseau : le faux serveur
        # n'a jamais vu la seconde requête.
        assert serveur.compter("/search") == 1

        lignes = lignes_pour(chemins["ledger"], "serp")
        assert [l["resultat"] for l in lignes] == ["ok", "budget_depasse"]

    def test_budget_apollo_epuise_ne_corrompt_pas_le_vault(
        self, env_faux_api, journal_vierge, vault_vide, chemins, pricing_test
    ):
        """Crédits Apollo épuisés en cours de route : les fiches déjà écrites
        restent valides, les suivantes sont écrites sans contact."""
        import run_discovery
        bus = _bus(chemins, pricing_test, budgets={"apollo": {"unites_max": {"credits": 1}}})
        run_discovery.run(icp_id=ICP_TEST, vault=chemins["vault"], api_io=bus)

        io = VaultIO(chemins["vault"])
        fiches = io.query()
        assert len(fiches) >= 4

        # Toutes les fiches se relisent et se revalident (aucune corruption).
        for path, _ in fiches:
            fiche = io.read_fiche(path)
            assert fiche.statut == "decouvert"
            assert fiche.nom

        assert any(f.contact_email for _, f in fiches), "le 1er crédit devait passer"
        assert any(not f.contact_email for _, f in fiches), "les suivants devaient être coupés"

        apollo = lignes_pour(chemins["ledger"], "apollo")
        assert any(l["resultat"] == "budget_depasse" for l in apollo)

    def test_reprise_apres_budget_est_idempotente(
        self, env_faux_api, journal_vierge, vault_vide, chemins, pricing_test
    ):
        import run_discovery
        serre = _bus(chemins, pricing_test, budgets={"apollo": {"unites_max": {"credits": 1}}})
        run_discovery.run(icp_id=ICP_TEST, vault=chemins["vault"], api_io=serre)
        io = VaultIO(chemins["vault"])
        noms = {f.nom for _, f in io.query()}

        # Budget rouvert : la relance ne duplique rien.
        large = _bus(chemins, pricing_test)
        run_discovery.run(icp_id=ICP_TEST, vault=chemins["vault"], api_io=large)
        assert {f.nom for _, f in io.query()} == noms


# ---------------------------------------------------------------------------
# 3. Machine à états et journal du vault
# ---------------------------------------------------------------------------

class TestGardeFousVault:

    def test_agent_ne_peut_pas_valider_une_fiche(self, vault_seme, chemins):
        io = VaultIO(chemins["vault"])
        path, fiche = next((p, f) for p, f in io.query(statut="diagnostique"))

        with pytest.raises(ValueError, match="réservée à l'humain"):
            io.transition(path, "valide", acteur="agent")

        assert io.read_fiche(path).statut == "diagnostique"

    @pytest.mark.parametrize("depart,cible", [
        ("decouvert", "valide"),
        ("decouvert", "contacte"),
        ("valide", "decouvert"),
        ("rejete", "valide"),
    ])
    def test_transitions_illegales_refusees(self, vault_seme, chemins, depart, cible):
        io = VaultIO(chemins["vault"])
        trouve = io.query(statut=depart)
        if not trouve:
            pytest.skip(f"aucune fiche {depart} dans le dataset")
        path, _ = trouve[0]
        with pytest.raises(ValueError, match="Transition illégale"):
            io.transition(path, cible, acteur="humain")
        assert io.read_fiche(path).statut == depart

    def test_journal_vault_append_only(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io
    ):
        import json
        import run_discovery
        run_discovery.run(icp_id=ICP_TEST, vault=chemins["vault"], api_io=api_io)

        runs_log = Path(chemins["vault"]).parent / "runs.log"
        assert runs_log.exists()
        entrees = [json.loads(l) for l in runs_log.read_text("utf-8").splitlines() if l.strip()]
        assert entrees
        assert all({"ts", "agent", "op", "fiche", "resultat"} <= set(e) for e in entrees)
        assert all(e["agent"] == "vault_io" for e in entrees)

    def test_grand_livre_est_du_jsonl_append_only(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io
    ):
        import run_discovery
        run_discovery.run(icp_id=ICP_TEST, vault=chemins["vault"], api_io=api_io)

        lignes = lignes_ledger(chemins["ledger"])
        assert lignes
        # Socle minimal garanti — les champs supplémentaires sont les bienvenus.
        socle = {"ts", "fournisseur", "endpoint", "unites", "cout_estime", "devise"}
        assert all(socle <= set(l) for l in lignes)
