// greenit.test.tsx — écran GreenIT en mode mock + agrégation incrémentale.
//
// Deux volets :
//   1. RENDU — l'écran charge l'agrégat, affiche les tuiles, les économies de
//      cache, l'état de la liaison temps réel, et surtout l'AVERTISSEMENT que
//      énergie/CO2e sont des estimations (exigence anti-hallucination).
//   2. LOGIQUE PURE — parsing défensif des événements SSE et agrégation
//      incrémentale côté client, testés sans DOM.

import { describe, expect, it } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { GreenIT } from "../pages/GreenIT";
import { api } from "../api";
import {
  appliquerAppel,
  fmtCo2,
  fmtOctets,
  fmtWh,
  parseAppel,
  tauxCache,
} from "../lib/greenit";
import { mockGreenit, mockGreenitAppels } from "../mocks/fixtures";
import type { GreenitAppel } from "../types";

function renderGreenIT() {
  return render(
    <MemoryRouter>
      <GreenIT />
    </MemoryRouter>,
  );
}

describe("écran GreenIT (mode mock)", () => {
  it("affiche le titre et les tuiles d'efficience", async () => {
    renderGreenIT();
    expect(screen.getByRole("heading", { name: /GreenIT/i })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText(/\$12\.47/)).toBeInTheDocument());
    // Énergie, CO2e et octets, formatés dans leur unité lisible.
    expect(screen.getByText(fmtWh(mockGreenit.energie_wh_total))).toBeInTheDocument();
    expect(screen.getByText(fmtCo2(mockGreenit.co2e_g_total))).toBeInTheDocument();
    expect(screen.getByText(fmtOctets(mockGreenit.octets_total))).toBeInTheDocument();
    expect(screen.getByText("31%")).toBeInTheDocument(); // taux de cache (96/310)
  });

  it("affiche l'avertissement ESTIMATION et la source des facteurs", async () => {
    renderGreenIT();
    // Le bandeau est rendu immédiatement, avant même l'agrégat.
    expect(screen.getByRole("note")).toBeInTheDocument();
    expect(
      screen.getByText(/sont des estimations/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/knowledge\/greenit\.yaml/).length).toBeGreaterThan(0);
    // Ces chiffres ne sont jamais présentés comme un bilan opposable.
    expect(screen.getByText(/bilan carbone opposable/i)).toBeInTheDocument();
  });

  it("affiche l'encart d'économies réalisées par le cache", async () => {
    renderGreenIT();
    const encart = await screen.findByRole("region", {
      name: /Économies réalisées par le cache/i,
    });
    const dans = within(encart);
    expect(dans.getByText(/Appels évités/i)).toBeInTheDocument();
    expect(dans.getByText("96")).toBeInTheDocument();
    expect(dans.getByText(/\$5\.59/)).toBeInTheDocument();
    // La méthode d'estimation accompagne le chiffre.
    expect(dans.getByText(/ESTIMATION — chaque cache-hit/)).toBeInTheDocument();
  });

  it("affiche l'état de la liaison temps réel et le flux en attente", async () => {
    renderGreenIT();
    const etats = await screen.findAllByRole("status");
    expect(etats.length).toBeGreaterThan(0);
    // Tant qu'aucun appel n'est arrivé, l'écran le dit au lieu d'inventer.
    await waitFor(() =>
      expect(screen.getByText(/En attente d’un appel d’API/)).toBeInTheDocument(),
    );
  });

  it("ventile par modèle et par fournisseur avec des barres accessibles", async () => {
    renderGreenIT();
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /Par modèle/i })).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("heading", { name: /Par fournisseur/i }),
    ).toBeInTheDocument();
    // Chaque barre porte un aria-label chiffré (lisible au lecteur d'écran).
    const barres = screen.getAllByRole("img");
    expect(barres.length).toBe(
      mockGreenit.par_modele.length + mockGreenit.par_fournisseur.length,
    );
    expect(
      screen.getByRole("img", { name: /claude-haiku-4-5/ }),
    ).toBeInTheDocument();
  });
});

describe("client api — greenit (mode mock)", () => {
  it("renvoie un agrégat étiqueté « estimation »", async () => {
    const g = await api.greenit();
    expect(g.estimation).toBe(true);
    expect(g.note_estimation).toMatch(/ESTIMATION/);
    expect(g.source_facteurs).toBe("knowledge/greenit.yaml");
  });

  it("expose des économies cohérentes avec le nombre de cache-hits", async () => {
    const g = await api.greenit();
    expect(g.economies.appels_evites).toBe(g.nb_cache_hits);
    expect(g.taux_cache).toBeCloseTo(
      tauxCache(g.nb_appels, g.nb_cache_hits),
      2,
    );
  });
});

describe("parseAppel — parsing défensif du flux SSE", () => {
  it("applique des défauts à 0/null quand les champs GreenIT sont absents", () => {
    // Cas réel : ancienne ligne de ledger, écrite avant l'instrumentation.
    const a = parseAppel(
      JSON.stringify({
        ts: "2026-01-10T10:00:00+00:00",
        fournisseur: "serp",
        endpoint: "search",
        unites: { requetes: 1 },
        cout_estime: 0.01,
      }),
    );
    expect(a).not.toBeNull();
    expect(a!.energie_wh).toBe(0);
    expect(a!.co2e_g).toBe(0);
    expect(a!.octets).toBe(0);
    expect(a!.duree_ms).toBe(0);
    expect(a!.modele).toBeNull();
    expect(a!.profil).toBeNull();
    expect(a!.cache_hit).toBe(false);
  });

  it("déduit les tokens des unités et somme les octets", () => {
    const a = parseAppel({
      fournisseur: "anthropic",
      endpoint: "messages",
      unites: { input_tokens: 1000, output_tokens: 250, requetes: 1 },
      octets_entrants: 4000,
      octets_sortants: 1000,
      modele: "claude-haiku-4-5",
    });
    expect(a!.tokens).toBe(1250); // les "requetes" ne sont pas des tokens
    expect(a!.octets).toBe(5000);
    expect(a!.modele).toBe("claude-haiku-4-5");
  });

  it("ne casse pas sur une charge utile invalide", () => {
    expect(parseAppel("pas du json")).toBeNull();
    expect(parseAppel("[1,2,3]")).toBeNull();
    expect(parseAppel("null")).toBeNull();
    // Valeur numérique aberrante → 0, jamais NaN.
    const a = parseAppel({ fournisseur: "serp", energie_wh: "beaucoup" });
    expect(a!.energie_wh).toBe(0);
  });
});

describe("appliquerAppel — agrégation incrémentale côté client", () => {
  const vide = {
    ...mockGreenit,
    cout_total_usd: 0,
    energie_wh_total: 0,
    co2e_g_total: 0,
    octets_total: 0,
    duree_ms_totale: 0,
    nb_appels: 0,
    nb_cache_hits: 0,
    nb_erreurs: 0,
    taux_cache: 0,
    economies: {
      appels_evites: 0,
      cout_evite_usd: 0,
      energie_wh_evitee: 0,
      co2e_evite_g: 0,
      methode: "",
    },
    par_modele: [],
    par_fournisseur: [],
  };

  const llm = mockGreenitAppels[0]; // anthropic / claude-haiku-4-5
  const places = mockGreenitAppels[1]; // google_places
  const cache = mockGreenitAppels[2]; // cache-hit serp
  const budget = mockGreenitAppels[5]; // budget_depasse

  it("cumule un appel réel dans les totaux et les ventilations", () => {
    const g = appliquerAppel(vide, llm);
    expect(g.nb_appels).toBe(1);
    expect(g.cout_total_usd).toBeCloseTo(llm.cout_estime, 6);
    expect(g.energie_wh_total).toBeCloseTo(llm.energie_wh, 6);
    expect(g.octets_total).toBe(llm.octets);
    expect(g.par_modele).toHaveLength(1);
    expect(g.par_modele[0].modele).toBe("claude-haiku-4-5");
    expect(g.par_fournisseur[0].fournisseur).toBe("anthropic");
    // Immutabilité : l'agrégat d'origine n'a pas bougé.
    expect(vide.nb_appels).toBe(0);
    expect(vide.par_modele).toHaveLength(0);
  });

  it("range les appels non-LLM sous « non-llm » et fusionne les répétitions", () => {
    let g = appliquerAppel(vide, places);
    g = appliquerAppel(g, places);
    expect(g.nb_appels).toBe(2);
    expect(g.par_modele).toHaveLength(1);
    expect(g.par_modele[0].modele).toBe("non-llm");
    expect(g.par_modele[0].nb_appels).toBe(2);
    expect(g.par_fournisseur[0].nb_appels).toBe(2);
  });

  it("compte un cache-hit comme appel évité, pas comme appel", () => {
    let g = appliquerAppel(vide, llm);
    g = appliquerAppel(g, cache);
    expect(g.nb_appels).toBe(1);
    expect(g.nb_cache_hits).toBe(1);
    expect(g.taux_cache).toBeCloseTo(0.5, 6);
    expect(g.economies.appels_evites).toBe(1);
    // Économie estimée = moyenne des appels réels déjà vus (ici, le seul).
    expect(g.economies.cout_evite_usd).toBeCloseTo(llm.cout_estime, 6);
    expect(g.economies.co2e_evite_g).toBeCloseTo(llm.co2e_g, 6);
    // Un cache-hit ne dépense rien : totaux inchangés.
    expect(g.cout_total_usd).toBeCloseTo(llm.cout_estime, 6);
  });

  it("compte un refus de budget en appel sans lui imputer coût ni empreinte", () => {
    const g = appliquerAppel(vide, budget);
    expect(g.nb_appels).toBe(1);
    expect(g.cout_total_usd).toBe(0);
    expect(g.energie_wh_total).toBe(0);
    expect(g.par_fournisseur).toHaveLength(0);
  });

  it("trie les ventilations par coût décroissant", () => {
    let g = appliquerAppel(vide, places); // 0.017
    g = appliquerAppel(g, mockGreenitAppels[3] as GreenitAppel); // sonnet, 0.0462
    expect(g.par_fournisseur[0].fournisseur).toBe("anthropic");
    expect(g.par_modele[0].modele).toBe("claude-sonnet-4-5");
  });
});

describe("formatage des unités physiques", () => {
  it("choisit l'échelle lisible pour les octets", () => {
    expect(fmtOctets(512)).toBe("512 o");
    expect(fmtOctets(2048)).toBe("2.0 Ko");
    expect(fmtOctets(5 * 1024 * 1024)).toBe("5.0 Mo");
  });

  it("choisit l'échelle lisible pour l'énergie et le CO2e", () => {
    expect(fmtWh(0)).toBe("0 Wh");
    expect(fmtWh(0.216)).toBe("216 mWh");
    expect(fmtWh(41.8)).toBe("41.80 Wh");
    expect(fmtWh(2500)).toBe("2.50 kWh");
    expect(fmtCo2(0.036)).toBe("36 mg");
    expect(fmtCo2(6.94)).toBe("6.94 g");
    expect(fmtCo2(1500)).toBe("1.50 kg");
  });
});
