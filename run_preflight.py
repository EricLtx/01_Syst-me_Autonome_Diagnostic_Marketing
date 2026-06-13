#!/usr/bin/env python3
"""
run_preflight.py — vérification GO / NO-GO avant le premier run réel (§7 de la spec J5).

Code de sortie : 0 = GO, 1 = NO-GO.
Pré-condition du cron J7 : lancer ce script avant tout run automatique.

Usage :
  python run_preflight.py                           # tous les contrôles
  python run_preflight.py --icp persona1-quebec     # + vérification ICP spécifique
  python run_preflight.py --strict                  # tests_verts devient bloquant
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from diagnostic.preflight import executer_preflights, formater_rapport, verdict_global


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Préflight J5 — vérification GO / NO-GO (code de sortie 0=GO / 1=NO-GO)"
    )
    parser.add_argument("--icp", default=None, metavar="ICP_ID",
                        help="Vérifie que cet ICP spécifique existe et est valide")
    parser.add_argument("--strict", action="store_true",
                        help="tests_verts devient bloquant (défaut : warn)")
    parser.add_argument("--vault", default="vault", metavar="CHEMIN")
    parser.add_argument("--cache-dir", default=".cache/api_io", metavar="CHEMIN")
    args = parser.parse_args()

    checks = executer_preflights(
        vault_path=Path(args.vault),
        cache_dir=Path(args.cache_dir),
        icp_id=args.icp,
        strict=args.strict,
    )

    print(formater_rapport(checks))

    go = verdict_global(checks)
    print("=" * 50)
    print(f"VERDICT : {'GO ✅' if go else 'NO-GO ❌'}")

    sys.exit(0 if go else 1)


if __name__ == "__main__":
    main()
