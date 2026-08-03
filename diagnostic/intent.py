"""
intent.py — évalue l'axe d'intention SANS jamais produire de score (ADR 0004).

Ce module est un CPU auxiliaire, pas le moteur de scoring : il consomme des
signaux déjà collectés (jamais de réseau, jamais d'écriture vault) et rejoue
les checks d'une rubrique d'intention un par un, indépendamment les uns des
autres.

Pourquoi ce module n'est pas une extension de `scoring.py`
------------------------------------------------------------
La note de cadrage CMO qui a fait réviser l'ADR 0004 en cours de route est
sans appel : « un score n'a pas de date, or la date EST l'information ». Un
événement d'intention n'a pas de poids relatif à renormaliser contre d'autres
événements — il a une date et une échéance. Réutiliser
`ScoringEngine.score()` (son agrégation, sa renormalisation par poids, son
`_couverture`) forcerait cette donnée dans un moule pensé pour une grandeur
qui ne se périme pas.

Ce qui SE réutilise, et rien de plus : les deux fonctions primitives et pures
de `scoring.py`, `_resolve` et `_check_passes` — l'évaluateur de check à
trois états (`ok`/`echec`/`inconnu`), indépendant de toute agrégation. C'est
la seule chose dont l'axe intention a besoin : savoir si UN check est observé
et vrai, avec la même discipline de trois états que le besoin.

`scoring.py` n'est pas modifié : zéro ligne (preuve exécutable par
`git diff diagnostic/scoring.py`, qui doit rester vide).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from diagnostic.models import EvenementIntention
from diagnostic.scoring import _check_passes, _resolve


def _comme_date(valeur: Any) -> date | None:
    """Normalise une date d'événement en `datetime.date`.

    Convention du projet (voir `website.py::derniere_maj`) : un collecteur
    écrit une date sous forme de chaîne ISO, jamais un objet `date` brut —
    un `date` brut dans `signaux` romprait la sérialisation JSON de
    `Diagnostic.to_json()`. Ce module est le seul endroit qui a besoin d'un
    calcul de calendrier ; c'est donc ici, et seulement ici, que la chaîne
    est reconvertie.
    """
    if valeur is None:
        return None
    if isinstance(valeur, date):
        return valeur
    try:
        return date.fromisoformat(str(valeur)[:10])
    except ValueError:
        return None


def evaluer_intention(
    rubrique_intention: dict[str, Any], signaux: dict[str, Any]
) -> list[EvenementIntention]:
    """Rejoue les checks d'une rubrique d'intention un par un, SANS agrégation
    ni renormalisation (ADR 0004, D1/D4) : pas de score composite, pas de
    « score d'intention » — une liste d'événements datés et périssables.

    Règles non négociables tenues ici :
      - un check `nature: etat` (ou sans `nature` déclarée, défaut `etat`)
        n'a rien à faire côté intention (B1) : seuls les checks explicitement
        `evenement` sont évalués ;
      - un check dont le résultat est `False` OU `None` ne produit JAMAIS
        d'événement — ni faille inversée, ni fabrication à partir d'un
        signal inconnu (même discipline à trois états que le besoin) ;
      - un événement sans date exploitable est ÉCARTÉ, jamais dégradé en
        état permanent (D2) — un recrutement « toujours ouvert » sans offre
        datée n'est pas un signal d'intention ;
      - `citable` défaut à `False` : un check ne devient citable au
        prospect que par déclaration explicite en YAML (D6). C'est ce champ,
        porté par chaque événement, que `serializers.py` doit vérifier avant
        de dériver `signal_intention` — ce module ne fait QUE le porter.
    """
    evenements: list[EvenementIntention] = []

    for dim_name, dim in rubrique_intention["dimensions"].items():
        for c in dim["checks"]:
            if c.get("nature", "etat") != "evenement":
                continue  # un check "etat" n'a rien à faire côté intention (B1)

            valeur = _resolve(signaux, c["signal"])
            if _check_passes(valeur, c["op"], c.get("value")) is not True:
                continue  # False ou None : ni faille inversée, ni évènement fabriqué

            date_evenement = _comme_date(_resolve(signaux, c["date_signal"]))
            if date_evenement is None:
                continue  # non daté : écarté, jamais traité comme permanent (D2)

            if "fenetre_jours" in c:
                fenetre = c["fenetre_jours"]
            else:
                fenetre = c.get("demi_vie_jours", 30) * 3

            jours = (date.today() - date_evenement).days
            evenements.append(EvenementIntention(
                dimension=dim_name,
                preuve=c["preuve"].format(jours=jours),
                date_evenement=date_evenement,
                expire_le=date_evenement + timedelta(days=fenetre),
                intensite=c.get("intensite", "moyenne"),
                citable=c.get("citable", False),   # sécurité par défaut (D6)
                fiabilite=c.get("fiabilite", "D_derive"),
            ))

    # Le plus récent en tête : c'est la candidate naturelle pour l'accroche
    # (même convention de tri que ScoringEngine pour les gaps par gravité).
    evenements.sort(key=lambda e: e.date_evenement, reverse=True)
    return evenements
