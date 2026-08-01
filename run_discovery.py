#!/usr/bin/env python3
"""
run_discovery.py — agent de découverte J4.

Phase 1a : SERP → candidates filtrées et dédupliquées.
Phase 1b : Apollo → contact enrichi par candidate.
Écriture atomique via VaultIO ; déduplication inter-runs via vault_io.exists().

Usage :
  python run_discovery.py --icp persona1-quebec
  python run_discovery.py --icp persona1-quebec --sans-contact
  python run_discovery.py --icp persona1-quebec --dry-run
  python run_discovery.py --icp persona1-quebec --enrichir-existants
  python run_discovery.py --icp persona1-quebec --vault chemin/vers/vault
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from diagnostic.api_io import ApiIO, BudgetExceeded
from diagnostic.config import load_icp, load_pricing
from diagnostic.discovery import DiscoveryCollector
from diagnostic.enrichment import Contact, PersonEnrichment
from diagnostic.icp_schema import Candidate, IcpConfig
from diagnostic.vault_io import VaultIO
from diagnostic.vault_schema import FicheProspect

_VAULT_PAR_DEFAUT = Path("vault")
_LEDGER_PATH = Path("api_usage.log")
_CACHE_DIR = Path(".cache/api_io")


# ---------------------------------------------------------------------------
# Mapping Candidate → FicheProspect
# ---------------------------------------------------------------------------

def _candidate_vers_fiche(
    candidate: Candidate,
    contact: Contact | None,
    icp: IcpConfig,
) -> FicheProspect:
    kwargs: dict = {
        "persona": icp.persona,
        "marche": icp.marche,
        "statut": "decouvert",
        "nom": candidate.nom,
        "site_web": candidate.site_web,
        "date_creation": date.today(),
        "source_decouverte": f"serp:{icp.icp_id}",
        "icp_id": candidate.icp_id,
        "opt_out": False,
    }
    if contact is not None:
        kwargs.update({
            "contact_nom": contact.nom_personne,
            "contact_titre": contact.titre,
            "contact_email": contact.email,
            "contact_email_source": contact.email_source,
            "contact_linkedin": contact.linkedin_url,
        })
    return FicheProspect(**kwargs)


# ---------------------------------------------------------------------------
# Mode --enrichir-existants : rejouer la phase 1b sur les fiches sans contact
# ---------------------------------------------------------------------------

def _enrichir_existants(
    icp: IcpConfig,
    api_io: ApiIO,
    vault_io: VaultIO,
    dry_run: bool,
) -> None:
    """Rejoue l'enrichissement Apollo sur les fiches existantes sans contact."""
    enrichment = PersonEnrichment(api_io=api_io, icp=icp)
    nb_enrichis = nb_erreurs = 0

    for path, fiche in vault_io.query():
        if fiche.icp_id != icp.icp_id:
            continue
        if fiche.contact_email is not None:
            continue  # déjà enrichie

        if not fiche.site_web:
            continue  # sans site_web, Apollo ne peut pas trouver

        if dry_run:
            print(f"  [DRY] enrichirait : {fiche.nom}")
            continue

        candidate = Candidate(
            nom=fiche.nom,
            site_web=fiche.site_web,
            icp_id=icp.icp_id,
            source="enrichissement-ulterieur",
            date_decouverte=date.today(),
        )

        try:
            contact = enrichment.enrich(candidate)
            if contact is not None:
                vault_io.update_frontmatter(
                    path,
                    contact_nom=contact.nom_personne,
                    contact_titre=contact.titre,
                    contact_email=contact.email,
                    contact_email_source=contact.email_source,
                    contact_linkedin=contact.linkedin_url,
                )
                nb_enrichis += 1
                print(f"  Enrichie : {fiche.nom} ({contact.nom_personne})")
        except BudgetExceeded as exc:
            print(f"[BUDGET APOLLO] {exc} — arrêt.", file=sys.stderr)
            break
        except Exception as exc:
            nb_erreurs += 1
            print(f"  [ERR] {fiche.nom}: {exc}")

    print(f"Enrichies : {nb_enrichis} | Erreurs : {nb_erreurs}")


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def run(
    *,
    icp_id: str,
    sans_contact: bool = False,
    dry_run: bool = False,
    enrichir_existants: bool = False,
    vault: str | Path = _VAULT_PAR_DEFAUT,
    api_io: ApiIO | None = None,
) -> None:
    """Point d'entrée appelable (injectable) de la découverte J4.

    Pourquoi ce paramètre `api_io` : l'orchestrateur Kemana-Flow crée UNE seule
    instance ApiIO (budgets partagés, grand livre unique) et l'injecte ici. En
    usage autonome (`api_io=None`), on fabrique le bus AVEC les budgets du YAML —
    câblage `budgets=` que le défaut AS-IS omettait (dépense non bornée).
    La logique métier de découverte reste intégralement dans ce module.
    """
    icp = load_icp(icp_id)
    if api_io is None:
        pricing = load_pricing()
        api_io = ApiIO(
            pricing, _LEDGER_PATH, cache_dir=_CACHE_DIR,
            budgets=(pricing.get("budgets") or None),
        )
    vault_io = VaultIO(Path(vault))

    if enrichir_existants:
        _enrichir_existants(icp, api_io, vault_io, dry_run=dry_run)
        return

    # --- Phase 1a : découverte SERP ----------------------------------------
    collector = DiscoveryCollector(api_io=api_io, icp=icp)
    try:
        candidates = collector.discover()
    except BudgetExceeded as exc:
        print(f"[BUDGET SERP] {exc} — arrêt de la découverte.", file=sys.stderr)
        candidates = []

    print(f"Candidates trouvées : {len(candidates)}")

    if dry_run:
        for c in candidates:
            print(f"  {c.nom:45s}  {c.site_web}")
        print("[DRY-RUN] Aucune fiche écrite dans le vault.")
        return

    # --- Phase 1b : enrichissement Apollo + écriture vault -----------------
    enrichment: PersonEnrichment | None = (
        None if sans_contact
        else PersonEnrichment(api_io=api_io, icp=icp)
    )

    nb_crees = nb_doublons = nb_enrichis = nb_erreurs = 0

    for candidate in candidates:
        # Dédup inter-runs — une fiche existante n'est jamais recréée
        if vault_io.exists(site_web=candidate.site_web) or vault_io.exists(nom=candidate.nom):
            nb_doublons += 1
            continue

        # Enrichissement Apollo (optionnel)
        contact: Contact | None = None
        if enrichment is not None:
            try:
                contact = enrichment.enrich(candidate)
                if contact is not None:
                    nb_enrichis += 1
            except BudgetExceeded as exc:
                print(f"[BUDGET APOLLO] {exc} — enrichissement arrêté.", file=sys.stderr)
                enrichment = None  # plus de crédits : on continue sans contact
            except Exception as exc:
                print(f"  [WARN] Enrichissement échoué ({candidate.nom}) : {exc}")

        # Écriture atomique via VaultIO
        try:
            fiche = _candidate_vers_fiche(candidate, contact, icp)
            vault_io.write_fiche(fiche)
            nb_crees += 1
        except Exception as exc:
            nb_erreurs += 1
            print(f"  [ERR] Écriture échouée ({candidate.nom}) : {exc}")

    print(
        f"Fiches créées : {nb_crees} | Doublons ignorés : {nb_doublons} | "
        f"Enrichies : {nb_enrichis} | Erreurs : {nb_erreurs}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agent de découverte J4 — SERP + Apollo → fiches decouvert"
    )
    parser.add_argument("--icp", required=True, metavar="ICP_ID",
                        help="Identifiant ICP (ex : persona1-quebec)")
    parser.add_argument("--sans-contact", action="store_true",
                        help="Phase 1a uniquement — zéro crédit Apollo")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche les candidates, n'écrit RIEN dans le vault")
    parser.add_argument("--enrichir-existants", action="store_true",
                        help="Rejoue la phase 1b sur les fiches sans contact")
    parser.add_argument("--vault", default=str(_VAULT_PAR_DEFAUT), metavar="CHEMIN",
                        help="Chemin du vault Obsidian")
    args = parser.parse_args()

    # Usage autonome : run() fabrique le bus AVEC budgets (câblage AS-IS corrigé).
    run(
        icp_id=args.icp,
        sans_contact=args.sans_contact,
        dry_run=args.dry_run,
        enrichir_existants=args.enrichir_existants,
        vault=args.vault,
    )


if __name__ == "__main__":
    main()
