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

DRY_RUN=false
for arg in "$@"; do
    if [ "$arg" == "--dry-run" ]; then
        DRY_RUN=true
    fi
done

echo "======================================================================"
echo "Guarded HPC Submission Wrapper: M2STATE_FRACFIX_RESTART2R12"
echo "======================================================================"

echo "--> Verifying SHA256 package manifest..."
python3 validate_package_manifest.py

if [ "$DRY_RUN" = true ]; then
    echo "--> Dry-run completed successfully. Zero qsub calls made."
    exit 0
fi

source job_notifications.sh
JOB_ID=$(qsub M2STATE_FRACFIX_RESTART2R12.pbs)
echo "Submitted Job ID: $JOB_ID"
notify_submitted "M2STATE_FRACFIX_RESTART2R12" "$JOB_ID" "normal_imfdfkmq" "submit_m2state_fracfix_restart2r12.sh"
