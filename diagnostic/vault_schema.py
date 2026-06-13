"""
vault_schema.py — source unique de vérité du frontmatter Obsidian.

Ce module est la « datasheet » du système :
- FicheProspect définit exactement ce que vault_io.py lit et écrit.
- Les enums Statut et Marche empêchent les valeurs fantaisistes.
- TRANSITIONS_* documente qui a le droit de faire quoi (cf. §5.2 de la spec).

Règles pydantic appliquées :
  extra = "allow"  → les annotations humaines dans Obsidian sont préservées
                     en round-trip, jamais effacées silencieusement.
  Validation à la lecture ET à l'écriture : une fiche éditée à la main
  peut être invalide → erreur explicite, fichier jamais écrasé.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums — valeurs légales pour les champs discriminants
# ---------------------------------------------------------------------------

class Statut(str, Enum):
    decouvert   = "decouvert"
    diagnostique = "diagnostique"
    valide      = "valide"
    contacte    = "contacte"
    rejete      = "rejete"


class Marche(str, Enum):
    quebec    = "quebec"
    romandie  = "romandie"
    france    = "france"
    suisse    = "suisse"
    espagne   = "espagne"


# ---------------------------------------------------------------------------
# Machine à états (§5.2) — source de vérité pour vault_io.transition()
# ---------------------------------------------------------------------------

# Transitions que les agents sont autorisés à déclencher.
TRANSITIONS_AGENT: dict[Statut, set[Statut]] = {
    Statut.decouvert: {Statut.diagnostique},
}

# Toutes les transitions légales (agent + humain).
# → rejete est accessible depuis tout état, réservé à l'humain.
TRANSITIONS_LEGALES: dict[Statut, set[Statut]] = {
    Statut.decouvert:    {Statut.diagnostique, Statut.rejete},
    Statut.diagnostique: {Statut.valide,        Statut.rejete},
    Statut.valide:       {Statut.contacte,      Statut.rejete},
    Statut.contacte:     {Statut.rejete},
    Statut.rejete:       set(),  # état final
}


# ---------------------------------------------------------------------------
# Modèle principal
# ---------------------------------------------------------------------------

class FicheProspect(BaseModel):
    """Frontmatter d'une fiche prospect dans le vault Obsidian.

    Champs inconnus (annotations humaines) : tolérés et préservés en round-trip.
    Ne jamais écraser silencieusement un champ inconnu — erreur explicite si
    le schéma obligatoire est violé.
    """

    model_config = ConfigDict(
        extra="allow",           # annotations humaines préservées
        use_enum_values=True,    # sérialise "decouvert" et non Statut.decouvert
    )

    # Discriminant de type — toujours "prospect" pour ces fiches
    type: Literal["prospect"] = "prospect"

    # Champs obligatoires
    persona: Literal[1, 2]
    marche: Marche
    statut: Statut
    nom: str
    date_creation: date

    # Champs optionnels (null tant que non renseignés)
    site_web: str | None = None
    score_global: int | None = Field(default=None, ge=0, le=100)
    gaps_majeurs: list[str] = Field(default_factory=list)
    source_decouverte: str = "manuel"
    date_diagnostic: date | None = None
    rapport: str | None = None  # wikilink [[30-Diagnostics/...]]

    # Champs ajoutés en J4 (tous optionnels — rétro-compatibles avec les fiches antérieures)
    contact_nom: str | None = None
    contact_titre: str | None = None
    contact_email: str | None = None
    contact_email_source: str | None = None  # statut Apollo ("verified", "guessed"…) — audit RGPD
    contact_linkedin: str | None = None      # référence uniquement, jamais scrapée
    icp_id: str | None = None
    opt_out: bool = False                    # si True : exclu de tout export/outreach (J5/J6)
