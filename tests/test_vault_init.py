"""
test_vault_init.py — critères d'acceptation Phase C.

Propriétés testées :
  1. Scaffold : tous les dossiers et fichiers attendus sont créés
  2. Idempotence : relancer init_vault ne modifie jamais un fichier existant
  3. Dashboard : contient exactement 3 blocs ```dataview avec les bons filtres
  4. Template : frontmatter minimal présent et parseable
  5. memory-map : mentionne tous les champs de FicheProspect
  6. Rubrique : copie dans 20-Rubrics/ si disponible dans knowledge/
  7. Git : dépôt initialisé dans vault/ (skip si git absent)
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from diagnostic.vault_init import init_vault, VAULT_DIRS
from diagnostic.vault_schema import FicheProspect


# ---------------------------------------------------------------------------
# 1. Scaffold complet
# ---------------------------------------------------------------------------

class TestScaffold:
    def test_tous_les_dossiers_crees(self, tmp_path):
        init_vault(tmp_path / "vault")
        vault = tmp_path / "vault"
        for rel in VAULT_DIRS:
            assert (vault / rel).is_dir(), f"Dossier absent : {rel}"

    def test_dashboard_cree(self, tmp_path):
        init_vault(tmp_path / "vault")
        assert (tmp_path / "vault" / "00-Dashboard.md").exists()

    def test_template_cree(self, tmp_path):
        init_vault(tmp_path / "vault")
        assert (tmp_path / "vault" / "_templates" / "fiche-prospect.md").exists()

    def test_memory_map_cree(self, tmp_path):
        init_vault(tmp_path / "vault")
        assert (tmp_path / "vault" / "90-Systeme" / "memory-map.md").exists()

    def test_journal_decisions_cree(self, tmp_path):
        init_vault(tmp_path / "vault")
        assert (tmp_path / "vault" / "90-Systeme" / "journal-decisions.md").exists()

    def test_gitignore_cree(self, tmp_path):
        init_vault(tmp_path / "vault")
        gi = tmp_path / "vault" / ".gitignore"
        assert gi.exists()
        content = gi.read_text(encoding="utf-8")
        assert ".obsidian/workspace" in content
        assert ".trash/" in content

    def test_resultat_contient_listes_created_skipped(self, tmp_path):
        result = init_vault(tmp_path / "vault")
        assert "created" in result
        assert "skipped" in result
        assert len(result["created"]) > 0


# ---------------------------------------------------------------------------
# 2. Idempotence
# ---------------------------------------------------------------------------

class TestIdempotence:
    def test_deuxieme_run_ne_cree_rien(self, tmp_path):
        init_vault(tmp_path / "vault")
        result2 = init_vault(tmp_path / "vault")
        # Tout doit être dans "skipped", rien dans "created"
        # (sauf éventuellement .git/ si git est absent — on tolère)
        created_non_git = [c for c in result2["created"] if not c.startswith(".git")]
        assert created_non_git == [], f"Fichiers recréés au 2e run : {created_non_git}"

    def test_deuxieme_run_ne_modifie_pas_contenu(self, tmp_path):
        init_vault(tmp_path / "vault")
        dashboard = tmp_path / "vault" / "00-Dashboard.md"
        content_avant = dashboard.read_bytes()

        # Modifie manuellement — simule annotation humaine
        dashboard.write_text("# Modifié par l'humain\n", encoding="utf-8")

        init_vault(tmp_path / "vault")
        assert dashboard.read_text(encoding="utf-8") == "# Modifié par l'humain\n"

    def test_idempotence_dirs_existants(self, tmp_path):
        """mkdir avec exist_ok=True ne lève jamais, même si le dossier est plein."""
        vault = tmp_path / "vault"
        init_vault(vault)
        # Ajouter une fiche dans 10-Prospects/
        fiche = vault / "10-Prospects" / "persona1-quebec" / "test.md"
        fiche.write_text("# test\n", encoding="utf-8")
        init_vault(vault)  # ne doit pas planter
        assert fiche.read_text(encoding="utf-8") == "# test\n"


# ---------------------------------------------------------------------------
# 3. Dashboard — 3 requêtes Dataview avec les bons filtres
# ---------------------------------------------------------------------------

class TestDashboard:
    def _content(self, tmp_path) -> str:
        init_vault(tmp_path / "vault")
        return (tmp_path / "vault" / "00-Dashboard.md").read_text(encoding="utf-8")

    def test_contient_trois_blocs_dataview(self, tmp_path):
        content = self._content(tmp_path)
        assert content.count("```dataview") == 3

    def test_filtre_diagnostique(self, tmp_path):
        content = self._content(tmp_path)
        assert 'statut = "diagnostique"' in content

    def test_filtre_valide_score_50(self, tmp_path):
        content = self._content(tmp_path)
        assert 'statut = "valide"' in content
        assert "score_global < 50" in content

    def test_pipeline_groupe_par_persona_marche(self, tmp_path):
        content = self._content(tmp_path)
        # La requête pipeline doit grouper
        assert "GROUP BY" in content

    def test_tri_score_croissant(self, tmp_path):
        content = self._content(tmp_path)
        assert "SORT score_global ASC" in content


# ---------------------------------------------------------------------------
# 4. Template fiche — frontmatter parseable
# ---------------------------------------------------------------------------

class TestTemplateFiche:
    def test_template_a_frontmatter_yaml(self, tmp_path):
        init_vault(tmp_path / "vault")
        content = (tmp_path / "vault" / "_templates" / "fiche-prospect.md").read_text(encoding="utf-8")
        assert content.startswith("---")
        # Extraire et parser le frontmatter
        end = content.index("\n---", 3)
        fm = yaml.safe_load(content[3:end])
        assert fm["type"] == "prospect"
        assert fm["statut"] == "decouvert"
        assert "nom" in fm
        assert "persona" in fm
        assert "marche" in fm

    def test_template_contient_date_creation(self, tmp_path):
        init_vault(tmp_path / "vault")
        content = (tmp_path / "vault" / "_templates" / "fiche-prospect.md").read_text(encoding="utf-8")
        assert "date_creation" in content


# ---------------------------------------------------------------------------
# 5. memory-map — mentionne tous les champs du schéma
# ---------------------------------------------------------------------------

class TestMemoryMap:
    def test_mentionne_tous_les_champs_fiche(self, tmp_path):
        init_vault(tmp_path / "vault")
        content = (tmp_path / "vault" / "90-Systeme" / "memory-map.md").read_text(encoding="utf-8")
        for field_name in FicheProspect.model_fields:
            assert field_name in content, f"Champ `{field_name}` absent du memory-map"

    def test_mentionne_tous_les_statuts(self, tmp_path):
        from diagnostic.vault_schema import Statut
        init_vault(tmp_path / "vault")
        content = (tmp_path / "vault" / "90-Systeme" / "memory-map.md").read_text(encoding="utf-8")
        for s in Statut:
            assert s.value in content, f"Statut `{s.value}` absent du memory-map"

    def test_mentionne_tous_les_marches(self, tmp_path):
        from diagnostic.vault_schema import Marche
        init_vault(tmp_path / "vault")
        content = (tmp_path / "vault" / "90-Systeme" / "memory-map.md").read_text(encoding="utf-8")
        for m in Marche:
            assert m.value in content, f"Marché `{m.value}` absent du memory-map"

    def test_mentionne_plan_dossiers(self, tmp_path):
        init_vault(tmp_path / "vault")
        content = (tmp_path / "vault" / "90-Systeme" / "memory-map.md").read_text(encoding="utf-8")
        assert "10-Prospects" in content
        assert "20-Rubrics" in content
        assert "30-Diagnostics" in content


# ---------------------------------------------------------------------------
# 6. Rubrique copiée dans 20-Rubrics/
# ---------------------------------------------------------------------------

class TestRubricCopie:
    def test_rubric_persona1_copiee(self, tmp_path):
        init_vault(tmp_path / "vault")
        dst = tmp_path / "vault" / "20-Rubrics" / "rubric_persona1.yaml"
        # Si la source existe dans knowledge/, la copie doit exister
        from diagnostic.vault_init import KNOWLEDGE_DIR
        src = KNOWLEDGE_DIR / "rubric_persona1.yaml"
        if src.exists():
            assert dst.exists(), "rubric_persona1.yaml non copié dans 20-Rubrics/"
            # Contenu identique
            assert dst.read_bytes() == src.read_bytes()
        else:
            pytest.skip("knowledge/rubric_persona1.yaml absent — test ignoré")

    def test_rubric_non_modifiee_au_second_run(self, tmp_path):
        from diagnostic.vault_init import KNOWLEDGE_DIR
        src = KNOWLEDGE_DIR / "rubric_persona1.yaml"
        if not src.exists():
            pytest.skip("knowledge/rubric_persona1.yaml absent")

        init_vault(tmp_path / "vault")
        dst = tmp_path / "vault" / "20-Rubrics" / "rubric_persona1.yaml"
        # Modifie la copie manuellement
        dst.write_text("# Modifié\n", encoding="utf-8")
        init_vault(tmp_path / "vault")  # second run
        # La modification doit être préservée (idempotence)
        assert dst.read_text(encoding="utf-8") == "# Modifié\n"


# ---------------------------------------------------------------------------
# 7. Git init
# ---------------------------------------------------------------------------

def _git_available() -> bool:
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


@pytest.mark.skipif(not _git_available(), reason="git non disponible")
class TestGitInit:
    def test_git_init_cree_depot(self, tmp_path):
        init_vault(tmp_path / "vault")
        assert (tmp_path / "vault" / ".git").is_dir()

    def test_git_init_idempotent(self, tmp_path):
        init_vault(tmp_path / "vault")
        init_vault(tmp_path / "vault")  # ne doit pas planter
        assert (tmp_path / "vault" / ".git").is_dir()
