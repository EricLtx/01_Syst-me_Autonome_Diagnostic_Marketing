#!/usr/bin/env python3
"""
faux_api_serveur.py — lance le faux serveur d'API tout seul.

Sert à travailler « comme en vrai » sans clé et sans dépense : le serveur
émule SerpAPI, Apollo, Google Places, l'API Messages d'Anthropic et les sites
web des prospects fictifs. On exporte ensuite les variables affichées, et TOUT
le système (run_discovery, run_diagnostic, run_pipeline…) tape dessus.

Usage :
  python scripts/faux_api_serveur.py                      # ports dynamiques
  python scripts/faux_api_serveur.py --port 8899          # port HTTP fixe
  python scripts/faux_api_serveur.py --sans-tls           # HTTP seul
  python scripts/faux_api_serveur.py --shell > /tmp/env.sh && source /tmp/env.sh

Exemple complet :
  python scripts/faux_api_serveur.py --port 8899 &        # laisse tourner
  export SERP_BASE_URL=http://127.0.0.1:8899 \
         APOLLO_BASE_URL=http://127.0.0.1:8899 \
         PLACES_BASE_URL=http://127.0.0.1:8899 \
         ANTHROPIC_BASE_URL=http://127.0.0.1:8899 \
         SERP_API_KEY=faux APOLLO_API_KEY=faux \
         GOOGLE_PLACES_API_KEY=faux ANTHROPIC_API_KEY=faux
  python scripts/seed_dataset.py --vault /tmp/vault_demo --base-url http://127.0.0.1:8899
  python run_diagnostic.py --out vault --vault /tmp/vault_demo

Arrêt : Ctrl-C.
"""

from __future__ import annotations

import argparse
import shlex
import sys
import time
from pathlib import Path

_RACINE = Path(__file__).resolve().parent.parent
if str(_RACINE) not in sys.path:
    sys.path.insert(0, str(_RACINE))

from tests.integration.faux_api import CATALOGUE, ServeurFauxApi  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Faux serveur d'API local (SERP, Apollo, Places, Anthropic, sites web)")
    parser.add_argument("--port", type=int, default=0,
                        help="Port HTTP (0 = port libre choisi par l'OS)")
    parser.add_argument("--port-https", type=int, default=0, dest="port_https",
                        help="Port HTTPS (0 = port libre)")
    parser.add_argument("--sans-tls", action="store_true",
                        help="N'expose que HTTP (pas de certificat auto-signé)")
    parser.add_argument("--shell", action="store_true",
                        help="N'affiche que les `export ...` (à sourcer)")
    args = parser.parse_args()

    serveur = ServeurFauxApi(
        tls=not args.sans_tls, port=args.port, port_tls=args.port_https).demarrer()

    env = serveur.variables_env()
    if args.shell:
        for cle, valeur in env.items():
            print(f"export {cle}={shlex.quote(valeur)}")
        sys.stdout.flush()
    else:
        print(f"HTTP  : {serveur.base_http}")
        if serveur.tls_actif:
            print(f"HTTPS : {serveur.base_https}   (certificat auto-signé : {serveur.chemin_cert})")
        else:
            print("HTTPS : désactivé")
        print("\nVariables d'environnement à exporter :")
        for cle, valeur in env.items():
            print(f"  export {cle}={shlex.quote(valeur)}")
        print("\nEntreprises servies (slug → site) :")
        for ent in CATALOGUE:
            print(f"  {ent.slug:26s} {serveur.url_site(ent.slug)}  [{ent.qualite}]")
        print("\nSondes : /__sante · /__journal        (Ctrl-C pour arrêter)")

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        serveur.arreter()


if __name__ == "__main__":
    main()
