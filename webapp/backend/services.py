"""
services.py — adaptateurs lecture seule au-dessus du package `diagnostic`.

Pourquoi cette couche : les routes FastAPI (app.py) restent minces et ignorent
tout du package `diagnostic`. Ici, et ici seulement, on touche VaultIO, usage,
preflight, icp_schema. Aucune écriture, aucun réseau : on n'appelle jamais
`.write_*`, `.transition`, `.update_frontmatter`, ni `api_io`. C'est une façade
de consultation, conforme au contrat « API strictement read-only ».
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

# --- Amorçage du sys.path : rendre `diagnostic` importable depuis la racine ---
# webapp/backend/services.py → parents[2] == racine du repo.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import yaml  # noqa: E402  (import après manip sys.path — volontaire)

from diagnostic.icp_schema import IcpConfig  # noqa: E402
from diagnostic.preflight import executer_preflights, verdict_global  # noqa: E402
from diagnostic.usage import agreger, charger_ledger  # noqa: E402
from diagnostic.vault_io import VaultIO  # noqa: E402

from webapp.backend import greenit as greenit_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Résolution des chemins (surchargables par variables d'environnement)
# ---------------------------------------------------------------------------

def repo_root() -> Path:
    return _REPO_ROOT


def vault_path() -> Path:
    """Racine du vault. VAULT_PATH prime, sinon <repo>/vault (défaut système)."""
    env = os.getenv("VAULT_PATH")
    return Path(env).resolve() if env else (_REPO_ROOT / "vault")


def ledger_path() -> Path:
    """Grand livre d'usage. Peut être absent → agrégat vide."""
    env = os.getenv("API_USAGE_LOG")
    return Path(env).resolve() if env else (_REPO_ROOT / "api_usage.log")


def runs_log_path() -> Path:
    env = os.getenv("RUNS_LOG")
    return Path(env).resolve() if env else (_REPO_ROOT / "runs.log")


def icp_dir() -> Path:
    return _REPO_ROOT / "icp"


def _preflight_root() -> Path:
    """Racine passée à executer_preflights (contrôle tests_verts).

    Pourquoi un override : le contrôle `tests_verts` lance `pytest tests/` en
    sous-processus (jusqu'à 120 s). En contexte de test d'API on veut éviter ce
    coût ; PREFLIGHT_ROOT_DIR permet de pointer ailleurs. En production, on
    laisse la racine réelle du repo.
    """
    env = os.getenv("PREFLIGHT_ROOT_DIR")
    return Path(env).resolve() if env else _REPO_ROOT


def _vault_io() -> VaultIO:
    """Instancie le bus vault en lecture. Ne crée rien, ne journalise rien
    tant qu'on n'appelle que query/read_fiche."""
    return VaultIO(vault_path())


# ---------------------------------------------------------------------------
# Helpers de sérialisation
# ---------------------------------------------------------------------------

def _iso(value: object) -> str | None:
    """Normalise une date/datetime en chaîne ISO ; laisse les str tels quels."""
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


# ---------------------------------------------------------------------------
# 1. Santé
# ---------------------------------------------------------------------------

def get_health() -> dict:
    vp = vault_path()
    # « initialisé » = présence du dossier des prospects (source des fiches).
    initialise = (vp / "10-Prospects").is_dir()
    return {
        "status": "ok",
        "vault_path": str(vp),
        "vault_initialise": initialise,
    }


# ---------------------------------------------------------------------------
# 2. Préflight
# ---------------------------------------------------------------------------

def get_preflight(icp_id: str | None = None) -> dict:
    checks = executer_preflights(
        vault_path=vault_path(),
        icp_id=icp_id,
        root_dir=_preflight_root(),
    )
    verdict = "GO" if verdict_global(checks) else "NO-GO"
    return {
        "verdict": verdict,
        "checks": [
            {"nom": c.nom, "niveau": c.niveau, "ok": c.ok, "message": c.message}
            for c in checks
        ],
    }


# ---------------------------------------------------------------------------
# 3. Entonnoir pipeline
# ---------------------------------------------------------------------------

_ETATS = ("decouvert", "diagnostique", "valide", "contacte", "rejete")


def get_funnel() -> dict:
    etats = {e: 0 for e in _ETATS}
    total = 0
    for _path, fiche in _vault_io().query():  # vault vide → [] → funnel à zéro
        statut = str(fiche.statut)
        if statut in etats:
            etats[statut] += 1
        total += 1
    return {"total": total, "etats": etats}


# ---------------------------------------------------------------------------
# 4-5. Prospects
# ---------------------------------------------------------------------------

def _fiche_to_list_item(path: Path, fiche) -> dict:
    return {
        "slug": path.stem,  # unique : VaultIO garantit des slugs sans collision
        "nom": fiche.nom,
        "site_web": fiche.site_web,
        "statut": str(fiche.statut),
        "persona": int(fiche.persona),
        "marche": str(fiche.marche),
        "score_global": fiche.score_global,
        "signal_chaud": fiche.signal_chaud,
        "gaps_majeurs": list(fiche.gaps_majeurs or []),
        "date_creation": _iso(fiche.date_creation),
        "date_diagnostic": _iso(fiche.date_diagnostic),
        "icp_id": fiche.icp_id,
        "opt_out": bool(fiche.opt_out),
        "contact_nom": fiche.contact_nom,
        "contact_email": fiche.contact_email,
    }


def list_prospects(
    statut: str | None = None,
    persona: int | None = None,
    marche: str | None = None,
) -> list[dict]:
    io = _vault_io()
    fiches = io.query(statut=statut, persona=persona, marche=marche)
    return [_fiche_to_list_item(path, fiche) for path, fiche in fiches]


def _resolve_rapport_md(fiche) -> str | None:
    """Lit le fichier 30-Diagnostics/*.md référencé par le wikilink `rapport`.

    Le wikilink a la forme `[[30-Diagnostics/<stem>]]`. On borne strictement la
    lecture au dossier 30-Diagnostics du vault (défense en profondeur contre un
    wikilink pointant ailleurs). Retourne None si absent/illisible.
    """
    lien = fiche.rapport
    if not lien:
        return None
    cible = lien.strip().strip("[]").strip()  # "30-Diagnostics/<stem>"
    # On ne garde que le nom de fichier pour éviter toute traversée de chemin.
    stem = Path(cible).name
    if not stem:
        return None
    rapport_path = (vault_path() / "30-Diagnostics" / f"{stem}.md").resolve()
    diag_dir = (vault_path() / "30-Diagnostics").resolve()
    try:
        rapport_path.relative_to(diag_dir)  # confine au dossier des diagnostics
    except ValueError:
        return None
    if not rapport_path.is_file():
        return None
    try:
        return rapport_path.read_text(encoding="utf-8")
    except OSError:
        return None


def get_prospect(slug: str) -> dict | None:
    """Retrouve une fiche par son slug (== path.stem). None si introuvable."""
    io = _vault_io()
    for path, fiche in io.query():
        if path.stem == slug:
            return {
                "fiche": fiche.model_dump(mode="json"),
                "rapport_md": _resolve_rapport_md(fiche),
            }
    return None


# ---------------------------------------------------------------------------
# 6. Usage
# ---------------------------------------------------------------------------

def get_usage(depuis: str | None = None) -> dict:
    depuis_date: date | None = None
    if depuis:
        # Erreur de format → remontée par app.py en 400 clair.
        depuis_date = date.fromisoformat(depuis)

    entries = charger_ledger(ledger_path(), depuis=depuis_date)
    usage = agreger(entries)

    par_fournisseur = [
        {
            "fournisseur": nom,
            "nb_appels": stat.nb_appels,
            "cout_total": round(stat.cout_total, 6),
            "unites": dict(stat.unites),
        }
        for nom, stat in sorted(usage.par_fournisseur.items())
    ]
    top_fiches = [
        {"fiche": nom, "cout": round(cout, 6)}
        for nom, cout in sorted(
            usage.par_fiche.items(), key=lambda kv: kv[1], reverse=True
        )[:10]
    ]
    return {
        "cout_total_usd": round(usage.cout_total, 6),
        "devise": "USD",
        "nb_appels": usage.nb_appels,
        "nb_cache_hits": usage.nb_cache_hits,
        "taux_cache": round(usage.taux_cache, 4),
        "par_fournisseur": par_fournisseur,
        "top_fiches": top_fiches,
    }


# ---------------------------------------------------------------------------
# 6 bis. GreenIT — agrégat d'efficience + suivi temps réel du ledger
# ---------------------------------------------------------------------------

def get_greenit(depuis: str | None = None) -> dict:
    """Agrégat coût / énergie / CO2e / octets du grand livre.

    Lecture volontairement défensive (voir greenit.py) : fonctionne avec un
    ledger absent, ancien (sans champs GreenIT) ou fraîchement instrumenté.
    """
    depuis_date: date | None = None
    if depuis:
        # Erreur de format → remontée par app.py en 400 clair.
        depuis_date = date.fromisoformat(depuis)

    path = ledger_path()
    lignes, illisibles = greenit_mod.lire_ledger(path, depuis=depuis_date)
    agregat = greenit_mod.agreger(lignes, nb_illisibles=illisibles)
    agregat["ledger_present"] = path.is_file()
    agregat["ledger_path"] = str(path)
    return agregat


def greenit_tail(*, depuis_debut: bool = False) -> greenit_mod.LedgerTail:
    """Instancie un suiveur incrémental du ledger (utilisé par le flux SSE)."""
    return greenit_mod.LedgerTail(ledger_path(), depuis_debut=depuis_debut)


def greenit_historique(n: int) -> list[dict]:
    """Les `n` derniers appels journalisés, pour amorcer le flux temps réel."""
    return greenit_mod.dernieres_lignes(ledger_path(), n)


# ---------------------------------------------------------------------------
# 7. ICP
# ---------------------------------------------------------------------------

def list_icp() -> list[dict]:
    d = icp_dir()
    if not d.is_dir():
        return []
    out: list[dict] = []
    for f in sorted(d.glob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            cfg = IcpConfig.model_validate(data)
        except Exception:
            # ICP illisible/invalide → ignoré (dégradation propre).
            continue
        out.append(
            {
                "icp_id": cfg.icp_id,
                "persona": cfg.persona,
                "marche": cfg.marche,
                "description": cfg.description,
            }
        )
    return out


# ---------------------------------------------------------------------------
# 8. Runs
# ---------------------------------------------------------------------------

def list_runs(limit: int = 50) -> list[dict]:
    """Dernières lignes de runs.log (JSONL), les plus récentes d'abord.

    Best-effort : fichier absent → [] ; ligne illisible → ignorée.
    """
    path = runs_log_path()
    if not path.is_file():
        return []
    try:
        lignes = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    objets: list[dict] = []
    for line in lignes:
        line = line.strip()
        if not line:
            continue
        try:
            objets.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    # Les plus récentes d'abord, bornées à `limit`.
    objets.reverse()
    if limit is not None and limit >= 0:
        objets = objets[:limit]
    return objets
