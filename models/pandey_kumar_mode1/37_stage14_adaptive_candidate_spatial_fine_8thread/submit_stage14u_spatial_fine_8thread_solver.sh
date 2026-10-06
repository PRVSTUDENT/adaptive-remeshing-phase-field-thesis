#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"

# Storage-compliance guard: reject launching from /home/
if [[ "$SCRIPT_DIR" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

if [ -f "./job_notifications.sh" ]; then
    source ./job_notifications.sh
    notification_load_config || true
fi

echo "Submitting 8-Thread Shared-Memory Spatial Fine (58k) Solver Job to PBS..."
JOB_ID=$(qsub submit_solver.pbs)
echo "Submitted PBS Job ID: $JOB_ID"

if type notify_submitted >/dev/null 2>&1; then
    notify_submitted "$JOB_ID" "PK_M1_14AM_8T" "8-Thread Shared-Memory Spatial Fine (58k) Adaptive Candidate"
fi
