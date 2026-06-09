"""
pipeline.py — l'orchestrateur. C'est la chaîne du schéma, en code.

  entrée -> collecteurs -> signaux -> scoring -> synthèse+QA -> sortie

Il ne contient AUCUNE logique métier : il branche les briques entre elles.
C'est volontaire — toute l'intelligence vit dans les collecteurs (les faits),
la rubrique (le jugement) et la synthèse (la rédaction).
"""

from __future__ import annotations

from typing import Any

from diagnostic.collectors.base import Collector
from diagnostic.models import Company, Diagnostic, now_iso
from diagnostic.scoring import ScoringEngine
from diagnostic.synthesis import synthesize


class DiagnosticPipeline:
    def __init__(
        self,
        collectors: list[Collector],
        rubrique: dict[str, Any],
        knowledge: dict[str, Any] | None = None,
    ):
        self.collectors = collectors
        self.engine = ScoringEngine(rubrique)
        self.knowledge = knowledge or {}

    def run(self, company: Company) -> Diagnostic:
        # 1) Collecte (chaque sonde échoue de son côté, jamais le pipeline)
        signaux: dict[str, Any] = {}
        for c in self.collectors:
            signaux[c.name] = c.safe_collect(company)

        # 2) Scoring (applique la rubrique)
        scores, failles = self.engine.score(signaux)

        # 3) Synthèse + QA (rédige le mini-audit et l'accroche)
        accroche, mini_audit = synthesize(company, signaux, scores, failles, self.knowledge)

        # 4) Sortie : l'objet Diagnostic complet
        return Diagnostic(
            entreprise=company,
            signaux=signaux,
            scores=scores,
            failles=failles,
            accroche=accroche,
            mini_audit=mini_audit,
            meta={
                "collecte_le": now_iso(),
                "collecteurs": [c.name for c in self.collectors],
                "rubrique": self.engine.rubrique.get("persona", "inconnue"),
            },
        )
