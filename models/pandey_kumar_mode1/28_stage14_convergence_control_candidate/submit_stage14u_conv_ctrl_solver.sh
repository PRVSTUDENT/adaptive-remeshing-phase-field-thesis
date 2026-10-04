#!/bin/bash
set -euo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/28_stage14_convergence_control_candidate
export NOTIFICATION_CONFIG=~/.config/adaptive-remeshing/notifications.env
source ./job_notifications.sh

JOB_ID=$(qsub submit_solver.pbs)
echo "SUBMITTED_JOB_ID: $JOB_ID"
notify_submitted "$JOB_ID" "PK_M1_14K_CC_SOLVE"
