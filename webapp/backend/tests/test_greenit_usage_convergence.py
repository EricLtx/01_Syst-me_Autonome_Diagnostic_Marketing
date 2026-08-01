"""
test_greenit_usage_convergence.py — filet de non-régression CROISÉ entre les
deux agrégateurs du grand livre.

Le problème qu'il couvre : `diagnostic.usage.agreger` (utilisé par
`run_usage.py` et par `/api/usage`) et `webapp.backend.greenit.agreger`
(utilisé par `/api/greenit`) calculent tous deux le **coût total** depuis le
même `api_usage.log`. Deux implémentations pour un chiffre financier, c'est une
duplication assumée — le tail SSE et la tolérance aux lignes dégradées
justifient le lecteur séparé — mais elle n'est acceptable que si quelqu'un
surveille leur convergence.

Sans ce test, un changement de convention dans `usage.py` (par exemple imputer
le coût des appels en erreur, ou compter les cache-hits comme des appels) ferait
diverger le cockpit de `run_usage.py` **en silence** : l'opératrice lirait deux
montants différents pour le même mois, sans savoir lequel croire.

Les fixtures sont écrites via `LedgerEntry.to_jsonl()` — et non en JSON brut
comme dans test_greenit.py — parce que la comparaison n'a de sens que sur le
domaine où les DEUX lecteurs sont définis : `charger_ledger` valide chaque
ligne avec le schéma strict. Les lignes dégradées, elles, sont testées côté
greenit seul (cf. test_greenit.py) : c'est justement là que les deux lecteurs
ne peuvent pas se comparer.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from diagnostic.api_schema import LedgerEntry  # noqa: E402
from diagnostic.usage import agreger as agreger_usage  # noqa: E402
from diagnostic.usage import charger_ledger  # noqa: E402

from webapp.backend import greenit as greenit_mod  # noqa: E402
from webapp.backend.app import app  # noqa: E402


# ---------------------------------------------------------------------------
# Ledger panaché : tous les cas qui font diverger deux conventions d'agrégation
# ---------------------------------------------------------------------------

def _ledger_panache() -> list[LedgerEntry]:
    return [
        # 1. Appel réel « ordinaire », fournisseur A.
        LedgerEntry(
            ts="2026-01-10T10:00:00+00:00",
            fournisseur="serp",
            endpoint="search",
            unites={"requetes": 1.0},
            cout_estime=0.0031,
            devise="USD",
            fiche="Climatisation Tremblay",
            octets_entrants=1000,
            octets_sortants=200,
            duree_ms=120.0,
            energie_wh=0.5,
            co2e_g=0.2,
        ),
        # 2. Cache-hit : ne doit compter comme appel dans AUCUNE des deux vues.
        LedgerEntry(
            ts="2026-01-10T10:05:00+00:00",
            fournisseur="serp",
            endpoint="search",
            unites={"requetes": 1.0},
            cout_estime=0.0,
            devise="USD",
            cache_hit=True,
        ),
        # 3. budget_depasse AVEC un cout_estime NON NUL : le piège. La ligne
        #    porte le coût qu'aurait eu l'appel, mais l'appel n'a pas eu lieu —
        #    l'imputer gonflerait la facture. Les deux vues doivent l'écarter.
        LedgerEntry(
            ts="2026-01-10T10:06:00+00:00",
            fournisseur="serp",
            endpoint="search",
            unites={"requetes": 1.0},
            cout_estime=0.0250,
            devise="USD",
            resultat="budget_depasse",
            detail="serp : plafond unités dépassé",
        ),
        # 4. Appel en ERREUR, fournisseur B : a bien consommé un appel réseau,
        #    donc son coût est imputé par les deux vues (convention actuelle).
        LedgerEntry(
            ts="2026-01-11T09:00:00+00:00",
            fournisseur="anthropic",
            endpoint="messages",
            unites={"input_tokens": 300.0},
            cout_estime=0.0040,
            devise="USD",
            resultat="erreur",
            detail="502 upstream",
            octets_entrants=120,
            octets_sortants=900,
            duree_ms=430.0,
            energie_wh=0.11,
            co2e_g=0.05,
        ),
        # 5. Appel LLM réel, fournisseur B, avec champs GreenIT complets.
        LedgerEntry(
            ts="2026-01-11T09:30:00+00:00",
            fournisseur="anthropic",
            endpoint="messages",
            unites={"input_tokens": 1000.0, "output_tokens": 200.0},
            cout_estime=0.0500,
            devise="USD",
            fiche="Climatisation Tremblay",
            octets_entrants=3000,
            octets_sortants=500,
            duree_ms=800.0,
            energie_wh=1.2,
            co2e_g=0.6,
            modele="claude-haiku-4-5",
            profil="standard",
        ),
        # 6. Ligne horodatée dans un autre fuseau : les deux vues filtrent sur
        #    `depuis` par des chemins différents (usage.py par `ts.date()`,
        #    greenit.py par les 10 premiers caractères ISO). Elles doivent
        #    aboutir à la même date locale.
        LedgerEntry(
            ts="2026-01-11T01:00:00+05:00",
            fournisseur="google_places",
            endpoint="text_search",
            unites={"requetes": 1.0},
            cout_estime=0.0170,
            devise="USD",
            octets_entrants=2048,
            duree_ms=95.0,
        ),
    ]


@pytest.fixture()
def ledger_panache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "api_usage.log"
    path.write_text(
        "\n".join(e.to_jsonl() for e in _ledger_panache()) + "\n", encoding="utf-8"
    )
    monkeypatch.setenv("API_USAGE_LOG", str(path))
    return path


def _cote_usage(path: Path, depuis: date | None = None):
    return agreger_usage(charger_ledger(path, depuis=depuis))


def _cote_greenit(path: Path, depuis: date | None = None) -> dict:
    lignes, illisibles = greenit_mod.lire_ledger(path, depuis=depuis)
    return greenit_mod.agreger(lignes, nb_illisibles=illisibles)


# ---------------------------------------------------------------------------
# 1. Convergence des fonctions d'agrégation
# ---------------------------------------------------------------------------

def test_convergence_cout_total(ledger_panache: Path) -> None:
    """Le chiffre financier doit être IDENTIQUE des deux côtés."""
    u = _cote_usage(ledger_panache)
    g = _cote_greenit(ledger_panache)
    assert g["cout_total_usd"] == pytest.approx(u.cout_total, abs=1e-9)
    # Valeur explicite : si elle change, c'est une décision, pas un accident.
    # 0.0031 (ok) + 0.0040 (erreur) + 0.0500 (llm) + 0.0170 (places) = 0.0741
    # Le budget_depasse (0.0250) et le cache-hit (0.0) sont exclus.
    assert u.cout_total == pytest.approx(0.0741, abs=1e-9)


def test_convergence_comptages(ledger_panache: Path) -> None:
    u = _cote_usage(ledger_panache)
    g = _cote_greenit(ledger_panache)
    assert g["nb_appels"] == u.nb_appels
    assert g["nb_cache_hits"] == u.nb_cache_hits
    assert g["taux_cache"] == pytest.approx(u.taux_cache, abs=1e-4)
    # 5 appels réels (dont 1 budget_depasse et 1 erreur) + 1 cache-hit.
    assert u.nb_appels == 5
    assert u.nb_cache_hits == 1
    assert u.taux_cache == pytest.approx(1 / 6, abs=1e-4)


def test_convergence_par_fournisseur(ledger_panache: Path) -> None:
    """Même ventilation des coûts par fournisseur (mêmes clés, mêmes montants)."""
    u = _cote_usage(ledger_panache)
    g = {f["fournisseur"]: f for f in _cote_greenit(ledger_panache)["par_fournisseur"]}
    assert set(g) == set(u.par_fournisseur)
    for nom, stat in u.par_fournisseur.items():
        assert g[nom]["cout"] == pytest.approx(stat.cout_total, abs=1e-9)
        assert g[nom]["nb_appels"] == stat.nb_appels


def test_convergence_avec_filtre_depuis(ledger_panache: Path) -> None:
    """Les deux filtres de date doivent découper le ledger au même endroit.

    Chemins différents : `usage.py` compare `entry.ts.date()` (datetime parsé,
    fuseau conservé), `greenit.py` compare les 10 premiers caractères ISO. La
    ligne en +05:00 est là pour que la différence, si elle existe, se voie.
    """
    for depuis in (date(2026, 1, 10), date(2026, 1, 11), date(2026, 1, 12)):
        u = _cote_usage(ledger_panache, depuis)
        g = _cote_greenit(ledger_panache, depuis)
        assert g["nb_appels"] == u.nb_appels, f"divergence nb_appels à {depuis}"
        assert g["nb_cache_hits"] == u.nb_cache_hits, f"divergence cache à {depuis}"
        assert g["cout_total_usd"] == pytest.approx(
            u.cout_total, abs=1e-9
        ), f"divergence coût à {depuis}"
    # Le 11 ne garde que les 3 lignes de ce jour (erreur, llm, places +05:00).
    assert _cote_usage(ledger_panache, date(2026, 1, 11)).nb_appels == 3


def test_convergence_ledger_vide(tmp_path: Path) -> None:
    """Cas limite : ni l'un ni l'autre ne doit inventer de chiffre."""
    absent = tmp_path / "rien.log"
    u = _cote_usage(absent)
    g = _cote_greenit(absent)
    assert (g["cout_total_usd"], g["nb_appels"], g["nb_cache_hits"]) == (
        u.cout_total,
        u.nb_appels,
        u.nb_cache_hits,
    ) == (0.0, 0, 0)


# ---------------------------------------------------------------------------
# 2. Convergence de bout en bout : ce que l'opératrice lit à l'écran
# ---------------------------------------------------------------------------

def test_convergence_endpoints_http(ledger_panache: Path) -> None:
    """/api/usage et /api/greenit doivent afficher le même coût, au centime.

    C'est la version qui compte vraiment : deux écrans du cockpit affichent ce
    montant, ils ne peuvent pas se contredire.
    """
    client = TestClient(app)
    usage = client.get("/api/usage").json()
    greenit = client.get("/api/greenit").json()

    assert greenit["cout_total_usd"] == pytest.approx(usage["cout_total_usd"], abs=1e-9)
    assert greenit["nb_appels"] == usage["nb_appels"]
    assert greenit["nb_cache_hits"] == usage["nb_cache_hits"]
    assert greenit["taux_cache"] == pytest.approx(usage["taux_cache"], abs=1e-4)
    assert greenit["devise"] == usage["devise"]

    # Même ventilation par fournisseur des deux côtés de l'API.
    cout_usage = {f["fournisseur"]: f["cout_total"] for f in usage["par_fournisseur"]}
    cout_green = {f["fournisseur"]: f["cout"] for f in greenit["par_fournisseur"]}
    assert cout_green.keys() == cout_usage.keys()
    for nom, montant in cout_usage.items():
        assert cout_green[nom] == pytest.approx(montant, abs=1e-9)


def test_convergence_endpoints_http_avec_depuis(ledger_panache: Path) -> None:
    client = TestClient(app)
    usage = client.get("/api/usage", params={"depuis": "2026-01-11"}).json()
    greenit = client.get("/api/greenit", params={"depuis": "2026-01-11"}).json()
    assert greenit["cout_total_usd"] == pytest.approx(usage["cout_total_usd"], abs=1e-9)
    assert greenit["nb_appels"] == usage["nb_appels"]
