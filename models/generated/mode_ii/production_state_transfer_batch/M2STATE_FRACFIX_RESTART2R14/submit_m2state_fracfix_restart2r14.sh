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

source ./job_notifications.sh
notification_load_config 2>/dev/null || true

echo "=== GUARDED SUBMISSION WRAPPER: M2STATE_FRACFIX_RESTART2R14 ==="
python3 validate_package_manifest.py

MODE="${1:---dry-run}"

if [ "$MODE" == "--dry-run" ]; then
    echo "DRY-RUN MODE: Package validated successfully. qsub call count = 0."
    exit 0
elif [ "$MODE" == "--execute" ]; then
    echo "EXECUTING GUARDED SUBMISSION..."
    JOB_ID=$(qsub M2STATE_FRACFIX_RESTART2R14.pbs)
    echo "SUBMITTED JOB: $JOB_ID"
    notify_submitted "M2STATE_FRACFIX_RESTART2R14" "$JOB_ID" "entry_imfdfkmq" "1" "16gb" "24:00:00"
    exit 0
else
    echo "Unknown mode: $MODE. Use --dry-run or --execute"
    exit 1
fi
