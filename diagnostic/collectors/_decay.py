"""
_decay.py — décroissance temporelle d'un événement, fonction pure (ADR 0004).

Ce que ce module N'EST PAS
--------------------------
Il n'est PAS câblé dans `intent.py` ni dans le scoring : la péremption d'un
`EvenementIntention` (§D2 de l'ADR) est déjà résolue par une date stockée
(`expire_le`) et une comparaison triviale à la lecture (`date.today() <=
expire_le`), sans recalcul. `decroissance()` sert un usage strictement
INFORMATIONNEL et optionnel — un affichage continu de l'intensité d'un
événement (utilisé par `scripts/benchmark_intention.py` pour illustrer
comment la priorisation se réordonnerait avec l'âge des signaux) — jamais un
score qui entrerait dans une décision.

Pourquoi une fonction séparée, sur le modèle de `_places.py`
-------------------------------------------------------------
Fonction pure, aucun état, aucun réseau, aucune classe `Collector` : exactement
le même patron que `diagnostic/collectors/_places.py`, qui distingue déjà un
échec technique d'une observation. Ici, la distinction est temporelle : la
décroissance ne s'applique QU'AUX ÉVÉNEMENTS DATÉS, jamais aux états (une note
d'avis basse ne « vieillit » pas — elle est vraie tant qu'elle est vraie).

⚠️ La forme fonctionnelle retenue (`2^(-âge / demi_vie)`) est une convention
d'outillage, pas un résultat empirique mesuré : les demi-vies commerciales
usuelles se contredisent d'un facteur 4 à 6 selon les fournisseurs, et aucune
n'est traçable. Même registre d'honnêteté que `energie_wh`/`co2e_g` en
GreenIT (ADR 0002) : une ESTIMATION comparative, jamais une mesure certifiée.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def decroissance(
    date_evenement: date, config: dict[str, Any], aujourdhui: date | None = None
) -> float:
    """Retourne un facteur dans [plancher, 1.0], décroissant avec l'âge.

    `config` = {"demi_vie_jours": int, "plancher": float} — donnée YAML, pas
    un réglage en dur (changer une demi-vie par secteur = éditer le YAML).

    Propriétés garanties (testées en isolation) :
      - vaut 1.0 à l'âge 0 (aujourd'hui même que l'événement) ;
      - vaut ~0.5 à la demi-vie déclarée ;
      - tend vers le plancher configuré au-delà, sans jamais tomber en
        dessous ;
      - strictement décroissante avec l'âge ;
      - fonction pure : deux appels identiques donnent le même résultat,
        aucune dépendance cachée à l'horloge système au-delà du paramètre
        explicite `aujourdhui`.
    """
    aujourdhui = aujourdhui if aujourdhui is not None else date.today()
    demi_vie = config.get("demi_vie_jours", 45)
    plancher = config.get("plancher", 0.0)

    age_jours = (aujourdhui - date_evenement).days
    if age_jours <= 0:
        return 1.0
    if demi_vie <= 0:
        return plancher

    facteur = 0.5 ** (age_jours / demi_vie)
    return max(plancher, min(1.0, facteur))
