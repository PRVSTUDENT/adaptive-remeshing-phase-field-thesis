#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

cd /scratch/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis || exit 1

source ./job_notifications.sh
notification_load_config || true

echo "=== SUBMITTING MODE-II PRODUCTION JOB-2_UEL SOLVER TO PBS ==="
JOB_ID=$(qsub submit_job2_uel_solver.pbs)
echo "Submitted PBS Job ID: $JOB_ID"

notify_submitted "$JOB_ID" "M2_J2_UEL_ADAPT" "Mode-II Paper-Grounded Adapted PFM Fracture Production Solve" || true
echo "=== SUBMISSION COMPLETE ==="
