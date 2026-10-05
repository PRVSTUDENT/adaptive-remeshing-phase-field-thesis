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

echo "=== PREFLIGHT VERIFICATION: M2STATE_FRACFIX_RESTART2R6 ==="
python3 validate_package_manifest.py

if [ "${1:-}" != "--execute" ]; then
    echo "DRY_RUN_SUCCESSFUL: qsub_call_count = 0"
    echo "To submit to scheduler, rerun with: ./submit_m2state_fracfix_restart2r6.sh --execute"
    exit 0
fi

echo "Submitting to PBS queue entry_imfdfkmq..."
JOB_ID=$(qsub M2STATE_FRACFIX_RESTART2R6.pbs)
echo "SUBMITTED_JOB_ID=$JOB_ID"

source ./job_notifications.sh
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-$HOME/.config/adaptive-remeshing/notifications.env}"
if [ -f "$NOTIFICATION_CONFIG" ]; then
    source "$NOTIFICATION_CONFIG"
fi

notify_submitted "M2STATE_FRACFIX_RESTART2R6" "$JOB_ID" "Submitted to entry_imfdfkmq (1 CPU, 16 GB, 24:00:00)"
