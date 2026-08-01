// api.ts — client API typé. En MODE MOCK (VITE_USE_MOCKS !== "false"), renvoie
// les fixtures locales sans toucher le réseau : l'app tourne et se build sans
// backend. Sinon, fetch vers /api (proxifié par Vite vers localhost:8000).

import type {
  EtatFlux,
  Funnel,
  Greenit,
  GreenitAppel,
  Health,
  Icp,
  Preflight,
  Prospect,
  ProspectDetail,
  ProspectFilters,
  RunEntry,
  Usage,
} from "./types";

import { parseAppel } from "./lib/greenit";

import {
  mockFunnel,
  mockGreenit,
  mockGreenitAppels,
  mockHealth,
  mockIcps,
  mockPreflight,
  mockProspectDetail,
  mockProspects,
  mockRuns,
  mockUsage,
} from "./mocks/fixtures";

// Défaut = mocks activés. On ne bascule sur le vrai backend que si la variable
// vaut explicitement "false".
export const USE_MOCKS: boolean =
  (import.meta.env?.VITE_USE_MOCKS ?? "true") !== "false";

const BASE = "/api";

// Petite latence simulée pour rendre visibles les états de chargement en démo.
function delay<T>(value: T, ms = 120): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} sur ${path}`);
  }
  return (await res.json()) as T;
}

function queryString(params: Record<string, string | number | undefined>): string {
  const usp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") usp.set(k, String(v));
  }
  const s = usp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  async health(): Promise<Health> {
    if (USE_MOCKS) return delay(mockHealth);
    return get<Health>("/health");
  },

  async preflight(icp?: string): Promise<Preflight> {
    if (USE_MOCKS) return delay(mockPreflight);
    return get<Preflight>(`/preflight${queryString({ icp })}`);
  },

  async funnel(): Promise<Funnel> {
    if (USE_MOCKS) return delay(mockFunnel);
    return get<Funnel>("/pipeline/funnel");
  },

  async prospects(filters: ProspectFilters = {}): Promise<Prospect[]> {
    if (USE_MOCKS) {
      const filtered = mockProspects.filter((p) => {
        if (filters.statut && p.statut !== filters.statut) return false;
        if (filters.persona !== undefined && p.persona !== filters.persona) return false;
        if (filters.marche && p.marche !== filters.marche) return false;
        return true;
      });
      return delay(filtered);
    }
    return get<Prospect[]>(
      `/prospects${queryString({
        statut: filters.statut,
        persona: filters.persona,
        marche: filters.marche,
      })}`,
    );
  },

  async prospect(slug: string): Promise<ProspectDetail> {
    if (USE_MOCKS) {
      const detail = mockProspectDetail(slug);
      if (!detail) throw new Error(`Prospect introuvable : ${slug}`);
      return delay(detail);
    }
    return get<ProspectDetail>(`/prospects/${encodeURIComponent(slug)}`);
  },

  async usage(depuis?: string): Promise<Usage> {
    if (USE_MOCKS) return delay(mockUsage);
    return get<Usage>(`/usage${queryString({ depuis })}`);
  },

  async icp(): Promise<Icp[]> {
    if (USE_MOCKS) return delay(mockIcps);
    return get<Icp[]>("/icp");
  },

  async runs(limit = 50): Promise<RunEntry[]> {
    if (USE_MOCKS) return delay(mockRuns.slice(0, limit));
    return get<RunEntry[]>(`/runs${queryString({ limit })}`);
  },

  async greenit(depuis?: string): Promise<Greenit> {
    if (USE_MOCKS) return delay(mockGreenit);
    return get<Greenit>(`/greenit${queryString({ depuis })}`);
  },
};

// ---------------------------------------------------------------------------
// Flux temps réel GreenIT (SSE) — avec repli en polling
// ---------------------------------------------------------------------------
// Trois régimes, choisis dans cet ordre :
//   1. MOCK          → rejeu périodique des fixtures, aucune connexion.
//   2. SSE           → EventSource sur /api/greenit/stream (temps réel réel).
//   3. POLLING       → si EventSource est indisponible (vieux navigateur, jsdom)
//                      ou si la connexion échoue : on interroge /api/greenit à
//                      intervalle fixe. L'écran l'annonce, il ne fait pas
//                      semblant d'être « en direct ».

export interface OptionsFluxGreenit {
  onAppel: (appel: GreenitAppel) => void;
  onEtat: (etat: EtatFlux) => void;
  /** Appelé par le repli polling avec un agrégat frais. */
  onAgregat?: (agregat: Greenit) => void;
  /** Nombre d'appels déjà journalisés à rejouer à l'ouverture. */
  historique?: number;
  /** Période du repli polling, en ms. */
  periodePollingMs?: number;
}

export interface AbonnementGreenit {
  fermer: () => void;
}

const MOCK_PERIODE_MS = 2500;
const MOCK_DELAI_INITIAL_MS = 1200;

export function souscrireGreenit(opts: OptionsFluxGreenit): AbonnementGreenit {
  const {
    onAppel,
    onEtat,
    onAgregat,
    historique = 25,
    periodePollingMs = 10_000,
  } = opts;

  // --- 1. Mode mock : flux simulé, déterministe, hors-ligne ---------------
  if (USE_MOCKS) {
    let i = 0;
    let intervalle: ReturnType<typeof setInterval> | undefined;
    const amorce = setTimeout(() => {
      onEtat("connecte");
      intervalle = setInterval(() => {
        const modele = mockGreenitAppels[i % mockGreenitAppels.length];
        i += 1;
        onAppel({ ...modele, ts: new Date().toISOString() });
      }, MOCK_PERIODE_MS);
    }, MOCK_DELAI_INITIAL_MS);

    return {
      fermer: () => {
        clearTimeout(amorce);
        if (intervalle) clearInterval(intervalle);
      },
    };
  }

  let ferme = false;
  let source: EventSource | null = null;
  let sondage: ReturnType<typeof setInterval> | undefined;

  // --- 3. Repli polling ---------------------------------------------------
  function demarrerPolling() {
    if (ferme || sondage) return;
    onEtat("polling");
    const tirer = () => {
      api
        .greenit()
        .then((g) => {
          if (!ferme) onAgregat?.(g);
        })
        .catch(() => {
          if (!ferme) onEtat("deconnecte");
        });
    };
    tirer();
    sondage = setInterval(tirer, periodePollingMs);
  }

  // --- 2. SSE -------------------------------------------------------------
  if (typeof EventSource === "undefined") {
    demarrerPolling();
  } else {
    onEtat("connexion");
    const qs = queryString({ historique, heartbeat_s: 15, duree_max_s: 3600 });
    source = new EventSource(`${BASE}/greenit/stream${qs}`);

    source.addEventListener("init", () => onEtat("connecte"));
    source.addEventListener("heartbeat", () => onEtat("connecte"));
    source.addEventListener("appel", (e) => {
      const appel = parseAppel((e as MessageEvent).data);
      if (appel) onAppel(appel);
    });
    source.addEventListener("fin", () => {
      // Le serveur borne la durée de vie du flux : on bascule en polling
      // plutôt que de laisser l'écran figé en « connecté ».
      source?.close();
      source = null;
      if (!ferme) demarrerPolling();
    });
    source.onerror = () => {
      // EventSource retente seul ; au-delà d'un état CLOSED, on replie.
      if (ferme) return;
      if (source && source.readyState === 2 /* CLOSED */) {
        source = null;
        demarrerPolling();
      } else {
        onEtat("connexion");
      }
    };
  }

  return {
    fermer: () => {
      ferme = true;
      if (sondage) clearInterval(sondage);
      source?.close();
      source = null;
    },
  };
}
