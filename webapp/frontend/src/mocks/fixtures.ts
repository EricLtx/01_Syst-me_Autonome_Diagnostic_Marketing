// fixtures.ts — jeu de données réaliste pour le MODE MOCK.
// Reflète l'AS-IS du système : préflight NO-GO (tarifs à 0, budgets à 0,
// clés API absentes) mais tests verts. 8 prospects couvrant tous les statuts
// et les 2 personas, un funnel cohérent, un usage à 3 fournisseurs.

import type {
  Funnel,
  Greenit,
  GreenitAppel,
  Health,
  Icp,
  Preflight,
  Prospect,
  ProspectDetail,
  RunEntry,
  Usage,
} from "../types";

export const mockHealth: Health = {
  status: "ok",
  vault_path: "vault",
  vault_initialise: true,
};

export const mockIcps: Icp[] = [
  {
    icp_id: "persona1-quebec",
    persona: 1,
    marche: "quebec",
    description:
      "Détaillant / installateur HVAC (climatisation, chauffage, thermopompe) — Québec",
  },
  {
    icp_id: "persona1-romandie",
    persona: 1,
    marche: "romandie",
    description:
      "Installateur chauffage / pompe à chaleur — Suisse romande (déploiement séquence 2)",
  },
  {
    icp_id: "persona2-france",
    persona: 2,
    marche: "france",
    description: "Agence de services B2B locale — France (persona secondaire)",
  },
];

// Préflight NO-GO réaliste : les 9 contrôles. Bloquants en échec = clés API,
// tarifs réels non renseignés (=0), budgets à 0. tests_verts (warn) OK.
export const mockPreflight: Preflight = {
  verdict: "NO-GO",
  checks: [
    {
      nom: "cles_api",
      niveau: "bloquant",
      ok: false,
      message:
        "Clés obligatoires absentes de l'environnement : SERP_API_KEY, APOLLO_API_KEY.",
    },
    {
      nom: "tarifs_reels",
      niveau: "bloquant",
      ok: false,
      message:
        "Tarifs non relevés (prix_par_unite = 0) : serp.recherche, apollo.enrichissement. Éditer knowledge/api_pricing.yaml.",
    },
    {
      nom: "tarifs_reels_date",
      niveau: "bloquant",
      ok: false,
      message: "Champ releve_le absent — date de relevé des tarifs non documentée.",
    },
    {
      nom: "budgets",
      niveau: "bloquant",
      ok: false,
      message:
        "Budgets de garde-fou à 0 : serp.unites_max.requetes, apollo.unites_max.credits. Borner le pilote avant tout run.",
    },
    {
      nom: "vault_initialise",
      niveau: "bloquant",
      ok: true,
      message: "Vault présent et scaffoldé (vault/).",
    },
    {
      nom: "cache_hors_vault",
      niveau: "bloquant",
      ok: true,
      message: "Cache de scraping situé hors du vault (.cache/api_io).",
    },
    {
      nom: "garde_fous_bus",
      niveau: "bloquant",
      ok: true,
      message:
        "AST walk OK : aucun import réseau (requests/anthropic) hors api_io.py.",
    },
    {
      nom: "icp_valide",
      niveau: "bloquant",
      ok: true,
      message: "ICP persona1-quebec chargé et validé (IcpConfig).",
    },
    {
      nom: "tests_verts",
      niveau: "warn",
      ok: true,
      message: "Suite de tests : 365 passés (dernier run local).",
    },
  ],
};

export const mockFunnel: Funnel = {
  total: 34,
  etats: {
    decouvert: 12,
    diagnostique: 9,
    valide: 7,
    contacte: 4,
    rejete: 2,
  },
};

const RAPPORT_TREMBLAY = `# Audit de marque — Climatisation Tremblay

**Score global : 42 / 100** — signal chaud

## Synthèse

Entreprise HVAC bien implantée à Québec mais dont la présence numérique
est en net retard sur ses concurrents directs. Le site existe mais ne
convertit pas : pas de preuve sociale, référencement local faible,
aucune fiche Google à jour.

## Failles majeures

- **SEO local absent** : aucune balise de localité, pas de mots-clés
  \`thermopompe Québec\`. Invisibilité sur les recherches géolocalisées.
- **Aucune preuve sociale** : zéro avis affiché, pas de témoignages.
- **Fiche Google non vérifiée** : établissement non revendiqué.

## Signaux collectés

| Signal | Valeur |
|---|---|
| Site répond | oui (200) |
| Dernière mise à jour | > 18 mois |
| Répond aux avis | non |
| Plateformes sociales | aucune détectée |

## Accroche suggérée

> « Vos concurrents captent les recherches "thermopompe Québec" que vous
> laissez filer — un correctif SEO local vous rendrait visible en 3 semaines. »
`;

export const mockProspects: Prospect[] = [
  {
    slug: "climatisation-tremblay",
    nom: "Climatisation Tremblay",
    site_web: "https://climatisation-tremblay.example",
    statut: "valide",
    persona: 1,
    marche: "quebec",
    score_global: 42,
    signal_chaud: true,
    gaps_majeurs: ["SEO local absent", "Aucune preuve sociale", "Fiche Google non vérifiée"],
    date_creation: "2026-07-12",
    date_diagnostic: "2026-07-14",
    icp_id: "persona1-quebec",
    opt_out: false,
    contact_nom: "Marc Tremblay",
    contact_email: "marc@climatisation-tremblay.example",
  },
  {
    slug: "thermopompe-levis",
    nom: "Thermopompe Lévis Inc.",
    site_web: "https://thermopompe-levis.example",
    statut: "valide",
    persona: 1,
    marche: "quebec",
    score_global: 58,
    signal_chaud: true,
    gaps_majeurs: ["Pas de blog / contenu", "Temps de chargement élevé"],
    date_creation: "2026-07-10",
    date_diagnostic: "2026-07-13",
    icp_id: "persona1-quebec",
    opt_out: false,
    contact_nom: "Julie Bergeron",
    contact_email: "jbergeron@thermopompe-levis.example",
  },
  {
    slug: "chauffage-sherbrooke",
    nom: "Chauffage Sherbrooke Enr.",
    site_web: "https://chauffage-sherbrooke.example",
    statut: "diagnostique",
    persona: 1,
    marche: "quebec",
    score_global: 71,
    signal_chaud: false,
    gaps_majeurs: ["Mobile non optimisé"],
    date_creation: "2026-07-18",
    date_diagnostic: "2026-07-20",
    icp_id: "persona1-quebec",
    opt_out: false,
    contact_nom: null,
    contact_email: null,
  },
  {
    slug: "climat-plus-laval",
    nom: "Climat Plus Laval",
    site_web: "https://climatplus-laval.example",
    statut: "contacte",
    persona: 1,
    marche: "quebec",
    score_global: 49,
    signal_chaud: true,
    gaps_majeurs: ["SEO local absent", "Aucun appel à l'action"],
    date_creation: "2026-06-28",
    date_diagnostic: "2026-07-02",
    icp_id: "persona1-quebec",
    opt_out: false,
    contact_nom: "Sophie Nadeau",
    contact_email: "sophie@climatplus-laval.example",
  },
  {
    slug: "hvac-longueuil",
    nom: "HVAC Longueuil Services",
    site_web: "https://hvac-longueuil.example",
    statut: "decouvert",
    persona: 1,
    marche: "quebec",
    score_global: null,
    signal_chaud: false,
    gaps_majeurs: [],
    date_creation: "2026-07-25",
    date_diagnostic: null,
    icp_id: "persona1-quebec",
    opt_out: false,
    contact_nom: null,
    contact_email: null,
  },
  {
    slug: "froid-tech-quebec",
    nom: "Froid-Tech Québec",
    site_web: "https://froid-tech.example",
    statut: "rejete",
    persona: 1,
    marche: "quebec",
    score_global: 88,
    signal_chaud: false,
    gaps_majeurs: [],
    date_creation: "2026-07-05",
    date_diagnostic: "2026-07-07",
    icp_id: "persona1-quebec",
    opt_out: true,
    contact_nom: null,
    contact_email: null,
  },
  {
    slug: "chaleur-romande",
    nom: "Chaleur Romande Sàrl",
    site_web: "https://chaleur-romande.example",
    statut: "diagnostique",
    persona: 1,
    marche: "romandie",
    score_global: 63,
    signal_chaud: false,
    gaps_majeurs: ["Pas de version mobile", "Coordonnées difficiles à trouver"],
    date_creation: "2026-07-22",
    date_diagnostic: "2026-07-24",
    icp_id: "persona1-romandie",
    opt_out: false,
    contact_nom: null,
    contact_email: null,
  },
  {
    slug: "agence-relance-france",
    nom: "Agence Relance (Lyon)",
    site_web: "https://agence-relance.example",
    statut: "valide",
    persona: 2,
    marche: "france",
    score_global: 37,
    signal_chaud: true,
    gaps_majeurs: ["Positionnement flou", "Aucune étude de cas", "SEO local absent"],
    date_creation: "2026-07-15",
    date_diagnostic: "2026-07-17",
    icp_id: "persona2-france",
    opt_out: false,
    contact_nom: "Olivier Fontaine",
    contact_email: "o.fontaine@agence-relance.example",
  },
];

const RAPPORTS: Record<string, string> = {
  "climatisation-tremblay": RAPPORT_TREMBLAY,
};

export function mockProspectDetail(slug: string): ProspectDetail | null {
  const p = mockProspects.find((x) => x.slug === slug);
  if (!p) return null;
  const rapport = RAPPORTS[slug] ?? null;
  return {
    fiche: {
      ...p,
      accroche:
        p.gaps_majeurs.length > 0
          ? `Vos concurrents exploitent « ${p.gaps_majeurs[0].toLowerCase()} » à votre place — un correctif ciblé vous remettrait dans la course.`
          : null,
      derniere_maj_site: p.date_diagnostic,
      source_email: p.contact_email ? "apollo" : null,
    },
    rapport_md: rapport,
  };
}

export const mockUsage: Usage = {
  cout_total_usd: 12.47,
  devise: "USD",
  nb_appels: 214,
  nb_cache_hits: 96,
  taux_cache: 0.449,
  par_fournisseur: [
    { fournisseur: "claude", nb_appels: 41, cout_total: 7.83, unites: 128400 },
    { fournisseur: "google_places", nb_appels: 118, cout_total: 3.9, unites: 118 },
    { fournisseur: "serp", nb_appels: 55, cout_total: 0.74, unites: 55 },
  ],
  top_fiches: [
    { fiche: "agence-relance-france", cout: 2.11 },
    { fiche: "climatisation-tremblay", cout: 1.87 },
    { fiche: "thermopompe-levis", cout: 1.42 },
    { fiche: "chaleur-romande", cout: 1.09 },
    { fiche: "climat-plus-laval", cout: 0.94 },
  ],
};

// --- GreenIT ---------------------------------------------------------------
// Agrégat d'efficience cohérent avec mockUsage (mêmes 3 fournisseurs, même
// taux de cache). Les valeurs d'énergie et de CO2e sont des ESTIMATIONS de
// démonstration — la fixture porte elle-même l'avertissement, comme le backend.

export const mockGreenit: Greenit = {
  cout_total_usd: 12.47,
  devise: "USD",
  energie_wh_total: 41.8,
  co2e_g_total: 6.94,
  octets_total: 27_918_336,
  duree_ms_totale: 186_420,
  nb_appels: 214,
  nb_cache_hits: 96,
  nb_erreurs: 3,
  nb_lignes_illisibles: 0,
  // Même formule que le backend : hits / (appels + hits) = 96 / 310.
  taux_cache: 0.3097,
  economies: {
    appels_evites: 96,
    cout_evite_usd: 5.59,
    energie_wh_evitee: 18.75,
    co2e_evite_g: 3.11,
    methode:
      "ESTIMATION — chaque cache-hit est valorisé à la moyenne des appels réels de même (fournisseur, endpoint). Sans appel réel comparable, l'économie est comptée à 0 plutôt qu'extrapolée.",
  },
  par_modele: [
    {
      modele: "claude-haiku-4-5",
      nb_appels: 34,
      tokens: 98_400,
      cout: 4.62,
      energie_wh: 22.1,
      co2e_g: 3.66,
      octets: 4_812_800,
      duree_ms: 91_200,
    },
    {
      modele: "claude-sonnet-4-5",
      nb_appels: 7,
      tokens: 30_000,
      cout: 3.21,
      energie_wh: 12.4,
      co2e_g: 2.06,
      octets: 1_998_848,
      duree_ms: 38_900,
    },
    {
      modele: "non-llm",
      nb_appels: 173,
      tokens: 0,
      cout: 4.64,
      energie_wh: 7.3,
      co2e_g: 1.22,
      octets: 21_106_688,
      duree_ms: 56_320,
    },
  ],
  par_fournisseur: [
    {
      fournisseur: "anthropic",
      nb_appels: 41,
      tokens: 128_400,
      cout: 7.83,
      energie_wh: 34.5,
      co2e_g: 5.72,
      octets: 6_811_648,
      duree_ms: 130_100,
    },
    {
      fournisseur: "google_places",
      nb_appels: 118,
      tokens: 0,
      cout: 3.9,
      energie_wh: 5.2,
      co2e_g: 0.86,
      octets: 15_204_352,
      duree_ms: 38_700,
    },
    {
      fournisseur: "serp",
      nb_appels: 55,
      tokens: 0,
      cout: 0.74,
      energie_wh: 2.1,
      co2e_g: 0.36,
      octets: 5_902_336,
      duree_ms: 17_620,
    },
  ],
  estimation: true,
  note_estimation:
    "energie_wh et co2e_g sont des ESTIMATIONS calculées à partir des facteurs paramétrables de knowledge/greenit.yaml (ordres de grandeur destinés à comparer des scénarios). Ce ne sont pas des mesures certifiées et elles ne constituent pas un bilan carbone opposable.",
  source_facteurs: "knowledge/greenit.yaml",
  couverture_greenit: 0.87,
  ledger_present: true,
  ledger_path: "api_usage.log",
};

function appel(p: Partial<GreenitAppel>): GreenitAppel {
  return {
    ts: new Date().toISOString(),
    fournisseur: "serp",
    endpoint: "search",
    unites: {},
    tokens: 0,
    cout_estime: 0,
    devise: "USD",
    fiche: null,
    cache_hit: false,
    resultat: "ok",
    detail: "",
    modele: null,
    profil: null,
    octets_entrants: 0,
    octets_sortants: 0,
    octets: 0,
    duree_ms: 0,
    energie_wh: 0,
    co2e_g: 0,
    greenit_instrumente: true,
    ...p,
  };
}

// Boucle d'appels rejouée par le flux simulé du mode mock : couvre un appel
// LLM, un appel Places, un cache-hit, une erreur et un refus de budget.
export const mockGreenitAppels: GreenitAppel[] = [
  appel({
    fournisseur: "anthropic",
    endpoint: "messages",
    modele: "claude-haiku-4-5",
    profil: "standard",
    unites: { input_tokens: 1840, output_tokens: 412 },
    tokens: 2252,
    cout_estime: 0.0091,
    fiche: "climatisation-tremblay",
    octets_entrants: 7360,
    octets_sortants: 1648,
    octets: 9008,
    duree_ms: 2140,
    energie_wh: 0.216,
    co2e_g: 0.036,
  }),
  appel({
    fournisseur: "google_places",
    endpoint: "place_details",
    unites: { requetes: 1 },
    cout_estime: 0.017,
    fiche: "thermopompe-levis",
    octets_entrants: 18_432,
    octets_sortants: 512,
    octets: 18_944,
    duree_ms: 310,
    energie_wh: 0.101,
    co2e_g: 0.017,
  }),
  appel({
    fournisseur: "serp",
    endpoint: "search",
    unites: { requetes: 1 },
    cout_estime: 0,
    cache_hit: true,
    fiche: "chauffage-sherbrooke",
    greenit_instrumente: false,
  }),
  appel({
    fournisseur: "anthropic",
    endpoint: "messages",
    modele: "claude-sonnet-4-5",
    profil: "qualite",
    unites: { input_tokens: 3900, output_tokens: 880 },
    tokens: 4780,
    cout_estime: 0.0462,
    fiche: "agence-relance-france",
    octets_entrants: 15_600,
    octets_sortants: 3520,
    octets: 19_120,
    duree_ms: 5210,
    energie_wh: 0.459,
    co2e_g: 0.076,
  }),
  appel({
    fournisseur: "http",
    endpoint: "get",
    unites: { requetes: 1 },
    cout_estime: 0,
    resultat: "erreur",
    detail: "timeout après 10 s",
    fiche: "hvac-longueuil",
    octets_entrants: 0,
    octets_sortants: 340,
    octets: 340,
    duree_ms: 10_000,
    energie_wh: 0.1,
    co2e_g: 0.017,
  }),
  appel({
    fournisseur: "serp",
    endpoint: "search",
    unites: { requetes: 1 },
    cout_estime: 0,
    resultat: "budget_depasse",
    detail: "serp : plafond unités dépassé (requetes : 0.0 + 1.0 > 0)",
    greenit_instrumente: false,
  }),
];

export const mockRuns: RunEntry[] = [
  { ts: "2026-07-25T14:02:11Z", op: "write_fiche", slug: "hvac-longueuil", etat: "decouvert" },
  { ts: "2026-07-24T09:41:03Z", op: "transition", slug: "chaleur-romande", de: "decouvert", vers: "diagnostique" },
  { ts: "2026-07-20T16:12:55Z", op: "transition", slug: "chauffage-sherbrooke", de: "decouvert", vers: "diagnostique" },
  { ts: "2026-07-17T11:08:30Z", op: "transition", slug: "agence-relance-france", de: "diagnostique", vers: "valide" },
  { ts: "2026-07-14T10:22:47Z", op: "transition", slug: "climatisation-tremblay", de: "diagnostique", vers: "valide" },
];
