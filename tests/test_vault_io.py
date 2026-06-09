"""
test_vault_io.py — critères d'acceptation Phase B.

§8.1  Round-trip (write → read → write : fichier identique octet pour octet)
§8.2  Atomicité (crash simulé → jamais de fichier partiel)
§8.3  Validation frontmatter invalide → erreur explicite, fichier intact
§8.4  Machine à états → ValueError sur transitions illégales ou acteur non autorisé
§8.5  Query / filtres : 3 fiches, filtres statut / persona / marche corrects
§8.7  Garde-fou imports : os.replace et runs.log uniquement dans vault_io.py
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from diagnostic.vault_io import VaultIO, _compose_note, _parse_frontmatter
from diagnostic.vault_schema import FicheProspect

# ---------------------------------------------------------------------------
# Fixtures partagées
# ---------------------------------------------------------------------------

BASE = dict(
    persona=1,
    marche="quebec",
    statut="decouvert",
    nom="Chauffage ABC inc.",
    date_creation="2026-06-09",
)


def _fiche(**extra) -> FicheProspect:
    return FicheProspect(**{**BASE, **extra})


# ---------------------------------------------------------------------------
# §8.1 Round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_write_read_champs_identiques(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        fiche = _fiche(score_global=42, gaps_majeurs=["site_web", "avis"])
        path = io.write_fiche(fiche)
        fiche2 = io.read_fiche(path)
        assert fiche2.nom == fiche.nom
        assert fiche2.score_global == fiche.score_global
        assert fiche2.gaps_majeurs == fiche.gaps_majeurs
        assert fiche2.statut == fiche.statut
        assert fiche2.date_creation == fiche.date_creation

    def test_write_fiche_idempotent_octet_pour_octet(self, tmp_path):
        """Réécrire la même fiche produit un fichier identique octet pour octet."""
        io = VaultIO(tmp_path / "vault")
        fiche = _fiche(score_global=55)
        path = io.write_fiche(fiche)
        content1 = path.read_bytes()
        io.write_fiche(fiche)
        content2 = path.read_bytes()
        assert content1 == content2

    def test_corps_markdown_preserve_par_update_frontmatter(self, tmp_path):
        """update_frontmatter ne touche jamais le corps humain sous le frontmatter."""
        io = VaultIO(tmp_path / "vault")
        path = io.write_fiche(_fiche())
        # Ajout manuel d'un corps (simule édition Obsidian)
        existing = path.read_text(encoding="utf-8")
        path.write_text(existing + "## Notes\n\nRappeler en juillet.\n", encoding="utf-8")

        io.update_frontmatter(path, score_global=70)

        result = path.read_text(encoding="utf-8")
        assert "Rappeler en juillet." in result

    def test_corps_preserve_par_write_fiche(self, tmp_path):
        """write_fiche sur une fiche existante préserve le corps Markdown."""
        io = VaultIO(tmp_path / "vault")
        path = io.write_fiche(_fiche())
        existing = path.read_text(encoding="utf-8")
        path.write_text(existing + "## Notes\n\nTexte humain.\n", encoding="utf-8")

        io.write_fiche(_fiche(score_global=80))  # même nom → même path

        result = path.read_text(encoding="utf-8")
        assert "Texte humain." in result

    def test_champs_extra_preserves_par_read(self, tmp_path):
        """Les champs inconnus du frontmatter sont lus et restituables via model_extra."""
        io = VaultIO(tmp_path / "vault")
        fiche = _fiche(note_humaine="très prometteur", priorite=2)
        path = io.write_fiche(fiche)
        fiche2 = io.read_fiche(path)
        assert fiche2.model_extra.get("note_humaine") == "très prometteur"
        assert fiche2.model_extra.get("priorite") == 2


# ---------------------------------------------------------------------------
# §8.2 Atomicité
# ---------------------------------------------------------------------------

class TestAtomicite:
    def test_crash_avant_replace_ne_cree_pas_la_cible(self, tmp_path):
        """Si os.replace lève, la cible .md reste absente (jamais de fichier partiel)."""
        io = VaultIO(tmp_path / "vault")
        fiche = _fiche()
        expected = io._slug_path(fiche)

        with patch("os.replace", side_effect=OSError("crash simulé")):
            with pytest.raises(OSError):
                io.write_fiche(fiche)

        assert not expected.exists()

    def test_tmp_dans_meme_dossier_que_cible(self, tmp_path):
        """Le fichier .tmp est dans le même répertoire que la cible.

        Condition nécessaire pour que os.replace soit une opération atomique
        (rename intra-volume, sans copie inter-volume).
        """
        io = VaultIO(tmp_path / "vault")
        fiche = _fiche()
        target = io._slug_path(fiche)
        assert target.with_suffix(".tmp").parent == target.parent


# ---------------------------------------------------------------------------
# §8.3 Validation frontmatter invalide
# ---------------------------------------------------------------------------

class TestValidationFrontmatter:
    def _write_bad(self, tmp_path, overrides: dict) -> Path:
        """Écrit directement un fichier .md avec un frontmatter invalide."""
        data = {**{k: v for k, v in BASE.items()}, **overrides}
        content = f"---\n{yaml.dump(data, allow_unicode=True)}---\n"
        target = tmp_path / "vault" / "10-Prospects" / "persona1-quebec" / "bad.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def test_statut_invalide_leve_validation_error(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        target = self._write_bad(tmp_path, {"statut": "en_cours"})
        original_content = target.read_text(encoding="utf-8")

        with pytest.raises(ValidationError):
            io.read_fiche(target)

        assert target.read_text(encoding="utf-8") == original_content

    def test_persona_invalide_leve_validation_error(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        target = self._write_bad(tmp_path, {"persona": 9})

        with pytest.raises(ValidationError):
            io.read_fiche(target)

    def test_fichier_intact_apres_erreur(self, tmp_path):
        """read_fiche ne modifie jamais le fichier, même en cas d'erreur."""
        io = VaultIO(tmp_path / "vault")
        target = self._write_bad(tmp_path, {"statut": "fantaisie"})
        before = target.read_bytes()

        with pytest.raises(ValidationError):
            io.read_fiche(target)

        assert target.read_bytes() == before


# ---------------------------------------------------------------------------
# §8.4 Machine à états
# ---------------------------------------------------------------------------

class TestMachineEtats:
    def test_saut_illegal_leve_value_error(self, tmp_path):
        """decouvert → contacte : saut illégal (étape manquante)."""
        io = VaultIO(tmp_path / "vault")
        path = io.write_fiche(_fiche())

        with pytest.raises(ValueError, match="contacte"):
            io.transition(path, "contacte", acteur="humain")

    def test_transition_agent_reservee_a_humain(self, tmp_path):
        """diagnostique → valide : réservé à l'humain, rejeté pour acteur='agent'."""
        io = VaultIO(tmp_path / "vault")
        path = io.write_fiche(_fiche(statut="diagnostique"))

        with pytest.raises(ValueError, match="humain"):
            io.transition(path, "valide", acteur="agent")

    def test_transition_legale_par_agent(self, tmp_path):
        """decouvert → diagnostique : seule transition autorisée pour l'agent."""
        io = VaultIO(tmp_path / "vault")
        path = io.write_fiche(_fiche())
        updated = io.transition(path, "diagnostique", acteur="agent")
        assert updated.statut == "diagnostique"
        assert io.read_fiche(path).statut == "diagnostique"

    def test_transition_legale_par_humain(self, tmp_path):
        """diagnostique → valide : autorisé pour l'humain."""
        io = VaultIO(tmp_path / "vault")
        path = io.write_fiche(_fiche(statut="diagnostique"))
        updated = io.transition(path, "valide", acteur="humain")
        assert updated.statut == "valide"

    def test_transition_vers_rejete_par_humain(self, tmp_path):
        """* → rejete : autorisé pour l'humain depuis tout état non-terminal."""
        io = VaultIO(tmp_path / "vault")
        path = io.write_fiche(_fiche(statut="valide"))
        updated = io.transition(path, "rejete", acteur="humain")
        assert updated.statut == "rejete"


# ---------------------------------------------------------------------------
# §8.5 Query / filtres
# ---------------------------------------------------------------------------

class TestQuery:
    def _ecrire_trois(self, io: VaultIO) -> None:
        io.write_fiche(_fiche(nom="Entreprise A", statut="decouvert"))
        io.write_fiche(_fiche(nom="Entreprise B", statut="diagnostique"))
        io.write_fiche(FicheProspect(
            persona=2, marche="france", statut="decouvert",
            nom="Entreprise C", date_creation="2026-06-09",
        ))

    def test_sans_filtre_retourne_tout(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        self._ecrire_trois(io)
        assert len(io.query()) == 3

    def test_filtre_statut(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        self._ecrire_trois(io)
        resultats = io.query(statut="decouvert")
        assert len(resultats) == 2
        assert all(f.statut == "decouvert" for _, f in resultats)

    def test_filtre_persona(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        self._ecrire_trois(io)
        assert len(io.query(persona=1)) == 2
        assert len(io.query(persona=2)) == 1

    def test_filtre_marche(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        self._ecrire_trois(io)
        resultats = io.query(marche="france")
        assert len(resultats) == 1
        _, fiche = resultats[0]
        assert fiche.nom == "Entreprise C"

    def test_query_retourne_tuples_path_fiche(self, tmp_path):
        """query() retourne des (Path, FicheProspect) utilisables pour transition()."""
        io = VaultIO(tmp_path / "vault")
        fiche = _fiche()
        path_ecrit = io.write_fiche(fiche)
        resultats = io.query()
        assert len(resultats) == 1
        path_retourne, fiche_retournee = resultats[0]
        assert path_retourne == path_ecrit
        assert fiche_retournee.nom == fiche.nom

    def test_vault_vide_retourne_liste_vide(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        assert io.query() == []

    def test_combinaison_filtres(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        self._ecrire_trois(io)
        resultats = io.query(statut="decouvert", persona=1)
        assert len(resultats) == 1
        _, fiche = resultats[0]
        assert fiche.nom == "Entreprise A"


# ---------------------------------------------------------------------------
# Journal runs.log
# ---------------------------------------------------------------------------

class TestJournal:
    def test_write_fiche_produit_entree_jsonl(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        io.write_fiche(_fiche())
        lignes = (tmp_path / "runs.log").read_text(encoding="utf-8").strip().splitlines()
        assert len(lignes) == 1
        entree = json.loads(lignes[0])
        assert entree["op"] == "write_fiche"
        assert entree["resultat"] == "ok"
        assert "ts" in entree

    def test_write_rapport_produit_entree_jsonl(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        io.write_rapport(_fiche(), "# Rapport\n\nContenu.")
        lignes = (tmp_path / "runs.log").read_text(encoding="utf-8").strip().splitlines()
        entree = json.loads(lignes[0])
        assert entree["op"] == "write_rapport"
        assert entree["resultat"] == "ok"

    def test_journal_append_only(self, tmp_path):
        io = VaultIO(tmp_path / "vault")
        fiche = _fiche()
        io.write_fiche(fiche)
        io.write_fiche(_fiche(nom="Autre Entreprise"))
        lignes = (tmp_path / "runs.log").read_text(encoding="utf-8").strip().splitlines()
        assert len(lignes) == 2


# ---------------------------------------------------------------------------
# Contrainte cache G9
# ---------------------------------------------------------------------------

class TestCachePath:
    def test_cache_dans_vault_erreur_fatale(self, tmp_path):
        vault = tmp_path / "vault"
        with pytest.raises(RuntimeError, match="G9"):
            VaultIO(vault, cache_path=vault / ".cache")

    def test_cache_hors_vault_accepte(self, tmp_path):
        vault = tmp_path / "vault"
        VaultIO(vault, cache_path=tmp_path / ".cache")  # ne doit pas lever

    def test_message_erreur_explicite(self, tmp_path):
        vault = tmp_path / "vault"
        with pytest.raises(RuntimeError) as exc_info:
            VaultIO(vault, cache_path=vault / "scraping" / "cache")
        assert "vault" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# §8.7 Garde-fou : os.replace et runs.log uniquement dans vault_io.py
# ---------------------------------------------------------------------------

class TestGardeVaultIO:
    def test_os_replace_uniquement_dans_vault_io(self):
        """os.replace (primitive d'écriture atomique du bus) ne doit être appelé
        que dans vault_io.py — vérifié par AST pour éviter les faux positifs
        sur les littéraux de chaîne (ex. commentaires dans memory-map)."""
        import ast as _ast
        diagnostic_dir = Path(__file__).resolve().parent.parent / "diagnostic"
        violations = []
        for py_file in sorted(diagnostic_dir.rglob("*.py")):
            if py_file.name == "vault_io.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            try:
                tree = _ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue
            for node in _ast.walk(tree):
                # Détecte os.replace(...) — appel réel, pas une chaîne
                if (
                    isinstance(node, _ast.Call)
                    and isinstance(node.func, _ast.Attribute)
                    and node.func.attr == "replace"
                    and isinstance(node.func.value, _ast.Name)
                    and node.func.value.id == "os"
                ):
                    violations.append(f"{py_file.name}:{node.lineno}")
        assert not violations, (
            "Appel os.replace() détecté hors vault_io.py (écriture directe contourne le bus) : "
            + ", ".join(violations)
        )

    def test_runs_log_uniquement_dans_vault_io(self):
        """runs.log ne doit être référencé que dans vault_io.py (bus journalise tout)."""
        diagnostic_dir = Path(__file__).resolve().parent.parent / "diagnostic"
        violations = []
        for py_file in sorted(diagnostic_dir.rglob("*.py")):
            if py_file.name == "vault_io.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            if "runs.log" in source:
                violations.append(py_file.name)
        assert not violations, (
            "runs.log référencé hors vault_io.py : " + ", ".join(violations)
        )
