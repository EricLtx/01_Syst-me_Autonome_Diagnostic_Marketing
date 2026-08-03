"""
models.py — le contrat de données du module.

C'est la pièce la plus importante : tant que la forme de `Diagnostic` ne
bouge pas, tout ce qui est en aval (qualification, rédaction, CRM) peut s'y
brancher sans rien casser. On code "autour" de ce contrat, pas l'inverse.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from typing import Any


@dataclass
class Company:
    """L'entrée du module : le strict minimum pour démarrer."""
    nom: str
    url: str
    region: str = ""


@dataclass
class Gap:
    """Une faille exploitable : la matière première de l'accroche d'outreach."""
    dimension: str
    gravite: str          # "haute" | "moyenne" | "basse"
    preuve: str           # phrase lisible, factuelle


@dataclass
class EvenementIntention:
    """Un événement d'intention observé : DATÉ et PÉRISSABLE, jamais un score.

    ADR 0004 (révisée) — pourquoi ce n'est pas un `Gap` de polarité inversée :
    un `Gap` porte un état (une faille reste une faille tant qu'elle est
    vraie) ; un `EvenementIntention` porte une DATE et une ÉCHÉANCE, deux
    informations qu'aucun score /100 ne peut représenter sans les perdre.
    Contrainte dure : `citable` défaut à `False` — un événement ne devient
    citable au prospect que par déclaration explicite en YAML (§D6 ADR 0004),
    symétrique de « jamais dérivé d'un signal inconnu ».
    """
    dimension: str
    preuve: str            # phrase factuelle, date déjà interpolée (ex. "offre du 12/07")
    date_evenement: date   # date du fait observé — jamais None (un événement non daté est écarté en amont, D2)
    expire_le: date        # péremption calculée UNE FOIS à l'évaluation (date_evenement + fenêtre)
    intensite: str         # "haute" | "moyenne" | "basse" — jugement commercial déclaré en YAML
    citable: bool          # True SEULEMENT si le prospect a publié ce fait pour être vu (D6)
    fiabilite: str         # axe UNIQUE de fiabilité de source, déclaré en YAML (D6, pas une matrice)


@dataclass
class Diagnostic:
    """La sortie. Double usage : machine (scores, failles) + humain (mini_audit)."""
    entreprise: Company
    signaux: dict[str, Any] = field(default_factory=dict)     # bruts, par collecteur
    scores: dict[str, float] = field(default_factory=dict)    # 0–100 par dimension + "global"
    failles: list[Gap] = field(default_factory=list)
    accroche: str = ""
    mini_audit: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    # Axe intention (ADR 0004) : liste d'événements datés, JAMAIS un second
    # score — ajout strictement additif, aucun champ existant modifié.
    evenements_intention: list[EvenementIntention] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        # `default=str` : seule concession nécessaire à l'ajout de
        # `EvenementIntention` (ses champs `date`/`date` ne sont pas
        # JSON-natifs). N'affecte AUCUN champ existant : avant cette ADR,
        # aucune valeur non JSON-native ne transitait par `signaux`/`scores`.
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, default=str)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
