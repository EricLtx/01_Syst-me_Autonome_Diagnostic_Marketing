// types.ts — contrat d'API consommé (backend FastAPI, préfixe /api).
// Ces types reflètent 1:1 les réponses documentées ; ils servent aussi de
// schéma pour les fixtures du mode mock.

export type Statut =
  | "decouvert"
  | "diagnostique"
  | "valide"
  | "contacte"
  | "rejete";

export type NiveauCheck = "bloquant" | "warn";

export type Verdict = "GO" | "NO-GO";

// 1. GET /api/health
export interface Health {
  status: string;
  vault_path: string;
  vault_initialise: boolean;
}

// 2. GET /api/preflight
export interface PreflightCheck {
  nom: string;
  niveau: NiveauCheck;
  ok: boolean;
  message: string;
}

export interface Preflight {
  verdict: Verdict;
  checks: PreflightCheck[];
}

// 3. GET /api/pipeline/funnel
export interface FunnelEtats {
  decouvert: number;
  diagnostique: number;
  valide: number;
  contacte: number;
  rejete: number;
}

export interface Funnel {
  total: number;
  etats: FunnelEtats;
}

// 4. GET /api/prospects
export interface Prospect {
  slug: string;
  nom: string;
  site_web: string | null;
  statut: Statut;
  /** Optionnel depuis l'ADR 0003 : un secteur est identifié par icp_id. */
  persona: number | null;
  marche: string;
  score_global: number | null;
  signal_chaud: boolean;
  gaps_majeurs: string[];
  date_creation: string | null;
  date_diagnostic: string | null;
  icp_id: string;
  opt_out: boolean;
  contact_nom: string | null;
  contact_email: string | null;
}

// 5. GET /api/prospects/{slug}
export interface ProspectDetail {
  fiche: Prospect & Record<string, unknown>;
  rapport_md: string | null;
}

// 6. GET /api/usage
export interface UsageFournisseur {
  fournisseur: string;
  nb_appels: number;
  cout_total: number;
  unites: number;
}

export interface UsageTopFiche {
  fiche: string;
  cout: number;
}

export interface Usage {
  cout_total_usd: number;
  devise: string;
  nb_appels: number;
  nb_cache_hits: number;
  taux_cache: number;
  par_fournisseur: UsageFournisseur[];
  top_fiches: UsageTopFiche[];
}

// 9. GET /api/greenit — observabilité d'efficience (coût / énergie / CO2e).
// ⚠️ energie_wh et co2e_g sont des ESTIMATIONS issues des facteurs
// paramétrables de knowledge/greenit.yaml, jamais des mesures certifiées.
// Le backend le déclare lui-même via `estimation` / `note_estimation`.
export interface GreenitParModele {
  modele: string;
  nb_appels: number;
  tokens: number;
  cout: number;
  energie_wh: number;
  co2e_g: number;
  octets: number;
  duree_ms: number;
}

export interface GreenitParFournisseur {
  fournisseur: string;
  nb_appels: number;
  tokens: number;
  cout: number;
  energie_wh: number;
  co2e_g: number;
  octets: number;
  duree_ms: number;
}

export interface GreenitEconomies {
  appels_evites: number;
  cout_evite_usd: number;
  energie_wh_evitee: number;
  co2e_evite_g: number;
  methode: string;
}

export interface Greenit {
  cout_total_usd: number;
  devise: string;
  energie_wh_total: number;
  co2e_g_total: number;
  octets_total: number;
  duree_ms_totale: number;
  nb_appels: number;
  nb_cache_hits: number;
  nb_erreurs: number;
  nb_lignes_illisibles: number;
  taux_cache: number;
  economies: GreenitEconomies;
  par_modele: GreenitParModele[];
  par_fournisseur: GreenitParFournisseur[];
  estimation: boolean;
  note_estimation: string;
  source_facteurs: string;
  couverture_greenit: number;
  ledger_present: boolean;
  ledger_path: string;
}

// 10. GET /api/greenit/stream (SSE) — un événement `appel` par ligne de ledger.
export interface GreenitAppel {
  ts: string | null;
  fournisseur: string;
  endpoint: string;
  unites: Record<string, number>;
  tokens: number;
  cout_estime: number;
  devise: string;
  fiche: string | null;
  cache_hit: boolean;
  resultat: string;
  detail: string;
  modele: string | null;
  profil: string | null;
  octets_entrants: number;
  octets_sortants: number;
  octets: number;
  duree_ms: number;
  energie_wh: number;
  co2e_g: number;
  greenit_instrumente: boolean;
}

// État de la liaison temps réel, affiché tel quel dans l'écran GreenIT.
export type EtatFlux =
  | "connexion"
  | "connecte"
  | "polling"
  | "deconnecte"
  | "termine";

// 7. GET /api/icp
export interface Icp {
  icp_id: string;
  persona: number;
  marche: string;
  description: string;
}

// 8. GET /api/runs
export interface RunEntry {
  [key: string]: unknown;
}

export interface ProspectFilters {
  statut?: Statut;
  persona?: number;
  marche?: string;
}
