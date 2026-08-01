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

**Le plus simple — tout lancer d'un coup** (backend + front déjà branchés) :

```bash
./webapp/start-dev.sh          # depuis la racine du dépôt ; Ctrl-C arrête les deux
./webapp/start-dev.sh --help   # options : --vault, --api-port, --web-port, --ledger, --mocks
```

Manuellement : le backend expose l'API sous `/api` sur `http://localhost:8000`,
Vite proxifie `/api` vers ce port (voir `vite.config.ts`, cible surchargeable
par `VITE_API_TARGET`).

```bash
# terminal 1 — depuis la racine du dépôt
VAULT_PATH=vault uvicorn webapp.backend.app:app --reload --port 8000

# terminal 2
cp .env.example .env      # puis VITE_USE_MOCKS=false
npm run dev               # /api → http://localhost:8000 (proxy Vite)
```

Ou en une ligne :

```bash
VITE_USE_MOCKS=false npm run dev
```

Le proxy est configuré sans buffering ni compression pour que le flux SSE de
`/api/greenit/stream` traverse en **temps réel** (sinon les événements
arriveraient tous à la fermeture de la requête).

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
- **/greenit** — efficience en **temps réel** (voir ci-dessous).
- **/preflight** — les contrôles GO/NO-GO avec niveau (bloquant/warn) et pastille.

## Écran GreenIT — observabilité temps réel

Tableau de bord d'efficience alimenté par le flux SSE `/api/greenit/stream` :

- **Tuiles** : coût total, énergie (Wh), CO₂e (g), octets transférés, taux de
  cache. Elles bougent **en direct** — chaque appel reçu est appliqué sur
  l'agrégat courant côté client (`src/lib/greenit.ts`, fonctions pures), avec
  exactement les conventions du backend (un cache-hit n'est pas un appel ; un
  `budget_depasse` n'impute ni coût ni empreinte).
- **Flux des appels** : les 40 derniers appels (heure, fournisseur/endpoint,
  modèle/profil, coût, octets, durée, CO₂e, état). L'**état de la liaison** est
  toujours affiché — `En direct`, `Connexion…`, `Repli polling`, `Déconnecté` —
  avec une forme distincte par état, pas seulement une couleur.
- **Repli automatique** : si `EventSource` est indisponible ou si la connexion
  tombe, le client bascule sur une interrogation périodique de `/api/greenit`.
  L'écran l'annonce explicitement au lieu de faire semblant d'être en direct.
- **Économies du cache** : appels évités, coût, énergie et CO₂e non dépensés.
- **Ventilations** : barres par modèle et par fournisseur, avec `aria-label`
  chiffré sur chaque barre.

> ⚠️ **Énergie et CO₂e sont des ESTIMATIONS** issues des facteurs paramétrables
> de `knowledge/greenit.yaml`. Un bandeau permanent et non masquable le rappelle
> en haut de l'écran, les tuiles concernées sont marquées `~` et sous-titrées
> « estimation », et la couverture réelle de l'instrumentation est affichée.
> Ces chiffres servent à comparer des scénarios, jamais à produire un bilan
> carbone opposable.

En **mode mock**, le flux est simulé : une boucle de 6 appels représentatifs
(LLM haiku, LLM sonnet, Places, cache-hit, erreur, refus de budget) est rejouée
toutes les 2,5 s — l'écran est donc démontrable entièrement hors-ligne.

## Contrat d'API consommé

Types dans `src/types.ts`, client typé dans `src/api.ts`. Endpoints (préfixe
`/api`) : `/health`, `/preflight`, `/pipeline/funnel`, `/prospects`,
`/prospects/{slug}`, `/usage`, `/icp`, `/runs`, `/greenit`, `/greenit/stream`
(SSE, consommé par `souscrireGreenit()`).

## Notes de conception

- **Rendu Markdown maison et sûr** (`src/lib/markdown.tsx`) : le Markdown est
  parsé vers des éléments React — aucun `dangerouslySetInnerHTML`, aucune
  injection HTML possible.
- **Thème** : suit `prefers-color-scheme` par défaut ; un toggle pose
  `data-theme` sur `:root` (persisté en `localStorage`).
- **Info-design** : l'état se lit à la forme (pastille de statut, rayure de
  sévérité), pas seulement à la couleur. Focus visible, `aria-label` sur les
  graphiques, `prefers-reduced-motion` respecté, tables scrollables.
