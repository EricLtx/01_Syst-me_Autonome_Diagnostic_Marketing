#!/usr/bin/env python3
"""
seed_dataset.py — sème le dataset minimal de démonstration dans un vault.

Produit un vault initialisé (scaffold de production, via `init_vault`) plus un
jeu de fiches couvrant TOUS les états qui comptent en aval :

  decouvert    ×2  — matière du pipeline de diagnostic
  diagnostique ×1  — en attente de la porte humaine
  valide       ×2  — exportables vers Kemana
  valide+opt_out×1 — doit être exclue de tout export (RGPD / CASL / nLPD)
  rejete       ×1  — état final

IDEMPOTENT : une fiche dont le `nom` existe déjà n'est pas récrite (statut,
score et annotations humaines survivent). `--forcer` récrit tout.

Usage :
  python scripts/seed_dataset.py --vault /tmp/vault_demo
  python scripts/seed_dataset.py --vault /tmp/vault_demo --forcer
  python scripts/seed_dataset.py --vault /tmp/vault_demo \
      --base-url http://127.0.0.1:8899     # sites servis par le faux serveur

Sans `--base-url`, les sites pointent sur des domaines `.test` (RFC 6761),
jamais résolvables : aucun risque de taper un vrai site par accident.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_RACINE = Path(__file__).resolve().parent.parent
if str(_RACINE) not in sys.path:
    sys.path.insert(0, str(_RACINE))

from tests.integration import dataset  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sème un dataset de démonstration dans un vault (idempotent)")
    parser.add_argument("--vault", required=True, metavar="CHEMIN",
                        help="Chemin du vault à initialiser et peupler")
    parser.add_argument("--base-url", default=None, metavar="URL",
                        help="Base HTTP du faux serveur : les sites deviennent "
                             "<URL>/sites/<slug> (défaut : domaines .test inertes)")
    parser.add_argument("--forcer", action="store_true",
                        help="Récrit les fiches déjà présentes (perd leur état)")
    args = parser.parse_args()

    vault = Path(args.vault)
    if args.base_url:
        base = args.base_url.rstrip("/")
        url_site = lambda slug: f"{base}/sites/{slug}"  # noqa: E731
    else:
        url_site = None

    print(f"Vault : {vault.resolve()}")
    resultat = dataset.semer(vault, url_site=url_site, forcer=args.forcer)

    if resultat["crees"]:
        print("\nFiches créées :")
        for nom in resultat["crees"]:
            print(f"  + {nom}")
    if resultat["existants"]:
        print("\nDéjà présentes (inchangées) :")
        for nom in resultat["existants"]:
            print(f"  · {nom}")

    compte = dataset.resume(vault)
    print("\nÉtat du vault par statut :")
    for statut in sorted(compte):
        print(f"  {statut:14s} {compte[statut]}")
    print(f"\nTerminé — {len(resultat['crees'])} créées, "
          f"{len(resultat['existants'])} inchangées.")


if __name__ == "__main__":
    main()
