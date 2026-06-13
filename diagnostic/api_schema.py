"""
api_schema.py — schéma du grand livre d'usage API (§5.3 de la spec J3).

LedgerEntry : une ligne JSONL dans api_usage.log.
compute_cout : calcule le coût estimé depuis api_pricing.yaml.

Ces deux éléments sont la source unique de vérité de ce qu'on journalise ;
api_io.py les utilise à chaque appel.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict


class LedgerEntry(BaseModel):
    """Une ligne du grand livre d'usage API — append-only dans api_usage.log."""

    model_config = ConfigDict(extra="forbid")

    ts: datetime                            # horodatage UTC ISO
    fournisseur: str                        # "anthropic" | "serp" | "google_places" | "apollo" | "http"
    endpoint: str                           # "messages" | "place_details" | ...
    unites: dict[str, float]                # {"input_tokens": 1200, "output_tokens": 350} | {"requetes": 1}
    cout_estime: float                      # somme(unites[k] * prix[k]) selon api_pricing.yaml
    devise: str                             # "USD"
    fiche: str | None = None               # nom de fiche concernée, si applicable
    cache_hit: bool = False                # True → cout_estime = 0, aucun appel réseau
    resultat: Literal["ok", "erreur", "budget_depasse"] = "ok"
    detail: str = ""                        # message d'erreur éventuel

    @classmethod
    def maintenant(cls, **kwargs) -> "LedgerEntry":
        """Constructeur avec ts = now UTC. Passe kwargs à __init__."""
        return cls(ts=datetime.now(timezone.utc), **kwargs)

    def to_jsonl(self) -> str:
        """Sérialise en une ligne JSONL (sans saut de ligne final)."""
        import json
        return json.dumps(self.model_dump(mode="json"), ensure_ascii=False)

    @classmethod
    def from_jsonl(cls, line: str) -> "LedgerEntry":
        """Désérialise depuis une ligne JSONL."""
        import json
        return cls.model_validate(json.loads(line))


def compute_cout(
    pricing: dict,
    fournisseur: str,
    endpoint: str,
    unites: dict[str, float],
) -> float:
    """Calcule le coût estimé en USD depuis la grille tarifaire.

    Retourne 0.0 si le fournisseur ou l'endpoint est absent de la grille
    (évite un crash sur un appel non tarifé plutôt que de bloquer le pipeline).
    """
    try:
        prix = (
            pricing["fournisseurs"][fournisseur]["endpoints"][endpoint]["prix_par_unite"]
        )
    except KeyError:
        return 0.0
    return sum(unites.get(k, 0.0) * v for k, v in prix.items())
