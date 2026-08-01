#!/usr/bin/env python3
"""
run_pipeline.py — CLI unique de l'orchestrateur DAG « Kemana-Flow » (Chantier CORE).

Lance la chaîne complète J1-J5 sous ordonnancement déterministe, ApiIO unique
(budgets partagés) et verrou anti-concurrence. Les run_*.py existants continuent
de fonctionner seuls : cette CLI ne les remplace pas, elle les orchestre.

Usage :
  python run_pipeline.py --icp persona1-quebec
  python run_pipeline.py --icp persona1-quebec --dry-run
  python run_pipeline.py --icp persona1-quebec --depuis diagnostic
  python run_pipeline.py --icp persona1-quebec --jusqu-a discovery
  python run_pipeline.py --icp persona1-quebec --vault chemin/vers/vault

Code de sortie : 0 = chaîne OK, 1 = arrêt (NO-GO préflight, budget dépassé,
nœud bloquant ou échec). Le préflight est la première porte : en mode réel un
NO-GO refuse le démarrage (pré-condition du cron J7) ; --dry-run informe mais
n'écrit rien et ne bloque pas.

Aucun import requests/anthropic au niveau module : l'orchestrateur ne touche
jamais le réseau, seul api_io le fait (vérifié par le garde-fou AST de preflight).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from diagnostic.orchestrator import (
    DagInvalide,
    Orchestrateur,
    VerrouExiste,
)

_STATUTS_ARRET = {"bloque", "budget_depasse", "echec"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Orchestrateur DAG Kemana-Flow — chaîne J1-J5 (préflight → découverte "
                    "→ diagnostic → [porte humaine] → export → usage)."
    )
    parser.add_argument("--icp", default=None, metavar="ICP_ID",
                        help="Identifiant ICP ciblé (ex : persona1-quebec)")
    parser.add_argument("--dry-run", action="store_true",
                        help="N'écrit RIEN ; le préflight informe sans bloquer")
    parser.add_argument("--depuis", default=None, metavar="NOEUD",
                        help="Démarre la chaîne à ce nœud (le reste de l'ordre est figé)")
    parser.add_argument("--jusqu-a", default=None, metavar="NOEUD", dest="jusqu_a",
                        help="Arrête la chaîne après ce nœud (inclus)")
    parser.add_argument("--vault", default="vault", metavar="CHEMIN",
                        help="Chemin du vault Obsidian")
    parser.add_argument("--dag", default=None, metavar="CHEMIN",
                        help="Fichier DAG YAML alternatif (défaut : dag_pipeline.yaml)")
    args = parser.parse_args()

    kwargs = dict(
        vault_path=Path(args.vault),
        icp_id=args.icp,
        dry_run=args.dry_run,
    )
    if args.dag:
        kwargs["dag_path"] = Path(args.dag)

    try:
        orch = Orchestrateur(**kwargs)
    except DagInvalide as exc:
        print(f"[DAG INVALIDE] {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"run_id : {orch.run_id}")
    try:
        resultats = orch.executer(depuis=args.depuis, jusqu_a=args.jusqu_a)
    except VerrouExiste as exc:
        print(f"[VERROU] {exc}", file=sys.stderr)
        print("Un run est déjà en cours sur ce vault — démarrage refusé.", file=sys.stderr)
        sys.exit(1)
    except DagInvalide as exc:
        print(f"[DAG] {exc}", file=sys.stderr)
        sys.exit(1)

    print("\nChaîne exécutée :")
    _SYMBOLE = {
        "execute": "✓", "saute": "→", "desactive": "·",
        "bloque": "✗", "budget_depasse": "■", "echec": "✗",
    }
    arret = False
    for r in resultats:
        print(f"  {_SYMBOLE.get(r.statut, '?')} {r.nom:16s} [{r.statut}] {r.message}")
        if r.statut in _STATUTS_ARRET:
            arret = True

    sys.exit(1 if arret else 0)


if __name__ == "__main__":
    main()
