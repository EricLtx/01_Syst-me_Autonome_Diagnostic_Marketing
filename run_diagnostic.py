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


def _build_pipeline(api_io=None) -> DiagnosticPipeline:
    """Construit le pipeline J1.

    `api_io` : injection de l'UNIQUE bus I/O. L'orchestrateur Kemana-Flow passe
    ici la même instance ApiIO que la découverte (budgets partagés, grand livre
    unique) ; le défaut AS-IS était qu'aucun ApiIO n'était jamais créé côté
    diagnostic. DiagnosticPipeline propage `api_io` dans ses collecteurs et sa
    synthèse. Sans injection (défaut) le comportement J1 hors-ligne est inchangé.
    """
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
        api_io=api_io,
    )


def _build_api_io():
    """Fabrique l'unique bus I/O métré, budgets inclus (config = données).

    Import local d'ApiIO : garde le module léger et hors du chemin d'import de
    `requests`/`anthropic` au niveau module.
    """
    from diagnostic.api_io import ApiIO
    from diagnostic.config import load_pricing
    pricing = load_pricing()
    return ApiIO(
        pricing,
        Path("api_usage.log"),
        cache_dir=Path(".cache/api_io"),
        budgets=(pricing.get("budgets") or None),
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

    # UNE seule instance ApiIO, injectée dans le pipeline (câblage AS-IS corrigé).
    api_io = _build_api_io()

    if args.out == "vault":
        # Import ici pour ne pas alourdir le mode standard
        from diagnostic.vault_runner import run_vault_mode
        vault_path = Path(args.vault)
        print(f"Vault : {vault_path.resolve()}")
        print("Traitement des fiches 'decouvert'...\n")
        result = run_vault_mode(vault_path, _build_pipeline(api_io))
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
        diag = _build_pipeline(api_io).run(company)

        if args.json:
            print(diag.to_json())
        else:
            print(diag.mini_audit)
            print("\n" + "─" * 60)
            print(f"ACCROCHE OUTREACH : {diag.accroche}")


if __name__ == "__main__":
    main()
