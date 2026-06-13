"""
test_usage.py — tests 7-8 de la spec J5 §6.

Test 7 : agrégation correcte — appels/cache/coûts/par_fournisseur/par_fiche
Test 8 : write_system_note + snapshot dans 90-Systeme/
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from diagnostic.api_schema import LedgerEntry
from diagnostic.usage import Usage, agreger, charger_ledger, formater_rapport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(
    fournisseur="serp",
    endpoint="search",
    unites=None,
    cout=0.10,
    cache_hit=False,
    fiche="Test HVAC",
    resultat="ok",
) -> LedgerEntry:
    return LedgerEntry(
        ts=datetime.now(timezone.utc),
        fournisseur=fournisseur,
        endpoint=endpoint,
        unites=unites or {"requetes": 1},
        cout_estime=cout,
        devise="USD",
        fiche=fiche,
        cache_hit=cache_hit,
        resultat=resultat,
    )


def _ledger_jsonl(entries: list[LedgerEntry], path: Path) -> None:
    path.write_text(
        "\n".join(e.to_jsonl() for e in entries) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Test 7 — Agrégation
# ---------------------------------------------------------------------------

class TestAgregation:
    def test_appels_et_cache_comptes(self):
        entries = [_entry(cache_hit=False), _entry(cache_hit=True)]
        usage = agreger(entries)
        assert usage.nb_appels == 1
        assert usage.nb_cache_hits == 1

    def test_cout_total(self):
        entries = [_entry(cout=0.10), _entry(cout=0.05)]
        usage = agreger(entries)
        assert abs(usage.cout_total - 0.15) < 1e-9

    def test_cache_hit_exclu_du_cout(self):
        entries = [_entry(cout=0.10, cache_hit=False), _entry(cout=0.99, cache_hit=True)]
        usage = agreger(entries)
        assert abs(usage.cout_total - 0.10) < 1e-9

    def test_budget_depasse_exclu_du_cout(self):
        entries = [_entry(cout=0.10, resultat="ok"), _entry(cout=0.50, resultat="budget_depasse")]
        usage = agreger(entries)
        assert abs(usage.cout_total - 0.10) < 1e-9

    def test_taux_cache(self):
        entries = [_entry(cache_hit=False)] * 3 + [_entry(cache_hit=True)] * 1
        usage = agreger(entries)
        assert abs(usage.taux_cache - 0.25) < 1e-9

    def test_taux_cache_zero_si_aucun_appel(self):
        assert agreger([]).taux_cache == 0.0

    def test_par_fournisseur(self):
        entries = [
            _entry(fournisseur="serp", cout=0.10),
            _entry(fournisseur="serp", cout=0.05),
            _entry(fournisseur="apollo", cout=0.20),
        ]
        usage = agreger(entries)
        assert "serp" in usage.par_fournisseur
        assert abs(usage.par_fournisseur["serp"].cout_total - 0.15) < 1e-9
        assert usage.par_fournisseur["serp"].nb_appels == 2
        assert abs(usage.par_fournisseur["apollo"].cout_total - 0.20) < 1e-9

    def test_par_fiche(self):
        entries = [
            _entry(fiche="Alpha HVAC", cout=0.10),
            _entry(fiche="Alpha HVAC", cout=0.05),
            _entry(fiche="Beta SA", cout=0.20),
        ]
        usage = agreger(entries)
        assert abs(usage.par_fiche["Alpha HVAC"] - 0.15) < 1e-9
        assert abs(usage.par_fiche["Beta SA"] - 0.20) < 1e-9

    def test_charger_ledger_from_file(self, tmp_path):
        entries_in = [_entry(cout=0.10), _entry(cout=0.05, cache_hit=True)]
        ledger = tmp_path / "api_usage.log"
        _ledger_jsonl(entries_in, ledger)
        entries_out = charger_ledger(ledger)
        assert len(entries_out) == 2

    def test_charger_ledger_fichier_absent(self, tmp_path):
        entries = charger_ledger(tmp_path / "absent.log")
        assert entries == []

    def test_ligne_malformee_ignoree_sans_exception(self, tmp_path):
        ledger = tmp_path / "api_usage.log"
        good = _entry(cout=0.10)
        ledger.write_text(
            good.to_jsonl() + "\n"
            + "LIGNE_CORROMPUE_NON_JSON\n"
            + good.to_jsonl() + "\n",
            encoding="utf-8",
        )
        erreurs: list[str] = []
        entries = charger_ledger(ledger, erreurs_out=erreurs)
        assert len(entries) == 2
        assert len(erreurs) == 1

    def test_nb_erreurs_dans_usage(self, tmp_path):
        ledger = tmp_path / "api_usage.log"
        good = _entry(cout=0.10)
        ledger.write_text(good.to_jsonl() + "\nBAD_LINE\n", encoding="utf-8")
        erreurs: list[str] = []
        entries = charger_ledger(ledger, erreurs_out=erreurs)
        usage = agreger(entries, nb_erreurs_lecture=len(erreurs))
        assert usage.nb_erreurs_lecture == 1

    def test_filtre_depuis(self, tmp_path):
        ledger = tmp_path / "api_usage.log"
        old = LedgerEntry(
            ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
            fournisseur="serp", endpoint="search",
            unites={"requetes": 1}, cout_estime=0.10, devise="USD",
        )
        new = _entry(cout=0.05)
        _ledger_jsonl([old, new], ledger)
        entries = charger_ledger(ledger, depuis=date(2025, 1, 1))
        assert len(entries) == 1

    def test_nb_entrees(self):
        entries = [_entry(), _entry(), _entry()]
        usage = agreger(entries)
        assert usage.nb_entrees == 3


# ---------------------------------------------------------------------------
# Test 8 — write_system_note + snapshot
# ---------------------------------------------------------------------------

class TestWriteSystemNote:
    def test_write_system_note_cree_fichier(self, tmp_path):
        from diagnostic.vault_io import VaultIO
        vault_path = tmp_path / "vault"
        (vault_path / "90-Systeme").mkdir(parents=True)
        vault_io = VaultIO(vault_path)
        path = vault_io.write_system_note("test-note.md", "# Test\nContenu\n")
        assert path.exists()
        assert path.read_text(encoding="utf-8") == "# Test\nContenu\n"

    def test_write_system_note_atomique(self, tmp_path):
        """Pas de .tmp résiduel après écriture."""
        from diagnostic.vault_io import VaultIO
        vault_path = tmp_path / "vault"
        (vault_path / "90-Systeme").mkdir(parents=True)
        vault_io = VaultIO(vault_path)
        vault_io.write_system_note("snap.md", "contenu")
        tmp_files = list((vault_path / "90-Systeme").glob("*.tmp"))
        assert tmp_files == []

    def test_write_system_note_journalisee(self, tmp_path):
        """L'opération apparaît dans runs.log."""
        from diagnostic.vault_io import VaultIO
        vault_path = tmp_path / "vault"
        (vault_path / "90-Systeme").mkdir(parents=True)
        vault_io = VaultIO(vault_path)
        vault_io.write_system_note("snap.md", "contenu")
        log = vault_io._log.read_text(encoding="utf-8")
        assert "write_system_note" in log
        assert "snap.md" in log

    def test_snapshot_usage_dans_vault(self, tmp_path):
        """formater_rapport() → write_system_note() → fichier dans 90-Systeme/."""
        from diagnostic.vault_io import VaultIO
        vault_path = tmp_path / "vault"
        (vault_path / "90-Systeme").mkdir(parents=True)
        vault_io = VaultIO(vault_path)

        entries = [_entry(cout=0.10), _entry(cache_hit=True)]
        usage = agreger(entries)
        rapport = formater_rapport(usage)

        today = date.today().isoformat()
        path = vault_io.write_system_note(f"usage-{today}.md", rapport)
        content = path.read_text(encoding="utf-8")
        assert "Rapport d'usage API" in content
        assert "Appels réels" in content

    def test_formater_rapport_contenu(self):
        entries = [
            _entry(fournisseur="serp", cout=0.10),
            _entry(fournisseur="apollo", cout=0.20),
            _entry(cache_hit=True),
        ]
        usage = agreger(entries)
        rapport = formater_rapport(usage)
        assert "serp" in rapport
        assert "apollo" in rapport
        assert "Cache hits" in rapport
        assert "Coût total" in rapport
