"""
preflight.py — vérifications GO / NO-GO avant le premier run réel (§7 de la spec J5).

Aucun réseau. Aucune clé utilisée (on vérifie leur présence, pas leur validité).
Sortie : liste de Check + verdict global (0=GO / 1=NO-GO pour run_preflight.py).

9 contrôles dans l'ordre de la spec :
  1. cles_api       — variables d'environnement présentes
  2. tarifs_reels   — prix non-placeholder + releve_le daté
  3. budgets        — garde-fous financiers > 0
  4. vault_initialise — dossiers vault créés
  5. cache_hors_vault — cache_dir pas sous vault/
  6. icp_valide     — au moins un ICP chargeable
  7. schema_export  — export_kemana.yaml cohérent
  8. tests_verts    — pytest -q passe
  9. garde_fous_bus — AST : pas de réseau ni d'écriture directe dans les modules J5
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

_MODULE_DIR = Path(__file__).resolve().parent
_KNOWLEDGE_DIR = _MODULE_DIR.parent / "knowledge"
_ICP_DIR = _MODULE_DIR.parent / "icp"

Niveau = Literal["bloquant", "warn"]


@dataclass
class Check:
    nom: str
    niveau: Niveau
    ok: bool
    message: str


# ---------------------------------------------------------------------------
# Contrôles individuels
# ---------------------------------------------------------------------------

def _check_cles_api() -> list[Check]:
    checks: list[Check] = []
    obligatoires = [("SERP_API_KEY", "bloquant"), ("APOLLO_API_KEY", "bloquant")]
    optionnelles = [("GOOGLE_PLACES_API_KEY", "warn"), ("ANTHROPIC_API_KEY", "warn")]
    for var, niveau in obligatoires + optionnelles:
        present = bool(os.getenv(var))
        checks.append(Check(
            nom="cles_api",
            niveau=niveau,
            ok=present,
            message=f"{var} {'présente' if present else 'ABSENTE'}",
        ))
    return checks


def _check_tarifs_reels(pricing_path: Path) -> list[Check]:
    try:
        pricing = yaml.safe_load(pricing_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [Check("tarifs_reels", "bloquant", False, f"Impossible de lire api_pricing.yaml : {exc}")]

    checks: list[Check] = []

    releve = pricing.get("releve_le")
    checks.append(Check(
        nom="tarifs_reels",
        niveau="bloquant",
        ok=bool(releve),
        message=f"releve_le = {releve!r}" + ("" if releve else " — À RENSEIGNER"),
    ))

    _SENTINELLES = {0, 0.0, None, "TODO", "placeholder", ""}
    for fourn in ("serp", "apollo"):
        fourn_cfg = pricing.get("fournisseurs", {}).get(fourn, {})
        endpoints = fourn_cfg.get("endpoints", {})
        for ep_nom, ep_cfg in endpoints.items():
            for unite, prix in (ep_cfg.get("prix_par_unite") or {}).items():
                ok = prix not in _SENTINELLES
                checks.append(Check(
                    nom="tarifs_reels",
                    niveau="bloquant",
                    ok=ok,
                    message=f"{fourn}.{ep_nom}.{unite} = {prix!r}"
                            + ("" if ok else " — placeholder, À RENSEIGNER"),
                ))
    return checks


def _check_budgets(pricing_path: Path) -> list[Check]:
    try:
        pricing = yaml.safe_load(pricing_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [Check("budgets", "bloquant", False, f"Impossible de lire api_pricing.yaml : {exc}")]

    budgets = pricing.get("budgets") or {}
    checks: list[Check] = []
    for fourn in ("serp", "apollo"):
        fourn_budgets = budgets.get(fourn, {})
        unites_max = fourn_budgets.get("unites_max", {})
        if not unites_max:
            checks.append(Check(
                "budgets", "bloquant", False,
                f"budgets.{fourn}.unites_max absent — À RENSEIGNER",
            ))
            continue
        for unite, valeur in unites_max.items():
            ok = isinstance(valeur, (int, float)) and valeur > 0
            checks.append(Check(
                nom="budgets",
                niveau="bloquant",
                ok=ok,
                message=f"budgets.{fourn}.{unite} = {valeur!r}"
                        + ("" if ok else " — 0 = non configuré, À RENSEIGNER"),
            ))
    return checks


def _check_vault_initialise(vault_path: Path) -> list[Check]:
    dossiers_attendus = [
        "10-Prospects",
        "20-Rubrics",
        "30-Diagnostics",
        "90-Systeme",
    ]
    checks: list[Check] = []
    for d in dossiers_attendus:
        ok = (vault_path / d).is_dir()
        checks.append(Check(
            nom="vault_initialise",
            niveau="bloquant",
            ok=ok,
            message=f"vault/{d}/" + (" OK" if ok else " ABSENT — lancer init_vault.py"),
        ))
    return checks


def _check_cache_hors_vault(vault_path: Path, cache_dir: Path) -> Check:
    vault_resolved = vault_path.resolve()
    cache_resolved = cache_dir.resolve()
    in_vault = False
    try:
        cache_resolved.relative_to(vault_resolved)
        in_vault = True
    except ValueError:
        pass
    return Check(
        nom="cache_hors_vault",
        niveau="bloquant",
        ok=not in_vault,
        message=f"cache_dir={cache_dir}" + (" — DANS le vault ! (contrainte G9)" if in_vault else " — hors vault OK"),
    )


def _check_icp_valide(icp_id: str | None = None) -> list[Check]:
    icp_files = sorted(_ICP_DIR.glob("*.yaml")) if _ICP_DIR.is_dir() else []
    if not icp_files:
        return [Check("icp_valide", "bloquant", False, "Aucun fichier ICP trouvé dans icp/")]

    checks: list[Check] = []
    if icp_id is not None:
        target = _ICP_DIR / f"{icp_id}.yaml"
        ok = target.exists()
        if ok:
            try:
                yaml.safe_load(target.read_text(encoding="utf-8"))
            except Exception as exc:
                ok = False
                checks.append(Check("icp_valide", "bloquant", False, f"{icp_id}.yaml invalide : {exc}"))
                return checks
        checks.append(Check(
            "icp_valide", "bloquant", ok,
            f"icp/{icp_id}.yaml" + (" OK" if ok else " INTROUVABLE"),
        ))
    else:
        chargeable = 0
        for f in icp_files:
            try:
                yaml.safe_load(f.read_text(encoding="utf-8"))
                chargeable += 1
            except Exception:
                pass
        ok = chargeable > 0
        checks.append(Check(
            "icp_valide", "bloquant", ok,
            f"{chargeable}/{len(icp_files)} ICP chargeables" + ("" if ok else " — AUCUN"),
        ))
    return checks


def _check_schema_export() -> Check:
    from diagnostic.export import charger_schema_kemana
    try:
        colonnes = charger_schema_kemana()
        return Check("schema_export", "bloquant", True, f"{len(colonnes)} colonnes Kemana OK")
    except FileNotFoundError:
        return Check("schema_export", "bloquant", False, "export_kemana.yaml introuvable")
    except ValueError as exc:
        return Check("schema_export", "bloquant", False, f"Schéma invalide : {exc}")


def _check_tests_verts(root_dir: Path, *, strict: bool = False) -> Check:
    niveau: Niveau = "bloquant" if strict else "warn"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no", "--no-header"],
            capture_output=True,
            text=True,
            cwd=root_dir,
            timeout=120,
        )
        ok = result.returncode == 0
        resume = (result.stdout.strip().splitlines() or ["(pas de sortie)"])[-1]
        return Check("tests_verts", niveau, ok, resume)
    except subprocess.TimeoutExpired:
        return Check("tests_verts", niveau, False, "pytest timeout (> 120s)")
    except Exception as exc:
        return Check("tests_verts", niveau, False, f"Impossible de lancer pytest : {exc}")


def _ast_module_importe(source: str, interdits: set[str]) -> list[str]:
    """Retourne la liste des modules interdits importés au niveau module dans source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    trouves: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                racine = alias.name.split(".")[0]
                if racine in interdits:
                    trouves.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                racine = node.module.split(".")[0]
                if racine in interdits:
                    trouves.append(node.module)
    return trouves


def _check_garde_fous_bus() -> list[Check]:
    """AST walk : les modules J5 n'importent ni requests ni anthropic au niveau module."""
    modules_j5 = [
        _MODULE_DIR / "export.py",
        _MODULE_DIR / "usage.py",
        _MODULE_DIR / "preflight.py",
        _MODULE_DIR.parent / "run_export.py",
        _MODULE_DIR.parent / "run_usage.py",
        _MODULE_DIR.parent / "run_preflight.py",
    ]
    interdits = {"requests", "anthropic"}
    checks: list[Check] = []
    for module_path in modules_j5:
        if not module_path.exists():
            checks.append(Check(
                "garde_fous_bus", "warn", True,
                f"{module_path.name} absent (pas encore créé)",
            ))
            continue
        source = module_path.read_text(encoding="utf-8")
        violations = _ast_module_importe(source, interdits)
        ok = len(violations) == 0
        checks.append(Check(
            nom="garde_fous_bus",
            niveau="bloquant",
            ok=ok,
            message=f"{module_path.name} : {'aucun import interdit' if ok else 'VIOLATION ' + str(violations)}",
        ))
    return checks


# ---------------------------------------------------------------------------
# Orchestrateur
# ---------------------------------------------------------------------------

def executer_preflights(
    *,
    vault_path: Path = Path("vault"),
    cache_dir: Path = Path(".cache/api_io"),
    pricing_path: Path | None = None,
    icp_id: str | None = None,
    strict: bool = False,
    root_dir: Path | None = None,
) -> list[Check]:
    """Exécute les 9 contrôles et retourne la liste complète de Check."""
    _pricing = pricing_path or _KNOWLEDGE_DIR / "api_pricing.yaml"
    _root = root_dir or _MODULE_DIR.parent

    checks: list[Check] = []
    checks += _check_cles_api()
    checks += _check_tarifs_reels(_pricing)
    checks += _check_budgets(_pricing)
    checks += _check_vault_initialise(vault_path)
    checks.append(_check_cache_hors_vault(vault_path, cache_dir))
    checks += _check_icp_valide(icp_id)
    checks.append(_check_schema_export())
    checks.append(_check_tests_verts(_root, strict=strict))
    checks += _check_garde_fous_bus()
    return checks


def verdict_global(checks: list[Check]) -> bool:
    """True = GO (tous les bloquants sont OK). False = NO-GO."""
    return all(c.ok for c in checks if c.niveau == "bloquant")


def formater_rapport(checks: list[Check]) -> str:
    lignes = ["# Rapport préflight J5", ""]
    nom_courant = None
    for c in checks:
        if c.nom != nom_courant:
            nom_courant = c.nom
            lignes.append(f"\n## {c.nom}")
        statut = "✅" if c.ok else ("❌" if c.niveau == "bloquant" else "⚠️")
        lignes.append(f"  {statut} [{c.niveau}] {c.message}")
    return "\n".join(lignes) + "\n"
