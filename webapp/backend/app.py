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

from fastapi import FastAPI, HTTPException, Query  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from webapp.backend import services  # noqa: E402
from webapp.backend.schemas import (  # noqa: E402
    FunnelResponse,
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
