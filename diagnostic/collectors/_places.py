"""
_places.py — distinguer une OBSERVATION Places d'un ÉCHEC TECHNIQUE.

Pourquoi ce module existe
-------------------------
`gbp.py` et `reviews.py` lisaient tous deux `data.get("results", [])` et
traitaient une liste vide comme « aucune fiche d'établissement trouvée ».

Or l'API Google Places répond **HTTP 200 avec une liste vide** dans des cas
qui n'ont rien d'une observation : clé absente ou invalide
(`REQUEST_DENIED`), quota dépassé (`OVER_QUERY_LIMIT`), requête malformée
(`INVALID_REQUEST`). C'est précisément la situation du dépôt aujourd'hui —
aucune clé n'est disponible — et le chemin de production injecte TOUJOURS un
`api_io` : les collecteurs partaient donc en réseau, recevaient
`{"status": "REQUEST_DENIED", "results": []}`, et concluaient
`verified=False` / `count=0`.

Conséquence mesurée : deux failles de gravité **haute** fabriquées pour
toute entreprise diagnostiquée — « Fiche d'établissement non vérifiée » et
« Moins de 10 avis » — dont la première alimentait l'accroche commerciale.
C'est exactement le défaut « inconnu compté comme échec » que le moteur de
scoring vient de corriger, réintroduit par une autre porte : non plus un
stub `None`, mais une réponse d'API mal interprétée.

La règle
--------
Seuls `OK` et `ZERO_RESULTS` sont des observations : l'API a réellement
regardé et a répondu. Tout le reste est un échec technique, et un échec
technique doit produire `None` — « je n'ai pas pu vérifier » — jamais une
valeur négative.
"""

from __future__ import annotations

from typing import Any

# Statuts pour lesquels la réponse traduit une OBSERVATION réelle.
# ZERO_RESULTS en fait partie : l'API a cherché et n'a rien trouvé, ce qui est
# un fait exploitable (l'entreprise n'a pas de fiche d'établissement).
STATUTS_OBSERVABLES: frozenset[str] = frozenset({"OK", "ZERO_RESULTS"})

# Statuts qui traduisent un échec technique côté appelant ou fournisseur.
# Ils ne disent RIEN de l'entreprise diagnostiquée.
STATUTS_ECHEC: frozenset[str] = frozenset({
    "REQUEST_DENIED",       # clé absente, invalide, ou API non activée
    "OVER_QUERY_LIMIT",     # quota / facturation
    "INVALID_REQUEST",      # requête malformée
    "UNKNOWN_ERROR",        # erreur serveur transitoire
})


def reponse_exploitable(data: Any) -> bool:
    """True si la réponse Places peut être interprétée comme une observation.

    Conservateur par construction : en cas de doute (réponse non-dict, statut
    inconnu), on répond False. Se tromper en renvoyant `None` coûte une
    dimension non notée ; se tromper dans l'autre sens fabrique une faille
    affirmée à un prospect.
    """
    if not isinstance(data, dict):
        return False
    statut = data.get("status")
    if statut is None:
        # Pas de champ `status` : on n'infère rien. Certaines variantes d'API
        # (Places « New ») répondent autrement ; tant qu'un collecteur ne les
        # gère pas explicitement, l'abstention est la bonne réponse.
        return False
    return statut in STATUTS_OBSERVABLES
