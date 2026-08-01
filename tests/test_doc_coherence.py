"""
test_doc_coherence.py — le chiffre documenté doit être le chiffre réel.

Pourquoi ce fichier existe
--------------------------
La revue de l'itération 2 a recalé deux fois le chantier documentation pour la
même famille de défaut : un compte de tests relevé en début de tâche, périmé à
la fin parce qu'un chantier frère avait atterri entre-temps. La contre-mesure
avait d'abord été *comportementale* (une consigne « re-vérifie tes chiffres »
dans le prompt de l'agent de documentation). Elle a échoué sur son propre
terrain : sa checklist contenait la commande qui rend le bon chiffre, et un
README affichait toujours l'ancien — dans le commit qui instituait la règle.

Le projet convertit sinon toute discipline en contrôle exécutable : garde-fou
AST des imports réseau, 9 contrôles de préflight, rubrique = donnée. La
cohérence documentaire était le seul invariant tenu par la bonne volonté. Elle
ne l'est plus : ce module compare ce que la documentation AFFIRME à ce que le
dépôt CONTIENT, et échoue sur l'écart.

Portée volontairement large : on scanne tout le Markdown du dépôt, pas
seulement les fichiers qu'un agent vient d'éditer — un chiffre périmé vit
précisément là où personne ne l'édite, c'est la définition du problème.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent

# docs/strategie/ est exclu : ce sont des analyses horodatées (livrables du chef
# de projet, journal de gouvernance). Elles CITENT l'état d'une itération passée
# — c'est leur fonction. Les figer serait réécrire l'histoire.
EXCLUS = ("docs/strategie/", "node_modules/", ".venv/", "dist/", "vault/")

# Les spécifications SPEC-J*.md décrivent l'état visé au moment de leur
# rédaction ; elles ne sont pas maintenues comme documentation vivante.
EXCLUS_FICHIERS = ("SPEC-J2", "SPEC-J3", "SPEC-J4", "SPEC-J5")


def _fichiers_markdown() -> list[Path]:
    out = []
    for p in RACINE.rglob("*.md"):
        rel = p.relative_to(RACINE).as_posix()
        if any(rel.startswith(e) or f"/{e}" in f"/{rel}" for e in EXCLUS):
            continue
        if any(p.name.startswith(f) for f in EXCLUS_FICHIERS):
            continue
        out.append(p)
    return sorted(out)


def _collecter(cible: str) -> dict[str, int]:
    """Compte les tests réellement collectés, par chemin.

    Une seule invocation de pytest par racine (la collecte est rapide,
    l'exécution n'a pas lieu). On agrège par fichier ET par préfixe de
    répertoire, pour pouvoir vérifier aussi bien « pytest tests/ » que
    « pytest tests/integration » ou un fichier précis.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", cible, "--collect-only", "-q",
         "-p", "no:cacheprovider"],
        cwd=RACINE, capture_output=True, text=True, timeout=300,
    )
    compte: dict[str, int] = {}
    for ligne in proc.stdout.splitlines():
        ligne = ligne.strip()
        if "::" not in ligne:
            continue
        chemin = ligne.split("::", 1)[0]
        if not chemin.endswith(".py"):
            continue
        # le fichier lui-même, puis chacun de ses répertoires parents
        compte[chemin] = compte.get(chemin, 0) + 1
        parts = Path(chemin).parts
        for i in range(1, len(parts)):
            prefixe = "/".join(parts[:i])
            compte[prefixe] = compte.get(prefixe, 0) + 1
            compte[prefixe + "/"] = compte[prefixe]
    return compte


@pytest.fixture(scope="module")
def comptes_reels() -> dict[str, int]:
    reels = _collecter("tests")
    reels.update(_collecter("webapp/backend/tests"))
    return reels


def _normaliser(cible: str) -> list[str]:
    """Variantes d'écriture d'un même chemin (avec/sans slash final)."""
    c = cible.strip().rstrip("/")
    return [c, c + "/"]


# Une ligne qui invoque pytest sur une cible ET annonce un nombre de tests
# est une affirmation vérifiable. C'est exactement le motif qui a produit les
# quatre chiffres périmés relevés par la revue.
_RE_PYTEST = re.compile(r"pytest\s+(?!-)([\w./\-]+)")
_RE_NB_TESTS = re.compile(r"(\d+)\s+tests?\b")


def test_commandes_pytest_documentees_annoncent_le_bon_compte(comptes_reels):
    """« pytest <cible> … # N tests » : N doit être le compte réel de <cible>."""
    ecarts: list[str] = []
    for md in _fichiers_markdown():
        for num, ligne in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            m_cible = _RE_PYTEST.search(ligne)
            m_nb = _RE_NB_TESTS.search(ligne)
            if not (m_cible and m_nb):
                continue
            cible = m_cible.group(1)
            if not (RACINE / cible.rstrip("/")).exists():
                continue  # cible inexistante : hors périmètre de ce contrôle
            reel = next((comptes_reels[v] for v in _normaliser(cible)
                         if v in comptes_reels), None)
            if reel is None:
                continue  # non collectable (ex. cible hors des deux racines)
            annonce = int(m_nb.group(1))
            if annonce != reel:
                rel = md.relative_to(RACINE).as_posix()
                ecarts.append(
                    f"{rel}:{num} annonce {annonce} tests pour « {cible} », "
                    f"réel = {reel}"
                )
    assert not ecarts, (
        "Chiffres de tests périmés dans la documentation :\n  - "
        + "\n  - ".join(ecarts)
        + "\n\nRe-mesure puis corrige. Ce contrôle remplace la consigne "
          "« re-vérifie tes chiffres » par un garde-fou exécutable."
    )


# Le tableau « État des tests » de CLAUDE.md est la référence la plus consultée
# du projet (mémoire de session). Chaque ligne est une affirmation vérifiable.
_RE_LIGNE_TABLEAU = re.compile(
    r"^\|\s*`(?:tests/)?(test_\w+\.py)`\s*\|.*?\|\s*\**(\d+)\**\s*\|\s*$"
)


def test_tableau_des_tests_de_claude_md_est_exact(comptes_reels):
    """Chaque ligne du tableau « État des tests » doit refléter le réel."""
    claude = RACINE / "CLAUDE.md"
    if not claude.exists():
        pytest.skip("CLAUDE.md absent")

    ecarts: list[str] = []
    verifiees = 0
    for num, ligne in enumerate(claude.read_text(encoding="utf-8").splitlines(), 1):
        m = _RE_LIGNE_TABLEAU.match(ligne)
        if not m:
            continue
        fichier, annonce = m.group(1), int(m.group(2))
        chemin = f"tests/{fichier}"
        if chemin not in comptes_reels:
            continue
        verifiees += 1
        if annonce != comptes_reels[chemin]:
            ecarts.append(
                f"CLAUDE.md:{num} — {fichier} annoncé {annonce}, "
                f"réel {comptes_reels[chemin]}"
            )

    assert verifiees >= 15, (
        f"Seules {verifiees} lignes du tableau ont pu être vérifiées : le format "
        "du tableau a probablement changé et ce contrôle ne protège plus rien."
    )
    assert not ecarts, "Tableau « État des tests » périmé :\n  - " + "\n  - ".join(ecarts)


def test_nombre_de_routes_api_documente(comptes_reels):
    """« N routes » dans la doc doit correspondre aux routes /api réelles."""
    pytest.importorskip("fastapi", reason="cockpit non installé")
    sys.path.insert(0, str(RACINE))
    from webapp.backend.app import app  # noqa: PLC0415

    reel = len([r for r in app.routes
                if getattr(r, "path", "").startswith("/api")])

    motif = re.compile(r"(\d+)\s+routes?\b")
    ecarts = []
    for md in _fichiers_markdown():
        for num, ligne in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if "route" not in ligne.lower() or "/api" not in ligne and "GET" not in ligne:
                continue
            m = motif.search(ligne)
            if m and int(m.group(1)) != reel:
                rel = md.relative_to(RACINE).as_posix()
                ecarts.append(f"{rel}:{num} annonce {m.group(1)} routes, réel = {reel}")
    assert not ecarts, "Nombre de routes /api périmé :\n  - " + "\n  - ".join(ecarts)


def test_nombre_d_ecrans_documente():
    """« N écrans » dans la doc doit correspondre aux routes React réelles."""
    app_tsx = RACINE / "webapp/frontend/src/App.tsx"
    if not app_tsx.exists():
        pytest.skip("front-end absent")

    reel = len(re.findall(r'<Route\s+path="/', app_tsx.read_text(encoding="utf-8")))
    motif = re.compile(r"(\d+)\s+écrans?\b")
    ecarts = []
    for md in _fichiers_markdown():
        for num, ligne in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            m = motif.search(ligne)
            if m and int(m.group(1)) != reel:
                rel = md.relative_to(RACINE).as_posix()
                ecarts.append(f"{rel}:{num} annonce {m.group(1)} écrans, réel = {reel}")
    assert not ecarts, "Nombre d'écrans périmé :\n  - " + "\n  - ".join(ecarts)


def test_nombre_d_invariants_documente():
    """« N invariants » doit correspondre aux sections « ## I<n> » réelles."""
    inv = RACINE / "docs/architecture/invariants.md"
    if not inv.exists():
        pytest.skip("invariants.md absent")

    texte = inv.read_text(encoding="utf-8")
    reel = len(re.findall(r"^##\s+I\d+\s+—", texte, flags=re.MULTILINE))
    motif = re.compile(r"(\d+)\s+invariants?\b")
    ecarts = []
    for md in _fichiers_markdown():
        for num, ligne in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            m = motif.search(ligne)
            if m and int(m.group(1)) != reel:
                rel = md.relative_to(RACINE).as_posix()
                ecarts.append(f"{rel}:{num} annonce {m.group(1)} invariants, réel = {reel}")
    assert not ecarts, "Nombre d'invariants périmé :\n  - " + "\n  - ".join(ecarts)


def test_nombre_d_agents_documente():
    """« N agents » doit correspondre aux définitions .claude/agents/*.md."""
    dossier = RACINE / ".claude/agents"
    if not dossier.exists():
        pytest.skip("écosystème d'agents absent")

    reel = len(list(dossier.glob("*.md")))
    motif = re.compile(r"(\d+)\s+(?:sous-)?agents?\b")
    ecarts = []
    for md in _fichiers_markdown():
        for num, ligne in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if "agent" not in ligne.lower():
                continue
            m = motif.search(ligne)
            if m and int(m.group(1)) != reel:
                rel = md.relative_to(RACINE).as_posix()
                ecarts.append(f"{rel}:{num} annonce {m.group(1)} agents, réel = {reel}")
    assert not ecarts, "Nombre d'agents périmé :\n  - " + "\n  - ".join(ecarts)
