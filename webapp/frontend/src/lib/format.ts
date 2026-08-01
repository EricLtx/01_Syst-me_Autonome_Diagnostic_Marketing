// format.ts — helpers d'affichage (chiffres, devises, libellés de statut).

import type { Statut } from "../types";

export const STATUT_LABEL: Record<Statut, string> = {
  decouvert: "Découvert",
  diagnostique: "Diagnostiqué",
  valide: "Validé",
  contacte: "Contacté",
  rejete: "Rejeté",
};

export const STATUTS: Statut[] = [
  "decouvert",
  "diagnostique",
  "valide",
  "contacte",
  "rejete",
];

export function fmtUsd(n: number, devise = "USD"): string {
  const sym = devise === "USD" ? "$" : devise === "EUR" ? "€" : "";
  return `${sym}${n.toFixed(2)}`;
}

export function fmtPct(ratio: number): string {
  return `${(ratio * 100).toFixed(0)}%`;
}

export function fmtInt(n: number): string {
  return n.toLocaleString("fr-CA");
}

export function scoreClass(score: number | null): string {
  if (score == null) return "s-na";
  if (score >= 70) return "s-hi";
  if (score >= 45) return "s-mid";
  return "s-lo";
}

export function fmtDate(d: string | null): string {
  if (!d) return "—";
  return d.slice(0, 10);
}
