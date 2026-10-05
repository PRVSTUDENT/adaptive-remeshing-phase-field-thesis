#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

PACKAGE_DIR="/scratch/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/15_energy_qualification_small"
cd "$PACKAGE_DIR" || exit 1

if [ ! -f ./job_notifications.sh ]; then
  echo "[SUBMIT ERROR] job_notifications.sh missing in $PACKAGE_DIR" >&2
  exit 10
fi

source ./job_notifications.sh
notification_load_config || true

echo "=== SUBMITTING PK_M1_ENERGY_SOLVE (64-Element Mini Verification) ==="
JOB_ID=$(qsub submit_solver.pbs)

echo "=== QSUB SUCCESS: JOB_ID=${JOB_ID} ==="

# Issue dual-channel submission notification
notify_submitted "${JOB_ID}" "PK_M1_ENERGY_SOLVE" "64-element serial 1-CPU Mode-I energy verification solve" || true

echo "SUBMITTED_JOB_ID=${JOB_ID}"
