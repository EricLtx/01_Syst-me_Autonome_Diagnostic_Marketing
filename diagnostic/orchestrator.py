"""
orchestrator.py — orchestrateur DAG déterministe « Kemana-Flow » (Chantier CORE).

Fine couche d'ORDONNANCEMENT au-dessus de J1-J5. ZÉRO logique métier : elle
branche, ordonne, journalise, s'arrête. Chaque nœud est un adaptateur MINCE
autour d'un entrypoint existant (préflight J5, découverte J4, diagnostic J1,
export/usage J5). La logique de chaque étape reste dans son module d'origine.

Pourquoi cette couche existe :
  - corriger le défaut AS-IS « chaque run_*.py fabrique son propre ApiIO » :
    une SEULE instance ApiIO (avec budgets) est créée ici et injectée dans les
    nœuds découverte ET diagnostic (et outreach futur) — un seul grand livre,
    un seul garde-fou budgétaire pour toute la chaîne ;
  - garantir un ordre déterministe (tri topologique + départage alphabétique) ;
  - refuser un démarrage concurrent (verrou de run hors vault) ;
  - s'arrêter proprement sur BudgetExceeded (fiches déjà écrites restent valides) ;
  - respecter la machine à états : l'orchestrateur ne déclenche QUE la transition
    agent decouvert → diagnostique (déléguée au code diagnostic existant) ; les
    transitions valide/contacte/rejete restent humaines (porte humaine dans Obsidian).

Le graphe est une DONNÉE (dag_pipeline.yaml) : ajouter/réordonner une étape =
éditer le YAML, jamais ce code.

NB : ce module ne touche JAMAIS le réseau lui-même — c'est api_io qui le fait.
Aucun import requests/anthropic au niveau module (vérifié par le garde-fou AST
de preflight._check_garde_fous_bus).
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from diagnostic.api_io import ApiIO, BudgetExceeded
from diagnostic.config import load_pricing
from diagnostic.vault_io import VaultIO

# Chemins par défaut (tous hors vault — cf. contrainte G9 + gitignore).
_RACINE = Path(__file__).resolve().parent.parent
_DAG_PAR_DEFAUT = _RACINE / "dag_pipeline.yaml"
_LEDGER_PAR_DEFAUT = _RACINE / "api_usage.log"
_CACHE_PAR_DEFAUT = _RACINE / ".cache" / "api_io"
_VERROU_PAR_DEFAUT = _RACINE / ".run.lock"
# Manifestes de run : sous .cache/ (gitignoré) — sert de trace de corrélation.
_MANIFESTES_DIR = _RACINE / ".cache" / "orchestrator"


# ---------------------------------------------------------------------------
# Exceptions du domaine ordonnancement
# ---------------------------------------------------------------------------

class DagInvalide(ValueError):
    """DAG mal formé : nœud dupliqué, dépendance inconnue, champ invalide."""


class CycleDetecte(DagInvalide):
    """Le graphe contient un cycle — aucun ordre topologique n'existe."""


class VerrouExiste(RuntimeError):
    """Un autre run détient déjà le verrou : démarrage concurrent refusé."""


# ---------------------------------------------------------------------------
# Modèle du graphe (données du YAML)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Noeud:
    """Un nœud du DAG. Purement descriptif : aucune logique métier ici."""
    nom: str
    depends_on: tuple[str, ...] = ()
    enabled: bool = True
    porte_humaine: bool = False
    # Plafond budgétaire optionnel propre au nœud (documentaire ; le garde-fou
    # réel reste ApiIO avec les budgets globaux). Conservé pour extensibilité.
    plafond_budget: dict[str, Any] | None = None


@dataclass
class ResultatNoeud:
    """Issue de l'exécution (ou du saut) d'un nœud."""
    nom: str
    statut: str  # execute | saute | desactive | bloque | budget_depasse | echec
    message: str = ""


@dataclass
class ContexteRun:
    """État partagé passé à chaque runner de nœud. Immuable côté nœud.

    C'est ici que vit l'unique ApiIO : chaque adaptateur qui a besoin du réseau
    reçoit CETTE instance, jamais la sienne.
    """
    run_id: str
    api_io: ApiIO
    vault_io: VaultIO
    vault_path: Path
    icp_id: str | None
    dry_run: bool
    ledger_path: Path
    cache_dir: Path
    # Résultats accumulés (lecture seule côté nœud, utile au diagnostic).
    resultats: list[ResultatNoeud] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Chargement + validation du DAG
# ---------------------------------------------------------------------------

def charger_dag(path: Path | str = _DAG_PAR_DEFAUT) -> list[Noeud]:
    """Charge et valide le DAG depuis le YAML. Lève DagInvalide si mal formé.

    Le graphe est une donnée : toute la structure vient du fichier, jamais du code.
    """
    path = Path(path)
    if not path.exists():
        raise DagInvalide(f"DAG introuvable : {path}")
    brut = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    noeuds_bruts = brut.get("noeuds")
    if not isinstance(noeuds_bruts, list) or not noeuds_bruts:
        raise DagInvalide("Le DAG doit contenir une liste 'noeuds' non vide.")

    noeuds: list[Noeud] = []
    vus: set[str] = set()
    for item in noeuds_bruts:
        if not isinstance(item, dict) or "nom" not in item:
            raise DagInvalide(f"Nœud invalide (attendu un mapping avec 'nom') : {item!r}")
        nom = item["nom"]
        if not isinstance(nom, str) or not nom:
            raise DagInvalide(f"'nom' de nœud invalide : {nom!r}")
        if nom in vus:
            raise DagInvalide(f"Nœud dupliqué : {nom!r}")
        vus.add(nom)

        depends = item.get("depends_on") or []
        if not isinstance(depends, list) or not all(isinstance(d, str) for d in depends):
            raise DagInvalide(f"'depends_on' de {nom!r} doit être une liste de noms.")

        enabled = item.get("enabled", True)
        porte_humaine = item.get("porte_humaine", False)
        if not isinstance(enabled, bool) or not isinstance(porte_humaine, bool):
            raise DagInvalide(f"'enabled'/'porte_humaine' de {nom!r} doivent être booléens.")

        plafond = item.get("plafond_budget")
        if plafond is not None and not isinstance(plafond, dict):
            raise DagInvalide(f"'plafond_budget' de {nom!r} doit être un mapping ou absent.")

        noeuds.append(Noeud(
            nom=nom,
            depends_on=tuple(depends),
            enabled=enabled,
            porte_humaine=porte_humaine,
            plafond_budget=plafond,
        ))

    # Toutes les dépendances doivent référencer des nœuds déclarés.
    for n in noeuds:
        for dep in n.depends_on:
            if dep not in vus:
                raise DagInvalide(f"Nœud {n.nom!r} dépend d'un nœud inconnu : {dep!r}")

    return noeuds


def tri_topologique(noeuds: list[Noeud]) -> list[Noeud]:
    """Ordre topologique DÉTERMINISTE (Kahn + départage alphabétique).

    Deux exécutions du même DAG donnent exactement la même séquence : le
    départage par nom rend l'ordre reproductible même quand plusieurs nœuds
    sont simultanément prêts. Lève CycleDetecte si le graphe boucle.
    """
    par_nom = {n.nom: n for n in noeuds}
    # Degré entrant = nombre de dépendances non encore satisfaites.
    degre = {n.nom: len(n.depends_on) for n in noeuds}
    # Adjacence : dep -> [nœuds qui en dépendent].
    successeurs: dict[str, list[str]] = {n.nom: [] for n in noeuds}
    for n in noeuds:
        for dep in n.depends_on:
            successeurs[dep].append(n.nom)

    prets = sorted([nom for nom, d in degre.items() if d == 0])
    ordre: list[Noeud] = []
    while prets:
        nom = prets.pop(0)  # toujours le plus petit nom → déterminisme
        ordre.append(par_nom[nom])
        for suiv in successeurs[nom]:
            degre[suiv] -= 1
            if degre[suiv] == 0:
                # Insertion triée pour préserver l'ordre alphabétique.
                _inserer_trie(prets, suiv)

    if len(ordre) != len(noeuds):
        restants = sorted(set(par_nom) - {n.nom for n in ordre})
        raise CycleDetecte(f"Cycle détecté dans le DAG (nœuds impliqués : {restants})")
    return ordre


def _inserer_trie(liste: list[str], valeur: str) -> None:
    """Insertion en maintenant l'ordre croissant (petites listes : O(n) suffit)."""
    i = 0
    while i < len(liste) and liste[i] < valeur:
        i += 1
    liste.insert(i, valeur)


# ---------------------------------------------------------------------------
# Verrou de run (anti-concurrence) — hors vault, libéré en try/finally
# ---------------------------------------------------------------------------

class RunLock:
    """Verrou exclusif matérialisé par un fichier créé atomiquement (O_EXCL).

    Un seul run peut détenir le verrou à la fois (cron + lancement manuel ne
    peuvent pas se marcher dessus sur le même vault). Le fichier porte le run_id
    et le pid pour diagnostic. Libéré dans __exit__ même en cas d'exception.

    On n'utilise PAS os.replace() ici : cet appel reste l'exclusivité de
    vault_io.py (contrainte J2). La création atomique passe par os.open(O_EXCL).
    """

    def __init__(self, path: Path, run_id: str) -> None:
        self._path = Path(path)
        self._run_id = run_id
        self._detenu = False

    def acquerir(self) -> "RunLock":
        try:
            fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            detail = ""
            try:
                detail = self._path.read_text(encoding="utf-8").strip()
            except OSError:
                pass
            raise VerrouExiste(
                f"Verrou déjà présent ({self._path}). Un run est en cours : {detail}"
            )
        try:
            payload = json.dumps({
                "run_id": self._run_id,
                "pid": os.getpid(),
                "ts": datetime.now(timezone.utc).isoformat(),
            }, ensure_ascii=False)
            os.write(fd, payload.encode("utf-8"))
        finally:
            os.close(fd)
        self._detenu = True
        return self

    def liberer(self) -> None:
        if self._detenu:
            try:
                self._path.unlink()
            except FileNotFoundError:
                pass
            self._detenu = False

    def __enter__(self) -> "RunLock":
        return self.acquerir()

    def __exit__(self, *exc) -> None:
        self.liberer()


# ---------------------------------------------------------------------------
# Orchestrateur
# ---------------------------------------------------------------------------

RunnerNoeud = Callable[[ContexteRun], ResultatNoeud]


class Orchestrateur:
    """Ordonnance et exécute le DAG. Ne contient AUCUNE logique métier.

    Paramètres clés :
      vault_path : racine du vault Obsidian.
      icp_id     : ICP ciblé (transmis aux nœuds découverte/diagnostic).
      dag_path   : fichier YAML du graphe (donnée).
      dry_run    : n'écrit rien (préflight informe mais ne bloque pas dur).
      api_io     : injection possible d'un ApiIO (tests) ; sinon UNE instance
                   est créée ici avec les budgets de load_pricing()['budgets'].
      runners    : override du registre {nom: callable} (tests) ; sinon les
                   adaptateurs minces réels.
    """

    def __init__(
        self,
        *,
        vault_path: Path | str = "vault",
        icp_id: str | None = None,
        dag_path: Path | str = _DAG_PAR_DEFAUT,
        dry_run: bool = False,
        api_io: ApiIO | None = None,
        pricing: dict | None = None,
        ledger_path: Path | str = _LEDGER_PAR_DEFAUT,
        cache_dir: Path | str = _CACHE_PAR_DEFAUT,
        lock_path: Path | str = _VERROU_PAR_DEFAUT,
        runners: dict[str, RunnerNoeud] | None = None,
    ) -> None:
        self.vault_path = Path(vault_path)
        self.icp_id = icp_id
        self.dry_run = dry_run
        self.ledger_path = Path(ledger_path)
        self.cache_dir = Path(cache_dir)
        self.lock_path = Path(lock_path)
        self.run_id = _nouveau_run_id()

        self.noeuds = charger_dag(dag_path)

        # UNE SEULE instance ApiIO pour toute la chaîne. C'est LE geste qui
        # corrige le défaut AS-IS (chaque run_*.py fabriquait la sienne, sans
        # budgets partagés). Budgets = donnée (api_pricing.yaml).
        if api_io is None:
            pricing = pricing or load_pricing()
            api_io = ApiIO(
                pricing,
                self.ledger_path,
                cache_dir=self.cache_dir,
                budgets=(pricing.get("budgets") or None),
                vault_path=self.vault_path,
            )
        self.api_io = api_io

        self.vault_io = VaultIO(self.vault_path)

        # Registre des adaptateurs. Surchargeable pour les tests (aucun réseau).
        self._runners: dict[str, RunnerNoeud] = {
            "preflight_gate": self._run_preflight_gate,
            "discovery": self._run_discovery,
            "diagnostic": self._run_diagnostic,
            "export": self._run_export,
            "usage_snapshot": self._run_usage_snapshot,
            "outreach": self._run_outreach,
        }
        if runners:
            self._runners.update(runners)

    # --- Prédicats d'idempotence (« nœud déjà satisfait ») ----------------

    def _est_satisfait(self, noeud: Noeud, ctx: ContexteRun) -> bool:
        """True si le travail du nœud est déjà fait → on le saute (reprise idempotente).

        Le diagnostic est satisfait quand il ne reste aucune fiche `decouvert`
        à traiter : re-lancer la chaîne au run suivant ne rediagnostique pas.
        Les autres nœuds ne définissent pas de court-circuit ici (la découverte
        est idempotente via la dédup vault ; l'export est lecture seule).
        """
        if noeud.nom == "diagnostic":
            return len(ctx.vault_io.query(statut="decouvert")) == 0
        return False

    # --- Boucle d'exécution -----------------------------------------------

    def executer(
        self,
        *,
        depuis: str | None = None,
        jusqu_a: str | None = None,
    ) -> list[ResultatNoeud]:
        """Exécute la chaîne en ordre topologique, sous verrou exclusif.

        --depuis / --jusqu-a restreignent la tranche exécutée (le reste du
        graphe reste dans l'ordre figé). Arrêt propre sur BudgetExceeded ou
        nœud bloquant. Le verrou est libéré en toute circonstance (try/finally
        via le context manager).
        """
        ordre = tri_topologique(self.noeuds)
        ordre = self._trancher(ordre, depuis, jusqu_a)

        ctx = ContexteRun(
            run_id=self.run_id,
            api_io=self.api_io,
            vault_io=self.vault_io,
            vault_path=self.vault_path,
            icp_id=self.icp_id,
            dry_run=self.dry_run,
            ledger_path=self.ledger_path,
            cache_dir=self.cache_dir,
        )

        resultats = ctx.resultats
        t_debut = datetime.now(timezone.utc)
        with RunLock(self.lock_path, self.run_id):
            for noeud in ordre:
                res = self._executer_noeud(noeud, ctx)
                resultats.append(res)
                # Arrêt de la chaîne : budget dépassé ou nœud bloquant/échec.
                if res.statut in ("budget_depasse", "bloque", "echec"):
                    break

        self._ecrire_manifeste(resultats, t_debut)
        return resultats

    def _executer_noeud(self, noeud: Noeud, ctx: ContexteRun) -> ResultatNoeud:
        if not noeud.enabled:
            return ResultatNoeud(noeud.nom, "desactive", "nœud désactivé dans le DAG")
        if self._est_satisfait(noeud, ctx):
            return ResultatNoeud(noeud.nom, "saute", "déjà satisfait (reprise idempotente)")
        runner = self._runners.get(noeud.nom)
        if runner is None:
            return ResultatNoeud(noeud.nom, "echec", f"aucun runner pour le nœud {noeud.nom!r}")
        try:
            res = runner(ctx)
            # Invariant : le résultat porte toujours le nom du nœud du DAG,
            # quelle que soit l'étiquette posée par l'adaptateur.
            res.nom = noeud.nom
            return res
        except BudgetExceeded as exc:
            # Arrêt propre : ce qui a déjà été écrit reste valide, la reprise
            # au run suivant est idempotente.
            return ResultatNoeud(noeud.nom, "budget_depasse", str(exc))

    @staticmethod
    def _trancher(
        ordre: list[Noeud], depuis: str | None, jusqu_a: str | None
    ) -> list[Noeud]:
        noms = [n.nom for n in ordre]
        i_debut = 0
        i_fin = len(ordre)
        if depuis is not None:
            if depuis not in noms:
                raise DagInvalide(f"--depuis : nœud inconnu {depuis!r}")
            i_debut = noms.index(depuis)
        if jusqu_a is not None:
            if jusqu_a not in noms:
                raise DagInvalide(f"--jusqu-a : nœud inconnu {jusqu_a!r}")
            i_fin = noms.index(jusqu_a) + 1
        return ordre[i_debut:i_fin]

    # --- Manifeste de corrélation -----------------------------------------

    def _ecrire_manifeste(self, resultats: list[ResultatNoeud], t_debut: datetime) -> None:
        """Trace le run (run_id + fenêtre temporelle + issues des nœuds).

        Cette fenêtre [t_debut, t_fin] sous un run_id unique corrèle a posteriori
        les lignes du journal d'écritures du vault ⇄ api_usage.log (toutes deux
        horodatées) : on n'a
        pas le droit de modifier le schéma de ces journaux, la corrélation se
        fait donc par intervalle temporel attribué au run_id. Écrit sous .cache/
        (gitignoré, hors vault). Best-effort : ne casse jamais le run.
        """
        try:
            _MANIFESTES_DIR.mkdir(parents=True, exist_ok=True)
            manifeste = {
                "run_id": self.run_id,
                "icp_id": self.icp_id,
                "dry_run": self.dry_run,
                "debut": t_debut.isoformat(),
                "fin": datetime.now(timezone.utc).isoformat(),
                "noeuds": [{"nom": r.nom, "statut": r.statut, "message": r.message}
                           for r in resultats],
            }
            (_MANIFESTES_DIR / f"{self.run_id}.json").write_text(
                json.dumps(manifeste, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass  # la trace est un confort, pas une condition de succès

    # --- Adaptateurs MINCES autour des entrypoints existants --------------
    #
    # Chaque runner branche un entrypoint J1-J5 SANS dupliquer sa logique.
    # Choix d'invocation (documenté) :
    #   - préflight : fonctions publiques diagnostic.preflight (décision de porte
    #     prise en process).
    #   - découverte : run_discovery.run(...) — l'unique ApiIO y est INJECTÉE.
    #   - diagnostic : run_diagnostic._build_pipeline(api_io) + vault_runner.run_vault_mode
    #     — l'unique ApiIO y est INJECTÉE ; c'est le code diagnostic qui fait la
    #     seule transition agent decouvert → diagnostique.
    #   - export / usage : fonctions publiques diagnostic.export / diagnostic.usage
    #     (aucun réseau, aucune injection ApiIO nécessaire).

    def _run_preflight_gate(self, ctx: ContexteRun) -> ResultatNoeud:
        from diagnostic.preflight import executer_preflights, verdict_global
        checks = executer_preflights(
            vault_path=ctx.vault_path,
            cache_dir=ctx.cache_dir,
            icp_id=ctx.icp_id,
        )
        go = verdict_global(checks)
        ko = [c.message for c in checks if c.niveau == "bloquant" and not c.ok]
        if go:
            return ResultatNoeud("preflight_gate", "execute", "GO — tous les bloquants OK")
        msg = "NO-GO — bloquants : " + "; ".join(ko[:5])
        if ctx.dry_run:
            # En dry-run on informe mais on n'arrête pas la chaîne (rien n'est écrit).
            return ResultatNoeud("preflight_gate", "execute", "[DRY] " + msg)
        return ResultatNoeud("preflight_gate", "bloque", msg)

    def _run_discovery(self, ctx: ContexteRun) -> ResultatNoeud:
        if ctx.icp_id is None:
            return ResultatNoeud("discovery", "echec", "--icp requis pour la découverte")
        import run_discovery  # entrypoint éditable : expose run(...) injectable
        run_discovery.run(
            icp_id=ctx.icp_id,
            vault=ctx.vault_path,
            dry_run=ctx.dry_run,
            api_io=ctx.api_io,  # l'unique ApiIO — pas une nouvelle instance
        )
        return ResultatNoeud("discovery", "execute", f"découverte {ctx.icp_id}")

    def _run_diagnostic(self, ctx: ContexteRun) -> ResultatNoeud:
        from diagnostic.vault_runner import run_vault_mode
        import run_diagnostic  # entrypoint éditable : _build_pipeline(api_io)
        if ctx.dry_run:
            n = len(ctx.vault_io.query(statut="decouvert"))
            return ResultatNoeud("diagnostic", "execute", f"[DRY] {n} fiche(s) decouvert à diagnostiquer")
        # UNE seule ApiIO injectée ; run_vault_mode fait la seule transition
        # agent autorisée : decouvert → diagnostique. Factory (pas un pipeline
        # unique construit ici) : chaque secteur rencontré dans le lot reçoit
        # SA rubrique/vocabulaire (ADR 0003, correction de B4).
        resultat = run_vault_mode(
            ctx.vault_path,
            lambda secteur_id: run_diagnostic._build_pipeline(secteur_id, api_io=ctx.api_io),
        )
        return ResultatNoeud(
            "diagnostic", "execute",
            f"{len(resultat['ok'])} diagnostiquée(s), {len(resultat['erreurs'])} erreur(s)",
        )

    def _run_export(self, ctx: ContexteRun) -> ResultatNoeud:
        # Fonctions publiques J5 (lecture seule, hors vault). Aucun réseau.
        from datetime import date
        from diagnostic.export import (
            charger_schema_kemana,
            collect_fiches_exportables,
            fiche_vers_ligne_kemana,
            lignes_vers_csv,
            verifier_chemin_hors_vault,
        )
        colonnes = charger_schema_kemana()
        fiches = collect_fiches_exportables(ctx.vault_io, icp_id=ctx.icp_id)
        lignes = [fiche_vers_ligne_kemana(f, colonnes) for f in fiches]
        if ctx.dry_run:
            return ResultatNoeud("export", "execute", f"[DRY] {len(lignes)} fiche(s) exportable(s)")
        suffixe = (ctx.icp_id or "tous").replace("/", "-")
        out = _RACINE / "exports" / f"kemana_{suffixe}_{date.today().isoformat()}.csv"
        verifier_chemin_hors_vault(out, ctx.vault_path)  # garde-fou : jamais dans le vault
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(lignes_vers_csv(lignes, colonnes))
        return ResultatNoeud("export", "execute", f"{len(lignes)} fiche(s) → {out.name}")

    def _run_usage_snapshot(self, ctx: ContexteRun) -> ResultatNoeud:
        # Fonctions publiques J5. Le snapshot passe par le bus vault (write_system_note).
        from datetime import date
        from diagnostic.usage import agreger, charger_ledger, formater_rapport
        entries = charger_ledger(ctx.ledger_path)
        rapport = formater_rapport(agreger(entries))
        if ctx.dry_run:
            return ResultatNoeud("usage_snapshot", "execute", "[DRY] rapport usage non écrit")
        ctx.vault_io.write_system_note(f"usage-{date.today().isoformat()}.md", rapport)
        return ResultatNoeud("usage_snapshot", "execute", "snapshot usage écrit")

    def _run_outreach(self, ctx: ContexteRun) -> ResultatNoeud:
        # J6 hors périmètre J+30 : placeholder no-op qui REFUSE de s'exécuter.
        # Il n'est atteint que si quelqu'un force enabled: true dans le DAG.
        return ResultatNoeud(
            "outreach", "bloque",
            "outreach (J6) non implémenté — porte humaine, activer après validation juridique",
        )


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def _nouveau_run_id() -> str:
    """Identifiant de run unique : horodaté (tri naturel) + suffixe aléatoire."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{ts}-{uuid.uuid4().hex[:6]}"
