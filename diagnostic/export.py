"""
export.py — couche de sortie J5 (§5 de la spec).

Logique pure : sélection, mapping, validation, sérialisation.
Aucun I/O réseau. Aucune écriture vault. Lecture seule.
L'écriture du fichier de sortie est déléguée à run_export.py.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

import yaml

from diagnostic.vault_schema import FicheProspect

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def charger_schema_kemana(path: Path | None = None) -> list[dict]:
    """Charge le schéma de colonnes Kemana et vérifie que chaque champ existe dans FicheProspect.

    Lève ValueError si un champ est absent du modèle.
    """
    p = path or KNOWLEDGE_DIR / "export_kemana.yaml"
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    colonnes = raw["colonnes"]
    champs_fiche = set(FicheProspect.model_fields.keys())
    for col in colonnes:
        champ = col["champ"]
        if champ not in champs_fiche:
            raise ValueError(
                f"Colonne Kemana : champ `{champ}` absent de FicheProspect. "
                f"Champs disponibles : {sorted(champs_fiche)}"
            )
    return colonnes


def verifier_chemin_hors_vault(out: Path, vault: Path) -> None:
    """Lève ValueError si le chemin de sortie est situé DANS le vault.

    Garde-fou absolu : les artefacts d'export ne doivent jamais polluer le vault.
    """
    out_resolved = out.resolve()
    vault_resolved = vault.resolve()
    in_vault = False
    try:
        out_resolved.relative_to(vault_resolved)
        in_vault = True
    except ValueError:
        pass
    if in_vault:
        raise ValueError(
            f"Le chemin de sortie `{out}` est situé DANS le vault (`{vault}`). "
            "Les artefacts d'export doivent rester hors du vault."
        )


def collect_fiches_exportables(
    vault_io: Any,
    *,
    icp_id: str | None = None,
) -> list[FicheProspect]:
    """Lit les fiches valide non opt_out via vault_io.query(). Lecture seule.

    Aucun réseau. Aucune écriture vault. Filtres cumulatifs.
    """
    result: list[FicheProspect] = []
    for _, fiche in vault_io.query(statut="valide"):
        if fiche.opt_out:
            continue
        if icp_id is not None and fiche.icp_id != icp_id:
            continue
        result.append(fiche)
    return result


def fiche_vers_ligne_kemana(fiche: FicheProspect, colonnes: list[dict]) -> dict[str, Any]:
    """Mappe une FicheProspect vers un dict de colonnes Kemana (ordre préservé)."""
    fiche_dict = fiche.model_dump(mode="json")
    return {col["entete"]: fiche_dict.get(col["champ"]) for col in colonnes}


def valider_ligne(ligne: dict, *, fiche_nom: str = "") -> list[str]:
    """Retourne les anomalies sans exclure la ligne.

    Chaque anomalie = donnée utile au premier contact qui manque.
    La ligne est toujours exportée ; les anomalies alimentent le rapport.
    """
    anomalies: list[str] = []
    prefix = f"{fiche_nom} : " if fiche_nom else ""
    if not ligne.get("Email"):
        anomalies.append(f"{prefix}email manquant")
    if ligne.get("Email") and not ligne.get("Source email"):
        anomalies.append(f"{prefix}source email absente (audit RGPD)")
    if not ligne.get("Signal chaud"):
        anomalies.append(f"{prefix}signal chaud absent")
    if not ligne.get("Nom"):
        anomalies.append(f"{prefix}nom du contact absent")
    return anomalies


def lignes_vers_csv(lignes: list[dict], colonnes: list[dict], encodage: str = "utf-8-sig") -> bytes:
    """Sérialise en CSV bytes avec encodage configurable (utf-8-sig pour Excel FR)."""
    entetes = [col["entete"] for col in colonnes]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=entetes, extrasaction="ignore", lineterminator="\r\n")
    writer.writeheader()
    if lignes:
        writer.writerows(lignes)
    return buf.getvalue().encode(encodage)


def lignes_vers_jsonl(lignes: list[dict]) -> bytes:
    """Sérialise en JSONL bytes UTF-8."""
    if not lignes:
        return b""
    return ("\n".join(json.dumps(l, ensure_ascii=False) for l in lignes) + "\n").encode("utf-8")
