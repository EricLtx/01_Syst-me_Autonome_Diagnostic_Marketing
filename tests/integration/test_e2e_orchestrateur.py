"""
test_e2e_orchestrateur.py — la chaîne complète sous l'orchestrateur DAG.

Ce que ces tests prouvent :
  - avec la grille tarifaire de TEST (prix et budgets non nuls) et des clés
    factices, le préflight passe GO — la porte d'entrée du cron J7 fonctionne ;
  - la chaîne préflight → découverte → diagnostic → export → usage s'exécute
    d'un bout à l'autre sur le faux serveur et laisse un état cohérent ;
  - une seconde exécution est idempotente (le diagnostic est « déjà satisfait »,
    la découverte ne duplique aucune fiche).

Neutralisation assumée : `preflight._check_tests_verts` relance `pytest tests/`
dans un sous-processus. Appelé DEPUIS un test, il se relancerait à l'infini —
on le remplace donc par un Check vert. Les 8 autres contrôles restent réels.
"""

from __future__ import annotations

import shutil
from datetime import date

import pytest

from diagnostic.preflight import Check, executer_preflights, verdict_global
from diagnostic.vault_io import VaultIO
from tests.integration import dataset
from tests.integration.dataset import ICP_TEST


@pytest.fixture()
def preflight_de_test(env_faux_api, monkeypatch, tmp_path):
    """Préflight réel, mais adossé à la grille tarifaire de test."""
    import diagnostic.preflight as pf

    knowledge = tmp_path / "knowledge_test"
    knowledge.mkdir(exist_ok=True)
    shutil.copy(dataset.PRICING_TEST, knowledge / "api_pricing.yaml")
    monkeypatch.setattr(pf, "_KNOWLEDGE_DIR", knowledge)
    monkeypatch.setattr(
        pf, "_check_tests_verts",
        lambda root_dir, strict=False: Check("tests_verts", "warn", True,
                                             "neutralisé (anti-récursion pytest)"),
    )
    return knowledge


def _orchestrateur(chemins, api_io, monkeypatch, tmp_path, **kwargs):
    import diagnostic.orchestrator as orch
    # Les artefacts de l'orchestrateur restent dans tmp_path (rien dans le dépôt).
    monkeypatch.setattr(orch, "_RACINE", tmp_path)
    monkeypatch.setattr(orch, "_MANIFESTES_DIR", tmp_path / "manifestes")
    return orch.Orchestrateur(
        vault_path=chemins["vault"],
        icp_id=ICP_TEST,
        api_io=api_io,
        ledger_path=chemins["ledger"],
        cache_dir=chemins["cache"],
        lock_path=chemins["verrou"],
        **kwargs,
    )


# ---------------------------------------------------------------------------
# 1. La porte préflight
# ---------------------------------------------------------------------------

class TestPreflight:

    def test_go_avec_pricing_de_test_et_cles_factices(
        self, preflight_de_test, vault_seme, chemins
    ):
        checks = executer_preflights(
            vault_path=chemins["vault"], cache_dir=chemins["cache"], icp_id=ICP_TEST)
        bloquants_ko = [c.message for c in checks if c.niveau == "bloquant" and not c.ok]
        assert bloquants_ko == []
        assert verdict_global(checks) is True

    def test_no_go_si_une_cle_obligatoire_manque(
        self, preflight_de_test, vault_seme, chemins, monkeypatch
    ):
        monkeypatch.delenv("SERP_API_KEY", raising=False)
        checks = executer_preflights(
            vault_path=chemins["vault"], cache_dir=chemins["cache"], icp_id=ICP_TEST)
        assert verdict_global(checks) is False

    def test_no_go_avec_la_grille_de_production_encore_a_zero(
        self, env_faux_api, vault_seme, chemins, monkeypatch
    ):
        """Rappel du contexte réel : tant que les tarifs/budgets sont à 0,
        le préflight DOIT refuser le départ."""
        import diagnostic.preflight as pf
        monkeypatch.setattr(
            pf, "_check_tests_verts",
            lambda root_dir, strict=False: Check("tests_verts", "warn", True, "neutralisé"))
        checks = executer_preflights(
            vault_path=chemins["vault"], cache_dir=chemins["cache"], icp_id=ICP_TEST)
        assert verdict_global(checks) is False
        assert any(c.nom == "tarifs_reels" and not c.ok for c in checks)
        assert any(c.nom == "budgets" and not c.ok for c in checks)


# ---------------------------------------------------------------------------
# 2. La chaîne complète
# ---------------------------------------------------------------------------

class TestChaineComplete:

    def test_chaine_produit_un_etat_coherent(
        self, preflight_de_test, journal_vierge, vault_seme, chemins, api_io,
        monkeypatch, tmp_path, ledger
    ):
        orch = _orchestrateur(chemins, api_io, monkeypatch, tmp_path)
        resultats = orch.executer()

        statuts = {r.nom: r.statut for r in resultats}
        assert statuts["preflight_gate"] == "execute"
        assert statuts["discovery"] == "execute"
        assert statuts["diagnostic"] == "execute"
        assert statuts["export"] == "execute"
        assert statuts["usage_snapshot"] == "execute"
        # J6 : déclaré dans le DAG mais enabled: false — jamais exécuté.
        assert statuts["outreach"] == "desactive"

        io = VaultIO(chemins["vault"])
        # Le diagnostic a vidé la file `decouvert` (seule transition d'agent).
        assert io.query(statut="decouvert") == []
        assert io.query(statut="diagnostique")
        # La porte humaine n'a pas été franchie : aucun `valide` supplémentaire.
        assert {f.nom for _, f in io.query(statut="valide")} == {
            "Clim Rive-Sud", "HVAC Saguenay", "Aéroclim Beauce"}

        # Artefacts de sortie, tous hors vault sauf le snapshot d'usage.
        exports = sorted((tmp_path / "exports").glob("*.csv"))
        assert len(exports) == 1
        contenu = exports[0].read_bytes().decode("utf-8-sig")
        assert "Clim Rive-Sud" in contenu
        assert "HVAC Saguenay" not in contenu       # opt_out, jamais exporté

        snapshot = chemins["vault"] / "90-Systeme" / f"usage-{date.today().isoformat()}.md"
        assert snapshot.exists()

        # Un seul grand livre pour toute la chaîne (ApiIO unique).
        fournisseurs = {l["fournisseur"] for l in ledger.lignes(chemins["ledger"])}
        assert {"serp", "apollo", "http", "google_places"} <= fournisseurs

    def test_seconde_execution_est_idempotente(
        self, preflight_de_test, journal_vierge, vault_seme, chemins, api_io,
        monkeypatch, tmp_path
    ):
        _orchestrateur(chemins, api_io, monkeypatch, tmp_path).executer()
        io = VaultIO(chemins["vault"])
        etat_1 = {f.nom: str(f.statut) for _, f in io.query()}

        resultats = _orchestrateur(chemins, api_io, monkeypatch, tmp_path).executer()
        etat_2 = {f.nom: str(f.statut) for _, f in io.query()}

        assert etat_2 == etat_1
        statuts = {r.nom: r.statut for r in resultats}
        assert statuts["diagnostic"] == "saute", "plus aucune fiche decouvert à traiter"
        assert statuts["export"] == "execute"

    def test_dry_run_n_ecrit_rien(
        self, preflight_de_test, journal_vierge, vault_seme, chemins, api_io,
        monkeypatch, tmp_path
    ):
        io = VaultIO(chemins["vault"])
        avant = {f.nom: str(f.statut) for _, f in io.query()}

        resultats = _orchestrateur(
            chemins, api_io, monkeypatch, tmp_path, dry_run=True).executer()

        assert all(r.statut in ("execute", "desactive", "saute") for r in resultats)
        assert {f.nom: str(f.statut) for _, f in io.query()} == avant
        assert not (tmp_path / "exports").exists()

    def test_verrou_refuse_deux_runs_simultanes(
        self, preflight_de_test, vault_seme, chemins, api_io, monkeypatch, tmp_path
    ):
        from diagnostic.orchestrator import RunLock, VerrouExiste
        verrou = RunLock(chemins["verrou"], "run-tenu-par-un-autre").acquerir()
        try:
            with pytest.raises(VerrouExiste):
                _orchestrateur(chemins, api_io, monkeypatch, tmp_path).executer()
        finally:
            verrou.liberer()
