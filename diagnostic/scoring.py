"""
scoring.py — le moteur de scoring.

Principe d'architecture #3, le plus important pour l'extensibilité :
la RUBRIQUE EST UNE DONNÉE, pas du code. Ce moteur est générique ; il ne
sait rien du HVAC. Il applique une rubrique YAML (knowledge/rubric_*.yaml).

Changer de persona (le cabinet d'avocats) = écrire une autre rubrique.
On ne retouche PAS ce fichier. C'est ça qui rend J6 (extension Suisse)
et le persona 2 quasi sans code.
"""

from __future__ import annotations

from typing import Any

from diagnostic.models import Gap


def _resolve(signaux: dict[str, Any], path: str) -> Any:
    """Résout 'website.https' -> signaux['website']['https'] (None si absent)."""
    collector, _, key = path.partition(".")
    return signaux.get(collector, {}).get(key)


def _check_passes(value: Any, op: str, expected: Any) -> bool:
    if value is None:
        return False
    if op == "is_true":
        return value is True
    if op == "gte":
        return isinstance(value, (int, float)) and value >= expected
    if op == "lte":
        return isinstance(value, (int, float)) and value <= expected
    if op == "exists":
        return True  # value n'est pas None, donc il existe
    raise ValueError(f"Opérateur inconnu dans la rubrique : {op}")


def _severity(points: int, max_points: int) -> str:
    ratio = points / max_points if max_points else 0
    if ratio >= 0.4:
        return "haute"
    if ratio >= 0.2:
        return "moyenne"
    return "basse"


class ScoringEngine:
    def __init__(self, rubrique: dict[str, Any]):
        self.rubrique = rubrique
        self.seuil_faille = rubrique.get("seuil_faille", 60)

    def score(self, signaux: dict[str, Any]) -> tuple[dict[str, float], list[Gap]]:
        scores: dict[str, float] = {}
        gaps: list[Gap] = []
        dims = self.rubrique["dimensions"]

        for dim_name, dim in dims.items():
            checks = dim["checks"]
            max_points = sum(c["points"] for c in checks)
            gained = 0
            for c in checks:
                value = _resolve(signaux, c["signal"])
                if _check_passes(value, c["op"], c.get("value")):
                    gained += c["points"]
                else:
                    gaps.append(Gap(
                        dimension=dim_name,
                        gravite=_severity(c["points"], max_points),
                        preuve=c["gap"],
                    ))
            scores[dim_name] = round(100 * gained / max_points, 1) if max_points else 0.0

        # Score global = moyenne pondérée par le "poids" de chaque dimension.
        total_poids = sum(d["poids"] for d in dims.values())
        scores["global"] = round(
            sum(scores[name] * dims[name]["poids"] for name in dims) / total_poids, 1
        ) if total_poids else 0.0

        # On trie les failles par gravité : la plus grave en premier
        # (= candidate naturelle pour l'accroche d'outreach).
        ordre = {"haute": 0, "moyenne": 1, "basse": 2}
        gaps.sort(key=lambda g: ordre.get(g.gravite, 9))
        return scores, gaps
