#!/usr/bin/env bash
# start-dev.sh — lance le cockpit complet : API FastAPI + front Vite, branchés
# l'un sur l'autre (le front tape le VRAI backend, pas les fixtures).
#
# Pourquoi un script plutôt que deux terminaux : le mode « branché » exige trois
# réglages cohérents (VITE_USE_MOCKS=false, port du proxy, VAULT_PATH). Les
# désynchroniser produit un front qui affiche des données de démonstration en
# croyant lire le vault — le pire des deux mondes pour un cockpit d'opérateur.
#
# Arrêt : Ctrl-C. Le trap arrête les DEUX processus (pas d'uvicorn orphelin qui
# garde le port 8000 occupé au prochain lancement).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage : ./webapp/start-dev.sh [options]

Lance ensemble :
  - le backend FastAPI (lecture seule)   http://localhost:8000  (docs sur /docs)
  - le front React/Vite                  http://localhost:5173

Options :
  --vault <chemin>    Racine du vault Obsidian à lire       (déf. $VAULT_PATH ou <repo>/vault)
  --api-port <n>      Port d'uvicorn                        (déf. $API_PORT ou 8000)
  --web-port <n>      Port de Vite                          (déf. $WEB_PORT ou 5173)
  --ledger <chemin>   Grand livre api_usage.log à suivre    (déf. $API_USAGE_LOG ou <repo>/api_usage.log)
  --mocks             Laisse le front en mode mock (fixtures locales)
  --no-install        N'installe pas les dépendances npm manquantes
  -h, --help          Cette aide

Variables d'environnement : toutes les options ont un équivalent (VAULT_PATH,
API_PORT, WEB_PORT, API_USAGE_LOG, VITE_USE_MOCKS). Un fichier webapp/.env est
chargé s'il existe (voir webapp/.env.example).

Exemples :
  ./webapp/start-dev.sh
  ./webapp/start-dev.sh --vault /data/vault-prod --api-port 8010 --web-port 5180
  VAULT_PATH=/data/vault ./webapp/start-dev.sh
EOF
}

# --- 1. Fichier .env optionnel (les variables déjà exportées gagnent) --------
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "${SCRIPT_DIR}/.env"
  set +a
  echo "· Configuration chargée depuis webapp/.env"
fi

INSTALL_NPM=1
VITE_USE_MOCKS="${VITE_USE_MOCKS:-false}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --vault)     VAULT_PATH="${2:?--vault attend un chemin}"; shift 2 ;;
    --api-port)  API_PORT="${2:?--api-port attend un numéro}"; shift 2 ;;
    --web-port)  WEB_PORT="${2:?--web-port attend un numéro}"; shift 2 ;;
    --ledger)    API_USAGE_LOG="${2:?--ledger attend un chemin}"; shift 2 ;;
    --mocks)     VITE_USE_MOCKS="true"; shift ;;
    --no-install) INSTALL_NPM=0; shift ;;
    -h|--help)   usage; exit 0 ;;
    *) echo "Option inconnue : $1" >&2; usage; exit 2 ;;
  esac
done

VAULT_PATH="${VAULT_PATH:-${REPO_ROOT}/vault}"
API_USAGE_LOG="${API_USAGE_LOG:-${REPO_ROOT}/api_usage.log}"
API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5173}"

# Chemins relatifs → absolus, résolus depuis la racine du repo (le backend
# lance ses propres résolutions ailleurs : on ne lui laisse aucune ambiguïté).
[[ "${VAULT_PATH}" = /* ]]     || VAULT_PATH="${REPO_ROOT}/${VAULT_PATH}"
[[ "${API_USAGE_LOG}" = /* ]]  || API_USAGE_LOG="${REPO_ROOT}/${API_USAGE_LOG}"
if [[ -n "${RUNS_LOG:-}" && "${RUNS_LOG}" != /* ]]; then
  RUNS_LOG="${REPO_ROOT}/${RUNS_LOG}"
fi

export VAULT_PATH API_USAGE_LOG
[[ -n "${RUNS_LOG:-}" ]] && export RUNS_LOG
[[ -n "${PREFLIGHT_ROOT_DIR:-}" ]] && export PREFLIGHT_ROOT_DIR
export VITE_USE_MOCKS
export VITE_API_TARGET="${VITE_API_TARGET:-http://localhost:${API_PORT}}"

# --- 2. Contrôles préalables ------------------------------------------------
PYTHON_BIN="${PYTHON_BIN:-python3}"
command -v "${PYTHON_BIN}" >/dev/null 2>&1 || PYTHON_BIN="python"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "✗ Python introuvable (essayé python3 puis python)." >&2
  exit 1
fi
if ! "${PYTHON_BIN}" -c "import uvicorn, fastapi" >/dev/null 2>&1; then
  echo "✗ FastAPI/uvicorn absents. Installer :" >&2
  echo "    pip install -r ${SCRIPT_DIR}/backend/requirements.txt" >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "✗ npm introuvable — nécessaire pour le front Vite." >&2
  exit 1
fi
if [[ ! -d "${VAULT_PATH}" ]]; then
  echo "⚠ Vault absent : ${VAULT_PATH}"
  echo "  L'API répondra quand même (listes vides, préflight NO-GO)."
  echo "  Pour l'initialiser :  ${PYTHON_BIN} ${REPO_ROOT}/init_vault.py"
fi
if [[ ! -f "${API_USAGE_LOG}" ]]; then
  echo "⚠ Grand livre absent : ${API_USAGE_LOG}"
  echo "  /api/greenit répondra à zéro et le flux temps réel attendra la 1re ligne."
fi
if [[ ${INSTALL_NPM} -eq 1 && ! -d "${SCRIPT_DIR}/frontend/node_modules" ]]; then
  echo "· Dépendances npm absentes → npm install"
  (cd "${SCRIPT_DIR}/frontend" && npm install) || exit 1
fi

# --- 3. Arrêt propre des deux processus -------------------------------------
API_PID=""
WEB_PID=""

arreter() {
  trap - INT TERM EXIT
  echo ""
  echo "· Arrêt du cockpit…"
  for pid in "${WEB_PID}" "${API_PID}"; do
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      # SIGTERM au groupe de processus : vite et uvicorn --reload ont des enfants.
      kill -TERM -"${pid}" 2>/dev/null || kill -TERM "${pid}" 2>/dev/null
    fi
  done
  sleep 0.5
  for pid in "${WEB_PID}" "${API_PID}"; do
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      kill -KILL -"${pid}" 2>/dev/null || kill -KILL "${pid}" 2>/dev/null
    fi
  done
  wait 2>/dev/null
  echo "· Terminé."
}
# Sur Ctrl-C : on arrête tout PUIS on sort tout de suite, sinon la boucle de
# surveillance reprendrait la main et signalerait à tort un serveur « mort ».
trap 'arreter; exit 130' INT TERM
trap arreter EXIT

# --- 4. Lancement -----------------------------------------------------------
cat <<EOF

  ┌─ Cockpit opérateur — diagnostic marketing ────────────────────────────
  │ API      http://localhost:${API_PORT}      (docs : /docs)
  │ Front    http://localhost:${WEB_PORT}
  │ Vault    ${VAULT_PATH}
  │ Ledger   ${API_USAGE_LOG}
  │ Mode     $( [[ "${VITE_USE_MOCKS}" == "false" ]] && echo "BRANCHÉ sur le backend (données réelles)" || echo "MOCK (fixtures locales)" )
  │ GreenIT  http://localhost:${WEB_PORT}/greenit  — flux temps réel SSE
  └───────────────────────────────────────────────  Ctrl-C pour tout arrêter

EOF

# setsid (si dispo) place chaque serveur dans son propre groupe de processus :
# le trap peut alors tuer toute la descendance d'un coup.
LANCEUR=""
command -v setsid >/dev/null 2>&1 && LANCEUR="setsid"

(cd "${REPO_ROOT}" && exec ${LANCEUR} "${PYTHON_BIN}" -m uvicorn webapp.backend.app:app \
  --reload --host 127.0.0.1 --port "${API_PORT}") &
API_PID=$!

(cd "${SCRIPT_DIR}/frontend" && exec ${LANCEUR} npm run dev -- --port "${WEB_PORT}" --strictPort) &
WEB_PID=$!

# Si l'un des deux meurt, on arrête l'autre (pas de demi-cockpit silencieux).
while kill -0 "${API_PID}" 2>/dev/null && kill -0 "${WEB_PID}" 2>/dev/null; do
  sleep 1
done
echo "✗ Un des deux serveurs s'est arrêté — arrêt de l'ensemble." >&2
