#!/usr/bin/env python3
"""
benchmark_intention.py — banc d'essai chiffré de l'axe intention (ADR 0004).

Exécute le pipeline J1 complet (besoin + intention) sur la cohorte HVAC
fictive du faux serveur d'intégration (`tests/integration/faux_api.py`,
9 entreprises), et produit un rapport CHIFFRÉ et REPRODUCTIBLE :

  - distribution des score_global (besoin) et des événements d'intention ;
  - pouvoir discriminant : combien de `signal_chaud` DISTINCTS sur N
    prospects ? combien de `signal_intention` DISTINCTS ? Métrique de
    référence explicite : AVANT les correctifs du 2026-08-01 (§CLAUDE.md,
    scoring.py), c'était 1 SEULE accroche pour TOUS les prospects — ce
    script mesure où le système en est aujourd'hui sur les DEUX axes ;
  - répartition par quadrant besoin × intention (D5, ADR 0004), seuils
    marqués [À CALIBRER] — jamais utilisée pour trier ou disqualifier ;
  - couverture moyenne (`_couverture`) et part des dimensions non observées ;
  - effet de la décroissance (`_decay.py`, usage INFORMATIONNEL, jamais
    câblé dans le scoring) : même cohorte, un même événement vieilli de
    0 / 30 / 90 / 180 jours → comment un affichage continu se réordonnerait.

Tourne SANS AUCUNE clé API (faux serveur local, boucle 127.0.0.0/8) et est
DÉTERMINISTE (rejouable à l'identique le même jour — les dates du faux
serveur sont relatives à `date.today()`, comme le reste du dépôt).

Usage :
    python scripts/benchmark_intention.py
    python scripts/benchmark_intention.py --json exports/benchmark_intention.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

_RACINE = Path(__file__).resolve().parent.parent
if str(_RACINE) not in sys.path:
    sys.path.insert(0, str(_RACINE))

from diagnostic.collectors._decay import decroissance
from diagnostic.config import load_pricing, load_rubrique_intention
from diagnostic.models import Company, Diagnostic
from diagnostic.serializers import diagnostic_to_fiche
from diagnostic.vault_schema import FicheProspect
from tests.integration.faux_api import CATALOGUE, ServeurFauxApi

# Seuils informationnels [À CALIBRER] — jamais utilisés pour disqualifier
# (ADR 0004, D5). Un score BAS = un besoin FORT (rubric_persona1.yaml:11-15).
SEUIL_BESOIN_FORT = 50  # score_global < ceci ⇒ besoin "fort"


# ---------------------------------------------------------------------------
# Exécution du pipeline sur la cohorte
# ---------------------------------------------------------------------------

def _build_api_io(cache_dir: Path, ledger_path: Path):
    """Instance ApiIO DÉDIÉE au benchmark — jamais le grand livre de
    production (`api_usage.log`), pour ne jamais polluer un run réel."""
    from diagnostic.api_io import ApiIO
    pricing = load_pricing()
    return ApiIO(
        pricing, ledger_path, cache_dir=cache_dir,
        budgets=(pricing.get("budgets") or None),
    )


def _fiche_vide(nom: str) -> FicheProspect:
    return FicheProspect(
        persona=1, marche="quebec", statut="decouvert",
        nom=nom, date_creation=date.today(),
    )


def executer_cohorte(serveur: ServeurFauxApi, api_io) -> list[dict[str, Any]]:
    """Diagnostique chaque entreprise du catalogue, retourne une ligne par
    prospect (dict JSON-safe) — c'est la matière première de tout le rapport.
    """
    import run_diagnostic
    pipeline = run_diagnostic._build_pipeline(1, api_io=api_io)

    lignes: list[dict[str, Any]] = []
    for ent in CATALOGUE:
        diag: Diagnostic = pipeline.run(Company(
            nom=ent.nom, url=serveur.url_site(ent.slug), region=ent.ville,
        ))
        fiche = diagnostic_to_fiche(diag, _fiche_vide(ent.nom))

        evenements = [
            {
                "dimension": e.dimension, "preuve": e.preuve,
                "date_evenement": e.date_evenement.isoformat(),
                "expire_le": e.expire_le.isoformat(),
                "intensite": e.intensite, "citable": e.citable,
                "fiabilite": e.fiabilite,
            }
            for e in diag.evenements_intention
        ]
        intention_forte = any(
            date.today() <= e.expire_le for e in diag.evenements_intention
        )
        lignes.append({
            "nom": ent.nom,
            "qualite_fixture": ent.qualite,
            "recrute_fixture": ent.recrute,
            "score_global": diag.scores.get("global"),
            "couverture": diag.scores.get("_couverture"),
            "nb_dimensions_non_observees": sum(
                1 for k, v in diag.scores.items()
                if v is None and k not in ("global",)
            ),
            "nb_dimensions_totales": sum(
                1 for k in diag.scores if k not in ("global", "_couverture")
            ),
            "signal_chaud": fiche.signal_chaud,
            "signal_intention": fiche.signal_intention,
            "evenements_intention": evenements,
            "intention_niveau": "fort" if intention_forte else "faible",
            "besoin_niveau": (
                "inconnu" if diag.scores.get("global") is None
                else "fort" if diag.scores["global"] < SEUIL_BESOIN_FORT
                else "faible"
            ),
        })
    return lignes


# ---------------------------------------------------------------------------
# Métriques
# ---------------------------------------------------------------------------

def distribution_score_global(lignes: list[dict]) -> dict[str, Any]:
    valeurs = [l["score_global"] for l in lignes if l["score_global"] is not None]
    if not valeurs:
        return {"n_observes": 0}
    return {
        "n_observes": len(valeurs),
        "min": min(valeurs), "max": max(valeurs),
        "moyenne": round(statistics.mean(valeurs), 1),
        "mediane": round(statistics.median(valeurs), 1),
        "valeurs": {l["nom"]: l["score_global"] for l in lignes},
    }


def pouvoir_discriminant(lignes: list[dict]) -> dict[str, Any]:
    """LA métrique de référence : avant les correctifs du 2026-08-01, TOUTES
    les entreprises recevaient la MÊME accroche (1 seul signal_chaud
    distinct sur N). Ce calcul mesure où en est le système aujourd'hui, sur
    les DEUX axes (besoin ET intention)."""
    signaux_chauds = [l["signal_chaud"] for l in lignes if l["signal_chaud"]]
    signaux_intention = [l["signal_intention"] for l in lignes if l["signal_intention"]]
    return {
        "n_prospects": len(lignes),
        "signal_chaud_distincts": len(set(signaux_chauds)),
        "signal_chaud_observes": len(signaux_chauds),
        "signal_intention_distincts": len(set(signaux_intention)),
        "signal_intention_observes": len(signaux_intention),
        "prospects_avec_intention": [
            l["nom"] for l in lignes if l["signal_intention"]
        ],
    }


def repartition_quadrant(lignes: list[dict]) -> dict[str, Any]:
    """Table de correspondance D5 — JAMAIS un calcul, une lecture croisée
    de deux libellés discrets. Seuils [À CALIBRER]."""
    quadrants: dict[str, list[str]] = {
        "Q1_fenetre (besoin fort + intention forte)": [],
        "Q2_concurrence (besoin faible + intention forte)": [],
        "Q3_reservoir (besoin fort + intention faible)": [],
        "Q4_rejet (besoin faible + intention faible)": [],
        "besoin_inconnu": [],
    }
    for l in lignes:
        if l["besoin_niveau"] == "inconnu":
            quadrants["besoin_inconnu"].append(l["nom"])
        elif l["besoin_niveau"] == "fort" and l["intention_niveau"] == "fort":
            quadrants["Q1_fenetre (besoin fort + intention forte)"].append(l["nom"])
        elif l["besoin_niveau"] == "faible" and l["intention_niveau"] == "fort":
            quadrants["Q2_concurrence (besoin faible + intention forte)"].append(l["nom"])
        elif l["besoin_niveau"] == "fort" and l["intention_niveau"] == "faible":
            quadrants["Q3_reservoir (besoin fort + intention faible)"].append(l["nom"])
        else:
            quadrants["Q4_rejet (besoin faible + intention faible)"].append(l["nom"])
    return {
        "seuil_besoin_fort": f"score_global < {SEUIL_BESOIN_FORT} [À CALIBRER]",
        "repartition": quadrants,
    }


def couverture_moyenne(lignes: list[dict]) -> dict[str, Any]:
    couvertures = [l["couverture"] for l in lignes if l["couverture"] is not None]
    part_non_observees = [
        l["nb_dimensions_non_observees"] / l["nb_dimensions_totales"]
        for l in lignes if l["nb_dimensions_totales"]
    ]
    return {
        "couverture_moyenne": round(statistics.mean(couvertures), 3) if couvertures else None,
        "part_dimensions_non_observees_moyenne": (
            round(statistics.mean(part_non_observees), 3) if part_non_observees else None
        ),
    }


def effet_decroissance(lignes: list[dict]) -> dict[str, Any]:
    """Illustration INFORMATIONNELLE (jamais câblée au scoring) : comment un
    même événement, vieilli de 0/30/90/180 jours, verrait son intensité
    continue décroître — et comment un classement par intensité (jamais
    utilisé par le système réel, qui n'ordonne rien automatiquement, D5)
    se réordonnerait au fil du temps.
    """
    rubrique = load_rubrique_intention(1) or {}
    config_decay = rubrique.get("decroissance", {"demi_vie_jours": 45, "plancher": 0.1})

    porteurs = [l for l in lignes if l["evenements_intention"]]
    if not porteurs:
        return {"config": config_decay, "porteurs": [], "note": "aucun événement dans la cohorte"}

    ages_jours = (0, 30, 90, 180)
    resultat: dict[str, Any] = {"config": config_decay, "par_age": {}}
    for age in ages_jours:
        date_simulee = date.today() - timedelta(days=age)
        facteurs = []
        for l in porteurs:
            for evt in l["evenements_intention"]:
                facteur = decroissance(date_simulee, config_decay)
                facteurs.append({"nom": l["nom"], "age_simule_jours": age, "intensite_continue": round(facteur, 3)})
        # Classement décroissant par intensité — illustratif seulement.
        facteurs.sort(key=lambda f: f["intensite_continue"], reverse=True)
        resultat["par_age"][str(age)] = facteurs
    return resultat


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

def construire_rapport(lignes: list[dict]) -> dict[str, Any]:
    return {
        "genere_le": date.today().isoformat(),
        "n_prospects": len(lignes),
        "distribution_score_global": distribution_score_global(lignes),
        "pouvoir_discriminant": pouvoir_discriminant(lignes),
        "quadrant_besoin_intention": repartition_quadrant(lignes),
        "couverture": couverture_moyenne(lignes),
        "effet_decroissance": effet_decroissance(lignes),
        "detail_par_prospect": lignes,
    }


def imprimer_rapport(rapport: dict[str, Any]) -> None:
    print("=" * 78)
    print("BANC D'ESSAI — axe intention (ADR 0004)")
    print(f"Généré le {rapport['genere_le']} · {rapport['n_prospects']} prospects (faux serveur HVAC)")
    print("=" * 78)

    dsg = rapport["distribution_score_global"]
    print("\n--- Distribution score_global (besoin) ---")
    if dsg.get("n_observes"):
        print(f"  n observés : {dsg['n_observes']}/{rapport['n_prospects']}")
        print(f"  min={dsg['min']} · max={dsg['max']} · moyenne={dsg['moyenne']} · médiane={dsg['mediane']}")
        for nom, score in dsg["valeurs"].items():
            print(f"    {nom:28s} {score}")
    else:
        print("  aucun score observé")

    pd = rapport["pouvoir_discriminant"]
    print("\n--- Pouvoir discriminant ---")
    print(f"  signal_chaud distincts     : {pd['signal_chaud_distincts']} / {pd['n_prospects']} "
          f"({pd['signal_chaud_observes']} observés)")
    print(f"  signal_intention distincts : {pd['signal_intention_distincts']} / {pd['n_prospects']} "
          f"({pd['signal_intention_observes']} observés)")
    print(f"  Référence : avant les correctifs du 2026-08-01, c'était 1 SEULE "
          f"accroche pour TOUS les prospects (0 pouvoir discriminant).")
    if pd["prospects_avec_intention"]:
        print(f"  Prospects avec intention détectée : {', '.join(pd['prospects_avec_intention'])}")

    qbi = rapport["quadrant_besoin_intention"]
    print(f"\n--- Quadrant besoin × intention (seuil : {qbi['seuil_besoin_fort']}) ---")
    for quadrant, noms in qbi["repartition"].items():
        print(f"  {quadrant:52s} : {len(noms)}  {noms if noms else ''}")

    cov = rapport["couverture"]
    print("\n--- Couverture ---")
    print(f"  couverture moyenne (_couverture)            : {cov['couverture_moyenne']}")
    print(f"  part moyenne de dimensions non observées    : {cov['part_dimensions_non_observees_moyenne']}")

    dec = rapport["effet_decroissance"]
    print("\n--- Effet de la décroissance (INFORMATIONNEL — jamais dans le scoring) ---")
    print(f"  config : {dec['config']}")
    if dec.get("par_age"):
        for age, facteurs in dec["par_age"].items():
            print(f"  âge simulé {age:>3s} j :", end=" ")
            print(", ".join(f"{f['nom']}={f['intensite_continue']}" for f in facteurs))
    else:
        print(f"  {dec.get('note')}")

    print("\n" + "=" * 78)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=None,
                        help="Chemin du rapport JSON (défaut : exports/benchmark_intention.json)")
    args = parser.parse_args()

    sortie_json = Path(args.json) if args.json else _RACINE / "exports" / "benchmark_intention.json"
    cache_dir = _RACINE / ".cache" / "benchmark_intention"
    ledger_path = cache_dir / "api_usage.log"
    cache_dir.mkdir(parents=True, exist_ok=True)

    serveur = ServeurFauxApi(tls=False).demarrer()
    try:
        api_io = _build_api_io(cache_dir / "api_io", ledger_path)
        lignes = executer_cohorte(serveur, api_io)
    finally:
        serveur.arreter()

    rapport = construire_rapport(lignes)
    imprimer_rapport(rapport)

    sortie_json.parent.mkdir(parents=True, exist_ok=True)
    sortie_json.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRapport JSON écrit : {sortie_json}")


if __name__ == "__main__":
    main()
