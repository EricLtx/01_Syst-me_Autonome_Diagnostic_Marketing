/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Déclaration locale plutôt que @types/node : ce fichier est le seul à lire
// l'environnement du processus, ajouter une dépendance de types complète pour
// une ligne serait disproportionné.
declare const process: { env: Record<string, string | undefined> };

// Cible du proxy /api. Surchargée par start-dev.sh quand le backend n'écoute
// pas sur 8000 (option --api-port).
const API_TARGET = process.env.VITE_API_TARGET ?? "http://localhost:8000";

// Proxy /api → backend FastAPI (utilisé uniquement quand VITE_USE_MOCKS=false).
// En mode mock (défaut), le client api.ts ne touche jamais le réseau.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
        // Le flux SSE /api/greenit/stream doit traverser le proxy SANS être
        // bufferisé, sinon le « temps réel » arrive par paquets en fin de
        // requête. On coupe donc la compression et on laisse la connexion
        // ouverte aussi longtemps que le backend la maintient.
        timeout: 0,
        proxyTimeout: 0,
        headers: { "Accept-Encoding": "identity" },
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.ts"],
    css: true,
  },
});
