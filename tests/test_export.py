"""
test_export.py — tests 1-6 de la spec J5 §5.

Test 1 : sélection — valide/non-opt_out exportée, opt_out exclue, autres statuts ignorés
Test 2 : mapping Kemana — 10 colonnes dans l'ordre, champ inexistant → ValueError
Test 3 : anomalies — email manquant → signalé, ligne quand même exportée
Test 4 : refus d'écrire dans le vault (verifier_chemin_hors_vault)
Test 5 : export lecture seule — write_fiche/transition/update_frontmatter jamais appelés
Test 6 : dry-run — aucun fichier créé, comptes corrects
"""

from __future__ import annotations

import csv
import io
import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from diagnostic.export import (
    charger_schema_kemana,
    collect_fiches_exportables,
    fiche_vers_ligne_kemana,
    lignes_vers_csv,
    lignes_vers_jsonl,
    valider_ligne,
    verifier_chemin_hors_vault,
)
from diagnostic.vault_schema import FicheProspect

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SCHEMA_REEL = Path(__file__).resolve().parent.parent / "knowledge" / "export_kemana.yaml"


def _fiche(statut="valide", opt_out=False, nom="Test HVAC", email=None, icp="persona1-quebec",
           signal_chaud=None, accroche=None, contact_nom=None) -> FicheProspect:
    return FicheProspect(
        persona=1, marche="quebec", statut=statut,
        nom=nom, date_creation=date.today(),
        opt_out=opt_out,
        contact_email=email,
        contact_email_source="verified" if email else None,
        icp_id=icp,
        signal_chaud=signal_chaud,
        accroche=accroche,
        contact_nom=contact_nom,
        site_web="https://test-hvac.ca",
        score_global=45,
    )


def _vault_avec_fiches(tmp_path: Path, fiches: list[FicheProspect]):
    from diagnostic.vault_io import VaultIO
    vault_path = tmp_path / "vault"
    (vault_path / "10-Prospects" / "persona1-quebec").mkdir(parents=True)
    (vault_path / "10-Prospects" / "persona2-france").mkdir(parents=True)
    vault_io = VaultIO(vault_path)
    for f in fiches:
        vault_io.write_fiche(f)
    return vault_path, vault_io


# ---------------------------------------------------------------------------
# Test 1 — Sélection
# ---------------------------------------------------------------------------

class TestSelection:
    def test_valide_non_opt_out_exportee(self, tmp_path):
        _, vault_io = _vault_avec_fiches(tmp_path, [
            _fiche(statut="valide", opt_out=False, nom="A HVAC"),
        ])
        fiches = collect_fiches_exportables(vault_io)
        assert len(fiches) == 1
        assert fiches[0].nom == "A HVAC"

    def test_valide_opt_out_exclue(self, tmp_path):
        _, vault_io = _vault_avec_fiches(tmp_path, [
            _fiche(statut="valide", opt_out=True, nom="B HVAC"),
        ])
        fiches = collect_fiches_exportables(vault_io)
        assert len(fiches) == 0

    def test_diagnostique_ignore(self, tmp_path):
        _, vault_io = _vault_avec_fiches(tmp_path, [
            _fiche(statut="diagnostique", opt_out=False, nom="C HVAC"),
        ])
        fiches = collect_fiches_exportables(vault_io)
        assert len(fiches) == 0

    def test_filtre_icp(self, tmp_path):
        f1 = _fiche(nom="A HVAC", icp="persona1-quebec")
        f2 = FicheProspect(
            persona=2, marche="france", statut="valide",
            nom="B France", date_creation=date.today(),
            icp_id="persona2-france",
        )
        vault_path, vault_io = _vault_avec_fiches(tmp_path, [f1, f2])
        fiches = collect_fiches_exportables(vault_io, icp_id="persona1-quebec")
        assert len(fiches) == 1
        assert fiches[0].nom == "A HVAC"

    def test_trois_fiches_une_exportee(self, tmp_path):
        _, vault_io = _vault_avec_fiches(tmp_path, [
            _fiche(statut="valide", opt_out=False, nom="A"),
            _fiche(statut="valide", opt_out=True, nom="B"),
            _fiche(statut="diagnostique", opt_out=False, nom="C"),
        ])
        fiches = collect_fiches_exportables(vault_io)
        assert len(fiches) == 1
        assert fiches[0].nom == "A"


# ---------------------------------------------------------------------------
# Test 2 — Mapping Kemana + validation schéma
# ---------------------------------------------------------------------------

class TestMappingKemana:
    def test_charger_schema_reel(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        assert len(colonnes) == 10
        entetes = [c["entete"] for c in colonnes]
        assert "Nom" in entetes
        assert "Signal chaud" in entetes
        assert "Email" in entetes

    def test_champ_inexistant_leve_valueerror(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(
            "colonnes:\n  - {entete: Test, champ: champ_qui_nexiste_pas}\nencodage: utf-8-sig\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="champ_qui_nexiste_pas"):
            charger_schema_kemana(bad)

    def test_ordre_colonnes_preserve(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiche = _fiche(
            nom="Tremblay HVAC", contact_nom="Jean T.",
            email="jean@t.ca", signal_chaud="Pas de HTTPS",
        )
        ligne = fiche_vers_ligne_kemana(fiche, colonnes)
        assert list(ligne.keys()) == [c["entete"] for c in colonnes]

    def test_valeurs_mappees_correctement(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiche = _fiche(
            nom="Tremblay HVAC",
            contact_nom="Jean T.",
            email="jean@t.ca",
            signal_chaud="Absence de site moderne",
        )
        ligne = fiche_vers_ligne_kemana(fiche, colonnes)
        assert ligne["Boîte"] == "Tremblay HVAC"
        assert ligne["Email"] == "jean@t.ca"
        assert ligne["Signal chaud"] == "Absence de site moderne"
        assert ligne["Statut"] == "valide"


# ---------------------------------------------------------------------------
# Test 3 — Anomalies
# ---------------------------------------------------------------------------

class TestAnomalies:
    def test_email_manquant_signale(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiche = _fiche(email=None, signal_chaud="Signal test")
        ligne = fiche_vers_ligne_kemana(fiche, colonnes)
        anomalies = valider_ligne(ligne, fiche_nom=fiche.nom)
        assert any("email manquant" in a for a in anomalies)

    def test_ligne_toujours_exportee_malgre_anomalie(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiche = _fiche(email=None, signal_chaud="Signal test")
        ligne = fiche_vers_ligne_kemana(fiche, colonnes)
        anomalies = valider_ligne(ligne)
        assert "Boîte" in ligne      # ligne bien produite
        assert len(anomalies) > 0   # anomalie signalée

    def test_source_email_absente_si_email_present(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiche = FicheProspect(
            persona=1, marche="quebec", statut="valide",
            nom="X", date_creation=date.today(),
            contact_email="x@x.ca",
            contact_email_source=None,  # absent !
            signal_chaud="Signal",
        )
        ligne = fiche_vers_ligne_kemana(fiche, colonnes)
        anomalies = valider_ligne(ligne, fiche_nom="X")
        assert any("source email" in a for a in anomalies)

    def test_signal_chaud_absent_signale(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiche = _fiche(email="a@a.ca", signal_chaud=None, contact_nom="Jean")
        ligne = fiche_vers_ligne_kemana(fiche, colonnes)
        anomalies = valider_ligne(ligne)
        assert any("signal chaud" in a for a in anomalies)

    def test_fiche_complete_zero_anomalie(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiche = _fiche(email="ok@ok.ca", signal_chaud="Pas de HTTPS", contact_nom="Jean")
        ligne = fiche_vers_ligne_kemana(fiche, colonnes)
        assert valider_ligne(ligne) == []


# ---------------------------------------------------------------------------
# Test 4 — Refus d'écrire dans le vault
# ---------------------------------------------------------------------------

class TestRefusVault:
    def test_chemin_dans_vault_leve_valueerror(self, tmp_path):
        vault = tmp_path / "vault"
        out = vault / "exports" / "liste.csv"
        with pytest.raises(ValueError, match="DANS le vault"):
            verifier_chemin_hors_vault(out, vault)

    def test_chemin_hors_vault_ok(self, tmp_path):
        vault = tmp_path / "vault"
        out = tmp_path / "exports" / "liste.csv"
        verifier_chemin_hors_vault(out, vault)  # ne lève pas

    def test_chemin_adjacent_hors_vault(self, tmp_path):
        vault = tmp_path / "vault"
        out = tmp_path / "vault_exports" / "liste.csv"  # commence par "vault" mais hors
        verifier_chemin_hors_vault(out, vault)  # ne lève pas


# ---------------------------------------------------------------------------
# Test 5 — Export lecture seule : vault_io ne reçoit aucun appel d'écriture
# ---------------------------------------------------------------------------

class TestExportLectureSeule:
    def test_write_fiche_jamais_appele(self):
        vault_io = MagicMock()
        vault_io.query.return_value = []
        collect_fiches_exportables(vault_io)
        vault_io.write_fiche.assert_not_called()

    def test_update_frontmatter_jamais_appele(self):
        vault_io = MagicMock()
        vault_io.query.return_value = []
        collect_fiches_exportables(vault_io)
        vault_io.update_frontmatter.assert_not_called()

    def test_transition_jamais_appelee(self):
        vault_io = MagicMock()
        vault_io.query.return_value = []
        collect_fiches_exportables(vault_io)
        vault_io.transition.assert_not_called()

    def test_vault_non_modifie_apres_export(self, tmp_path):
        """Vérification réelle : lire les mtimes avant et après export."""
        f = _fiche(nom="Alpha HVAC", email="a@a.ca", signal_chaud="Signal")
        vault_path, vault_io = _vault_avec_fiches(tmp_path, [f])

        prospects_dir = vault_path / "10-Prospects"
        mtimes_avant = {p: p.stat().st_mtime for p in prospects_dir.rglob("*.md")}

        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiches = collect_fiches_exportables(vault_io)
        for fiche in fiches:
            fiche_vers_ligne_kemana(fiche, colonnes)

        mtimes_apres = {p: p.stat().st_mtime for p in prospects_dir.rglob("*.md")}
        assert mtimes_avant == mtimes_apres


# ---------------------------------------------------------------------------
# Test 6 — Sérialisation CSV / JSONL
# ---------------------------------------------------------------------------

class TestSerialisation:
    def test_csv_encode_utf8sig(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiche = _fiche(nom="Écolé Réfrig.", email="e@e.ca", signal_chaud="Sig")
        ligne = fiche_vers_ligne_kemana(fiche, colonnes)
        data = lignes_vers_csv([ligne], colonnes)
        assert data[:3] == b"\xef\xbb\xbf"  # BOM utf-8-sig

    def test_csv_contient_toutes_les_colonnes(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiche = _fiche(nom="A", email="a@a.ca", signal_chaud="S")
        ligne = fiche_vers_ligne_kemana(fiche, colonnes)
        data = lignes_vers_csv([ligne], colonnes)
        text = data.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        assert len(rows) == 1
        assert "Signal chaud" in rows[0]
        assert "Email" in rows[0]

    def test_jsonl_une_ligne_par_fiche(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        fiches = [
            _fiche(nom="A", email="a@a.ca", signal_chaud="S1"),
            _fiche(nom="B", email="b@b.ca", signal_chaud="S2"),
        ]
        lignes = [fiche_vers_ligne_kemana(f, colonnes) for f in fiches]
        data = lignes_vers_jsonl(lignes)
        lignes_out = [json.loads(l) for l in data.decode("utf-8").strip().splitlines()]
        assert len(lignes_out) == 2

    def test_csv_vide_si_aucune_fiche(self):
        colonnes = charger_schema_kemana(SCHEMA_REEL)
        data = lignes_vers_csv([], colonnes)
        text = data.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        assert list(reader) == []

    def test_jsonl_vide_si_aucune_fiche(self):
        data = lignes_vers_jsonl([])
        assert data == b""
