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


# docs/CHANGELOG.md cite légitimement des totaux passés (« le cockpit est passé
# de 8 routes à 10 », « l'itération 1 comptait 5 écrans »). Même raison que
# docs/strategie/ : un journal d'avancement doit pouvoir énoncer un chiffre
# révolu. Il reste soumis au contrôle des commandes `pytest`, lui : un changelog
# cite des totaux d'hier, il ne propose pas des commandes à exécuter aujourd'hui.
EXCLUS_TOTAUX = ("docs/CHANGELOG.md",)


def _fichiers_markdown(*, pour_totaux: bool = False) -> list[Path]:
    out = []
    for p in RACINE.rglob("*.md"):
        rel = p.relative_to(RACINE).as_posix()
        if any(rel.startswith(e) or f"/{e}" in f"/{rel}" for e in EXCLUS):
            continue
        if any(p.name.startswith(f) for f in EXCLUS_FICHIERS):
            continue
        if pour_totaux and rel in EXCLUS_TOTAUX:
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
# Toute ligne qui SE PRÉSENTE comme une ligne de tableau de tests est candidate.
# Le contrôle exige ensuite qu'elles soient TOUTES exploitables : c'est ce qui
# interdit l'approximation (`~20`), qu'un plancher chiffré laisserait passer.
_RE_CANDIDATE_TABLEAU = re.compile(r"^\|\s*`(?:tests/)?test_\w+\.py`\s*\|")


def test_tableau_des_tests_de_claude_md_est_exact(comptes_reels):
    """Chaque ligne du tableau « État des tests » doit refléter le réel.

    Seuil auto-calibrant : on n'exige pas « au moins N lignes vérifiées » (un
    plancher arbitraire laisse une marge, et cette marge est exactement le
    nombre d'approximations qu'on peut réintroduire sans que rien ne proteste).
    On exige que TOUTE ligne ressemblant à une ligne de tableau soit exploitable.
    Le mode de défaillance réel est l'érosion — une ligne devient approximative,
    puis deux — pas l'effondrement du format.
    """
    claude = RACINE / "CLAUDE.md"
    if not claude.exists():
        pytest.skip("CLAUDE.md absent")

    lignes = claude.read_text(encoding="utf-8").splitlines()
    candidates = [(n, l) for n, l in enumerate(lignes, 1)
                  if _RE_CANDIDATE_TABLEAU.match(l)]

    ecarts: list[str] = []
    non_exploitables: list[str] = []
    for num, ligne in candidates:
        m = _RE_LIGNE_TABLEAU.match(ligne)
        if not m:
            non_exploitables.append(
                f"CLAUDE.md:{num} — compte non exploitable (approximation « ~ », "
                f"cellule vide ou format modifié) : {ligne.strip()[:90]}"
            )
            continue
        fichier, annonce = m.group(1), int(m.group(2))
        chemin = f"tests/{fichier}"
        if chemin not in comptes_reels:
            non_exploitables.append(
                f"CLAUDE.md:{num} — {fichier} listé mais introuvable dans la collecte"
            )
            continue
        if annonce != comptes_reels[chemin]:
            ecarts.append(
                f"CLAUDE.md:{num} — {fichier} annoncé {annonce}, "
                f"réel {comptes_reels[chemin]}"
            )

    assert candidates, (
        "Aucune ligne de tableau de tests trouvée dans CLAUDE.md : le format a "
        "changé et ce contrôle ne protège plus rien."
    )
    assert not non_exploitables, (
        "Comptes non vérifiables (un compte documenté doit être exact, jamais "
        "approximatif) :\n  - " + "\n  - ".join(non_exploitables)
    )
    assert not ecarts, "Tableau « État des tests » périmé :\n  - " + "\n  - ".join(ecarts)


# L'en-tête « ## État des tests (N dans `tests/` + M backend + …) » est la ligne
# la plus lue du projet : c'est le chiffre qu'un humain — et l'agent, à chaque
# session — retient. Elle ne porte aucune commande `pytest`, donc elle échappait
# au contrôle des commandes.
_RE_ENTETE_TESTS = re.compile(
    r"##\s*État des tests\s*\((\d+)\s+dans\s+`tests/`\s*\+\s*(\d+)\s+backend"
)


def test_entete_etat_des_tests_est_exact(comptes_reels):
    """L'en-tête « État des tests » de CLAUDE.md doit annoncer les vrais totaux."""
    claude = RACINE / "CLAUDE.md"
    if not claude.exists():
        pytest.skip("CLAUDE.md absent")

    texte = claude.read_text(encoding="utf-8")
    m = _RE_ENTETE_TESTS.search(texte)
    assert m, (
        "En-tête « ## État des tests (N dans `tests/` + M backend … ) » introuvable "
        "ou reformulé : ce contrôle ne protège plus rien."
    )
    annonce_tests, annonce_backend = int(m.group(1)), int(m.group(2))
    reel_tests = comptes_reels.get("tests/", 0)
    reel_backend = comptes_reels.get("webapp/backend/tests/", 0)

    assert annonce_tests == reel_tests, (
        f"En-tête CLAUDE.md : {annonce_tests} annoncés dans tests/, réel {reel_tests}"
    )
    assert annonce_backend == reel_backend, (
        f"En-tête CLAUDE.md : {annonce_backend} backend annoncés, réel {reel_backend}"
    )


def test_nombre_de_routes_api_documente(comptes_reels):
    """« N routes » dans la doc doit correspondre aux routes /api réelles."""
    pytest.importorskip("fastapi", reason="cockpit non installé")
    sys.path.insert(0, str(RACINE))
    from webapp.backend.app import app  # noqa: PLC0415

    reel = len([r for r in app.routes
                if getattr(r, "path", "").startswith("/api")])

    # Filtre volontairement simple : « N routes » suffit. L'ancien filtre exigeait
    # aussi « /api » ou « GET » sur la ligne, ce qui laissait passer la prose
    # (« le cockpit expose 3 routes au total »).
    motif = re.compile(r"(\d+)\s+routes?\b")
    ecarts = []
    for md in _fichiers_markdown(pour_totaux=True):
        for num, ligne in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
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
    for md in _fichiers_markdown(pour_totaux=True):
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
    for md in _fichiers_markdown(pour_totaux=True):
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
    for md in _fichiers_markdown(pour_totaux=True):
        for num, ligne in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if "agent" not in ligne.lower():
                continue
            m = motif.search(ligne)
            if m and int(m.group(1)) != reel:
                rel = md.relative_to(RACINE).as_posix()
                ecarts.append(f"{rel}:{num} annonce {m.group(1)} agents, réel = {reel}")
    assert not ecarts, "Nombre d'agents périmé :\n  - " + "\n  - ".join(ecarts)


# ---------------------------------------------------------------------------
# Chiffres DÉRIVÉS DU CODE (pas des comptes de tests)
#
# La revue a signalé une bombe à retardement : « 8 modules » (garde-fous bus)
# et « 9 contrôles » (préflight) décrivent des structures du code et ne sont
# couverts par rien. Ils sont justes aujourd'hui — mais le jour où la dette I4
# sera payée (ajout de diagnostic/greenit.py à _check_garde_fous_bus),
# « 8 modules » deviendra faux en silence. C'est un défaut datable ; on le
# désamorce maintenant.
# ---------------------------------------------------------------------------

def test_nombre_de_modules_sous_garde_fou_bus_documente():
    """« N modules » (garde-fou AST) doit refléter _check_garde_fous_bus()."""
    sys.path.insert(0, str(RACINE))
    from diagnostic.preflight import _check_garde_fous_bus  # noqa: PLC0415

    reel = len(_check_garde_fous_bus())
    motif = re.compile(r"\*{0,2}(\d+)\*{0,2}\s+modules?\b")
    ecarts = []
    for md in _fichiers_markdown(pour_totaux=True):
        for num, ligne in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if "module" not in ligne.lower():
                continue
            # on ne vise que les énoncés parlant du garde-fou de bus
            if not any(k in ligne.lower() for k in ("garde-fou", "garde-fous",
                                                    "requests", "anthropic", "ast")):
                continue
            m = motif.search(ligne)
            if m and int(m.group(1)) != reel:
                rel = md.relative_to(RACINE).as_posix()
                ecarts.append(f"{rel}:{num} annonce {m.group(1)} modules, réel = {reel}")
    assert not ecarts, (
        "Nombre de modules sous garde-fou AST périmé :\n  - " + "\n  - ".join(ecarts)
    )


def test_nombre_de_controles_preflight_documente():
    """« N contrôles » doit refléter les familles de contrôles du préflight.

    On compte par ANALYSE STATIQUE, jamais en exécutant `executer_preflights()` :
    celui-ci inclut le contrôle `tests_verts`, qui relance `pytest tests/` en
    sous-processus — appelé depuis un test, il se relancerait indéfiniment. Le
    piège avait déjà été signalé par le chantier d'intégration ; on ne le retend
    pas ici.
    """
    import ast  # noqa: PLC0415

    source = (RACINE / "diagnostic" / "preflight.py").read_text(encoding="utf-8")
    fn = next(
        (n for n in ast.walk(ast.parse(source))
         if isinstance(n, ast.FunctionDef) and n.name == "executer_preflights"),
        None,
    )
    assert fn is not None, "executer_preflights introuvable : contrôle caduc"

    # Une famille de contrôle = un appel à un `_check_*` dans l'orchestrateur.
    familles = {
        n.func.id for n in ast.walk(fn)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id.startswith("_check_")
    }
    reel = len(familles)
    assert reel > 0, "aucun _check_* détecté : le contrôle ne protège plus rien"

    motif = re.compile(r"\*{0,2}(\d+)\*{0,2}\s+contrôles?\b")
    ecarts = []
    for md in _fichiers_markdown(pour_totaux=True):
        for num, ligne in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            m = motif.search(ligne)
            if m and int(m.group(1)) != reel:
                rel = md.relative_to(RACINE).as_posix()
                ecarts.append(f"{rel}:{num} annonce {m.group(1)} contrôles, réel = {reel}")
    assert not ecarts, (
        "Nombre de contrôles préflight périmé :\n  - " + "\n  - ".join(ecarts)
    )
