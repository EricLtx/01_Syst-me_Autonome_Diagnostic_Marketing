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
  persona: number;
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
