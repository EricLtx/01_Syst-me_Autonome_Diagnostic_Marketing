"""
api_io.py — contrôleur de bus d'I/O périphérique (§5 de la spec J3).

Seul module autorisé à toucher le réseau externe. Convention appliquée par
le test §9.6 (AST walk sur imports requests / anthropic).

Chaque appel est :
  - caché idempotent (disque, hors vault)
  - soumis à un budget configurable (interruption avant appel si dépassé)
  - journalisé dans api_usage.log (JSONL, append-only) avec unités et coût estimé

Dans l'analogie micro-ordinateur : ceci est le contrôleur DMA réseau.
Comme vault_io médie le stockage, api_io médie le réseau. Aucun module
extérieur n'ouvre une socket directement.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from diagnostic.api_schema import LedgerEntry, compute_cout


# ---------------------------------------------------------------------------
# Exception publique
# ---------------------------------------------------------------------------

class BudgetExceeded(Exception):
    """Levée avant l'appel réseau si le plafond budgétaire serait dépassé."""


# ---------------------------------------------------------------------------
# Mesureurs par fournisseur (réponse brute → dict d'unités)
# ---------------------------------------------------------------------------

def mesurer_anthropic(reponse: Any) -> dict[str, float]:
    """Extrait les tokens depuis l'objet Message d'Anthropic."""
    usage = reponse.usage
    unites: dict[str, float] = {
        "input_tokens":  float(getattr(usage, "input_tokens",  0) or 0),
        "output_tokens": float(getattr(usage, "output_tokens", 0) or 0),
    }
    for champ in ("cache_read_input_tokens", "cache_creation_input_tokens"):
        val = getattr(usage, champ, None)
        if val:
            unites[champ] = float(val)
    return unites


MESUREURS_DEFAUT: dict[str, Callable[[Any], dict[str, float]]] = {
    "anthropic":     mesurer_anthropic,
    "serp":          lambda r: {"requetes": 1.0},
    "google_places": lambda r: {"requetes": 1.0},
    "http":          lambda r: {"requetes": 1.0},
    "apollo":        lambda r: {"credits": 1.0},
}


# ---------------------------------------------------------------------------
# ApiIO — contrôleur de bus
# ---------------------------------------------------------------------------

class ApiIO:
    """Bus controller I/O : seul module autorisé à appeler le réseau externe.

    Paramètres
    ----------
    pricing    : grille tarifaire chargée depuis knowledge/api_pricing.yaml
    ledger_path: chemin de api_usage.log (hors vault, append-only)
    cache_dir  : répertoire cache disque ; si None, cache désactivé
    budgets    : { "fournisseur": {"cout_max": X} | {"unites_max": {"unite": N}} }
    vault_path : si fourni, vérifie que cache_dir est hors du vault
    """

    def __init__(
        self,
        pricing: dict,
        ledger_path: Path,
        cache_dir: Path | None = None,
        budgets: dict | None = None,
        vault_path: Path | None = None,
    ) -> None:
        self.pricing = pricing
        self._ledger = Path(ledger_path)
        self._budgets = budgets or {}
        self._cache_dir: Path | None = Path(cache_dir) if cache_dir else None

        # Guard : cache hors vault (même esprit que contrainte G9 de J2)
        if self._cache_dir is not None and vault_path is not None:
            cache_res = self._cache_dir.resolve()
            vault_res = Path(vault_path).resolve()
            try:
                cache_res.relative_to(vault_res)
                raise RuntimeError(
                    f"Cache ({cache_res}) est situé DANS le vault ({vault_res}). "
                    "Le cache d'appels API doit rester hors du vault."
                )
            except ValueError:
                pass  # cache bien hors du vault

        # Registres en mémoire (recalculés depuis le ledger au démarrage)
        self._registres: dict[str, dict[str, Any]] = self._charger_registres()

    # --- Registres --------------------------------------------------------

    def _charger_registres(self) -> dict[str, dict[str, Any]]:
        """Recompute totaux courants depuis le ledger. Source de vérité = fichier."""
        registres: dict[str, dict[str, Any]] = {}
        if not self._ledger.exists():
            return registres
        for line in self._ledger.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = LedgerEntry.from_jsonl(line)
            except Exception:
                continue
            # Les cache hits et les interruptions budget ne comptent pas dans les totaux
            if entry.cache_hit or entry.resultat == "budget_depasse":
                continue
            reg = registres.setdefault(entry.fournisseur, {"cout": 0.0, "unites": {}})
            reg["cout"] += entry.cout_estime
            for k, v in entry.unites.items():
                reg["unites"][k] = reg["unites"].get(k, 0.0) + v
        return registres

    def _mettre_a_jour_registres(self, fournisseur: str, unites: dict, cout: float) -> None:
        reg = self._registres.setdefault(fournisseur, {"cout": 0.0, "unites": {}})
        reg["cout"] += cout
        for k, v in unites.items():
            reg["unites"][k] = reg["unites"].get(k, 0.0) + v

    # --- Budget -----------------------------------------------------------

    def _unites_precheck(self, fournisseur: str, endpoint: str) -> dict[str, float]:
        """Unités minimales pour le budget pre-check (1 par unité tarifée).

        Pour les APIs à coût fixe (serp : 1 requête = 0,01 $), l'estimation est
        exacte. Pour les APIs token-based (anthropic), c'est un minorant ; le
        pre-check protège du dépassement gross mais pas de chaque token.
        """
        try:
            prix = self.pricing["fournisseurs"][fournisseur]["endpoints"][endpoint]["prix_par_unite"]
            return {k: 1.0 for k in prix}
        except KeyError:
            return {"requetes": 1.0}

    def _verifier_budget(
        self, fournisseur: str, unites: dict[str, float], cout: float
    ) -> None:
        contrainte = self._budgets.get(fournisseur, {})
        if not contrainte:
            return
        reg = self._registres.get(fournisseur, {"cout": 0.0, "unites": {}})

        if "cout_max" in contrainte:
            if reg["cout"] + cout > contrainte["cout_max"]:
                raise BudgetExceeded(
                    f"{fournisseur} : plafond coût dépassé "
                    f"({reg['cout']:.6f} + {cout:.6f} > {contrainte['cout_max']} USD)"
                )

        if "unites_max" in contrainte:
            for unite, max_val in contrainte["unites_max"].items():
                actuel = reg["unites"].get(unite, 0.0)
                prochain = unites.get(unite, 0.0)
                if actuel + prochain > max_val:
                    raise BudgetExceeded(
                        f"{fournisseur} : plafond unités dépassé "
                        f"({unite} : {actuel} + {prochain} > {max_val})"
                    )

    # --- Cache disque -----------------------------------------------------

    def _cache_path(self, fournisseur: str, endpoint: str, cache_key: str) -> Path:
        assert self._cache_dir is not None
        digest = hashlib.sha256(
            f"{fournisseur}:{endpoint}:{cache_key}".encode()
        ).hexdigest()[:24]
        return self._cache_dir / f"{fournisseur}_{endpoint}_{digest}.json"

    def _lire_cache(self, fournisseur: str, endpoint: str, cache_key: str) -> Any:
        if self._cache_dir is None:
            return None
        path = self._cache_path(fournisseur, endpoint, cache_key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _ecrire_cache(
        self, fournisseur: str, endpoint: str, cache_key: str, reponse: Any
    ) -> None:
        if self._cache_dir is None:
            return
        path = self._cache_path(fournisseur, endpoint, cache_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = json.dumps(reponse, ensure_ascii=False)
        except (TypeError, ValueError):
            return  # réponse non sérialisable JSON → cache silencieusement ignoré
        path.write_text(data, encoding="utf-8")

    # --- Journal ----------------------------------------------------------

    def _journaliser(
        self,
        fournisseur: str,
        endpoint: str,
        unites: dict[str, float],
        cout: float,
        fiche: str | None,
        cache_hit: bool,
        resultat: str,
        detail: str = "",
    ) -> None:
        entry = LedgerEntry.maintenant(
            fournisseur=fournisseur,
            endpoint=endpoint,
            unites=unites,
            cout_estime=cout,
            devise=self.pricing.get("devise", "USD"),
            fiche=fiche,
            cache_hit=cache_hit,
            resultat=resultat,
            detail=detail,
        )
        self._ledger.parent.mkdir(parents=True, exist_ok=True)
        with self._ledger.open("a", encoding="utf-8") as f:
            f.write(entry.to_jsonl() + "\n")

    # --- API publique -----------------------------------------------------

    def call(
        self,
        fournisseur: str,
        endpoint: str,
        fn: Callable[[], Any],
        *,
        fiche: str | None = None,
        cache_key: str | None = None,
        measure: Callable[[Any], dict[str, float]] | None = None,
    ) -> Any:
        """Médiatise un appel réseau externe.

        1. Cache hit → retourne valeur cachée, journalise cache_hit=True, cout=0.
        2. Budget pre-check → BudgetExceeded si plafond atteint (fn jamais appelée).
        3. Exécute fn().
        4. Mesure les unités consommées (mesureur fourni ou défaut par fournisseur).
        5. Calcule le coût depuis pricing, journalise une LedgerEntry.
        6. Met en cache si cache_key fourni et réponse sérialisable.
        Retourne la réponse brute de fn().
        """
        # 1. Cache hit
        if cache_key is not None:
            cached = self._lire_cache(fournisseur, endpoint, cache_key)
            if cached is not None:
                self._journaliser(fournisseur, endpoint, {}, 0.0, fiche, True, "ok")
                return cached

        # 2. Budget pre-check (estimé sur 1 unité avant d'appeler)
        unites_pre = self._unites_precheck(fournisseur, endpoint)
        cout_pre = compute_cout(self.pricing, fournisseur, endpoint, unites_pre)
        try:
            self._verifier_budget(fournisseur, unites_pre, cout_pre)
        except BudgetExceeded as exc:
            self._journaliser(
                fournisseur, endpoint, unites_pre, cout_pre,
                fiche, False, "budget_depasse", str(exc),
            )
            raise

        # 3. Exécuter fn()
        try:
            reponse = fn()
        except Exception as exc:
            self._journaliser(fournisseur, endpoint, {}, 0.0, fiche, False, "erreur", str(exc))
            raise

        # 4. Mesure réelle des unités
        mesureur = measure or MESUREURS_DEFAUT.get(fournisseur, lambda r: {"requetes": 1.0})
        try:
            unites = mesureur(reponse)
        except Exception:
            unites = {"requetes": 1.0}
        cout = compute_cout(self.pricing, fournisseur, endpoint, unites)

        # 5. Journaliser
        self._journaliser(fournisseur, endpoint, unites, cout, fiche, False, "ok")

        # 6. Mettre à jour les registres en mémoire
        self._mettre_a_jour_registres(fournisseur, unites, cout)

        # 7. Écrire dans le cache
        if cache_key is not None:
            self._ecrire_cache(fournisseur, endpoint, cache_key, reponse)

        return reponse
