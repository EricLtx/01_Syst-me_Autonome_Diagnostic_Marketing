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

Principe GreenIT : le modèle n'est PAS en dur. `greenit.choisir_modele()` route
vers le plus petit modèle par défaut et n'escalade que sur condition explicite
(règles YAML). Le prompt est borné avant émission. Voir knowledge/greenit.yaml.
"""

from __future__ import annotations

import os
from typing import Any

from diagnostic import greenit
from diagnostic.models import Company, Gap

# Repli si la config GreenIT est absente : le modèle le moins cher, jamais le plus gros.
MODELE_REPLI = "claude-haiku-4-5-20251001"


def synthesize(
    company: Company,
    signaux: dict[str, Any],
    scores: dict[str, float],
    gaps: list[Gap],
    knowledge: dict[str, Any] | None = None,
    api_io=None,
) -> tuple[str, str]:
    """Retourne (accroche, mini_audit).

    Stratégie d'efficience : une première passe au profil routé (le plus frugal
    possible). Si la QA rejette le résultat, une seule seconde passe est tentée
    au profil d'escalade — et seulement si l'escalade change réellement de modèle
    (sinon on paierait deux fois le même échec).
    """
    if os.getenv("ANTHROPIC_API_KEY"):
        config = greenit.charger_config()
        modele_vu: set[str] = set()
        for quality_check_echoue in (False, True):
            contexte = _contexte_routage(scores, gaps, quality_check_echoue)
            modele, profil = greenit.choisir_modele(contexte, config)
            if modele in modele_vu:
                break  # l'escalade ne change rien : inutile de rappeler
            modele_vu.add(modele)
            try:
                accroche, audit = _synthese_llm(
                    company, scores, gaps, knowledge or {}, api_io=api_io,
                    config=config, modele=modele, profil=profil,
                )
            except Exception:  # noqa: BLE001 — en cas de souci, on ne bloque jamais
                break
            ok, _ = quality_check(audit, gaps, company)
            if ok:
                return accroche, audit
    return _synthese_repli(company, scores, gaps)


def _contexte_routage(
    scores: dict[str, float], gaps: list[Gap], quality_check_echoue: bool
) -> dict[str, Any]:
    """Faits observables qui alimentent les règles de routage YAML.

    Volontairement plat et sérialisable : les règles se lisent dans le YAML, pas
    ici. Ajouter un critère de routage = ajouter une clé ici + une règle là-bas.
    """
    return {
        "nb_failles": len(gaps),
        "score_global": float(scores.get("global", 0) or 0),
        "quality_check_echoue": quality_check_echoue,
    }


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
    company: Company, scores: dict[str, float], gaps: list[Gap], knowledge: dict[str, Any],
    api_io=None,
    config: dict[str, Any] | None = None,
    modele: str | None = None,
    profil: str | None = None,
) -> tuple[str, str]:
    """Rédaction par le LLM, strictement ancrée dans les failles fournies.

    Le modèle et le budget de sortie viennent du routage GreenIT, jamais d'une
    constante en dur : changer de modèle = éditer knowledge/greenit.yaml.
    """
    import anthropic  # import paresseux : pas de dépendance dure

    config = config if config is not None else greenit.charger_config()
    if modele is None or profil is None:
        modele, profil = greenit.choisir_modele(_contexte_routage(scores, gaps, False), config)
    modele = modele or MODELE_REPLI  # dernier filet : jamais d'appel sans modèle défini
    max_tokens = greenit.max_tokens_du_profil(profil, config)

    # Frugalité #1 : borner l'ENTRÉE. Le bloc de failles est la seule partie du
    # prompt dont la taille n'est pas maîtrisée (elle croît avec le prospect).
    faits = "\n".join(f"- [{g.gravite}] {g.dimension} : {g.preuve}" for g in gaps) or "- (aucune faille)"
    faits = greenit.tronquer_contexte(faits, config)
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
    # Plafond de dernier recours sur le prompt assemblé (ne se déclenche pas en
    # régime normal : le bloc de failles est déjà borné au-dessus).
    prompt = greenit.tronquer_contexte(prompt, config, cle="troncature_prompt_caracteres")

    client = anthropic.Anthropic()
    fn = lambda: client.messages.create(
        model=modele, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}]
    )

    if api_io is not None:
        # Via bus : tokens, empreinte, modèle et profil comptabilisés dans api_usage.log
        def _mesure(r):
            u = r.usage
            return {
                "input_tokens":  float(getattr(u, "input_tokens",  0) or 0),
                "output_tokens": float(getattr(u, "output_tokens", 0) or 0),
            }
        msg = api_io.call(
            "anthropic", "messages", fn,
            fiche=company.nom, measure=_mesure,
            region=company.region or None, modele=modele, profil=profil,
            octets_sortants=len(prompt.encode("utf-8")),
        )
    else:
        msg = fn()

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
