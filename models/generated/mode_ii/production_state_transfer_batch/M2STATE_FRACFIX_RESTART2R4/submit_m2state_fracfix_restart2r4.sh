#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
elif [ "${1:-}" = "--execute" ]; then
    DRY_RUN=false
else
    echo "Usage: $0 --dry-run | --execute"
    exit 1
fi

echo "=== M2STATE_FRACFIX_RESTART2R4 PREFLIGHT CHECK ==="
python3 validate_package_manifest.py || { echo "ERROR: PACKAGE_MANIFEST verification failed"; exit 1; }

if [ "$DRY_RUN" = "true" ]; then
    echo "DRY_RUN_SUCCESSFUL: qsub_call_count=0"
    exit 0
fi

echo "Executing guarded PBS submission..."
source ./job_notifications.sh 2>/dev/null || true
JOB_OUTPUT=$(qsub M2STATE_FRACFIX_RESTART2R4.pbs)
JOB_ID=$(echo "$JOB_OUTPUT" | tail -n 1)
echo "SUBMITTED_JOB_ID: $JOB_ID"
notify_submitted "$JOB_ID" "M2STATE_FRACFIX_RESTART2R4" "Queue: entry_imfdfkmq, 1 CPU, 16GB, 24h" 2>/dev/null || true
