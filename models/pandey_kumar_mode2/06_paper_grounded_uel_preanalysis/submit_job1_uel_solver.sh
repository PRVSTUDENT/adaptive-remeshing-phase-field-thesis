#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f ./job_notifications.sh ]; then
  echo "[LAUNCHER ERROR] job_notifications.sh missing" >&2
  exit 10
fi

source ./job_notifications.sh
notification_load_config || true

JOB_ID=$(qsub submit_solver.pbs)
echo "Submitted Mode-II Job-1_UEL Miehe Preanalysis Solver: $JOB_ID"
notify_submitted "$JOB_ID" "M2_J1_MIEHE_PRE" "Mode-II Job-1_UEL Coarse Miehe Preanalysis Solver (2,960 elements, 1 CPU)" || true
