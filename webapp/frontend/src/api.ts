// api.ts — client API typé. En MODE MOCK (VITE_USE_MOCKS !== "false"), renvoie
// les fixtures locales sans toucher le réseau : l'app tourne et se build sans
// backend. Sinon, fetch vers /api (proxifié par Vite vers localhost:8000).

import type {
  Funnel,
  Health,
  Icp,
  Preflight,
  Prospect,
  ProspectDetail,
  ProspectFilters,
  RunEntry,
  Usage,
} from "./types";

import {
  mockFunnel,
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
};
