#!/usr/bin/env python3
"""
init_vault.py — initialise le vault Obsidian (scaffold idempotent).

Usage :
    python init_vault.py                        # vault/ à côté du script
    python init_vault.py --vault chemin/vault   # chemin explicite
    python init_vault.py --vault $VAULT_PATH

Peut être relancé sans risque : aucun fichier existant n'est modifié.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagnostic.vault_init import init_vault

DEFAULT_VAULT = Path(__file__).resolve().parent / "vault"


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise le vault Obsidian (idempotent)")
    parser.add_argument(
        "--vault",
        default=os.environ.get("VAULT_PATH", str(DEFAULT_VAULT)),
        help="Chemin du vault (défaut : ./vault ou $VAULT_PATH)",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault)
    print(f"Vault : {vault_path.resolve()}")

    result = init_vault(vault_path)

    if result["created"]:
        print("\nCréés :")
        for item in result["created"]:
            print(f"  + {item}")

    if result["skipped"]:
        print("\nDéjà présents (inchangés) :")
        for item in result["skipped"]:
            print(f"  · {item}")

    print(f"\nTerminé — {len(result['created'])} créés, {len(result['skipped'])} inchangés.")
    print("\nPour sauvegarder l'état du vault :")
    print("  cd vault && git add -A && git commit -m \"snapshot $(date +%Y-%m-%d)\"")


if __name__ == "__main__":
    main()
