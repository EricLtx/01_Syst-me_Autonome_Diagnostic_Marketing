# Cockpit opérateur — Système Autonome de Diagnostic Marketing

SPA React qui donne à l'opératrice (consultante marketing solo) une **vue de
pilotage** en complément d'Obsidian : état du pipeline de prospection B2B,
prospects et leurs diagnostics, coûts API, verdict préflight GO/NO-GO.

C'est un **cockpit** (scanné et opéré), pas un document.

## Stack

React 18 + Vite + TypeScript · react-router-dom · Vitest + @testing-library/react.
CSS maison (design system par variables, thème clair/sombre). Aucune webfont,
aucune dépendance réseau au runtime — l'app est offline-friendly.

## Démarrage rapide (mode mock — sans backend)

```bash
cd webapp/frontend
npm install
npm run dev        # http://localhost:5173 — données de démonstration
```

En mode mock (défaut), le client `src/api.ts` renvoie les fixtures de
`src/mocks/fixtures.ts` : 8 prospects couvrant tous les statuts et les 2
personas, un funnel cohérent, un préflight **NO-GO** réaliste (tarifs à 0,
budgets à 0, clés absentes, mais tests verts), un usage à 3 fournisseurs, et un
rapport Markdown d'exemple. Aucun réseau n'est touché.

## Brancher le vrai backend (FastAPI)

Le backend expose l'API sous `/api` sur `http://localhost:8000`. Vite proxifie
`/api` vers ce port (voir `vite.config.ts`).

```bash
cp .env.example .env
# éditer .env :
#   VITE_USE_MOCKS=false
npm run dev        # /api → http://localhost:8000 (proxy Vite)
```

Ou en une ligne :

```bash
VITE_USE_MOCKS=false npm run dev
```

## Scripts

| Commande | Effet |
|---|---|
| `npm run dev` | Serveur de dev Vite (mock par défaut). |
| `npm run build` | `tsc -b` (typecheck) puis `vite build` (bundle de prod). |
| `npm run preview` | Sert le build de prod localement. |
| `npm run test` | Suite Vitest (jsdom) en une passe. |
| `npm run test:watch` | Vitest en mode watch. |

## Écrans

- **/** — Dashboard : bandeau verdict GO/NO-GO, entonnoir du pipeline, tuiles de
  coûts, raccourci vers les prospects à plus fort signal.
- **/prospects** — table filtrable (statut / persona / marché), tri par score.
- **/prospects/:slug** — fiche complète + rendu Markdown sûr du rapport, contact
  avec mention RGPD, gaps majeurs, accroche.
- **/usage** — coûts par fournisseur (table + barres), top fiches, taux de cache.
- **/preflight** — les contrôles GO/NO-GO avec niveau (bloquant/warn) et pastille.

## Contrat d'API consommé

Types dans `src/types.ts`, client typé dans `src/api.ts`. Endpoints (préfixe
`/api`) : `/health`, `/preflight`, `/pipeline/funnel`, `/prospects`,
`/prospects/{slug}`, `/usage`, `/icp`, `/runs`.

## Notes de conception

- **Rendu Markdown maison et sûr** (`src/lib/markdown.tsx`) : le Markdown est
  parsé vers des éléments React — aucun `dangerouslySetInnerHTML`, aucune
  injection HTML possible.
- **Thème** : suit `prefers-color-scheme` par défaut ; un toggle pose
  `data-theme` sur `:root` (persisté en `localStorage`).
- **Info-design** : l'état se lit à la forme (pastille de statut, rayure de
  sévérité), pas seulement à la couleur. Focus visible, `aria-label` sur les
  graphiques, `prefers-reduced-motion` respecté, tables scrollables.
