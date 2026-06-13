"""
usage.py — agrégation du grand livre d'usage API (§6 de la spec J5).

Fonctions pures sans I/O réseau. charger_ledger() est le seul I/O (lecture fichier).
Le snapshot vault est géré par run_usage.py via vault_io.write_system_note().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from diagnostic.api_schema import LedgerEntry


@dataclass
class UsageParFournisseur:
    cout_total: float = 0.0
    unites: dict[str, float] = field(default_factory=dict)
    nb_appels: int = 0


@dataclass
class Usage:
    """Résultat agrégé du grand livre d'usage."""
    nb_entrees: int = 0
    nb_erreurs_lecture: int = 0     # lignes JSONL illisibles (tronquées, corrompues)
    cout_total: float = 0.0
    nb_appels: int = 0              # hors cache hits
    nb_cache_hits: int = 0
    par_fournisseur: dict[str, UsageParFournisseur] = field(default_factory=dict)
    par_fiche: dict[str, float] = field(default_factory=dict)  # fiche → cout total

    @property
    def taux_cache(self) -> float:
        total = self.nb_appels + self.nb_cache_hits
        return self.nb_cache_hits / total if total else 0.0


def charger_ledger(
    path: Path,
    *,
    depuis: date | None = None,
    erreurs_out: list[str] | None = None,
) -> list[LedgerEntry]:
    """Lit api_usage.log (JSONL). Lignes illisibles ignorées (ne lève jamais).

    erreurs_out : si fourni, reçoit les lignes brutes non parsées (pour comptage).
    """
    if not path.exists():
        return []
    entrees: list[LedgerEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = LedgerEntry.from_jsonl(line)
        except Exception:
            if erreurs_out is not None:
                erreurs_out.append(line)
            continue
        if depuis is not None and entry.ts.date() < depuis:
            continue
        entrees.append(entry)
    return entrees


def agreger(entries: list[LedgerEntry], *, nb_erreurs_lecture: int = 0) -> Usage:
    """Calcule les totaux depuis la liste d'entrées du ledger."""
    usage = Usage(nb_entrees=len(entries), nb_erreurs_lecture=nb_erreurs_lecture)

    for entry in entries:
        if entry.cache_hit:
            usage.nb_cache_hits += 1
            continue

        usage.nb_appels += 1
        if entry.resultat == "budget_depasse":
            continue

        usage.cout_total += entry.cout_estime

        f = usage.par_fournisseur.setdefault(entry.fournisseur, UsageParFournisseur())
        f.cout_total += entry.cout_estime
        f.nb_appels += 1
        for k, v in entry.unites.items():
            f.unites[k] = f.unites.get(k, 0.0) + v

        if entry.fiche:
            usage.par_fiche[entry.fiche] = (
                usage.par_fiche.get(entry.fiche, 0.0) + entry.cout_estime
            )

    return usage


def formater_rapport(usage: Usage) -> str:
    """Génère un rapport Markdown du tableau d'usage."""
    lignes = [
        "# Rapport d'usage API",
        "",
        f"- Appels réels : {usage.nb_appels}",
        f"- Cache hits   : {usage.nb_cache_hits}  (taux : {usage.taux_cache:.0%})",
        f"- Coût total estimé : {usage.cout_total:.4f} USD",
    ]

    if usage.nb_erreurs_lecture:
        lignes.append(
            f"\n> ⚠ {usage.nb_erreurs_lecture} ligne(s) illisible(s) ignorée(s) dans le ledger."
        )

    if usage.par_fournisseur:
        lignes += [
            "",
            "## Par fournisseur",
            "",
            "| Fournisseur | Appels | Coût USD |",
            "|---|---|---|",
        ]
        for fourn, stat in sorted(usage.par_fournisseur.items()):
            lignes.append(f"| {fourn} | {stat.nb_appels} | {stat.cout_total:.4f} |")

    if usage.par_fiche:
        top = sorted(usage.par_fiche.items(), key=lambda x: x[1], reverse=True)[:10]
        lignes += [
            "",
            "## Par fiche (top 10)",
            "",
            "| Fiche | Coût USD |",
            "|---|---|",
        ]
        for nom_fiche, cout in top:
            lignes.append(f"| {nom_fiche} | {cout:.4f} |")

    return "\n".join(lignes) + "\n"
