"""
test_vault_io_historique.py — VaultIO.append_historique() (ADR 0004 D3).

Infrastructure « posée, pas exploitée » : aucun collecteur actuel n'écrit
encore ici, mais le mécanisme doit être prouvé en isolation — append-only,
jamais d'écrasement, jamais de `os.replace()` sur ce chemin.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from diagnostic.vault_io import VaultIO


def test_append_historique_cree_le_fichier_jsonl(tmp_path: Path):
    io = VaultIO(tmp_path / "vault")
    path = io.append_historique("chauffage-abc", "avis", "cadence_avis_par_mois", 1.2, "reviews")
    assert path == tmp_path / "vault" / "40-Historique" / "chauffage-abc.jsonl"
    assert path.exists()


def test_deux_appels_successifs_produisent_deux_lignes_distinctes(tmp_path: Path):
    """Append-only : jamais un écrasement, deux observations coexistent."""
    io = VaultIO(tmp_path / "vault")
    io.append_historique("chauffage-abc", "avis", "cadence_avis_par_mois", 1.2, "reviews")
    io.append_historique("chauffage-abc", "avis", "cadence_avis_par_mois", 1.5, "reviews")

    path = tmp_path / "vault" / "40-Historique" / "chauffage-abc.jsonl"
    lignes = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
    assert len(lignes) == 2
    assert lignes[0]["valeur"] == 1.2
    assert lignes[1]["valeur"] == 1.5


def test_contenu_de_la_ligne_jsonl(tmp_path: Path):
    io = VaultIO(tmp_path / "vault")
    io.append_historique("clim-rive-sud", "avis", "note_bucket", "4-4.5", "reviews")
    path = tmp_path / "vault" / "40-Historique" / "clim-rive-sud.jsonl"
    entry = json.loads(path.read_text(encoding="utf-8").strip())
    assert entry["dimension"] == "avis"
    assert entry["cle"] == "note_bucket"
    assert entry["valeur"] == "4-4.5"
    assert entry["source"] == "reviews"
    assert "ts" in entry


def test_fichiers_distincts_par_slug(tmp_path: Path):
    io = VaultIO(tmp_path / "vault")
    io.append_historique("entreprise-a", "avis", "cle", 1, "reviews")
    io.append_historique("entreprise-b", "avis", "cle", 2, "reviews")
    historique_dir = tmp_path / "vault" / "40-Historique"
    assert {p.stem for p in historique_dir.glob("*.jsonl")} == {"entreprise-a", "entreprise-b"}


def test_journalise_dans_runs_log(tmp_path: Path):
    """Comme toute écriture du bus, append_historique laisse une trace dans
    runs.log (via _journal(), jamais en écriture directe par un agent)."""
    vault = tmp_path / "vault"
    io = VaultIO(vault, log_path=tmp_path / "runs.log")
    io.append_historique("chauffage-abc", "avis", "cle", 1, "reviews")
    lignes = (tmp_path / "runs.log").read_text(encoding="utf-8").splitlines()
    entries = [json.loads(l) for l in lignes]
    assert any(e["op"] == "append_historique" for e in entries)


def test_aucun_appel_os_replace_sur_ce_chemin(tmp_path: Path):
    """D12.8 : append-only — jamais os.replace() sur ce chemin d'écriture,
    contrairement à write_fiche/update_frontmatter/write_rapport."""
    io = VaultIO(tmp_path / "vault")
    with patch("os.replace") as mock_replace:
        io.append_historique("chauffage-abc", "avis", "cle", 1, "reviews")
    mock_replace.assert_not_called()
