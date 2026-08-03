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
from diagnostic.intent import evaluer_intention
from diagnostic.models import Company, Diagnostic, EvenementIntention, now_iso
from diagnostic.scoring import ScoringEngine
from diagnostic.synthesis import synthesize


class DiagnosticPipeline:
    def __init__(
        self,
        collectors: list[Collector],
        rubrique: dict[str, Any],
        knowledge: dict[str, Any] | None = None,
        api_io=None,
        rubrique_intention: dict[str, Any] | None = None,
    ):
        self.collectors = collectors
        self.engine = ScoringEngine(rubrique)
        self.knowledge = knowledge or {}
        self._api_io = api_io
        # None (défaut) = axe intention non configuré pour ce secteur → le
        # comportement J1 existant est inchangé à l'identique (ADR 0004).
        self.rubrique_intention = rubrique_intention
        # Injecter api_io dans les collecteurs qui le supportent
        if api_io is not None:
            for c in self.collectors:
                if hasattr(c, "_api_io"):
                    c._api_io = api_io

    def run(self, company: Company) -> Diagnostic:
        # 1) Collecte (chaque sonde échoue de son côté, jamais le pipeline)
        signaux: dict[str, Any] = {}
        for c in self.collectors:
            result = c.safe_collect(company)
            signaux[c.name] = result
            # Après website : propager les signaux bruts aux collecteurs dépendants
            # (SeoCollector, SocialCollector, LegitimiteCollector n'ont pas
            # d'accès réseau propre)
            if c.name == "website":
                for other in self.collectors:
                    if hasattr(other, "_website_signals"):
                        other._website_signals = result

        # 2) Scoring (applique la rubrique de besoin — inchangé)
        scores, failles = self.engine.score(signaux)

        # 2bis) Axe intention (ADR 0004) : SANS agrégation, une simple liste
        # d'événements datés — jamais un second score. `scoring.py` n'est
        # jamais appelé pour cet axe (voir diagnostic/intent.py).
        evenements_intention: list[EvenementIntention] = []
        if self.rubrique_intention is not None:
            evenements_intention = evaluer_intention(self.rubrique_intention, signaux)

        # 3) Synthèse + QA (rédige le mini-audit et l'accroche)
        accroche, mini_audit = synthesize(company, signaux, scores, failles, self.knowledge, api_io=self._api_io)

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
            evenements_intention=evenements_intention,
        )
