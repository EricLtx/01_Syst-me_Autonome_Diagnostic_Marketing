"""
test_api.py — tests de la façade HTTP read-only du cockpit.

Chaque test monte un vault temporaire (via VaultIO.write_fiche) et/ou un
api_usage.log temporaire, pointe VAULT_PATH / API_USAGE_LOG dessus, puis
interroge chaque endpoint avec fastapi.testclient.TestClient.

Pourquoi PREFLIGHT_ROOT_DIR pointe sur un dossier vide : le contrôle
`tests_verts` du préflight lance `pytest tests/` en sous-processus. On le
neutralise (dossier sans tests → retour rapide) pour ne pas relancer toute la
suite depuis un test d'API.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Racine du repo pour importer `diagnostic` (parents[3] : tests → backend → webapp → repo).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from diagnostic.api_schema import LedgerEntry  # noqa: E402
from diagnostic.vault_io import VaultIO  # noqa: E402
from diagnostic.vault_schema import FicheProspect  # noqa: E402

from webapp.backend import services  # noqa: E402
from webapp.backend.app import app  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _init_vault_dirs(vault: Path) -> None:
    for d in ("10-Prospects", "20-Rubrics", "30-Diagnostics", "90-Systeme"):
        (vault / d).mkdir(parents=True, exist_ok=True)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def vault_peuple(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Vault temporaire avec une fiche diagnostiquée + son rapport."""
    vault = tmp_path / "vault"
    _init_vault_dirs(vault)

    io = VaultIO(vault, log_path=tmp_path / "runs.log")

    fiche = FicheProspect(
        persona=1,
        marche="quebec",
        statut="diagnostique",
        nom="Climatisation Tremblay",
        date_creation=date(2026, 1, 15),
        site_web="https://tremblay-hvac.example",
        score_global=42,
        gaps_majeurs=["Pas de HTTPS", "Fiche Google absente"],
        date_diagnostic=date(2026, 1, 20),
        icp_id="persona1-quebec",
        contact_nom="Jean Tremblay",
        contact_email="jean@tremblay-hvac.example",
        signal_chaud="Aucune fiche Google Business",
    )
    # On écrit d'abord le rapport, puis on branche le wikilink dans la fiche.
    rapport_path = io.write_rapport(fiche, "# Audit\n\nContenu du rapport de test.\n")
    fiche.rapport = f"[[30-Diagnostics/{rapport_path.stem}]]"
    io.write_fiche(fiche)

    # Une seconde fiche à un autre état, pour l'entonnoir et les filtres.
    fiche2 = FicheProspect(
        persona=1,
        marche="quebec",
        statut="valide",
        nom="Chauffage ABC",
        date_creation=date(2026, 2, 1),
        icp_id="persona1-quebec",
    )
    io.write_fiche(fiche2)

    monkeypatch.setenv("VAULT_PATH", str(vault))
    monkeypatch.setenv("RUNS_LOG", str(tmp_path / "runs.log"))
    monkeypatch.setenv("PREFLIGHT_ROOT_DIR", str(tmp_path / "vide"))
    (tmp_path / "vide").mkdir(exist_ok=True)
    return vault


@pytest.fixture()
def vault_vide(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Vault temporaire NON initialisé (aucun dossier)."""
    vault = tmp_path / "vault_vide"
    monkeypatch.setenv("VAULT_PATH", str(vault))
    monkeypatch.setenv("API_USAGE_LOG", str(tmp_path / "absent.log"))
    monkeypatch.setenv("RUNS_LOG", str(tmp_path / "absent-runs.log"))
    monkeypatch.setenv("PREFLIGHT_ROOT_DIR", str(tmp_path / "vide"))
    (tmp_path / "vide").mkdir(exist_ok=True)
    return vault


# ---------------------------------------------------------------------------
# 1. Health
# ---------------------------------------------------------------------------

def test_health_ok(client: TestClient, vault_peuple: Path) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["vault_initialise"] is True
    assert body["vault_path"] == str(vault_peuple)


def test_health_vault_vide(client: TestClient, vault_vide: Path) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["vault_initialise"] is False


# ---------------------------------------------------------------------------
# 3. Funnel
# ---------------------------------------------------------------------------

def test_funnel(client: TestClient, vault_peuple: Path) -> None:
    r = client.get("/api/pipeline/funnel")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["etats"]["diagnostique"] == 1
    assert body["etats"]["valide"] == 1
    assert body["etats"]["decouvert"] == 0


def test_funnel_vault_vide(client: TestClient, vault_vide: Path) -> None:
    r = client.get("/api/pipeline/funnel")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert all(v == 0 for v in body["etats"].values())


# ---------------------------------------------------------------------------
# 4-5. Prospects (liste + détail)
# ---------------------------------------------------------------------------

def test_prospects_list(client: TestClient, vault_peuple: Path) -> None:
    r = client.get("/api/prospects")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    slugs = {it["slug"] for it in items}
    assert "climatisation-tremblay" in slugs
    tremblay = next(it for it in items if it["slug"] == "climatisation-tremblay")
    assert tremblay["score_global"] == 42
    assert tremblay["contact_email"] == "jean@tremblay-hvac.example"
    assert "Pas de HTTPS" in tremblay["gaps_majeurs"]


def test_prospects_filtre_statut(client: TestClient, vault_peuple: Path) -> None:
    r = client.get("/api/prospects", params={"statut": "valide"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["slug"] == "chauffage-abc"


def test_prospects_vault_vide(client: TestClient, vault_vide: Path) -> None:
    r = client.get("/api/prospects")
    assert r.status_code == 200
    assert r.json() == []


def test_prospect_detail(client: TestClient, vault_peuple: Path) -> None:
    r = client.get("/api/prospects/climatisation-tremblay")
    assert r.status_code == 200
    body = r.json()
    assert body["fiche"]["nom"] == "Climatisation Tremblay"
    assert body["fiche"]["statut"] == "diagnostique"
    assert "Contenu du rapport de test" in body["rapport_md"]


def test_prospect_detail_introuvable(client: TestClient, vault_peuple: Path) -> None:
    r = client.get("/api/prospects/inexistant")
    assert r.status_code == 404
    assert "detail" in r.json()


# ---------------------------------------------------------------------------
# 6. Usage
# ---------------------------------------------------------------------------

@pytest.fixture()
def ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "api_usage.log"
    lignes = [
        LedgerEntry(
            ts="2026-01-10T10:00:00+00:00",
            fournisseur="serp",
            endpoint="search",
            unites={"requetes": 1},
            cout_estime=0.01,
            devise="USD",
            fiche="Climatisation Tremblay",
        ).to_jsonl(),
        LedgerEntry(
            ts="2026-01-10T10:05:00+00:00",
            fournisseur="serp",
            endpoint="search",
            unites={"requetes": 1},
            cout_estime=0.0,
            devise="USD",
            cache_hit=True,
        ).to_jsonl(),
        LedgerEntry(
            ts="2026-01-11T09:00:00+00:00",
            fournisseur="anthropic",
            endpoint="messages",
            unites={"input_tokens": 1000, "output_tokens": 200},
            cout_estime=0.05,
            devise="USD",
            fiche="Climatisation Tremblay",
        ).to_jsonl(),
    ]
    path.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    monkeypatch.setenv("API_USAGE_LOG", str(path))
    return path


def test_usage(client: TestClient, ledger: Path) -> None:
    r = client.get("/api/usage")
    assert r.status_code == 200
    body = r.json()
    assert body["devise"] == "USD"
    assert body["nb_appels"] == 2  # 2 appels réels (le cache_hit ne compte pas)
    assert body["nb_cache_hits"] == 1
    assert abs(body["cout_total_usd"] - 0.06) < 1e-9
    fournisseurs = {f["fournisseur"] for f in body["par_fournisseur"]}
    assert fournisseurs == {"serp", "anthropic"}
    assert body["top_fiches"][0]["fiche"] == "Climatisation Tremblay"


def test_usage_depuis(client: TestClient, ledger: Path) -> None:
    r = client.get("/api/usage", params={"depuis": "2026-01-11"})
    assert r.status_code == 200
    body = r.json()
    # Seule l'entrée anthropic du 11 est conservée.
    assert body["nb_appels"] == 1
    assert abs(body["cout_total_usd"] - 0.05) < 1e-9


def test_usage_date_invalide(client: TestClient, ledger: Path) -> None:
    r = client.get("/api/usage", params={"depuis": "pas-une-date"})
    assert r.status_code == 400


def test_usage_ledger_absent(client: TestClient, vault_vide: Path) -> None:
    # vault_vide pointe API_USAGE_LOG sur un fichier absent → agrégat vide.
    r = client.get("/api/usage")
    assert r.status_code == 200
    body = r.json()
    assert body["nb_appels"] == 0
    assert body["cout_total_usd"] == 0.0
    assert body["par_fournisseur"] == []


# ---------------------------------------------------------------------------
# 7. ICP
# ---------------------------------------------------------------------------

def test_icp(client: TestClient) -> None:
    r = client.get("/api/icp")
    assert r.status_code == 200
    items = r.json()
    ids = {it["icp_id"] for it in items}
    assert "persona1-quebec" in ids
    quebec = next(it for it in items if it["icp_id"] == "persona1-quebec")
    assert quebec["persona"] == 1
    assert quebec["marche"] == "quebec"
    assert quebec["description"]


# ---------------------------------------------------------------------------
# 2. Préflight
# ---------------------------------------------------------------------------

def test_preflight(client: TestClient, vault_peuple: Path) -> None:
    r = client.get("/api/preflight")
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] in ("GO", "NO-GO")
    assert isinstance(body["checks"], list)
    assert body["checks"]
    for c in body["checks"]:
        assert set(c.keys()) == {"nom", "niveau", "ok", "message"}


def test_preflight_vault_vide(client: TestClient, vault_vide: Path) -> None:
    # Vault non initialisé → au moins un bloquant échoue → NO-GO en AS-IS.
    r = client.get("/api/preflight")
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "NO-GO"


# ---------------------------------------------------------------------------
# 8. Runs
# ---------------------------------------------------------------------------

def test_runs_present(client: TestClient, vault_peuple: Path) -> None:
    # Les écritures de fixture ont produit des lignes dans runs.log.
    r = client.get("/api/runs", params={"limit": 10})
    assert r.status_code == 200
    objets = r.json()
    assert isinstance(objets, list)
    assert objets  # write_rapport + write_fiche ont journalisé
    assert "op" in objets[0]


def test_runs_absent(client: TestClient, vault_vide: Path) -> None:
    r = client.get("/api/runs")
    assert r.status_code == 200
    assert r.json() == []
