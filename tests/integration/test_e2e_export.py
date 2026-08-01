"""
test_e2e_export.py — flux de sortie J5, de bout en bout.

Chaîne réellement exercée : vault semé → `run_export.main()` (le VRAI point
d'entrée CLI, pas une réimplémentation) → fichier Kemana CSV/JSONL hors vault
+ rapport d'anomalies.

L'assertion centrale est réglementaire : une fiche `opt_out: true` ne doit
JAMAIS sortir, quel que soit son statut ou son score (RGPD / CASL / nLPD).
"""

from __future__ import annotations

import csv
import json
import sys

import pytest

from diagnostic.vault_io import VaultIO


def _exporter(monkeypatch, chemins, *args) -> None:
    """Appelle le vrai CLI d'export avec des arguments donnés."""
    import run_export
    argv = ["run_export.py", "--vault", str(chemins["vault"]), *args]
    monkeypatch.setattr(sys, "argv", argv)
    run_export.main()


def _lire_csv(path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class TestFluxExport:

    def test_opt_out_est_exclu_absolument(self, vault_seme, chemins, monkeypatch, tmp_path):
        sortie = tmp_path / "kemana.csv"
        _exporter(monkeypatch, chemins, "--out", str(sortie))

        lignes = _lire_csv(sortie)
        boites = {l["Boîte"] for l in lignes}

        # HVAC Saguenay est `valide`, bien notée, avec un email vérifié…
        # et opt_out: true. Elle ne doit apparaître nulle part.
        io = VaultIO(chemins["vault"])
        opt_out = [f.nom for _, f in io.query(statut="valide") if f.opt_out]
        assert "HVAC Saguenay" in opt_out, "le dataset doit contenir un opt_out"
        assert "HVAC Saguenay" not in boites
        assert "HVAC Saguenay" not in sortie.read_bytes().decode("utf-8-sig")

        # Les autres fiches validées sont bien là.
        assert "Clim Rive-Sud" in boites
        assert "Aéroclim Beauce" in boites

    def test_seules_les_fiches_valide_sortent(self, vault_seme, chemins, monkeypatch, tmp_path):
        sortie = tmp_path / "kemana.csv"
        _exporter(monkeypatch, chemins, "--out", str(sortie))
        boites = {l["Boîte"] for l in _lire_csv(sortie)}

        assert "Climatisation Tremblay" not in boites   # decouvert
        assert "CVAC Gagnon et Fils" not in boites      # diagnostique
        assert "Froid Boréal" not in boites             # rejete

    def test_colonnes_kemana_et_contenu(self, vault_seme, chemins, monkeypatch, tmp_path):
        sortie = tmp_path / "kemana.csv"
        _exporter(monkeypatch, chemins, "--out", str(sortie))

        lignes = _lire_csv(sortie)
        entetes = list(lignes[0].keys())
        assert entetes == ["Nom", "Titre", "Boîte", "ICP", "Email", "Source email",
                           "Site", "Score", "Signal chaud", "Statut"]

        rive_sud = next(l for l in lignes if l["Boîte"] == "Clim Rive-Sud")
        assert rive_sud["Nom"] == "Karine Meunier"
        assert rive_sud["Email"] == "karine@clim-rive-sud.test"
        assert rive_sud["Source email"] == "verified"
        assert rive_sud["Statut"] == "valide"
        assert rive_sud["Signal chaud"]

    def test_rapport_anomalies_pour_fiche_sans_email(
        self, vault_seme, chemins, monkeypatch, tmp_path
    ):
        sortie = tmp_path / "kemana.csv"
        _exporter(monkeypatch, chemins, "--out", str(sortie))

        anomalies = sortie.with_suffix(".anomalies.txt")
        assert anomalies.exists()
        texte = anomalies.read_text(encoding="utf-8")
        assert "Aéroclim Beauce" in texte and "email manquant" in texte

    def test_export_est_en_lecture_seule(
        self, vault_seme, chemins, monkeypatch, tmp_path, journal_vierge
    ):
        """Aucune transition d'état, aucun appel réseau."""
        io = VaultIO(chemins["vault"])
        avant = {f.nom: str(f.statut) for _, f in io.query()}

        _exporter(monkeypatch, chemins, "--out", str(tmp_path / "kemana.csv"))

        apres = {f.nom: str(f.statut) for _, f in io.query()}
        assert apres == avant
        assert journal_vierge.journal == []

    def test_refuse_decrire_dans_le_vault(self, vault_seme, chemins, monkeypatch):
        cible = chemins["vault"] / "10-Prospects" / "fuite.csv"
        with pytest.raises(SystemExit) as exc:
            _exporter(monkeypatch, chemins, "--out", str(cible))
        assert exc.value.code == 1
        assert not cible.exists()

    def test_format_jsonl(self, vault_seme, chemins, monkeypatch, tmp_path):
        sortie = tmp_path / "kemana.jsonl"
        _exporter(monkeypatch, chemins, "--format", "jsonl", "--out", str(sortie))

        objets = [json.loads(l) for l in sortie.read_text("utf-8").splitlines() if l.strip()]
        assert objets
        assert all("HVAC Saguenay" != o["Boîte"] for o in objets)

    def test_dry_run_n_ecrit_aucun_fichier(self, vault_seme, chemins, monkeypatch, tmp_path):
        sortie = tmp_path / "kemana.csv"
        _exporter(monkeypatch, chemins, "--dry-run", "--out", str(sortie))
        assert not sortie.exists()

    def test_filtre_par_icp(self, vault_seme, chemins, monkeypatch, tmp_path):
        sortie = tmp_path / "kemana.csv"
        _exporter(monkeypatch, chemins, "--icp", "persona9-inconnu", "--out", str(sortie))
        assert _lire_csv(sortie) == []
