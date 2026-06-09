"""
synthesis.py — la couche de raisonnement + le contrôle qualité.

Principe #1 (rappel) : le LLM ne va PAS chercher de données. Il reçoit des
signaux et des failles DÉJÀ établis, et il rédige. Il ne peut donc pas
inventer un fait : il n'a que ce qu'on lui donne.

Principe #4 : un pas de QA non négociable. Le mini-audit part à un vrai
prospect. On vérifie qu'il s'appuie sur les failles réelles avant de le
laisser sortir ; sinon on retombe sur le repli déterministe.

Le module tourne SANS clé API (repli déterministe). Tu branches le LLM
quand tu veux, en posant ANTHROPIC_API_KEY dans l'environnement.
"""

from __future__ import annotations

import os
from typing import Any

from diagnostic.models import Company, Gap

MODELE = "claude-sonnet-4-6"  # bon rapport qualité/coût pour de la rédaction


def synthesize(
    company: Company,
    signaux: dict[str, Any],
    scores: dict[str, float],
    gaps: list[Gap],
    knowledge: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Retourne (accroche, mini_audit)."""
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            accroche, audit = _synthese_llm(company, scores, gaps, knowledge or {})
            ok, _ = quality_check(audit, gaps, company)
            if ok:
                return accroche, audit
        except Exception:  # noqa: BLE001 — en cas de souci, on ne bloque jamais
            pass
    return _synthese_repli(company, scores, gaps)


def quality_check(audit: str, gaps: list[Gap], company: Company) -> tuple[bool, list[str]]:
    """Garde-fou simple : l'audit est-il non vide, nominatif, et adossé aux failles ?"""
    issues: list[str] = []
    if len(audit.strip()) < 40:
        issues.append("Audit trop court")
    if company.nom and company.nom.lower() not in audit.lower():
        issues.append("L'entreprise n'est pas nommée")
    if gaps and not any(g.preuve[:20].lower() in audit.lower() for g in gaps[:3]):
        issues.append("Les failles principales ne sont pas reprises")
    return (len(issues) == 0, issues)


def _accroche_depuis_gaps(gaps: list[Gap]) -> str:
    return gaps[0].preuve if gaps else "Présence digitale globalement solide."


def _synthese_repli(company: Company, scores: dict[str, float], gaps: list[Gap]) -> tuple[str, str]:
    """Version 100 % déterministe : fonctionne hors-ligne, sans LLM."""
    glob = scores.get("global", 0)
    lignes = [
        f"# Mini-audit de marque — {company.nom}",
        "",
        f"Score global de maturité digitale : **{glob}/100**.",
        "",
        "## Points de friction prioritaires",
    ]
    for g in gaps[:5]:
        lignes.append(f"- ({g.gravite}) {g.preuve}")
    if not gaps:
        lignes.append("- Aucun point bloquant détecté sur les dimensions mesurées.")
    lignes += ["", "## Détail par dimension"]
    for dim, val in scores.items():
        if dim != "global":
            lignes.append(f"- {dim} : {val}/100")
    return _accroche_depuis_gaps(gaps), "\n".join(lignes)


def _synthese_llm(
    company: Company, scores: dict[str, float], gaps: list[Gap], knowledge: dict[str, Any]
) -> tuple[str, str]:
    """Rédaction par le LLM, strictement ancrée dans les failles fournies."""
    import anthropic  # import paresseux : pas de dépendance dure

    faits = "\n".join(f"- [{g.gravite}] {g.dimension} : {g.preuve}" for g in gaps) or "- (aucune faille)"
    ton = knowledge.get("ton", "professionnel, direct, sans jargon")
    preuve = knowledge.get("preuve", "")

    prompt = (
        f"Tu rédiges un mini-audit de marque pour un prospect : {company.nom} ({company.region}).\n"
        f"Score global : {scores.get('global')}/100.\n"
        f"FAILLES CONSTATÉES (n'invente RIEN au-delà de cette liste) :\n{faits}\n\n"
        f"Ton de voix : {ton}.\n"
        f"{('Preuve à mobiliser : ' + preuve) if preuve else ''}\n"
        "Produis : (1) une accroche d'une phrase pour un email, "
        "(2) un mini-audit en markdown (120 mots max), factuel, orienté action. "
        "Format : première ligne = ACCROCHE: ..., puis le markdown."
    )

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODELE, max_tokens=600, messages=[{"role": "user", "content": prompt}]
    )
    texte = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    accroche, audit = _split_sortie(texte, gaps)
    return accroche, audit


def _split_sortie(texte: str, gaps: list[Gap]) -> tuple[str, str]:
    accroche = _accroche_depuis_gaps(gaps)
    audit = texte.strip()
    for ligne in texte.splitlines():
        if ligne.strip().upper().startswith("ACCROCHE:"):
            accroche = ligne.split(":", 1)[1].strip()
            audit = texte.replace(ligne, "", 1).strip()
            break
    return accroche, audit
