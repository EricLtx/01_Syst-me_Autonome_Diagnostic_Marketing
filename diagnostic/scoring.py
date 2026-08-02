"""
scoring.py — le moteur de scoring.

Principe d'architecture #3, le plus important pour l'extensibilité :
la RUBRIQUE EST UNE DONNÉE, pas du code. Ce moteur est générique ; il ne
sait rien du HVAC. Il applique une rubrique YAML (knowledge/rubric_*.yaml).

Changer de persona (le cabinet d'avocats) = écrire une autre rubrique.
On ne retouche PAS ce fichier.

TROIS ÉTATS, PAS DEUX
---------------------
Un check peut valoir `ok`, `echec` ou **`inconnu`**. C'est la correction du
défaut central du moteur : auparavant, un signal absent (`None`) était compté
comme un échec. Conséquence mesurée sur le système réel : sans clé Google
Places, `gbp` et `reviews` renvoient `None`, donc les dimensions
`presence_locale` et `avis` valaient 0/100 pour TOUS les prospects — 45 % de
la pondération fabriquée à zéro — et le moteur émettait des failles dont le
texte avouait lui-même « à confirmer ». Une entreprise au site irréprochable
plafonnait à 27,5/100, et les trois entreprises testées recevaient la même
accroche.

Deux règles en découlent, et elles sont non négociables :

1. **Un signal inconnu ne produit JAMAIS de faille.** Une faille est une
   affirmation adossée à un fait observé (invariant J1 n°4). « Je n'ai pas
   regardé » n'est pas « c'est mauvais ».
2. **Le score est renormalisé sur ce qui a été réellement observé.** Une
   dimension dont aucun check n'est connu n'a pas de score (`None`) et sort
   du calcul global, au lieu de le tirer vers le bas.

Comme un score renormalisé sur peu d'observations est fragile, le moteur
publie `scores["_couverture"]` : la part du poids total réellement évaluée.
Un 30/100 avec 100 % de couverture et un 30/100 avec 40 % de couverture ne
se lisent pas de la même façon, et l'opératrice doit pouvoir faire la
différence avant de contacter qui que ce soit.

LA GRAVITÉ EST UN JUGEMENT, PAS UNE DIVISION
--------------------------------------------
La gravité d'une faille se déclare dans la rubrique (`gravite:`). Elle était
auparavant déduite du poids du check rapporté au total de sa dimension, ce
qui la rendait dépendante du NOMBRE de checks voisins : « Site web
inaccessible » ressortait en `moyenne` parce qu'il cohabitait avec cinq
autres checks, tandis qu'un check isolé devenait mécaniquement `haute`.
Le repli automatique est conservé pour les rubriques qui ne déclarent pas
`gravite`, mais toute rubrique sérieuse doit la déclarer.
"""

from __future__ import annotations

from typing import Any, Literal

from diagnostic.models import Gap

# Résultat d'un check : True = ok, False = échec observé, None = non observé.
Resultat = bool | None

GRAVITES: tuple[str, ...] = ("haute", "moyenne", "basse")


def _resolve(signaux: dict[str, Any], path: str) -> Any:
    """Résout 'website.https' -> signaux['website']['https'] (None si absent)."""
    collector, _, key = path.partition(".")
    return signaux.get(collector, {}).get(key)


def _check_passes(value: Any, op: str, expected: Any) -> Resultat:
    """Évalue un check. Retourne None quand le signal n'a pas été observé.

    `None` ne veut pas dire « faux » : il veut dire « on ne sait pas ». Le
    collecteur correspondant était en mode dégradé (pas de clé API, source
    injoignable), et le moteur doit s'abstenir plutôt que d'inventer.
    """
    if value is None:
        return None
    if op == "is_true":
        return value is True
    if op == "gte":
        return isinstance(value, (int, float)) and value >= expected
    if op == "lte":
        return isinstance(value, (int, float)) and value <= expected
    if op == "exists":
        return True  # value n'est pas None, donc il existe
    if op == "non_vide":
        # Pour les signaux de type liste ou chaîne (ex. plateformes sociales).
        # Une liste vide est une observation NÉGATIVE, pas une absence
        # d'observation : le collecteur a bien regardé et n'a rien trouvé.
        return len(value) > 0 if isinstance(value, (list, tuple, str, dict)) else False
    raise ValueError(f"Opérateur inconnu dans la rubrique : {op}")


def _severity_repli(points: int, max_points: int) -> str:
    """Repli quand la rubrique ne déclare pas `gravite` sur un check.

    Conservé pour la rétro-compatibilité des rubriques existantes. Déduire la
    gravité du poids relatif est un pis-aller : le résultat dépend du nombre
    de checks de la dimension, pas de l'importance commerciale de la faille.
    """
    ratio = points / max_points if max_points else 0
    if ratio >= 0.4:
        return "haute"
    if ratio >= 0.2:
        return "moyenne"
    return "basse"


class ScoringEngine:
    def __init__(self, rubrique: dict[str, Any]):
        self.rubrique = rubrique

    def score(
        self, signaux: dict[str, Any]
    ) -> tuple[dict[str, float | None], list[Gap]]:
        scores: dict[str, float | None] = {}
        gaps: list[Gap] = []
        dims = self.rubrique["dimensions"]

        poids_evalue = 0.0        # poids des dimensions réellement observées
        poids_total = 0.0

        for dim_name, dim in dims.items():
            checks = dim["checks"]
            poids_dim = dim["poids"]
            poids_total += poids_dim

            max_points_connus = 0   # dénominateur : uniquement ce qu'on a pu observer
            gained = 0
            # Repli de gravité : basé sur le total DÉCLARÉ de la dimension, pour
            # rester stable quel que soit le nombre de signaux manquants.
            max_points_declares = sum(c["points"] for c in checks)

            for c in checks:
                value = _resolve(signaux, c["signal"])
                resultat = _check_passes(value, c["op"], c.get("value"))

                if resultat is None:
                    continue  # non observé : ni point, ni dénominateur, ni faille

                max_points_connus += c["points"]
                if resultat:
                    gained += c["points"]
                else:
                    gravite = c.get("gravite") or _severity_repli(
                        c["points"], max_points_declares
                    )
                    if gravite not in GRAVITES:
                        raise ValueError(
                            f"Gravité invalide dans la rubrique pour "
                            f"{c['signal']!r} : {gravite!r} (attendu : {GRAVITES})"
                        )
                    gaps.append(Gap(
                        dimension=dim_name,
                        gravite=gravite,
                        preuve=c["gap"],
                    ))

            if max_points_connus:
                scores[dim_name] = round(100 * gained / max_points_connus, 1)
                poids_evalue += poids_dim
            else:
                # Aucun signal de cette dimension n'a pu être observé.
                # On ne fabrique pas un 0 : on déclare l'ignorance.
                scores[dim_name] = None

        # Score global : moyenne pondérée sur les SEULES dimensions observées.
        connues = [n for n in dims if scores[n] is not None]
        poids_connus = sum(dims[n]["poids"] for n in connues)
        if poids_connus:
            total = sum(scores[n] * dims[n]["poids"] for n in connues)  # type: ignore[operator]
            scores["global"] = round(total / poids_connus, 1)
        else:
            scores["global"] = None

        # Couverture : part du poids total réellement évaluée. Sert à savoir
        # quelle confiance accorder au score global (clé préfixée par « _ » :
        # ce n'est pas une dimension de la rubrique).
        scores["_couverture"] = (
            round(poids_evalue / poids_total, 3) if poids_total else 0.0
        )

        # Tri par gravité : la plus grave en premier (= candidate naturelle
        # pour l'accroche). `sorted` est stable, donc à gravité égale l'ordre
        # des dimensions de la rubrique est préservé.
        ordre = {"haute": 0, "moyenne": 1, "basse": 2}
        gaps.sort(key=lambda g: ordre.get(g.gravite, 9))
        return scores, gaps
