"""
vault_runner.py — orchestrateur du mode « --out vault ».

Lit toutes les fiches `decouvert` dans le vault, exécute le pipeline J1
sur chacune, écrit le rapport et met à jour le frontmatter.

Principe n°2 (échec isolé) : si le pipeline échoue sur une fiche, elle reste
`decouvert`, l'erreur est journalisée, et le traitement des autres continue.
"""
from __future__ import annotations

from pathlib import Path

from diagnostic.collectors.gbp import GbpCollector
from diagnostic.collectors.reviews import ReviewsCollector
from diagnostic.collectors.seo import SeoCollector
from diagnostic.collectors.social import SocialCollector
from diagnostic.collectors.website import WebsiteCollector
from diagnostic.config import load_knowledge, load_rubrique
from diagnostic.models import Company
from diagnostic.pipeline import DiagnosticPipeline
from diagnostic.serializers import diagnostic_to_fiche, diagnostic_to_rapport_md
from diagnostic.vault_io import VaultIO


def make_default_pipeline() -> DiagnosticPipeline:
    """Construit le pipeline J1 standard avec la rubrique persona 1."""
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


def run_vault_mode(
    vault_path: Path,
    pipeline: DiagnosticPipeline | None = None,
) -> dict[str, list[str]]:
    """Traite toutes les fiches `decouvert` dans le vault.

    Workflow par fiche :
      1. Construit Company depuis la fiche
      2. Exécute le pipeline de diagnostic
      3. Écrit le rapport dans 30-Diagnostics/ (journalisé)
      4. Met à jour le frontmatter (score, gaps, date, wikilink rapport)
      5. Effectue la transition decouvert → diagnostique (journalisée)

    Retourne {"ok": [noms], "erreurs": [messages]} pour le CLI.
    """
    io = VaultIO(Path(vault_path))
    if pipeline is None:
        pipeline = make_default_pipeline()

    fiches = io.query(statut="decouvert")
    ok: list[str] = []
    erreurs: list[str] = []

    for fiche_path, fiche in fiches:
        try:
            company = Company(
                nom=fiche.nom,
                url=fiche.site_web or "",
                region=str(fiche.marche),
            )

            diag = pipeline.run(company)

            # Rapport Markdown + wikilink
            rapport_md = diagnostic_to_rapport_md(diag)
            rapport_path = io.write_rapport(fiche, rapport_md)
            wikilink = f"[[30-Diagnostics/{rapport_path.stem}]]"

            # Mise à jour du frontmatter (hors statut)
            fiche_maj = diagnostic_to_fiche(diag, fiche)
            io.update_frontmatter(
                fiche_path,
                score_global=fiche_maj.score_global,
                gaps_majeurs=fiche_maj.gaps_majeurs,
                date_diagnostic=fiche_maj.date_diagnostic,
                rapport=wikilink,
                signal_chaud=fiche_maj.signal_chaud,
                accroche=fiche_maj.accroche,
            )

            # Transition d'état (journalisée dans vault_io.transition)
            io.transition(fiche_path, "diagnostique", acteur="agent")
            ok.append(fiche.nom)

        except Exception as exc:
            io.log_erreur("vault_runner", fiche_path.name, str(exc))
            erreurs.append(f"{fiche.nom} : {exc}")

    return {"ok": ok, "erreurs": erreurs}
