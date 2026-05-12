#!/usr/bin/env bash
set -euo pipefail

# 用法：
# ./scripts/start_datahub_worker.sh
# WORKER_NAME=datahub-default-worker POLL_SECONDS=5 BATCH_SIZE=5 ./scripts/start_datahub_worker.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

WORKER_NAME="${WORKER_NAME:-datahub-default-worker}"
POLL_SECONDS="${POLL_SECONDS:-5}"
BATCH_SIZE="${BATCH_SIZE:-5}"

cd "${API_DIR}"

if [[ -f "${API_DIR}/venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${API_DIR}/venv/bin/activate"
fi

echo "[DataHub] starting worker..."
echo "[DataHub] api_dir=${API_DIR}"
echo "[DataHub] worker_name=${WORKER_NAME} poll_seconds=${POLL_SECONDS} batch_size=${BATCH_SIZE}"

python -m app.datahub.jobs.worker \
  --worker-name "${WORKER_NAME}" \
  --poll-seconds "${POLL_SECONDS}" \
  --batch-size "${BATCH_SIZE}"
