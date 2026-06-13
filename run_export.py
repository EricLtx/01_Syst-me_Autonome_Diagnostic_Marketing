#!/usr/bin/env python3
"""
run_export.py — agent d'export J5 (couche de sortie Kemana).

Lecture seule sur le vault. Aucune transition d'état. Idempotent.
Aucun appel réseau : lit les fiches valide, produit le fichier, s'arrête.

Usage :
  python run_export.py                                   # CSV toutes fiches valide/non opt_out
  python run_export.py --icp persona1-quebec             # filtré par ICP
  python run_export.py --format jsonl                    # JSONL au lieu de CSV
  python run_export.py --out exports/cible-qc.csv        # chemin explicite (hors vault)
  python run_export.py --dry-run                         # aperçu, n'écrit RIEN
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from diagnostic.export import (
    charger_schema_kemana,
    collect_fiches_exportables,
    fiche_vers_ligne_kemana,
    lignes_vers_csv,
    lignes_vers_jsonl,
    valider_ligne,
    verifier_chemin_hors_vault,
)
from diagnostic.vault_io import VaultIO

_VAULT_PAR_DEFAUT = Path("vault")
_EXPORTS_DIR = Path("exports")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export J5 — fiches valide → liste Kemana (CSV / JSONL). Lecture seule."
    )
    parser.add_argument("--icp", default=None, metavar="ICP_ID", help="Filtrer par ICP")
    parser.add_argument("--format", choices=["csv", "jsonl"], default="csv", dest="fmt")
    parser.add_argument("--out", default=None, metavar="CHEMIN", help="Fichier de sortie (hors vault)")
    parser.add_argument("--dry-run", action="store_true", help="Affiche les comptes, n'écrit RIEN")
    parser.add_argument("--vault", default=str(_VAULT_PAR_DEFAUT), metavar="CHEMIN")
    args = parser.parse_args()

    vault_path = Path(args.vault)
    vault_io = VaultIO(vault_path)

    try:
        colonnes = charger_schema_kemana()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERREUR] Schéma Kemana invalide : {exc}", file=sys.stderr)
        sys.exit(1)

    # Comptes pour le rapport
    all_valides = vault_io.query(statut="valide")
    nb_valides_total = len(all_valides)
    nb_opt_out = sum(1 for _, f in all_valides if f.opt_out)

    fiches = collect_fiches_exportables(vault_io, icp_id=args.icp)

    lignes: list[dict] = []
    toutes_anomalies: list[str] = []
    for fiche in fiches:
        ligne = fiche_vers_ligne_kemana(fiche, colonnes)
        anomalies = valider_ligne(ligne, fiche_nom=fiche.nom)
        toutes_anomalies.extend(anomalies)
        lignes.append(ligne)

    nb_filtrees_icp = nb_valides_total - nb_opt_out - len(lignes) if args.icp else 0

    print(
        f"Fiches valide (total) : {nb_valides_total} | "
        f"Exclues opt_out : {nb_opt_out}"
        + (f" | Filtrées ICP : {nb_filtrees_icp}" if args.icp else "")
        + f" | Exportées : {len(lignes)} | Anomalies : {len(toutes_anomalies)}"
    )

    if toutes_anomalies:
        print("Anomalies :")
        for a in toutes_anomalies:
            print(f"  ⚠ {a}")

    if args.dry_run:
        print("[DRY-RUN] Aucun fichier écrit.")
        return

    # Chemin de sortie
    suffixe = args.icp.replace("/", "-") if args.icp else "tous"
    today = date.today().isoformat()
    ext = "jsonl" if args.fmt == "jsonl" else "csv"
    out_path = Path(args.out) if args.out else _EXPORTS_DIR / f"kemana_{suffixe}_{today}.{ext}"

    try:
        verifier_chemin_hors_vault(out_path, vault_path)
    except ValueError as exc:
        print(f"[ERREUR FATALE] {exc}", file=sys.stderr)
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if args.fmt == "jsonl":
        out_path.write_bytes(lignes_vers_jsonl(lignes))
    else:
        out_path.write_bytes(lignes_vers_csv(lignes, colonnes))
    print(f"Fichier écrit : {out_path}")

    if toutes_anomalies:
        anomalies_path = out_path.with_suffix(".anomalies.txt")
        anomalies_path.write_text("\n".join(toutes_anomalies) + "\n", encoding="utf-8")
        print(f"Anomalies : {anomalies_path}")


if __name__ == "__main__":
    main()
