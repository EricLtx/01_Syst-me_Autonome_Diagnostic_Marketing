"""
test_greenit.py — observabilité GreenIT : agrégat `/api/greenit` et flux SSE
`/api/greenit/stream`.

Deux exigences structurent ces tests :

1. **Tolérance au ledger hétérogène.** `api_usage.log` peut être absent, ne
   contenir que des lignes ANCIENNES (sans `energie_wh`/`co2e_g`/…), panacher
   ancien et nouveau, ou porter des lignes corrompues. Chacun de ces cas a son
   test : la vue doit répondre 200 partout.
   Les lignes des fixtures sont écrites en JSON brut, et non via `LedgerEntry` :
   non pas parce que celui-ci refuserait les champs GreenIT (il les déclare
   désormais), mais parce qu'on doit pouvoir fabriquer ici des lignes que ce
   schéma d'écriture REJETTE — ligne tronquée, `resultat` hors énumération,
   champ inconnu de demain — précisément les cas que la vue doit encaisser.

2. **Flux borné.** Le SSE est toujours ouvert avec `limite` et/ou `duree_max_s`
   pour que chaque test se termine sans dépendre d'un timeout externe.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Racine du repo pour importer `webapp` (parents[3] : tests → backend → webapp → repo).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from webapp.backend import greenit as greenit_mod  # noqa: E402
from webapp.backend.app import app  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures : jeux de lignes JSONL bruts
# ---------------------------------------------------------------------------

def _ecrire(path: Path, lignes: list[dict]) -> Path:
    path.write_text(
        "\n".join(json.dumps(o, ensure_ascii=False) for o in lignes) + "\n",
        encoding="utf-8",
    )
    return path


# Ligne « ancienne » : exactement les champs de LedgerEntry, zéro champ GreenIT.
LIGNE_ANCIENNE = {
    "ts": "2026-01-10T10:00:00+00:00",
    "fournisseur": "google_places",
    "endpoint": "text_search",
    "unites": {"requetes": 1.0},
    "cout_estime": 0.02,
    "devise": "USD",
    "fiche": "Climatisation Tremblay",
    "cache_hit": False,
    "resultat": "ok",
    "detail": "",
}

# Ligne « enrichie » : champs GreenIT présents (contrat imposé).
LIGNE_SERP = {
    "ts": "2026-01-10T10:01:00+00:00",
    "fournisseur": "serp",
    "endpoint": "search",
    "unites": {"requetes": 1.0},
    "cout_estime": 0.01,
    "devise": "USD",
    "fiche": "Climatisation Tremblay",
    "cache_hit": False,
    "resultat": "ok",
    "detail": "",
    "octets_entrants": 1000,
    "octets_sortants": 200,
    "duree_ms": 120.0,
    "energie_wh": 0.5,
    "co2e_g": 0.2,
    "modele": None,
    "profil": None,
}

LIGNE_CACHE = {
    "ts": "2026-01-10T10:02:00+00:00",
    "fournisseur": "serp",
    "endpoint": "search",
    "unites": {"requetes": 1.0},
    "cout_estime": 0.0,
    "devise": "USD",
    "cache_hit": True,
    "resultat": "ok",
}

LIGNE_LLM = {
    "ts": "2026-01-11T09:00:00+00:00",
    "fournisseur": "anthropic",
    "endpoint": "messages",
    "unites": {"input_tokens": 1000.0, "output_tokens": 200.0},
    "cout_estime": 0.05,
    "devise": "USD",
    "fiche": "Climatisation Tremblay",
    "cache_hit": False,
    "resultat": "ok",
    "detail": "",
    "octets_entrants": 3000,
    "octets_sortants": 500,
    "duree_ms": 800.0,
    "energie_wh": 1.2,
    "co2e_g": 0.6,
    "modele": "claude-haiku-4-5",
    "profil": "standard",
}

LIGNE_BUDGET = {
    "ts": "2026-01-11T09:05:00+00:00",
    "fournisseur": "serp",
    "endpoint": "search",
    "unites": {"requetes": 1.0},
    "cout_estime": 0.0,
    "devise": "USD",
    "cache_hit": False,
    "resultat": "budget_depasse",
    "detail": "serp : plafond unités dépassé",
}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def ledger_mixte(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Ledger panaché : 2 lignes enrichies, 1 ancienne, 1 cache-hit, 1 budget."""
    path = _ecrire(
        tmp_path / "api_usage.log",
        [LIGNE_SERP, LIGNE_CACHE, LIGNE_ANCIENNE, LIGNE_LLM, LIGNE_BUDGET],
    )
    monkeypatch.setenv("API_USAGE_LOG", str(path))
    return path


@pytest.fixture()
def ledger_ancien(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Ledger 100 % « avant GreenIT » : aucun champ d'empreinte."""
    path = _ecrire(tmp_path / "api_usage.log", [LIGNE_ANCIENNE, LIGNE_CACHE])
    monkeypatch.setenv("API_USAGE_LOG", str(path))
    return path


@pytest.fixture()
def ledger_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "nexiste-pas.log"
    monkeypatch.setenv("API_USAGE_LOG", str(path))
    return path


# ---------------------------------------------------------------------------
# 1. Agrégat — cas dégradés (ledger absent / sans champs GreenIT)
# ---------------------------------------------------------------------------

def test_greenit_ledger_absent(client: TestClient, ledger_absent: Path) -> None:
    """Exigence explicite : répondre 200 même sans fichier de grand livre."""
    r = client.get("/api/greenit")
    assert r.status_code == 200
    b = r.json()
    assert b["nb_appels"] == 0
    assert b["nb_cache_hits"] == 0
    assert b["cout_total_usd"] == 0.0
    assert b["energie_wh_total"] == 0.0
    assert b["co2e_g_total"] == 0.0
    assert b["octets_total"] == 0
    assert b["taux_cache"] == 0.0
    assert b["par_modele"] == []
    assert b["par_fournisseur"] == []
    assert b["economies"]["appels_evites"] == 0
    assert b["ledger_present"] is False


def test_greenit_lignes_anciennes_sans_champs(
    client: TestClient, ledger_ancien: Path
) -> None:
    """Anciennes lignes seules → coût agrégé, empreinte à 0, aucune exception."""
    r = client.get("/api/greenit")
    assert r.status_code == 200
    b = r.json()
    assert b["nb_appels"] == 1
    assert b["nb_cache_hits"] == 1
    assert abs(b["cout_total_usd"] - 0.02) < 1e-9
    # Aucun champ GreenIT → empreinte nulle, et couverture annoncée à 0.
    assert b["energie_wh_total"] == 0.0
    assert b["co2e_g_total"] == 0.0
    assert b["octets_total"] == 0
    assert b["couverture_greenit"] == 0.0
    # Le coût évité, lui, reste estimable depuis la moyenne des jumeaux.
    assert b["economies"]["appels_evites"] == 1
    assert b["economies"]["co2e_evite_g"] == 0.0


def test_greenit_ligne_corrompue_ignoree(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "api_usage.log"
    path.write_text(
        json.dumps(LIGNE_SERP) + "\n{ceci n'est pas du json\n" + json.dumps(LIGNE_LLM) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("API_USAGE_LOG", str(path))
    r = client.get("/api/greenit")
    assert r.status_code == 200
    b = r.json()
    assert b["nb_appels"] == 2
    assert b["nb_lignes_illisibles"] == 1


# ---------------------------------------------------------------------------
# 2. Agrégat — totaux, ventilations, économies
# ---------------------------------------------------------------------------

def test_greenit_totaux(client: TestClient, ledger_mixte: Path) -> None:
    r = client.get("/api/greenit")
    assert r.status_code == 200
    b = r.json()
    # 4 appels réels (serp, places, llm, budget_depasse) + 1 cache-hit.
    assert b["nb_appels"] == 4
    assert b["nb_cache_hits"] == 1
    assert abs(b["taux_cache"] - 0.2) < 1e-9
    # budget_depasse n'a rien dépensé : ni coût, ni empreinte.
    assert abs(b["cout_total_usd"] - 0.08) < 1e-9
    assert abs(b["energie_wh_total"] - 1.7) < 1e-9
    assert abs(b["co2e_g_total"] - 0.8) < 1e-9
    assert b["octets_total"] == 4700
    assert abs(b["duree_ms_totale"] - 920.0) < 1e-9


def test_greenit_par_modele(client: TestClient, ledger_mixte: Path) -> None:
    r = client.get("/api/greenit")
    par_modele = {m["modele"]: m for m in r.json()["par_modele"]}
    assert set(par_modele) == {"claude-haiku-4-5", "non-llm"}
    haiku = par_modele["claude-haiku-4-5"]
    assert haiku["nb_appels"] == 1
    assert haiku["tokens"] == 1200.0  # input + output
    assert abs(haiku["cout"] - 0.05) < 1e-9
    assert abs(haiku["energie_wh"] - 1.2) < 1e-9
    # Les appels non-LLM sont regroupés sous une étiquette explicite.
    assert par_modele["non-llm"]["nb_appels"] == 2
    assert abs(par_modele["non-llm"]["cout"] - 0.03) < 1e-9


def test_greenit_par_fournisseur(client: TestClient, ledger_mixte: Path) -> None:
    r = client.get("/api/greenit")
    lignes = r.json()["par_fournisseur"]
    noms = [f["fournisseur"] for f in lignes]
    assert set(noms) == {"anthropic", "google_places", "serp"}
    # Tri par coût décroissant : anthropic (0.05) en tête.
    assert noms[0] == "anthropic"
    serp = next(f for f in lignes if f["fournisseur"] == "serp")
    assert serp["octets"] == 1200
    assert abs(serp["energie_wh"] - 0.5) < 1e-9


def test_greenit_economies_estimees_depuis_cache(
    client: TestClient, ledger_mixte: Path
) -> None:
    """Un cache-hit = un appel évité, valorisé à la moyenne de ses jumeaux."""
    eco = client.get("/api/greenit").json()["economies"]
    assert eco["appels_evites"] == 1
    # Le seul appel serp/search réel coûte 0.01, 0.5 Wh, 0.2 g CO2e.
    assert abs(eco["cout_evite_usd"] - 0.01) < 1e-9
    assert abs(eco["energie_wh_evitee"] - 0.5) < 1e-9
    assert abs(eco["co2e_evite_g"] - 0.2) < 1e-9
    # L'étiquette « estimation » doit voyager avec le chiffre.
    assert "ESTIMATION" in eco["methode"]


def test_greenit_etiquette_estimation(client: TestClient, ledger_mixte: Path) -> None:
    """Anti-hallucination : la réponse déclare que l'empreinte est estimée."""
    b = client.get("/api/greenit").json()
    assert b["estimation"] is True
    assert "ESTIMATION" in b["note_estimation"]
    assert b["source_facteurs"] == "knowledge/greenit.yaml"
    # 2 lignes instrumentées sur 3 appels réellement exécutés.
    assert abs(b["couverture_greenit"] - 2 / 3) < 1e-3


def test_greenit_filtre_depuis(client: TestClient, ledger_mixte: Path) -> None:
    r = client.get("/api/greenit", params={"depuis": "2026-01-11"})
    assert r.status_code == 200
    b = r.json()
    # Ne restent que la ligne LLM et la ligne budget_depasse du 11.
    assert b["nb_appels"] == 2
    assert abs(b["cout_total_usd"] - 0.05) < 1e-9
    assert b["nb_cache_hits"] == 0


def test_greenit_depuis_invalide(client: TestClient, ledger_mixte: Path) -> None:
    r = client.get("/api/greenit", params={"depuis": "hier"})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# 3. Flux SSE
# ---------------------------------------------------------------------------

def _evenements(texte: str) -> list[tuple[str, dict]]:
    """Découpe une réponse text/event-stream en (nom d'événement, données)."""
    out: list[tuple[str, dict]] = []
    for bloc in texte.split("\n\n"):
        nom = None
        data = None
        for ligne in bloc.splitlines():
            if ligne.startswith("event: "):
                nom = ligne[len("event: "):]
            elif ligne.startswith("data: "):
                data = json.loads(ligne[len("data: "):])
        if nom is not None:
            out.append((nom, data if data is not None else {}))
    return out


def test_stream_content_type_et_init(client: TestClient, ledger_absent: Path) -> None:
    r = client.get(
        "/api/greenit/stream",
        params={"duree_max_s": 0.3, "intervalle_s": 0.05},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["cache-control"].startswith("no-cache")
    evts = _evenements(r.text)
    assert evts[0][0] == "init"
    assert evts[0][1]["ledger_present"] is False
    # Anti-hallucination jusque dans le flux.
    assert evts[0][1]["estimation"] is True
    assert evts[-1][0] == "fin"
    assert evts[-1][1]["raison"] == "duree_max"


def test_stream_pousse_les_lignes_du_ledger(
    client: TestClient, ledger_mixte: Path
) -> None:
    """depuis_debut + limite : le flux rejoue le fichier puis se ferme net."""
    r = client.get(
        "/api/greenit/stream",
        params={
            "depuis_debut": True,
            "limite": 2,
            "duree_max_s": 5,
            "intervalle_s": 0.05,
        },
    )
    assert r.status_code == 200
    evts = _evenements(r.text)
    appels = [d for n, d in evts if n == "appel"]
    assert len(appels) == 2
    assert appels[0]["fournisseur"] == "serp"
    # Chaque événement est normalisé : les champs GreenIT sont toujours présents.
    for champ in ("energie_wh", "co2e_g", "octets", "duree_ms", "modele", "tokens"):
        assert champ in appels[0]
    assert evts[-1] == ("fin", {"raison": "limite", "evenements": 2})


def test_stream_temps_reel_nouvelle_ligne(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Une ligne ajoutée APRÈS l'ouverture du flux doit être poussée.

    Le tail se positionne en fin de fichier à l'ouverture de la requête : la
    ligne préexistante ne doit donc PAS être rejouée. Un thread écrit une
    nouvelle ligne pendant que la requête est en vol (TestClient ne restitue le
    corps qu'à la fin du flux, on ne peut pas écrire depuis la boucle de
    lecture) ; `limite=1` referme le flux dès qu'elle est poussée.
    """
    path = _ecrire(tmp_path / "api_usage.log", [LIGNE_ANCIENNE])
    monkeypatch.setenv("API_USAGE_LOG", str(path))

    def ecrire_pendant_le_flux() -> None:
        time.sleep(0.4)  # le flux est ouvert et le tail calé sur la fin du fichier
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(LIGNE_LLM) + "\n")

    ecrivain = threading.Thread(target=ecrire_pendant_le_flux, daemon=True)
    ecrivain.start()
    try:
        r = client.get(
            "/api/greenit/stream",
            params={"limite": 1, "duree_max_s": 8, "intervalle_s": 0.05},
        )
    finally:
        ecrivain.join(timeout=5)

    assert r.status_code == 200
    appels = [d for n, d in _evenements(r.text) if n == "appel"]
    assert len(appels) == 1
    assert appels[0]["fournisseur"] == "anthropic"
    assert appels[0]["modele"] == "claude-haiku-4-5"
    assert appels[0]["profil"] == "standard"
    assert appels[0]["tokens"] == 1200.0


def test_stream_historique(client: TestClient, ledger_mixte: Path) -> None:
    r = client.get(
        "/api/greenit/stream",
        params={"historique": 3, "duree_max_s": 0.3, "intervalle_s": 0.05},
    )
    evts = _evenements(r.text)
    appels = [d for n, d in evts if n == "appel"]
    assert len(appels) == 3  # les 3 dernières lignes du ledger
    assert appels[-1]["resultat"] == "budget_depasse"


def test_stream_heartbeat(client: TestClient, ledger_absent: Path) -> None:
    """Sans trafic, le flux envoie des battements pour rester vivant."""
    r = client.get(
        "/api/greenit/stream",
        params={"duree_max_s": 0.5, "intervalle_s": 0.05, "heartbeat_s": 0.05},
    )
    noms = [n for n, _ in _evenements(r.text)]
    assert "heartbeat" in noms
    assert noms[-1] == "fin"


# ---------------------------------------------------------------------------
# 4. Unités : normalisation défensive et tail incrémental
# ---------------------------------------------------------------------------

def test_normaliser_defauts_sur_ligne_minimale() -> None:
    ligne = greenit_mod.normaliser({"fournisseur": "serp"})
    assert ligne["energie_wh"] == 0.0
    assert ligne["co2e_g"] == 0.0
    assert ligne["octets"] == 0
    assert ligne["duree_ms"] == 0.0
    assert ligne["modele"] is None
    assert ligne["profil"] is None
    assert ligne["cache_hit"] is False
    assert ligne["greenit_instrumente"] is False


def test_normaliser_valeurs_aberrantes() -> None:
    """Un champ GreenIT null / textuel ne doit pas faire tomber la vue."""
    ligne = greenit_mod.normaliser(
        {
            "fournisseur": "serp",
            "energie_wh": None,
            "co2e_g": "0.4",
            "duree_ms": "pas-un-nombre",
            "unites": {"input_tokens": "500", "requetes": 1},
        }
    )
    assert ligne["energie_wh"] == 0.0
    assert ligne["co2e_g"] == 0.4
    assert ligne["duree_ms"] == 0.0
    assert ligne["tokens"] == 500.0  # seules les unités « token » comptent


def test_tail_ligne_partielle_puis_complete(tmp_path: Path) -> None:
    """Une ligne en cours d'écriture n'est publiée qu'une fois terminée."""
    path = tmp_path / "api_usage.log"
    path.write_text("", encoding="utf-8")
    tail = greenit_mod.LedgerTail(path, depuis_debut=True)

    moitie = json.dumps(LIGNE_SERP)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(moitie[:20])
    assert tail.lire_nouvelles() == []  # ligne incomplète → rien

    with path.open("a", encoding="utf-8") as fh:
        fh.write(moitie[20:] + "\n")
    lignes = tail.lire_nouvelles()
    assert len(lignes) == 1
    assert lignes[0]["fournisseur"] == "serp"


def test_tail_troncature_repart_de_zero(tmp_path: Path) -> None:
    path = _ecrire(tmp_path / "api_usage.log", [LIGNE_SERP, LIGNE_LLM])
    tail = greenit_mod.LedgerTail(path)
    assert tail.lire_nouvelles() == []  # démarrage en fin de fichier

    _ecrire(path, [LIGNE_ANCIENNE])  # fichier remplacé, plus court
    lignes = tail.lire_nouvelles()
    assert len(lignes) == 1
    assert lignes[0]["fournisseur"] == "google_places"


def test_tail_fichier_absent(tmp_path: Path) -> None:
    tail = greenit_mod.LedgerTail(tmp_path / "rien.log")
    assert tail.offset == 0
    assert tail.lire_nouvelles() == []
