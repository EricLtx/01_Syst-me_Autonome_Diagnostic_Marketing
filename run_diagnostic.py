#!/usr/bin/env python3
"""
run_diagnostic.py — point d'entrée CLI du J1.

Exemple :
    python run_diagnostic.py --nom "Climatisation Tremblay" \
        --url "https://exemple-hvac.ca" --region "Québec, QC"

Sans clé API, la synthèse retombe sur le repli déterministe : ça tourne
hors-ligne. Avec ANTHROPIC_API_KEY, le mini-audit est rédigé par le LLM.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permet de lancer depuis n'importe quel répertoire sans pip install -e
sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagnostic.collectors.gbp import GbpCollector
from diagnostic.collectors.reviews import ReviewsCollector
from diagnostic.collectors.seo import SeoCollector
from diagnostic.collectors.social import SocialCollector
from diagnostic.collectors.website import WebsiteCollector
from diagnostic.config import load_knowledge, load_rubrique
from diagnostic.models import Company
from diagnostic.pipeline import DiagnosticPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnostic de marque (persona 1 — HVAC)")
    parser.add_argument("--nom", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--region", default="")
    parser.add_argument("--json", action="store_true", help="Sortie JSON complète")
    args = parser.parse_args()

    company = Company(nom=args.nom, url=args.url, region=args.region)
    pipeline = DiagnosticPipeline(
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

    diag = pipeline.run(company)

    if args.json:
        print(diag.to_json())
    else:
        print(diag.mini_audit)
        print("\n" + "─" * 60)
        print(f"ACCROCHE OUTREACH : {diag.accroche}")


if __name__ == "__main__":
    main()
