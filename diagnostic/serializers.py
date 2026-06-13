"""
serializers.py — pont entre le pipeline J1 et le vault Obsidian.

Fonctions pures, sans I/O. Appelées par vault_runner.py.
"""
from __future__ import annotations

from datetime import date

from diagnostic.models import Diagnostic
from diagnostic.vault_schema import FicheProspect


def diagnostic_to_fiche(diag: Diagnostic, fiche: FicheProspect) -> FicheProspect:
    """Projette les résultats d'un Diagnostic dans une FicheProspect existante.

    Champs mis à jour : score_global, gaps_majeurs, date_diagnostic.
    Le champ `rapport` (wikilink) est géré séparément après write_rapport(),
    car le chemin du fichier n'est connu qu'après l'écriture.
    Les champs d'identité (nom, persona, marche, statut) ne sont pas touchés.
    """
    score_brut = diag.scores.get("global", 0)
    score = max(0, min(100, round(score_brut)))

    # Dédupliquer les dimensions sans perdre l'ordre d'importance
    gaps: list[str] = list(dict.fromkeys(g.dimension for g in diag.failles))

    # Dériver signal_chaud depuis les failles (préserve le contrat JSON de Diagnostic)
    hautes = [g for g in diag.failles if g.gravite == "haute"]
    signal_chaud = (hautes[0].preuve if hautes else
                    diag.failles[0].preuve if diag.failles else
                    diag.accroche) or None

    return fiche.model_copy(update={
        "score_global": score,
        "gaps_majeurs": gaps,
        "date_diagnostic": date.today(),
        "signal_chaud": signal_chaud,
        "accroche": diag.accroche or None,
    })


def diagnostic_to_rapport_md(diag: Diagnostic) -> str:
    """Génère un rapport Markdown lisible depuis un Diagnostic.

    Inclut : synthèse LLM, scores par dimension avec barre visuelle,
    tableau des gaps, accroche d'outreach.
    """
    nom = diag.entreprise.nom
    url = diag.entreprise.url or "—"
    score = max(0, min(100, round(diag.scores.get("global", 0))))
    today = date.today().isoformat()
    rubrique = diag.meta.get("rubrique", "?")
    collecteurs = ", ".join(diag.meta.get("collecteurs", []))

    # Scores par dimension (hors "global")
    scores_lignes: list[str] = []
    for dim, val in diag.scores.items():
        if dim == "global":
            continue
        v = max(0, min(100, round(val)))
        barre = "█" * (v // 10) + "░" * (10 - v // 10)
        scores_lignes.append(f"| `{dim}` | {v} | {barre} |")
    scores_table = "\n".join(scores_lignes) if scores_lignes else "| — | — | — |"

    # Gaps détectés
    if diag.failles:
        gaps_lignes = [
            f"| `{g.dimension}` | {g.gravite} | {g.preuve} |"
            for g in diag.failles
        ]
        gaps_table = "\n".join(gaps_lignes)
    else:
        gaps_table = "| — | — | Aucun gap majeur détecté |"

    return f"""\
---
type: rapport
entreprise: {nom}
date_rapport: {today}
score_global: {score}
---

# Rapport de diagnostic — {nom}

*Généré le {today} · Score global : **{score}/100** · Rubrique persona {rubrique}*

---

## Synthèse

{diag.mini_audit}

---

## Scores par dimension

| Dimension | Score /100 | Visuel |
|---|---|---|
{scores_table}

---

## Gaps détectés

| Dimension | Gravité | Observation |
|---|---|---|
{gaps_table}

---

## Accroche d'outreach

> {diag.accroche}

---

*Source : {url}*
*Collecteurs : {collecteurs} · Pipeline J2*
"""
