"""
schemas.py — modèles de réponse Pydantic de l'API cockpit (lecture seule).

Pourquoi des modèles dédiés plutôt que renvoyer directement les objets du
package `diagnostic` : on veut un contrat de sortie stable pour le front-end,
découplé des structures internes (FicheProspect, Usage, Check…). Si un champ
interne change de forme, l'adaptateur (services.py) absorbe le choc ; le
contrat HTTP reste identique.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# --- 1. /api/health --------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    vault_path: str
    vault_initialise: bool


# --- 2. /api/preflight -----------------------------------------------------

class CheckOut(BaseModel):
    # On recopie exactement les champs de diagnostic.preflight.Check.
    # Le champ s'appelle bien `message` (et non `detail`).
    nom: str
    niveau: str
    ok: bool
    message: str


class PreflightResponse(BaseModel):
    verdict: str  # "GO" | "NO-GO"
    checks: list[CheckOut]


# --- 3. /api/pipeline/funnel ----------------------------------------------

class FunnelEtats(BaseModel):
    decouvert: int = 0
    diagnostique: int = 0
    valide: int = 0
    contacte: int = 0
    rejete: int = 0


class FunnelResponse(BaseModel):
    total: int
    etats: FunnelEtats


# --- 4. /api/prospects (liste) --------------------------------------------

class ProspectListItem(BaseModel):
    # Vue « liste » : les champs utiles à une table de cockpit, pas tout le
    # frontmatter (voir ProspectDetail pour la vue complète).
    slug: str
    nom: str
    site_web: str | None = None
    statut: str
    persona: int
    marche: str
    score_global: int | None = None
    signal_chaud: str | None = None
    gaps_majeurs: list[str] = []
    date_creation: str | None = None
    date_diagnostic: str | None = None
    icp_id: str | None = None
    opt_out: bool = False
    contact_nom: str | None = None
    contact_email: str | None = None


# --- 5. /api/prospects/{slug} (détail) ------------------------------------

class ProspectDetail(BaseModel):
    # `fiche` = model_dump(mode="json") complet de la FicheProspect (extra
    # compris) ; on le laisse en dict libre pour ne rien perdre des
    # annotations humaines portées par extra="allow".
    fiche: dict[str, Any]
    rapport_md: str | None = None


# --- 6. /api/usage ---------------------------------------------------------

class UsageParFournisseurOut(BaseModel):
    fournisseur: str
    nb_appels: int
    cout_total: float
    unites: dict[str, float] = {}


class TopFicheOut(BaseModel):
    fiche: str
    cout: float


class UsageResponse(BaseModel):
    cout_total_usd: float
    devise: str = "USD"
    nb_appels: int
    nb_cache_hits: int
    taux_cache: float
    par_fournisseur: list[UsageParFournisseurOut] = []
    top_fiches: list[TopFicheOut] = []


# --- 9. /api/greenit -------------------------------------------------------
# ⚠️ `energie_wh` et `co2e_g` sont des ESTIMATIONS (facteurs paramétrables de
# knowledge/greenit.yaml), jamais des mesures certifiées. Le contrat porte cette
# mise en garde jusque dans la réponse (`estimation`, `note_estimation`) pour
# qu'aucun consommateur ne puisse les présenter comme un bilan opposable.

class GreenitParModeleOut(BaseModel):
    modele: str
    nb_appels: int
    tokens: float
    cout: float
    energie_wh: float
    co2e_g: float
    octets: int = 0
    duree_ms: float = 0.0


class GreenitParFournisseurOut(BaseModel):
    fournisseur: str
    nb_appels: int
    tokens: float
    cout: float
    energie_wh: float
    co2e_g: float
    octets: int = 0
    duree_ms: float = 0.0


class GreenitEconomiesOut(BaseModel):
    # Économies déduites des cache-hits : un cache-hit = un appel évité.
    appels_evites: int
    cout_evite_usd: float
    energie_wh_evitee: float = 0.0
    co2e_evite_g: float
    methode: str = ""


class GreenitResponse(BaseModel):
    cout_total_usd: float
    devise: str = "USD"
    energie_wh_total: float
    co2e_g_total: float
    octets_total: int
    duree_ms_totale: float
    nb_appels: int
    nb_cache_hits: int
    nb_erreurs: int = 0
    nb_lignes_illisibles: int = 0
    taux_cache: float
    economies: GreenitEconomiesOut
    par_modele: list[GreenitParModeleOut] = []
    par_fournisseur: list[GreenitParFournisseurOut] = []
    # Métadonnées d'honnêteté : estimation, source des facteurs, part des appels
    # réellement instrumentés (le reste compte pour 0 dans l'empreinte).
    estimation: bool = True
    note_estimation: str = ""
    source_facteurs: str = "knowledge/greenit.yaml"
    couverture_greenit: float = 0.0
    ledger_present: bool = False
    ledger_path: str = ""


# --- 7. /api/icp -----------------------------------------------------------

class IcpOut(BaseModel):
    icp_id: str
    persona: int
    marche: str
    description: str


# --- Erreurs ---------------------------------------------------------------

class ErrorResponse(BaseModel):
    # Toute erreur est renvoyée en JSON clair (jamais de stacktrace brute).
    detail: str
