#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

JOB_NAME="M2REF_H2_FULL_U050"
PBS_SCRIPT="M2REF_H2_FULL_U050.pbs"

echo "=== GUARDED SUBMISSION WRAPPER: $JOB_NAME ==="

# Validate manifest
python3 validate_package_manifest.py

if [ "${1:-}" != "--execute" ]; then
    echo "DRY-RUN MODE: Validation passed. To submit, pass --execute"
    exit 0
fi

echo "EXECUTING GUARDED SUBMISSION..."
SUBMIT_OUTPUT=$(qsub "$PBS_SCRIPT")
echo "SUBMITTED JOB: $SUBMIT_OUTPUT"

# Telegram notification
if [ -f "./job_notifications.sh" ]; then
    source ./job_notifications.sh
    notification_load_config || true
    notify_submitted "$JOB_NAME" "$JOB_NAME" "$SUBMIT_OUTPUT" || true
fi
