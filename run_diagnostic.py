#!/usr/bin/env python3
"""
run_diagnostic.py — point d'entrée CLI.

Mode standard (défaut) :
    python run_diagnostic.py --nom "Climatisation Tremblay" \\
        --url "https://exemple-hvac.ca" --region "Québec, QC"

Mode vault (traite toutes les fiches 'decouvert') :
    python run_diagnostic.py --out vault --vault vault/
    python run_diagnostic.py --out vault          # utilise $VAULT_PATH ou vault/

Sans clé API la synthèse retombe sur le repli déterministe.
Avec ANTHROPIC_API_KEY le mini-audit est rédigé par le LLM.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagnostic.collectors.gbp import GbpCollector
from diagnostic.collectors.reviews import ReviewsCollector
from diagnostic.collectors.seo import SeoCollector
from diagnostic.collectors.social import SocialCollector
from diagnostic.collectors.website import WebsiteCollector
from diagnostic.config import load_knowledge, load_rubrique
from diagnostic.models import Company
from diagnostic.pipeline import DiagnosticPipeline

DEFAULT_VAULT = Path(__file__).resolve().parent / "vault"


def _build_pipeline() -> DiagnosticPipeline:
    return DiagnosticPipeline(
        collectors=[
            WebsiteCollector(),
            GbpCollector(),
            ReviewsCollector(),
            SeoCollector(),
            SocialCollector(),
        ],
        rubrique=load_rubrique(),
        knowledge=load_knowledge(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnostic de marque (persona 1 — HVAC)")
    parser.add_argument("--nom", default=None, help="Nom de l'entreprise (mode standard)")
    parser.add_argument("--url", default=None, help="URL du site (mode standard)")
    parser.add_argument("--region", default="")
    parser.add_argument("--json", action="store_true", help="Sortie JSON complète (mode standard)")
    parser.add_argument(
        "--out",
        choices=["json", "vault"],
        default="json",
        help="Mode de sortie : 'json' (défaut) ou 'vault'",
    )
    parser.add_argument(
        "--vault",
        default=os.environ.get("VAULT_PATH", str(DEFAULT_VAULT)),
        help="Chemin du vault (mode --out vault, défaut : ./vault ou $VAULT_PATH)",
    )
    args = parser.parse_args()

    if args.out == "vault":
        # Import ici pour ne pas alourdir le mode standard
        from diagnostic.vault_runner import run_vault_mode
        vault_path = Path(args.vault)
        print(f"Vault : {vault_path.resolve()}")
        print("Traitement des fiches 'decouvert'...\n")
        result = run_vault_mode(vault_path, _build_pipeline())
        for nom in result["ok"]:
            print(f"  ✓ {nom}")
        for err in result["erreurs"]:
            print(f"  ✗ {err}")
        print(f"\n{len(result['ok'])} traitées · {len(result['erreurs'])} erreurs")

    else:
        # Mode standard : comportement J1 inchangé
        if not args.nom or not args.url:
            parser.error("--nom et --url sont requis en mode --out json (défaut)")

        company = Company(nom=args.nom, url=args.url, region=args.region)
        diag = _build_pipeline().run(company)

        if args.json:
            print(diag.to_json())
        else:
            print(diag.mini_audit)
            print("\n" + "─" * 60)
            print(f"ACCROCHE OUTREACH : {diag.accroche}")


if __name__ == "__main__":
    main()
