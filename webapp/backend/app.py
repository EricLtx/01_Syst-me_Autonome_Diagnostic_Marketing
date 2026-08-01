"""
app.py — façade HTTP read-only du cockpit opérateur (FastAPI).

Complément web d'Obsidian : expose en lecture le vault et les agrégats du
système de diagnostic. AUCUNE écriture vault, AUCUN appel réseau sortant,
AUCUNE transition d'état, AUCUN appel à api_io. Les routes restent minces :
toute la logique d'accès à `diagnostic` vit dans services.py.

Lancement :
    VAULT_PATH=/chemin/vers/vault uvicorn webapp.backend.app:app --reload
"""
from __future__ import annotations

import sys
from pathlib import Path

# --- sys.path : rendre `diagnostic` importable même lancé hors racine repo ---
# webapp/backend/app.py → parents[2] == racine du repo.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import asyncio  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402
from typing import AsyncIterator  # noqa: E402

from fastapi import FastAPI, HTTPException, Query, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402

from webapp.backend import greenit as greenit_mod  # noqa: E402
from webapp.backend import services  # noqa: E402
from webapp.backend.schemas import (  # noqa: E402
    FunnelResponse,
    GreenitResponse,
    HealthResponse,
    IcpOut,
    PreflightResponse,
    ProspectDetail,
    ProspectListItem,
    UsageResponse,
)

app = FastAPI(
    title="Cockpit opérateur — API diagnostic marketing",
    description="Façade HTTP strictement en lecture seule au-dessus du vault.",
    version="1.0.0",
)

# CORS : le front de dev (Vite) tourne sur 5173. On autorise localhost et
# 127.0.0.1 pour couvrir les deux façons d'y accéder.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 1. Santé
# ---------------------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse, tags=["systeme"])
def health() -> HealthResponse:
    return HealthResponse(**services.get_health())


# ---------------------------------------------------------------------------
# 2. Préflight
# ---------------------------------------------------------------------------

@app.get("/api/preflight", response_model=PreflightResponse, tags=["systeme"])
def preflight(icp: str | None = Query(default=None)) -> PreflightResponse:
    try:
        data = services.get_preflight(icp_id=icp)
    except Exception as exc:  # dégradation propre : jamais de stacktrace brute
        raise HTTPException(status_code=500, detail=f"Préflight indisponible : {exc}")
    return PreflightResponse(**data)


# ---------------------------------------------------------------------------
# 3. Entonnoir pipeline
# ---------------------------------------------------------------------------

@app.get("/api/pipeline/funnel", response_model=FunnelResponse, tags=["pipeline"])
def funnel() -> FunnelResponse:
    return FunnelResponse(**services.get_funnel())


# ---------------------------------------------------------------------------
# 4-5. Prospects
# ---------------------------------------------------------------------------

@app.get("/api/prospects", response_model=list[ProspectListItem], tags=["prospects"])
def prospects(
    statut: str | None = Query(default=None),
    persona: int | None = Query(default=None),
    marche: str | None = Query(default=None),
) -> list[ProspectListItem]:
    items = services.list_prospects(statut=statut, persona=persona, marche=marche)
    return [ProspectListItem(**it) for it in items]


@app.get("/api/prospects/{slug}", response_model=ProspectDetail, tags=["prospects"])
def prospect_detail(slug: str) -> ProspectDetail:
    data = services.get_prospect(slug)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Fiche introuvable : {slug}")
    return ProspectDetail(**data)


# ---------------------------------------------------------------------------
# 6. Usage
# ---------------------------------------------------------------------------

@app.get("/api/usage", response_model=UsageResponse, tags=["usage"])
def usage(depuis: str | None = Query(default=None)) -> UsageResponse:
    try:
        data = services.get_usage(depuis=depuis)
    except ValueError:
        # Format de date invalide → 400 clair (attendu : YYYY-MM-DD).
        raise HTTPException(
            status_code=400,
            detail="Paramètre 'depuis' invalide, format attendu : YYYY-MM-DD.",
        )
    return UsageResponse(**data)


# ---------------------------------------------------------------------------
# 9. GreenIT — agrégat d'efficience
# ---------------------------------------------------------------------------

@app.get("/api/greenit", response_model=GreenitResponse, tags=["greenit"])
def greenit(depuis: str | None = Query(default=None)) -> GreenitResponse:
    """Coût, énergie, CO2e, octets et économies de cache du grand livre.

    ⚠️ energie_wh / co2e_g sont des ESTIMATIONS (facteurs de
    knowledge/greenit.yaml), pas des mesures. La réponse le déclare
    explicitement (`estimation`, `note_estimation`).
    """
    try:
        data = services.get_greenit(depuis=depuis)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Paramètre 'depuis' invalide, format attendu : YYYY-MM-DD.",
        )
    return GreenitResponse(**data)


# ---------------------------------------------------------------------------
# 10. GreenIT — flux temps réel (SSE)
# ---------------------------------------------------------------------------

def _sse(evenement: str, donnees: dict) -> str:
    """Formate un message Server-Sent Events (une trame `event:` + `data:`)."""
    charge = json.dumps(donnees, ensure_ascii=False)
    return f"event: {evenement}\ndata: {charge}\n\n"


@app.get("/api/greenit/stream", tags=["greenit"])
async def greenit_stream(
    request: Request,
    historique: int = Query(default=0, ge=0, le=200),
    limite: int = Query(default=0, ge=0, le=10_000),
    duree_max_s: float = Query(default=300.0, gt=0, le=3600),
    intervalle_s: float = Query(default=1.0, gt=0, le=30),
    heartbeat_s: float = Query(default=15.0, gt=0, le=120),
    depuis_debut: bool = Query(default=False),
) -> StreamingResponse:
    """Suit `api_usage.log` en direct : une trame SSE par nouvelle ligne.

    Paramètres de bornage — indispensables pour qu'un test (ou un client
    distrait) ne laisse pas tourner un générateur indéfiniment :
      - `limite`      : nombre max d'événements `appel` avant fermeture (0 = illimité) ;
      - `duree_max_s` : durée de vie maximale du flux ;
      - `intervalle_s`: période de scrutation du fichier ;
      - `heartbeat_s` : période des trames `heartbeat` (garde la connexion vivante
        à travers les proxies et permet au front d'afficher « connecté ») ;
      - `historique`  : rejoue les N dernières lignes déjà journalisées à l'ouverture ;
      - `depuis_debut`: suit le fichier depuis l'octet 0 au lieu de sa fin.

    Lecture seule stricte : on ne fait qu'ouvrir le journal en lecture.
    """
    tail = services.greenit_tail(depuis_debut=depuis_debut)
    passe = services.greenit_historique(historique) if historique else []

    async def flux() -> AsyncIterator[str]:
        debut = time.monotonic()
        dernier_battement = debut
        envoyes = 0

        yield _sse(
            "init",
            {
                "ts": greenit_mod.horodatage(),
                "offset": tail.offset,
                "ledger_present": tail.path.is_file(),
                "estimation": True,
                "note_estimation": greenit_mod.NOTE_ESTIMATION,
            },
        )
        for ligne in passe:
            yield _sse("appel", ligne)

        # Boucle de scrutation. Si le client raccroche, Starlette annule la
        # tâche : la CancelledError remonte et referme le générateur — rien à
        # libérer nous-mêmes (le tail ne garde aucun descripteur ouvert).
        raison = "duree_max"
        while True:
            # Déconnexion détectée par sondage non bloquant → arrêt propre.
            if await request.is_disconnected():
                raison = "deconnexion"
                break

            for ligne in tail.lire_nouvelles():
                yield _sse("appel", ligne)
                envoyes += 1
                dernier_battement = time.monotonic()
                if limite and envoyes >= limite:
                    break

            if limite and envoyes >= limite:
                raison = "limite"
                break

            maintenant = time.monotonic()
            if maintenant - debut >= duree_max_s:
                raison = "duree_max"
                break
            if maintenant - dernier_battement >= heartbeat_s:
                dernier_battement = maintenant
                yield _sse(
                    "heartbeat",
                    {"ts": greenit_mod.horodatage(), "offset": tail.offset},
                )

            await asyncio.sleep(intervalle_s)

        yield _sse("fin", {"raison": raison, "evenements": envoyes})

    return StreamingResponse(
        flux(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            # Désactive la bufferisation côté proxy (nginx) : sans ça, le flux
            # arrive par paquets et perd tout intérêt « temps réel ».
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# 7. ICP
# ---------------------------------------------------------------------------

@app.get("/api/icp", response_model=list[IcpOut], tags=["icp"])
def icp() -> list[IcpOut]:
    return [IcpOut(**it) for it in services.list_icp()]


# ---------------------------------------------------------------------------
# 8. Runs
# ---------------------------------------------------------------------------

@app.get("/api/runs", tags=["systeme"])
def runs(limit: int = Query(default=50, ge=0, le=1000)) -> list[dict]:
    # Objets JSONL bruts de runs.log (best-effort, [] si absent).
    return services.list_runs(limit=limit)
