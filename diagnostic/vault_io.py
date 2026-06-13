"""
vault_io.py — contrôleur de bus du vault Obsidian (§4 de la spec J2).

Seul module autorisé à lire/écrire dans vault/. Convention appliquée par
le test §8.7 (grep AST sur os.replace).

Toutes les écritures sont :
  - atomiques : fichier .tmp dans le même répertoire + os.replace()
  - journalisées : une ligne JSONL dans runs.log (jamais par les agents)
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml
from pydantic import ValidationError

from diagnostic.vault_schema import (
    TRANSITIONS_AGENT,
    TRANSITIONS_LEGALES,
    FicheProspect,
    Statut,
)


# ---------------------------------------------------------------------------
# Utilitaires internes (non exportés)
# ---------------------------------------------------------------------------

def _slugify(nom: str) -> str:
    """Convertit un nom d'entreprise en slug de fichier.
    'Chauffage ABC inc.' → 'chauffage-abc-inc'
    """
    slug = nom.lower()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Sépare le bloc YAML frontmatter du corps Markdown.

    Retourne ({}, text) si pas de frontmatter détecté.
    """
    if not text.startswith("---"):
        return {}, text
    rest = text[3:]  # tout après le --- d'ouverture
    idx = rest.find("\n---")
    if idx == -1:
        return {}, text
    fm_str = rest[:idx].strip()
    body = rest[idx + 4:].lstrip("\n")
    return yaml.safe_load(fm_str) or {}, body


def _compose_note(fm_dict: dict, body: str) -> str:
    """Assemble dict frontmatter + corps en note Markdown."""
    fm_yaml = yaml.dump(fm_dict, allow_unicode=True, sort_keys=False, default_flow_style=False)
    if body:
        return f"---\n{fm_yaml}---\n\n{body}"
    return f"---\n{fm_yaml}---\n"


# ---------------------------------------------------------------------------
# VaultIO — contrôleur de bus
# ---------------------------------------------------------------------------

class VaultIO:
    """Bus controller : seul module autorisé à lire/écrire dans vault/.

    Paramètres
    ----------
    vault_path : chemin racine du vault Obsidian
    log_path   : chemin du journal runs.log (défaut : ../runs.log)
    cache_path : si fourni, vérifie que le cache est HORS du vault (G9)
    """

    def __init__(
        self,
        vault_path: Path,
        log_path: Path | None = None,
        cache_path: Path | None = None,
    ) -> None:
        self.vault = Path(vault_path).resolve()
        self._log = Path(log_path) if log_path else self.vault.parent / "runs.log"

        # G9 : le cache de scraping doit rester hors du vault
        if cache_path is not None:
            cache_resolved = Path(cache_path).resolve()
            try:
                cache_resolved.relative_to(self.vault)
                # Si on arrive ici, le cache EST dans le vault → erreur fatale
                raise RuntimeError(
                    f"Cache ({cache_resolved}) est situé DANS le vault ({self.vault}). "
                    "Le cache de scraping doit rester hors du vault (contrainte G9)."
                )
            except ValueError:
                pass  # cache bien hors du vault

    # --- Helpers privés ---------------------------------------------------

    def _prospect_dir(self, fiche: FicheProspect) -> Path:
        return self.vault / "10-Prospects" / f"persona{fiche.persona}-{fiche.marche}"

    def _slug_path(self, fiche: FicheProspect) -> Path:
        return self._prospect_dir(fiche) / f"{_slugify(fiche.nom)}.md"

    def _unique_path(self, fiche: FicheProspect) -> Path:
        """Chemin sans collision : ajoute -2, -3, … si le slug existe déjà."""
        base = self._slug_path(fiche)
        if not base.exists():
            return base
        stem = base.stem
        suffix = 2
        while True:
            candidate = base.parent / f"{stem}-{suffix}.md"
            if not candidate.exists():
                return candidate
            suffix += 1

    def _atomic_write(self, path: Path, content: str) -> None:
        """Écriture atomique : .tmp dans le même volume puis os.replace()."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)

    def _journal(self, agent: str, op: str, fiche: str, resultat: str, detail: str = "") -> None:
        """Ajoute une ligne JSONL dans runs.log. Appelé uniquement par le bus."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "op": op,
            "fiche": fiche,
            "resultat": resultat,
            "detail": detail,
        }
        with self._log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # --- API publique -------------------------------------------------------

    def write_fiche(self, fiche: FicheProspect) -> Path:
        """Crée ou écrase une fiche. Atomique, idempotent, journalisé.

        Si une fiche avec le même nom existe déjà, le corps Markdown humain
        est préservé. Les champs extra portés par l'objet fiche sont conservés
        (ils font partie de model_dump).
        """
        existing = self.exists(nom=fiche.nom)
        if existing:
            _, body = _parse_frontmatter(existing.read_text(encoding="utf-8"))
            path = existing
        else:
            body = ""
            path = self._unique_path(fiche)

        content = _compose_note(fiche.model_dump(mode="json"), body)
        self._atomic_write(path, content)
        self._journal("vault_io", "write_fiche", path.name, "ok")
        return path

    def read_fiche(self, fiche_path: Path) -> FicheProspect:
        """Lit et valide une fiche. Lève ValidationError si le frontmatter est invalide."""
        text = Path(fiche_path).read_text(encoding="utf-8")
        fm_dict, _ = _parse_frontmatter(text)
        return FicheProspect.model_validate(fm_dict)

    def update_frontmatter(self, fiche_path: Path, **champs) -> FicheProspect:
        """Met à jour des champs spécifiques sans toucher au corps Markdown.

        Préserve les champs extra (annotations humaines) et le corps.
        Valide avant d'écrire : jamais d'écrasement silencieux d'un état invalide.
        """
        text = Path(fiche_path).read_text(encoding="utf-8")
        fm_dict, body = _parse_frontmatter(text)
        fm_dict.update(champs)
        fiche = FicheProspect.model_validate(fm_dict)
        content = _compose_note(fiche.model_dump(mode="json"), body)
        self._atomic_write(fiche_path, content)
        return fiche

    def query(
        self,
        *,
        statut: str | None = None,
        persona: int | None = None,
        marche: str | None = None,
    ) -> list[tuple[Path, FicheProspect]]:
        """Scan du dossier 10-Prospects/ avec filtres optionnels.

        Retourne des tuples (path, fiche) — le path est nécessaire aux appelants
        pour transition() et update_frontmatter(). Filesystem scan sans index ;
        suffisant à l'échelle visée (centaines de fiches).
        """
        prospects_dir = self.vault / "10-Prospects"
        if not prospects_dir.exists():
            return []

        results: list[tuple[Path, FicheProspect]] = []
        for md_file in sorted(prospects_dir.rglob("*.md")):
            try:
                fm_dict, _ = _parse_frontmatter(md_file.read_text(encoding="utf-8"))
                fiche = FicheProspect.model_validate(fm_dict)
            except Exception:
                continue  # fiche corrompue ou non-prospect → ignorée silencieusement

            if statut is not None and fiche.statut != statut:
                continue
            if persona is not None and fiche.persona != persona:
                continue
            if marche is not None and fiche.marche != marche:
                continue
            results.append((md_file, fiche))

        return results

    def transition(
        self,
        fiche_path: Path,
        nouveau_statut: str,
        acteur: Literal["agent", "humain"] = "humain",
    ) -> FicheProspect:
        """Applique une transition d'état en respectant §5.2.

        Lève ValueError si la transition est illégale ou si l'acteur n'est
        pas autorisé pour cette transition.
        """
        fiche = self.read_fiche(fiche_path)
        ancien = Statut(fiche.statut)
        nouveau = Statut(nouveau_statut)

        cibles_legales = TRANSITIONS_LEGALES.get(ancien, set())
        if nouveau not in cibles_legales:
            raise ValueError(
                f"Transition illégale : {ancien.value} → {nouveau.value}. "
                f"Depuis '{ancien.value}', transitions possibles : "
                f"{sorted(s.value for s in cibles_legales)}"
            )

        if acteur == "agent":
            cibles_agent = TRANSITIONS_AGENT.get(ancien, set())
            if nouveau not in cibles_agent:
                raise ValueError(
                    f"Transition {ancien.value} → {nouveau.value} non autorisée "
                    f"pour acteur='agent' : réservée à l'humain."
                )

        updated = self.update_frontmatter(fiche_path, statut=nouveau.value)
        self._journal(
            "vault_io", "transition", Path(fiche_path).name, "ok",
            f"{ancien.value}→{nouveau.value} acteur={acteur}",
        )
        return updated

    def write_rapport(self, fiche: FicheProspect, contenu_md: str) -> Path:
        """Écrit un rapport de diagnostic dans 30-Diagnostics/. Atomique, journalisé."""
        path = self.vault / "30-Diagnostics" / f"{_slugify(fiche.nom)}.md"
        self._atomic_write(path, contenu_md)
        self._journal("vault_io", "write_rapport", path.name, "ok")
        return path

    def log_erreur(self, agent: str, fiche: str, detail: str) -> None:
        """Journalise une erreur de traitement depuis l'orchestrateur.

        Permet à vault_runner de tracer les échecs pipeline dans runs.log
        sans accéder directement à _journal.
        """
        self._journal(agent, "erreur_pipeline", fiche, "erreur", detail)

    def write_system_note(self, filename: str, content: str) -> Path:
        """Écrit une note système dans vault/90-Systeme/. Atomique, journalisée."""
        path = self.vault / "90-Systeme" / filename
        self._atomic_write(path, content)
        self._journal("vault_io", "write_system_note", filename, "ok")
        return path

    def exists(
        self,
        *,
        nom: str | None = None,
        site_web: str | None = None,
    ) -> Path | None:
        """Retourne le chemin d'une fiche existante (par nom ou site_web), ou None.

        Sert à la déduplication (préparation J3) et à la localisation pour
        les mises à jour sans stocker le chemin côté appelant.
        """
        prospects_dir = self.vault / "10-Prospects"
        if not prospects_dir.exists():
            return None

        for md_file in prospects_dir.rglob("*.md"):
            try:
                fm_dict, _ = _parse_frontmatter(md_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            if nom is not None and fm_dict.get("nom") == nom:
                return md_file
            if site_web is not None and fm_dict.get("site_web") == site_web:
                return md_file

        return None
