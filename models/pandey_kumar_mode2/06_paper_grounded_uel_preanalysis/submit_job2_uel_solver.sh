#!/bin/bash
set -euo pipefail

PACKAGE_DIR="/home/pr21vyci/projects/mode2_reproduction_worktree/models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis"
cd "$PACKAGE_DIR" || exit 1

source ./job_notifications.sh
notification_load_config || true

echo "=== SUBMITTING MODE-II ADAPTED FRACTURE JOB-2_UEL SOLVER TO PBS ==="
JOB_ID=$(qsub submit_job2_uel_solver.pbs)
echo "Submitted PBS Job ID: $JOB_ID"

notify_submitted "$JOB_ID" "M2_J2_ADAPTED_FRACTURE" "Mode-II Miehe Adapted Refined PFM Fracture Production Solve" || true
echo "=== SUBMISSION COMPLETE ==="
