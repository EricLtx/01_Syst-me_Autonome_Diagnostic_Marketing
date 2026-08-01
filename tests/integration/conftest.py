"""
conftest.py — fixtures des tests d'intégration bout-en-bout.

Principe d'hermétisme (aucun test ne doit jamais sortir de la machine) :
  - le faux serveur écoute sur un port dynamique de la boucle locale ;
  - toutes les bases d'API (`*_BASE_URL`) sont redirigées vers lui ;
  - les clés sont factices — aucun test ne dépend d'une vraie clé ;
  - vault, grand livre (`api_usage.log`) et cache disque vivent dans `tmp_path`.

TOLÉRANCE AU SCHÉMA DU GRAND LIVRE : `lignes_ledger()` renvoie des dicts bruts
et les tests n'inspectent QUE les clés qui les concernent. `LedgerEntry` peut
gagner des champs optionnels (octets, durée, énergie, CO2e, modèle, profil…)
sans casser un seul test d'intégration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

_RACINE = Path(__file__).resolve().parents[2]
if str(_RACINE) not in sys.path:
    sys.path.insert(0, str(_RACINE))

from tests.integration import dataset  # noqa: E402
from tests.integration.faux_api import ServeurFauxApi  # noqa: E402


# ---------------------------------------------------------------------------
# Faux serveur d'API (une instance pour toute la session : démarrage ~50 ms)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def serveur() -> ServeurFauxApi:
    srv = ServeurFauxApi().demarrer()
    try:
        yield srv
    finally:
        srv.arreter()


@pytest.fixture()
def journal_vierge(serveur: ServeurFauxApi) -> ServeurFauxApi:
    """Repart d'un journal de requêtes vide (assertions de comptage fiables)."""
    serveur.reinitialiser_journal()
    return serveur


# ---------------------------------------------------------------------------
# Environnement redirigé vers le faux serveur
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_faux_api(serveur: ServeurFauxApi, monkeypatch: pytest.MonkeyPatch) -> ServeurFauxApi:
    """Redirige bases d'API + clés factices, et l'ICP vers la fixture de test."""
    for cle, valeur in serveur.variables_env().items():
        monkeypatch.setenv(cle, valeur)

    # L'ICP est une donnée : on pointe le répertoire de fixtures plutôt que
    # d'ajouter un fichier dans icp/ (dossier de production).
    import diagnostic.config as config
    import diagnostic.preflight as preflight
    monkeypatch.setattr(config, "ICP_DIR", dataset.ICP_DIR_TEST)
    monkeypatch.setattr(preflight, "_ICP_DIR", dataset.ICP_DIR_TEST)
    return serveur


# ---------------------------------------------------------------------------
# Grille tarifaire de test / bus I/O / vault
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def pricing_test() -> dict:
    return yaml.safe_load(dataset.PRICING_TEST.read_text(encoding="utf-8"))


@pytest.fixture()
def chemins(tmp_path: Path) -> dict[str, Path]:
    """Chemins hermétiques : vault, grand livre, cache, exports, verrou."""
    return {
        "vault": tmp_path / "vault",
        "ledger": tmp_path / "api_usage.log",
        "cache": tmp_path / ".cache" / "api_io",
        "exports": tmp_path / "exports",
        "verrou": tmp_path / ".run.lock",
    }


@pytest.fixture()
def vault_vide(chemins: dict[str, Path]) -> Path:
    """Vault initialisé (scaffold de production) mais sans aucune fiche."""
    dataset.initialiser_vault(chemins["vault"])
    return chemins["vault"]


@pytest.fixture()
def vault_seme(chemins: dict[str, Path], serveur: ServeurFauxApi) -> Path:
    """Vault initialisé + dataset semé, sites pointant sur le faux serveur.

    Les fiches semées visent le serveur en HTTP (pas HTTPS) : c'est le cas
    « site pauvre » réaliste, et cela produit la faille « Pas de HTTPS ».
    """
    dataset.semer(chemins["vault"], url_site=lambda slug: serveur.url_site(slug))
    return chemins["vault"]


@pytest.fixture()
def api_io(chemins: dict[str, Path], pricing_test: dict):
    """Bus I/O de test : grand livre, cache et budgets isolés dans tmp_path."""
    from diagnostic.api_io import ApiIO
    return ApiIO(
        pricing_test,
        chemins["ledger"],
        cache_dir=chemins["cache"],
        budgets=pricing_test.get("budgets"),
        vault_path=chemins["vault"],
    )


# ---------------------------------------------------------------------------
# Helpers d'assertion
# ---------------------------------------------------------------------------

def lignes_ledger(chemin: Path) -> list[dict]:
    """Lit api_usage.log en dicts BRUTS (tolérant aux champs supplémentaires).

    On ne valide volontairement pas via LedgerEntry ici : de nouveaux champs
    optionnels peuvent apparaître, les tests d'intégration ne doivent jamais
    s'y opposer.
    """
    if not Path(chemin).exists():
        return []
    lignes: list[dict] = []
    for ligne in Path(chemin).read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if ligne:
            lignes.append(json.loads(ligne))
    return lignes


def lignes_pour(chemin: Path, fournisseur: str) -> list[dict]:
    return [l for l in lignes_ledger(chemin) if l.get("fournisseur") == fournisseur]


@pytest.fixture()
def ledger():
    """Expose les helpers de lecture du grand livre aux tests."""
    class _Ledger:
        lignes = staticmethod(lignes_ledger)
        pour = staticmethod(lignes_pour)
    return _Ledger()
