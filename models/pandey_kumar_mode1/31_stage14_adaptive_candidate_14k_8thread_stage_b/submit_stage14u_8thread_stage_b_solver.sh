#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f ./job_notifications.sh ]; then
  echo "[LAUNCHER ERROR] job_notifications.sh missing" >&2
  exit 10
fi

source ./job_notifications.sh
notification_load_config || true

JOB_ID=$(qsub submit_solver.pbs)
echo "Submitted 8-Thread Stage-B Solver: $JOB_ID"
notify_submitted "$JOB_ID" "PK_M1_14K_8T_STAGE_B" "8-Thread Shared-Memory Stage-B Determinism Repeat Solver (14,483 elements)" || true
