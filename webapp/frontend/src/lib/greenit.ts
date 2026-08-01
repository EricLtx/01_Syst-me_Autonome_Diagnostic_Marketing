// greenit.ts — fonctions PURES de l'écran d'efficience : parsing défensif des
// événements SSE, agrégation incrémentale côté client, formatage des unités.
//
// Pourquoi une agrégation côté client : le flux temps réel doit faire bouger
// les tuiles sans attendre un nouvel appel à /api/greenit. On applique donc
// chaque événement reçu sur le dernier agrégat connu, avec exactement les mêmes
// conventions que le backend (un cache-hit n'est pas un appel ; un appel
// `budget_depasse` n'a rien dépensé).
//
// ⚠️ energie_wh / co2e_g restent des ESTIMATIONS (facteurs de
// knowledge/greenit.yaml) — ces fonctions ne font que les additionner.

import type { Greenit, GreenitAppel } from "../types";

function nombre(v: unknown, defaut = 0): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v);
    if (Number.isFinite(n)) return n;
  }
  return defaut;
}

function texte(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const t = v.trim();
  return t === "" ? null : t;
}

/**
 * Normalise un événement `appel` du flux SSE.
 * Défensif par contrat : les champs GreenIT sont optionnels côté ledger, et
 * une charge utile inattendue ne doit jamais casser l'écran (→ null).
 */
export function parseAppel(brut: string | unknown): GreenitAppel | null {
  let obj: unknown = brut;
  if (typeof brut === "string") {
    try {
      obj = JSON.parse(brut);
    } catch {
      return null;
    }
  }
  if (obj === null || typeof obj !== "object" || Array.isArray(obj)) return null;
  const o = obj as Record<string, unknown>;

  const unites: Record<string, number> = {};
  if (o.unites && typeof o.unites === "object" && !Array.isArray(o.unites)) {
    for (const [k, v] of Object.entries(o.unites as Record<string, unknown>)) {
      unites[k] = nombre(v);
    }
  }
  const tokensCalcules = Object.entries(unites)
    .filter(([k]) => k.toLowerCase().includes("token"))
    .reduce((s, [, v]) => s + v, 0);

  const octetsEntrants = nombre(o.octets_entrants);
  const octetsSortants = nombre(o.octets_sortants);

  return {
    ts: texte(o.ts),
    fournisseur: texte(o.fournisseur) ?? "inconnu",
    endpoint: texte(o.endpoint) ?? "",
    unites,
    tokens: nombre(o.tokens, tokensCalcules),
    cout_estime: nombre(o.cout_estime),
    devise: texte(o.devise) ?? "USD",
    fiche: texte(o.fiche),
    cache_hit: o.cache_hit === true,
    resultat: texte(o.resultat) ?? "ok",
    detail: typeof o.detail === "string" ? o.detail : "",
    modele: texte(o.modele),
    profil: texte(o.profil),
    octets_entrants: octetsEntrants,
    octets_sortants: octetsSortants,
    octets: nombre(o.octets, octetsEntrants + octetsSortants),
    duree_ms: nombre(o.duree_ms),
    energie_wh: nombre(o.energie_wh),
    co2e_g: nombre(o.co2e_g),
    greenit_instrumente: o.greenit_instrumente === true,
  };
}

/** Clé d'identité d'un appel dans le flux (évite les doublons de rejeu). */
export function cleAppel(a: GreenitAppel, index: number): string {
  return `${a.ts ?? "?"}|${a.fournisseur}|${a.endpoint}|${index}`;
}

/**
 * Applique un appel reçu en direct sur l'agrégat courant (immutable).
 * Mêmes règles que le backend : cache-hit → pas un appel ; `budget_depasse` →
 * compté en appel mais sans coût ni empreinte (aucun octet n'a circulé).
 */
export function appliquerAppel(base: Greenit, appel: GreenitAppel): Greenit {
  const suivant: Greenit = {
    ...base,
    economies: { ...base.economies },
    par_modele: base.par_modele.map((m) => ({ ...m })),
    par_fournisseur: base.par_fournisseur.map((f) => ({ ...f })),
  };

  if (appel.cache_hit) {
    suivant.nb_cache_hits += 1;
    suivant.economies.appels_evites += 1;
    // Économie estimée = moyenne observée des appels réels déjà agrégés.
    if (suivant.nb_appels > 0) {
      suivant.economies.cout_evite_usd += suivant.cout_total_usd / suivant.nb_appels;
      suivant.economies.energie_wh_evitee +=
        suivant.energie_wh_total / suivant.nb_appels;
      suivant.economies.co2e_evite_g += suivant.co2e_g_total / suivant.nb_appels;
    }
    suivant.taux_cache = tauxCache(suivant.nb_appels, suivant.nb_cache_hits);
    return suivant;
  }

  suivant.nb_appels += 1;
  if (appel.resultat === "erreur") suivant.nb_erreurs += 1;
  suivant.taux_cache = tauxCache(suivant.nb_appels, suivant.nb_cache_hits);
  if (appel.resultat === "budget_depasse") return suivant;

  suivant.cout_total_usd += appel.cout_estime;
  suivant.energie_wh_total += appel.energie_wh;
  suivant.co2e_g_total += appel.co2e_g;
  suivant.octets_total += appel.octets;
  suivant.duree_ms_totale += appel.duree_ms;

  const modele = appel.modele ?? "non-llm";
  const ligneM = suivant.par_modele.find((m) => m.modele === modele);
  if (ligneM) {
    ligneM.nb_appels += 1;
    ligneM.tokens += appel.tokens;
    ligneM.cout += appel.cout_estime;
    ligneM.energie_wh += appel.energie_wh;
    ligneM.co2e_g += appel.co2e_g;
    ligneM.octets += appel.octets;
    ligneM.duree_ms += appel.duree_ms;
  } else {
    suivant.par_modele.push({
      modele,
      nb_appels: 1,
      tokens: appel.tokens,
      cout: appel.cout_estime,
      energie_wh: appel.energie_wh,
      co2e_g: appel.co2e_g,
      octets: appel.octets,
      duree_ms: appel.duree_ms,
    });
  }

  const ligneF = suivant.par_fournisseur.find(
    (f) => f.fournisseur === appel.fournisseur,
  );
  if (ligneF) {
    ligneF.nb_appels += 1;
    ligneF.tokens += appel.tokens;
    ligneF.cout += appel.cout_estime;
    ligneF.energie_wh += appel.energie_wh;
    ligneF.co2e_g += appel.co2e_g;
    ligneF.octets += appel.octets;
    ligneF.duree_ms += appel.duree_ms;
  } else {
    suivant.par_fournisseur.push({
      fournisseur: appel.fournisseur,
      nb_appels: 1,
      tokens: appel.tokens,
      cout: appel.cout_estime,
      energie_wh: appel.energie_wh,
      co2e_g: appel.co2e_g,
      octets: appel.octets,
      duree_ms: appel.duree_ms,
    });
  }

  suivant.par_modele.sort((a, b) => b.cout - a.cout || a.modele.localeCompare(b.modele));
  suivant.par_fournisseur.sort(
    (a, b) => b.cout - a.cout || a.fournisseur.localeCompare(b.fournisseur),
  );
  return suivant;
}

export function tauxCache(nbAppels: number, nbCacheHits: number): number {
  const total = nbAppels + nbCacheHits;
  return total > 0 ? nbCacheHits / total : 0;
}

// ---------------------------------------------------------------------------
// Formatage — unités physiques lisibles, sans jamais mentir sur la précision
// ---------------------------------------------------------------------------

/** Octets → Ko/Mo/Go (base 1024), 1 décimale au-delà du kilo. */
export function fmtOctets(n: number): string {
  const abs = Math.abs(n);
  if (abs < 1024) return `${Math.round(n)} o`;
  if (abs < 1024 ** 2) return `${(n / 1024).toFixed(1)} Ko`;
  if (abs < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} Mo`;
  return `${(n / 1024 ** 3).toFixed(2)} Go`;
}

/** Wh → mWh sous 1 Wh, kWh au-delà de 1000. */
export function fmtWh(n: number): string {
  const abs = Math.abs(n);
  if (abs === 0) return "0 Wh";
  if (abs < 1) return `${(n * 1000).toFixed(0)} mWh`;
  if (abs < 1000) return `${n.toFixed(2)} Wh`;
  return `${(n / 1000).toFixed(2)} kWh`;
}

/** Grammes de CO2e → g sous 1 kg, kg au-delà. */
export function fmtCo2(n: number): string {
  const abs = Math.abs(n);
  if (abs === 0) return "0 g";
  if (abs < 1) return `${(n * 1000).toFixed(0)} mg`;
  if (abs < 1000) return `${n.toFixed(2)} g`;
  return `${(n / 1000).toFixed(2)} kg`;
}

/** Millisecondes → ms / s / min. */
export function fmtDuree(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)} ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)} s`;
  return `${(ms / 60_000).toFixed(1)} min`;
}

/** Heure locale HH:MM:SS depuis un ts ISO (— si absent/illisible). */
export function fmtHeure(ts: string | null): string {
  if (!ts) return "—";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts.slice(11, 19) || "—";
  return d.toLocaleTimeString("fr-CA", { hour12: false });
}
