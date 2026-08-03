"""
vault_runner.py — orchestrateur du mode « --out vault ».

Lit toutes les fiches `decouvert` dans le vault, exécute le pipeline J1
sur chacune, écrit le rapport et met à jour le frontmatter.

Principe n°2 (échec isolé) : si le pipeline échoue sur une fiche, elle reste
`decouvert`, l'erreur est journalisée, et le traitement des autres continue.

ADR 0003 (multi-industrie) — correction de B4 : AVANT, un seul pipeline était
construit avec la rubrique persona 1, avant la boucle, puis appliqué à TOUTES
les fiches quel que soit leur secteur. Écrire une seconde rubrique n'avait
alors aucun effet. Désormais, chaque fiche est résolue à SON secteur
(`secteur_id_for_fiche`) et un pipeline est construit — et mis en cache — PAR
secteur rencontré dans le lot, pas par run.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from diagnostic.collectors.gbp import GbpCollector
from diagnostic.collectors.legitimite import LegitimiteCollector
from diagnostic.collectors.reviews import ReviewsCollector
from diagnostic.collectors.seo import SeoCollector
from diagnostic.collectors.social import SocialCollector
from diagnostic.collectors.website import WebsiteCollector
from diagnostic.config import (
    load_certifications,
    load_icp,
    load_knowledge,
    load_rubrique,
    load_rubrique_intention,
    load_vocabulaire,
    load_vocabulaire_intention,
)
from diagnostic.models import Company
from diagnostic.pipeline import DiagnosticPipeline
from diagnostic.serializers import diagnostic_to_fiche, diagnostic_to_rapport_md
from diagnostic.vault_io import VaultIO
from diagnostic.vault_schema import FicheProspect

# Marché par défaut pour la résolution des motifs de légitimité
# (`legitimite.py`, ADR 0004) : seul marché ayant un ICP réel dans ce dépôt
# à ce jour (persona1-quebec.yaml). Une licence professionnelle (RBQ, RGE,
# suissetec...) est propre à une juridiction, pas à un secteur d'activité —
# voir `config.py::load_certifications` pour le schéma prévu pour d'autres
# marchés. Limite assumée : ce câblage ne varie pas encore par fiche, même
# simplification déjà acceptée pour `vocabulaire_offre` (partagé par secteur).
MARCHE_CERTIFICATIONS_PAR_DEFAUT = "quebec"


def secteur_id_for_fiche(fiche: FicheProspect) -> str:
    """Résout la clé de configuration (rubrique/vocabulaire) pour CETTE fiche.

    Priorité à l'ICP (`icp_id` → `IcpConfig.secteur_id`, qui peut être un
    secteur inédit) ; repli sur `persona{N}` si `icp_id` est absent ou
    introuvable — une fiche antérieure à J4 (pas d'`icp_id`) doit rester
    diagnostiquable sans lever d'exception.
    """
    if fiche.icp_id:
        try:
            return load_icp(fiche.icp_id).secteur_id  # type: ignore[return-value]
        except Exception:
            pass  # ICP introuvable/invalide → repli déterministe ci-dessous
    persona = fiche.persona if fiche.persona is not None else 1
    return f"persona{persona}"


def make_pipeline_for_secteur(secteur_id: str, api_io=None) -> DiagnosticPipeline:
    """Construit le pipeline J1 pour CE secteur (rubrique + vocabulaire propres).

    C'est le geste qui corrige B4 : `run_vault_mode` appelle cette factory une
    fois par `secteur_id` rencontré dans le lot, jamais une fois pour tout le
    run.
    """
    vocabulaire = (load_vocabulaire(secteur_id) or {}).get("mots_offre")
    vocabulaire_intention = (load_vocabulaire_intention(secteur_id) or {}).get("mots_recrutement")
    motifs_legitimite = load_certifications(MARCHE_CERTIFICATIONS_PAR_DEFAUT)
    return DiagnosticPipeline(
        collectors=[
            WebsiteCollector(
                vocabulaire_offre=vocabulaire,
                vocabulaire_intention=vocabulaire_intention,
            ),
            GbpCollector(),
            ReviewsCollector(),
            SeoCollector(),
            SocialCollector(),
            LegitimiteCollector(motifs=motifs_legitimite),
        ],
        rubrique=load_rubrique(secteur_id),
        knowledge=load_knowledge(secteur_id),
        api_io=api_io,
        rubrique_intention=load_rubrique_intention(secteur_id),
    )


def run_vault_mode(
    vault_path: Path,
    pipeline=None,
) -> dict[str, list[str]]:
    """Traite toutes les fiches `decouvert` dans le vault.

    `pipeline` accepte trois formes (résolues par fiche, jamais une seule
    fois avant la boucle) :
      - un `DiagnosticPipeline` déjà construit (ou un double de test type
        `MagicMock`) : appliqué tel quel à TOUTES les fiches — comportement
        historique préservé pour les call sites existants. Le discriminant
        est `hasattr(pipeline, "run")` et non `isinstance(...)` : un
        `MagicMock` n'est pas une instance de `DiagnosticPipeline`, mais il
        répond à `.run` — `isinstance` casserait ces doubles de test.
      - une factory `Callable[[secteur_id], DiagnosticPipeline]` : appelée
        une fois par secteur rencontré (mise en cache), pour injecter par
        exemple une `ApiIO` partagée (voir `orchestrator.py`, `run_diagnostic.py`).
      - `None` (défaut) : résolution par fiche via `make_pipeline_for_secteur`,
        sans injection réseau — comportement hors-ligne du mode CLI nu.

    Workflow par fiche :
      1. Résout le pipeline propre à SON secteur
      2. Construit Company depuis la fiche
      3. Exécute le pipeline de diagnostic
      4. Écrit le rapport dans 30-Diagnostics/ (journalisé)
      5. Met à jour le frontmatter (score, gaps, date, wikilink rapport)
      6. Effectue la transition decouvert → diagnostique (journalisée)

    Retourne {"ok": [noms], "erreurs": [messages]} pour le CLI.
    """
    io = VaultIO(Path(vault_path))
    fiches = io.query(statut="decouvert")
    ok: list[str] = []
    erreurs: list[str] = []

    # Un pipeline par secteur_id rencontré dans CE lot (pas par run entier).
    pipelines_par_secteur: dict[str, DiagnosticPipeline] = {}

    for fiche_path, fiche in fiches:
        try:
            if hasattr(pipeline, "run"):
                pl = pipeline
            else:
                secteur_id = secteur_id_for_fiche(fiche)
                if secteur_id not in pipelines_par_secteur:
                    fabrique: Callable[[str], DiagnosticPipeline] = (
                        pipeline if callable(pipeline) else make_pipeline_for_secteur
                    )
                    pipelines_par_secteur[secteur_id] = fabrique(secteur_id)
                pl = pipelines_par_secteur[secteur_id]

            company = Company(
                nom=fiche.nom,
                url=fiche.site_web or "",
                region=str(fiche.marche),
            )

            diag = pl.run(company)

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
                signal_intention=fiche_maj.signal_intention,
                date_intention=fiche_maj.date_intention,
                intention_expire_le=fiche_maj.intention_expire_le,
            )

            # Transition d'état (journalisée dans vault_io.transition)
            io.transition(fiche_path, "diagnostique", acteur="agent")
            ok.append(fiche.nom)

        except Exception as exc:
            io.log_erreur("vault_runner", fiche_path.name, str(exc))
            erreurs.append(f"{fiche.nom} : {exc}")

    return {"ok": ok, "erreurs": erreurs}
