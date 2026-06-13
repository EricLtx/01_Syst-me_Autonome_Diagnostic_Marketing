#!/usr/bin/env python3
"""
run_usage.py — visualisation de l'usage API J5 (§6 de la spec).

Lit api_usage.log (JSONL), agrège, affiche. Aucun appel réseau.
Avec --snapshot : enregistre le rapport dans vault/90-Systeme/ via vault_io.

Usage :
  python run_usage.py                         # rapport console depuis le début
  python run_usage.py --depuis 2025-01-01     # filtré par date de début
  python run_usage.py --snapshot              # rapport console + snapshot vault
  python run_usage.py --ledger autre.log      # ledger alternatif
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from diagnostic.usage import agreger, charger_ledger, formater_rapport

_LEDGER_PAR_DEFAUT = Path("api_usage.log")
_VAULT_PAR_DEFAUT = Path("vault")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Usage API J5 — agrégat api_usage.log. Lecture seule."
    )
    parser.add_argument("--depuis", default=None, metavar="AAAA-MM-JJ",
                        help="Ne compter que les entrées depuis cette date")
    parser.add_argument("--snapshot", action="store_true",
                        help="Enregistre le rapport dans vault/90-Systeme/")
    parser.add_argument("--ledger", default=str(_LEDGER_PAR_DEFAUT), metavar="CHEMIN")
    parser.add_argument("--vault", default=str(_VAULT_PAR_DEFAUT), metavar="CHEMIN")
    args = parser.parse_args()

    depuis: date | None = None
    if args.depuis:
        try:
            depuis = date.fromisoformat(args.depuis)
        except ValueError:
            print(f"[ERREUR] Date invalide : {args.depuis} (format attendu : AAAA-MM-JJ)",
                  file=sys.stderr)
            sys.exit(1)

    ledger_path = Path(args.ledger)
    if not ledger_path.exists():
        print(f"[AVERTISSEMENT] Ledger introuvable : {ledger_path}", file=sys.stderr)

    erreurs: list[str] = []
    entries = charger_ledger(ledger_path, depuis=depuis, erreurs_out=erreurs)
    usage = agreger(entries, nb_erreurs_lecture=len(erreurs))
    rapport = formater_rapport(usage)

    print(rapport)

    if args.snapshot:
        from diagnostic.vault_io import VaultIO
        vault_path = Path(args.vault)
        vault_io = VaultIO(vault_path)
        today = date.today().isoformat()
        filename = f"usage-{today}.md"
        path = vault_io.write_system_note(filename, rapport)
        print(f"Snapshot écrit : {path}")


if __name__ == "__main__":
    main()
