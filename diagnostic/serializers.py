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
    # Un score global à None signifie « rien n'a pu être observé ». On le
    # propage tel quel plutôt que de le convertir en 0 : un 0 fabriqué ferait
    # remonter la fiche en tête du classement par besoin, exactement à
    # l'inverse de la réalité.
    score_brut = diag.scores.get("global")
    score = None if score_brut is None else max(0, min(100, round(score_brut)))

    # Dédupliquer les dimensions sans perdre l'ordre d'importance
    gaps: list[str] = list(dict.fromkeys(g.dimension for g in diag.failles))

    # Dériver signal_chaud depuis les failles (préserve le contrat JSON de Diagnostic)
    hautes = [g for g in diag.failles if g.gravite == "haute"]
    signal_chaud = (hautes[0].preuve if hautes else
                    diag.failles[0].preuve if diag.failles else
                    diag.accroche) or None

    # Dériver l'axe intention (ADR 0004) : contrainte dure symétrique de
    # celle de signal_chaud — jamais dérivé d'un signal inconnu. Ici,
    # jamais dérivé d'un événement non `citable` (D6) : certains signaux ne
    # servent qu'à prioriser en interne et seraient désastreux à prononcer
    # devant le prospect. `evenements_intention` est déjà trié du plus
    # récent au plus ancien (diagnostic/intent.py) : le premier événement
    # citable est la meilleure candidate pour l'accroche.
    citables = [e for e in diag.evenements_intention if e.citable]
    evenement_principal = citables[0] if citables else None

    return fiche.model_copy(update={
        "score_global": score,
        "gaps_majeurs": gaps,
        "date_diagnostic": date.today(),
        "signal_chaud": signal_chaud,
        "accroche": diag.accroche or None,
        "signal_intention": evenement_principal.preuve if evenement_principal else None,
        "date_intention": evenement_principal.date_evenement if evenement_principal else None,
        "intention_expire_le": evenement_principal.expire_le if evenement_principal else None,
    })


# --- Seuils du dossier d'audit (ADR 0005) ---------------------------------
# Tous `[À CALIBRER]` : ce sont des points de départ raisonnables, pas des
# mesures. Aucun n'a été validé par la consultante.

# En dessous de cette part de rubrique réellement observée, l'audit se déclare
# PARTIEL. Sans ce seuil, « audit complet » serait une formule décorative :
# c'est ici que la promesse devient vérifiable.
SEUIL_AUDIT_COMPLET: float = 0.80  # [À CALIBRER]

# Au-dessus de ce score, une dimension observée est nommée comme point fort.
SEUIL_POINT_FORT: float = 70.0  # [À CALIBRER]

# Ordre de traitement des écarts. Une gravité inconnue passe en dernier plutôt
# qu'en premier : on ne fait pas remonter en tête ce qu'on n'a pas su qualifier.
_ORDRE_GRAVITE: dict[str, int] = {"haute": 0, "moyenne": 1, "basse": 2}


def _plan_action(diag: Diagnostic, scores_par_dim: dict[str, float]) -> list[str]:
    """Ordonne les écarts en séquence d'action, de façon déterministe.

    Deux clés, dans cet ordre : la gravité déclarée dans la rubrique, puis le
    score de la dimension concernée (croissant — la dimension la plus faible
    d'abord). Aucun LLM n'intervient : la priorité d'un écart se déduit de
    faits déjà établis, pas d'un jugement rédactionnel.

    On n'utilise volontairement PAS les poids de la rubrique : ils ne figurent
    pas dans `Diagnostic`, et les y faire entrer élargirait un contrat que
    l'ADR 0004 vient de stabiliser. Le score de la dimension est un proxy
    suffisant et déjà disponible.
    """
    ordonnes = sorted(
        diag.failles,
        key=lambda g: (
            _ORDRE_GRAVITE.get(g.gravite, 99),
            scores_par_dim.get(g.dimension, 50.0),
        ),
    )
    return [
        f"| {rang} | `{g.dimension}` | {g.gravite} | {g.preuve} |"
        for rang, g in enumerate(ordonnes, start=1)
    ]


def diagnostic_to_rapport_md(diag: Diagnostic) -> str:
    """Génère un rapport Markdown lisible depuis un Diagnostic.

    Inclut : synthèse LLM, scores par dimension avec barre visuelle,
    tableau des gaps, accroche d'outreach.
    """
    nom = diag.entreprise.nom
    url = diag.entreprise.url or "—"
    score_brut = diag.scores.get("global")
    score = "non évalué" if score_brut is None else max(0, min(100, round(score_brut)))
    today = date.today().isoformat()
    rubrique = diag.meta.get("rubrique", "?")
    collecteurs = ", ".join(diag.meta.get("collecteurs", []))

    # Part de la rubrique réellement observée. Sans elle, un score renormalisé
    # sur peu de signaux se lirait comme un score complet.
    couverture = diag.scores.get("_couverture")
    couverture_txt = "—" if couverture is None else f"{round(couverture * 100)} %"

    # Scores par dimension (hors "global" et hors clés techniques « _… »).
    # Une dimension non observée est affichée comme telle : elle n'est pas
    # ramenée à 0, sans quoi le rapport affirmerait un fait jamais constaté.
    scores_lignes: list[str] = []
    scores_par_dim: dict[str, float] = {}
    dims_non_observees: list[str] = []
    points_forts: list[str] = []
    for dim, val in diag.scores.items():
        if dim == "global" or dim.startswith("_"):
            continue
        if val is None:
            scores_lignes.append(f"| `{dim}` | non observé | `société non mesurée` |")
            # Une dimension non observée n'est pas un trou : c'est une question
            # à poser en rendez-vous. C'est le retournement central de l'ADR
            # 0005 — la limite du système devient une matière de conversation.
            dims_non_observees.append(dim)
            continue
        v = max(0, min(100, round(val)))
        scores_par_dim[dim] = float(val)
        barre = "█" * (v // 10) + "░" * (10 - v // 10)
        scores_lignes.append(f"| `{dim}` | {v} | {barre} |")
        if val >= SEUIL_POINT_FORT:
            points_forts.append(f"| `{dim}` | {v} |")
    scores_table = "\n".join(scores_lignes) if scores_lignes else "| — | — | — |"

    # Complétude de l'audit : la promesse « audit complet » n'a de sens que si
    # le document sait dire quand il ne l'est pas.
    if couverture is None:
        verdict_completude = "complétude inconnue"
    elif couverture >= SEUIL_AUDIT_COMPLET:
        verdict_completude = "audit complet"
    else:
        verdict_completude = "**audit PARTIEL**"

    # Plan d'action : la séquence de travail, en tête du document.
    plan_lignes = _plan_action(diag, scores_par_dim)
    plan_table = (
        "\n".join(plan_lignes) if plan_lignes
        else "| — | — | — | Aucun écart majeur détecté sur les dimensions observées |"
    )

    # Points forts : un audit qui n'énumère que des fautes est moins crédible,
    # et prive la consultante de ses points d'appui en rendez-vous.
    forts_table = (
        "\n".join(points_forts) if points_forts
        else "| — | Aucune dimension observée n'atteint le seuil de point fort |"
    )

    # À vérifier : la liste de questions de l'opératrice.
    if dims_non_observees:
        a_verifier = "\n".join(
            f"- `{d}` — non observé par le système ; à confirmer auprès de l'entreprise."
            for d in dims_non_observees
        )
    else:
        a_verifier = "- Toutes les dimensions de la rubrique ont été observées."

    # Note : il n'y a plus de table « Écarts détectés » non ordonnée. Elle
    # dupliquait ligne pour ligne le plan d'action priorisé, au même endroit du
    # document, sans rien ajouter — la seule différence était l'absence d'ordre.

    # Section « Signaux d'intention » (ADR 0004) : rendue seulement si au
    # moins un événement a été détecté — un axe non configuré pour ce
    # secteur ne doit pas afficher une section vide et intrigante. Un
    # événement non `citable` est affiché ici (usage interne, opérateur
    # humain) mais NE PEUT PAS alimenter `signal_intention` (serializers.py,
    # diagnostic_to_fiche) : la contrainte dure ne s'applique qu'à la phrase
    # envoyée au prospect, pas à ce rapport de pilotage interne.
    section_intention = ""
    if diag.evenements_intention:
        lignes_intention = [
            f"| `{e.dimension}` | {e.intensite} | {e.fiabilite} | "
            f"{'oui' if e.citable else 'non'} | {e.expire_le.isoformat()} | {e.preuve} |"
            for e in diag.evenements_intention
        ]
        section_intention = f"""
---

## Signaux d'intention

| Dimension | Intensité | Fiabilité | Citable | Expire le | Observation |
|---|---|---|---|---|---|
{chr(10).join(lignes_intention)}
"""

    return f"""\
---
type: rapport
entreprise: {nom}
date_rapport: {today}
score_global: {score}
---

# Audit marketing express — {nom}

*Généré le {today} · {verdict_completude} · Couverture : {couverture_txt} · Rubrique persona {rubrique}*

> **Document de travail interne.** Il prépare l'entretien ; il n'est pas
> destiné à être remis tel quel. Chaque observation ci-dessous est adossée à
> un fait collecté — ce qui n'a pas été observé est dit comme tel, jamais
> comblé.

---

## Synthèse

{diag.mini_audit}

---

## Écarts détectés — plan d'action priorisé

Ordonné par gravité, puis par faiblesse de la dimension. Séquence déterministe :
aucune rédaction ne réordonne ce tableau. Chaque ligne est adossée à un fait
collecté.

| # | Dimension | Gravité | Écart constaté |
|---|---|---|---|
{plan_table}

---

## Points forts

Ce sur quoi l'entreprise peut s'appuyer — et sur quoi ouvrir la conversation.

| Dimension | Score /100 |
|---|---|
{forts_table}

---

## À vérifier en entretien

Ce que le système n'a **pas** pu observer. Ce ne sont pas des lacunes de
l'entreprise : ce sont les questions à poser.

{a_verifier}
{section_intention}
---

## Scores par dimension

Instrument de lecture interne, **non comparable d'une entreprise à l'autre** :
chaque score est renormalisé sur les seules dimensions observées, et deux
entreprises couvertes différemment ne passent pas le même examen.

| Dimension | Score /100 | Visuel |
|---|---|---|
{scores_table}

*Score global : **{score}/100** sur une couverture de {couverture_txt}.*

---

## Accroche d'outreach

> {diag.accroche}

---

*Source : {url}*
*Collecteurs : {collecteurs} · Pipeline J2*
"""
