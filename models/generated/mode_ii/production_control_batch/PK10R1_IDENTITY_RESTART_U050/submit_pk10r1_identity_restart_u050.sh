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

echo "=== Guarded Wrapper for PK10R1_IDENTITY_RESTART_U050 ==="

if [ -f "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" ]; then
    source "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
elif [ -f "./job_notifications.sh" ]; then
    source "./job_notifications.sh"
fi

echo "1. Validating package manifest..."
python3 validate_package_manifest.py

if [[ "${1:-}" == "--dry-run" ]]; then
    echo "DRY_RUN_PASS: Package is valid and ready for submission."
    exit 0
elif [[ "${1:-}" == "--execute" ]]; then
    echo "2. Submitting PBS job..."
    JOB_ID=$(qsub PK10R1_IDENTITY_RESTART_U050.pbs)
    echo "SUBMITTED: $JOB_ID"
    if type notify_submitted >/dev/null 2>&1; then
        notify_submitted "PK10R1_IDENTITY_RESTART_U050" "$JOB_ID"
    fi
    exit 0
else
    echo "Usage: $0 --dry-run | --execute"
    exit 1
fi
