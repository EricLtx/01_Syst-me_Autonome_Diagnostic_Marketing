"""
test_orchestrator.py — orchestrateur DAG « Kemana-Flow » (Chantier CORE).

Couvre les critères d'acceptation du chantier :
  - chargement / validation du DAG (nœud dupliqué, dépendance inconnue, types) ;
  - tri topologique DÉTERMINISTE + départage alphabétique ;
  - refus de cycle (CycleDetecte) ;
  - verrou de run : refus de démarrage concurrent, libération en try/finally ;
  - reprise idempotente : un nœud déjà satisfait est sauté (diagnostic sans
    fiche `decouvert`) ;
  - restriction machine à états : l'orchestrateur ne franchit jamais la porte
    humaine (diagnostique → valide reste interdit à l'agent) ;
  - injection d'UNE instance ApiIO unique avec budgets, partagée par les nœuds
    découverte et diagnostic (mockable — aucun réseau réel).

Aucun test ne touche le réseau : les runners réseau sont surchargés par des
stubs ou l'ApiIO est un sentinel injecté.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from diagnostic.orchestrator import (
    CycleDetecte,
    DagInvalide,
    Noeud,
    Orchestrateur,
    ResultatNoeud,
    RunLock,
    VerrouExiste,
    charger_dag,
    tri_topologique,
)
from diagnostic.vault_io import VaultIO
from diagnostic.vault_schema import FicheProspect


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

class _FakeApiIO:
    """Sentinel injectable : identité vérifiable, aucun réseau."""


def _ecrire_dag(tmp_path: Path, noeuds: list[dict], version: int = 1) -> Path:
    p = tmp_path / "dag.yaml"
    p.write_text(yaml.dump({"version": version, "noeuds": noeuds}, allow_unicode=True),
                 encoding="utf-8")
    return p


def _dag_lineaire(tmp_path: Path) -> Path:
    return _ecrire_dag(tmp_path, [
        {"nom": "preflight_gate", "depends_on": []},
        {"nom": "discovery", "depends_on": ["preflight_gate"]},
        {"nom": "diagnostic", "depends_on": ["discovery"]},
        {"nom": "export", "depends_on": ["diagnostic"], "porte_humaine": True},
        {"nom": "usage_snapshot", "depends_on": ["export"]},
        {"nom": "outreach", "depends_on": ["export"], "enabled": False, "porte_humaine": True},
    ])


def _vault_init(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    for d in ("10-Prospects", "20-Rubrics", "30-Diagnostics", "90-Systeme"):
        (vault / d).mkdir(parents=True, exist_ok=True)
    return vault


def _fiche_decouvert(nom: str = "Climatisation Test") -> FicheProspect:
    return FicheProspect(
        persona=1, marche="quebec", statut="decouvert", nom=nom,
        site_web="https://exemple-hvac.ca", date_creation=date.today(),
        source_decouverte="serp:persona1-quebec", icp_id="persona1-quebec",
        opt_out=False,
    )


def _orch(tmp_path: Path, **kw) -> Orchestrateur:
    """Orchestrateur de test : ApiIO sentinel, verrou/ledger/cache sous tmp."""
    if "vault_path" not in kw:
        kw["vault_path"] = _vault_init(tmp_path)
    kw.setdefault("dag_path", _dag_lineaire(tmp_path))
    kw.setdefault("api_io", _FakeApiIO())
    kw.setdefault("ledger_path", tmp_path / "api_usage.log")
    kw.setdefault("cache_dir", tmp_path / ".cache" / "api_io")
    kw.setdefault("lock_path", tmp_path / ".run.lock")
    return Orchestrateur(**kw)


# ---------------------------------------------------------------------------
# 1 — Chargement / validation du DAG
# ---------------------------------------------------------------------------

class TestChargementDag:
    def test_dag_reel_charge(self):
        noeuds = charger_dag(Path(__file__).resolve().parent.parent / "dag_pipeline.yaml")
        noms = {n.nom for n in noeuds}
        assert {"preflight_gate", "discovery", "diagnostic", "export",
                "usage_snapshot", "outreach"} <= noms

    def test_dag_reel_outreach_desactive(self):
        noeuds = charger_dag(Path(__file__).resolve().parent.parent / "dag_pipeline.yaml")
        outreach = next(n for n in noeuds if n.nom == "outreach")
        assert outreach.enabled is False
        assert outreach.porte_humaine is True

    def test_fichier_absent(self, tmp_path):
        with pytest.raises(DagInvalide):
            charger_dag(tmp_path / "inexistant.yaml")

    def test_liste_vide(self, tmp_path):
        p = _ecrire_dag(tmp_path, [])
        with pytest.raises(DagInvalide):
            charger_dag(p)

    def test_noeud_duplique(self, tmp_path):
        p = _ecrire_dag(tmp_path, [
            {"nom": "a", "depends_on": []},
            {"nom": "a", "depends_on": []},
        ])
        with pytest.raises(DagInvalide, match="dupliqué"):
            charger_dag(p)

    def test_dependance_inconnue(self, tmp_path):
        p = _ecrire_dag(tmp_path, [{"nom": "a", "depends_on": ["fantome"]}])
        with pytest.raises(DagInvalide, match="inconnu"):
            charger_dag(p)

    def test_enabled_non_booleen(self, tmp_path):
        p = _ecrire_dag(tmp_path, [{"nom": "a", "depends_on": [], "enabled": "oui"}])
        with pytest.raises(DagInvalide):
            charger_dag(p)

    def test_depends_on_mal_type(self, tmp_path):
        p = _ecrire_dag(tmp_path, [{"nom": "a", "depends_on": "preflight_gate"}])
        with pytest.raises(DagInvalide):
            charger_dag(p)


# ---------------------------------------------------------------------------
# 2 — Tri topologique déterministe
# ---------------------------------------------------------------------------

class TestTriTopologique:
    def test_ordre_chaine_lineaire(self, tmp_path):
        noeuds = charger_dag(_dag_lineaire(tmp_path))
        ordre = [n.nom for n in tri_topologique(noeuds)]
        assert ordre.index("preflight_gate") < ordre.index("discovery")
        assert ordre.index("discovery") < ordre.index("diagnostic")
        assert ordre.index("diagnostic") < ordre.index("export")
        assert ordre.index("export") < ordre.index("usage_snapshot")
        assert ordre.index("export") < ordre.index("outreach")

    def test_determinisme_independant_de_l_ordre_source(self):
        # Deux nœuds racines simultanément prêts → départage alphabétique.
        a = [Noeud("b"), Noeud("a"), Noeud("c", depends_on=("a", "b"))]
        b = [Noeud("a"), Noeud("c", depends_on=("a", "b")), Noeud("b")]
        assert [n.nom for n in tri_topologique(a)] == ["a", "b", "c"]
        assert [n.nom for n in tri_topologique(b)] == ["a", "b", "c"]

    def test_departage_alphabetique_apres_liberation(self):
        # racine → libère z et a en même temps : a doit passer avant z.
        noeuds = [Noeud("racine"), Noeud("z", depends_on=("racine",)),
                  Noeud("a", depends_on=("racine",))]
        ordre = [n.nom for n in tri_topologique(noeuds)]
        assert ordre == ["racine", "a", "z"]

    def test_cycle_detecte(self):
        noeuds = [Noeud("a", depends_on=("b",)), Noeud("b", depends_on=("a",))]
        with pytest.raises(CycleDetecte):
            tri_topologique(noeuds)

    def test_cycle_via_yaml(self, tmp_path):
        p = _ecrire_dag(tmp_path, [
            {"nom": "a", "depends_on": ["b"]},
            {"nom": "b", "depends_on": ["a"]},
        ])
        with pytest.raises(CycleDetecte):
            tri_topologique(charger_dag(p))


# ---------------------------------------------------------------------------
# 3 — Verrou de run (anti-concurrence)
# ---------------------------------------------------------------------------

class TestVerrou:
    def test_acquisition_cree_le_fichier(self, tmp_path):
        lock = RunLock(tmp_path / ".run.lock", "run-x")
        lock.acquerir()
        assert (tmp_path / ".run.lock").exists()
        lock.liberer()
        assert not (tmp_path / ".run.lock").exists()

    def test_second_acquisition_refusee(self, tmp_path):
        p = tmp_path / ".run.lock"
        RunLock(p, "run-1").acquerir()
        with pytest.raises(VerrouExiste):
            RunLock(p, "run-2").acquerir()

    def test_context_manager_libere_sur_exception(self, tmp_path):
        p = tmp_path / ".run.lock"
        with pytest.raises(RuntimeError):
            with RunLock(p, "run-1"):
                raise RuntimeError("boom")
        # Libéré malgré l'exception → un nouveau run peut démarrer.
        assert not p.exists()
        RunLock(p, "run-2").acquerir()  # ne lève pas

    def test_orchestrateur_refuse_demarrage_concurrent(self, tmp_path):
        # Un verrou déjà posé (autre run) → executer() lève VerrouExiste.
        lock_path = tmp_path / ".run.lock"
        RunLock(lock_path, "run-en-cours").acquerir()
        orch = _orch(tmp_path, lock_path=lock_path,
                     runners={n: (lambda ctx: ResultatNoeud("x", "execute"))
                              for n in ("preflight_gate", "discovery", "diagnostic",
                                        "export", "usage_snapshot", "outreach")})
        with pytest.raises(VerrouExiste):
            orch.executer()

    def test_verrou_libere_apres_run_normal(self, tmp_path):
        stub = lambda ctx: ResultatNoeud("x", "execute")
        orch = _orch(tmp_path, dry_run=True,
                     runners={n: stub for n in ("preflight_gate", "discovery",
                              "diagnostic", "export", "usage_snapshot", "outreach")})
        orch.executer()
        assert not (tmp_path / ".run.lock").exists()  # libéré en fin de run


# ---------------------------------------------------------------------------
# 4 — Injection d'UNE instance ApiIO unique (budgets)
# ---------------------------------------------------------------------------

class TestApiIoUnique:
    def test_meme_instance_injectee_discovery_et_diagnostic(self, tmp_path):
        captures: dict[str, object] = {}

        def cap(nom):
            def _r(ctx):
                captures[nom] = ctx.api_io
                return ResultatNoeud(nom, "execute")
            return _r

        api = _FakeApiIO()
        vault = _vault_init(tmp_path)
        VaultIO(vault).write_fiche(_fiche_decouvert())  # sinon diagnostic est « satisfait »
        orch = _orch(tmp_path, vault_path=vault, api_io=api, dry_run=True, runners={
            "preflight_gate": cap("preflight_gate"),
            "discovery": cap("discovery"),
            "diagnostic": cap("diagnostic"),
            "export": cap("export"),
            "usage_snapshot": cap("usage_snapshot"),
            "outreach": cap("outreach"),
        })
        orch.executer()
        # L'ApiIO passé aux nœuds réseau est EXACTEMENT l'instance unique.
        assert captures["discovery"] is api
        assert captures["diagnostic"] is api
        assert orch.api_io is api

    def test_construction_apiio_avec_budgets_depuis_pricing(self, tmp_path, monkeypatch):
        import diagnostic.orchestrator as orch_mod
        pricing = {
            "fournisseurs": {"serp": {"unite": "requete",
                             "endpoints": {"search": {"prix_par_unite": {"requetes": 0.01}}}}},
            "budgets": {"serp": {"unites_max": {"requetes": 500}}},
        }
        monkeypatch.setattr(orch_mod, "load_pricing", lambda: pricing)
        # api_io=None → l'orchestrateur en fabrique UNE avec les budgets du YAML.
        orch = Orchestrateur(
            vault_path=_vault_init(tmp_path),
            dag_path=_dag_lineaire(tmp_path),
            api_io=None,
            ledger_path=tmp_path / "api_usage.log",
            cache_dir=tmp_path / ".cache" / "api_io",
            lock_path=tmp_path / ".run.lock",
        )
        assert orch.api_io._budgets == {"serp": {"unites_max": {"requetes": 500}}}


# ---------------------------------------------------------------------------
# 5 — Reprise idempotente (nœud satisfait sauté)
# ---------------------------------------------------------------------------

class TestRepriseIdempotente:
    def test_diagnostic_saute_si_aucune_fiche_decouvert(self, tmp_path):
        vault = _vault_init(tmp_path)  # vault vide → rien à diagnostiquer
        invoques: list[str] = []

        def runner(nom):
            def _r(ctx):
                invoques.append(nom)
                return ResultatNoeud(nom, "execute")
            return _r

        orch = _orch(tmp_path, vault_path=vault, dry_run=True, runners={
            n: runner(n) for n in ("preflight_gate", "discovery", "diagnostic",
                                    "export", "usage_snapshot", "outreach")})
        resultats = orch.executer()
        diag = next(r for r in resultats if r.nom == "diagnostic")
        assert diag.statut == "saute"          # satisfait → non exécuté
        assert "diagnostic" not in invoques    # son runner n'a jamais été appelé
        assert "discovery" in invoques         # les autres nœuds, si.

    def test_diagnostic_non_satisfait_avec_fiche_decouvert(self, tmp_path):
        vault = _vault_init(tmp_path)
        VaultIO(vault).write_fiche(_fiche_decouvert())
        orch = _orch(tmp_path, vault_path=vault)
        noeud_diag = next(n for n in orch.noeuds if n.nom == "diagnostic")
        from diagnostic.orchestrator import ContexteRun
        ctx = ContexteRun(
            run_id="t", api_io=orch.api_io, vault_io=orch.vault_io,
            vault_path=vault, icp_id=None, dry_run=True,
            ledger_path=orch.ledger_path, cache_dir=orch.cache_dir,
        )
        assert orch._est_satisfait(noeud_diag, ctx) is False


# ---------------------------------------------------------------------------
# 6 — Restriction machine à états (porte humaine intangible)
# ---------------------------------------------------------------------------

class TestMachineEtats:
    def test_transition_agent_vers_valide_interdite(self, tmp_path):
        """La porte humaine : l'agent ne peut PAS diagnostique → valide."""
        vault = _vault_init(tmp_path)
        io = VaultIO(vault)
        fiche = _fiche_decouvert()
        path = io.write_fiche(fiche)
        io.transition(path, "diagnostique", acteur="agent")  # seule transition permise
        with pytest.raises(ValueError):
            io.transition(path, "valide", acteur="agent")

    def test_export_ne_transitionne_pas(self, tmp_path):
        """Le nœud export est lecture seule : une fiche diagnostique le reste."""
        vault = _vault_init(tmp_path)
        io = VaultIO(vault)
        path = io.write_fiche(_fiche_decouvert())
        io.transition(path, "diagnostique", acteur="agent")

        orch = _orch(tmp_path, vault_path=vault, icp_id=None, dry_run=True)
        from diagnostic.orchestrator import ContexteRun
        ctx = ContexteRun(
            run_id="t", api_io=orch.api_io, vault_io=io, vault_path=vault,
            icp_id=None, dry_run=True, ledger_path=orch.ledger_path,
            cache_dir=orch.cache_dir,
        )
        orch._run_export(ctx)  # dry-run : lecture seule
        assert io.read_fiche(path).statut == "diagnostique"

    def test_chaine_complete_ne_valide_aucune_fiche(self, tmp_path):
        """Chaîne entière (runners stubbés hors diagnostic) : porte humaine non franchie."""
        vault = _vault_init(tmp_path)
        io = VaultIO(vault)
        path = io.write_fiche(_fiche_decouvert())
        io.transition(path, "diagnostique", acteur="agent")

        stub = lambda ctx: ResultatNoeud("x", "execute")
        orch = _orch(tmp_path, vault_path=vault, dry_run=True, runners={
            n: stub for n in ("preflight_gate", "discovery", "diagnostic",
                              "export", "usage_snapshot", "outreach")})
        orch.executer()
        assert io.read_fiche(path).statut == "diagnostique"  # jamais → valide


# ---------------------------------------------------------------------------
# 7 — Séquencement, portes, gate préflight, tranches
# ---------------------------------------------------------------------------

class TestExecution:
    def test_noeud_desactive_saute(self, tmp_path):
        # outreach enabled:false → statut desactive, jamais exécuté.
        stub = lambda ctx: ResultatNoeud("x", "execute")
        orch = _orch(tmp_path, dry_run=True, runners={
            n: stub for n in ("preflight_gate", "discovery", "diagnostic",
                              "export", "usage_snapshot")})  # pas de runner outreach
        resultats = orch.executer()
        outreach = next(r for r in resultats if r.nom == "outreach")
        assert outreach.statut == "desactive"

    def test_gate_nogo_bloque_en_mode_reel(self, tmp_path, monkeypatch):
        # Préflight NO-GO simulé → bloque + arrêt chaîne. On mocke le préflight
        # pour ne PAS relancer pytest (le vrai _check_tests_verts spawn la suite).
        from diagnostic.preflight import Check
        import diagnostic.preflight as pf
        monkeypatch.setattr(pf, "executer_preflights",
                            lambda **kw: [Check("cles_api", "bloquant", False, "SERP absente")])
        monkeypatch.setattr(pf, "verdict_global", lambda checks: False)

        appels: list[str] = []

        def compteur(nom):
            return lambda ctx: (appels.append(nom), ResultatNoeud(nom, "execute"))[1]

        orch = _orch(tmp_path, dry_run=False, runners={
            "discovery": compteur("discovery"),
            "diagnostic": compteur("diagnostic"),
            "export": compteur("export"),
            "usage_snapshot": compteur("usage_snapshot"),
            "outreach": compteur("outreach"),
        })  # preflight_gate garde son vrai runner (mais préflight mocké)
        resultats = orch.executer()
        gate = resultats[0]
        assert gate.nom == "preflight_gate"
        assert gate.statut == "bloque"
        assert len(resultats) == 1  # chaîne stoppée à la porte
        assert appels == []  # aucun nœud aval exécuté

    def test_gate_go_execute(self, tmp_path, monkeypatch):
        # Préflight GO simulé → la chaîne continue.
        from diagnostic.preflight import Check
        import diagnostic.preflight as pf
        monkeypatch.setattr(pf, "executer_preflights",
                            lambda **kw: [Check("cles_api", "bloquant", True, "OK")])
        monkeypatch.setattr(pf, "verdict_global", lambda checks: True)

        stub = lambda ctx: ResultatNoeud("x", "execute")
        orch = _orch(tmp_path, dry_run=False, runners={
            n: stub for n in ("discovery", "diagnostic", "export",
                              "usage_snapshot", "outreach")})
        resultats = orch.executer()
        assert resultats[0].statut == "execute"
        assert len(resultats) > 1  # la chaîne continue après un GO

    def test_gate_nogo_dry_run_informe_sans_bloquer(self, tmp_path, monkeypatch):
        from diagnostic.preflight import Check
        import diagnostic.preflight as pf
        monkeypatch.setattr(pf, "executer_preflights",
                            lambda **kw: [Check("cles_api", "bloquant", False, "SERP absente")])
        monkeypatch.setattr(pf, "verdict_global", lambda checks: False)

        stub = lambda ctx: ResultatNoeud("x", "execute")
        orch = _orch(tmp_path, dry_run=True, runners={
            n: stub for n in ("discovery", "diagnostic", "export",
                              "usage_snapshot", "outreach")})
        resultats = orch.executer()
        gate = resultats[0]
        assert gate.statut == "execute"  # dry-run : informe, ne bloque pas
        assert len(resultats) > 1  # la chaîne continue

    def test_tranche_depuis(self, tmp_path):
        stub = lambda ctx: ResultatNoeud("x", "execute")
        orch = _orch(tmp_path, dry_run=True, runners={
            n: stub for n in ("preflight_gate", "discovery", "diagnostic",
                              "export", "usage_snapshot", "outreach")})
        resultats = orch.executer(depuis="diagnostic")
        noms = [r.nom for r in resultats]
        assert "preflight_gate" not in noms
        assert "discovery" not in noms
        assert noms[0] == "diagnostic"

    def test_tranche_jusqu_a(self, tmp_path):
        stub = lambda ctx: ResultatNoeud("x", "execute")
        orch = _orch(tmp_path, dry_run=True, runners={
            n: stub for n in ("preflight_gate", "discovery", "diagnostic",
                              "export", "usage_snapshot", "outreach")})
        resultats = orch.executer(jusqu_a="discovery")
        noms = [r.nom for r in resultats]
        assert noms == ["preflight_gate", "discovery"]

    def test_tranche_noeud_inconnu(self, tmp_path):
        orch = _orch(tmp_path, dry_run=True)
        with pytest.raises(DagInvalide):
            orch.executer(depuis="fantome")

    def test_budget_exceeded_arret_propre(self, tmp_path):
        from diagnostic.api_io import BudgetExceeded

        def leve_budget(ctx):
            raise BudgetExceeded("serp : plafond dépassé")

        stub = lambda ctx: ResultatNoeud("x", "execute")
        orch = _orch(tmp_path, dry_run=True, runners={
            "preflight_gate": stub,
            "discovery": leve_budget,
            "diagnostic": stub, "export": stub,
            "usage_snapshot": stub, "outreach": stub,
        })
        resultats = orch.executer()
        disc = next(r for r in resultats if r.nom == "discovery")
        assert disc.statut == "budget_depasse"
        # Arrêt : aucun nœud après discovery.
        assert [r.nom for r in resultats] == ["preflight_gate", "discovery"]
        # Verrou libéré malgré l'arrêt.
        assert not (tmp_path / ".run.lock").exists()

    def test_outreach_runner_refuse_si_force(self, tmp_path):
        # Si un opérateur force enabled:true, le runner refuse (J6 non implémenté).
        orch = _orch(tmp_path, dry_run=True)
        from diagnostic.orchestrator import ContexteRun
        ctx = ContexteRun(
            run_id="t", api_io=orch.api_io, vault_io=orch.vault_io,
            vault_path=orch.vault_path, icp_id=None, dry_run=True,
            ledger_path=orch.ledger_path, cache_dir=orch.cache_dir,
        )
        res = orch._run_outreach(ctx)
        assert res.statut == "bloque"
        assert "J6" in res.message
