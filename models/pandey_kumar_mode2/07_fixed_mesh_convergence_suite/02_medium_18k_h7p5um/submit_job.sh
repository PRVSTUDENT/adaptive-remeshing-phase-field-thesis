#!/bin/bash
set -euo pipefail
cd "/scratch9/pr21vyci/runs/mode2_fixed_convergence/02_medium_18k_h7p5um"

if [ -f ./job_notifications.sh ]; then
  source ./job_notifications.sh
  notification_load_config || true
fi

JOB_ID=$(qsub "/scratch9/pr21vyci/runs/mode2_fixed_convergence/02_medium_18k_h7p5um/submit_solver.pbs")
echo "SUBMITTED_JOB_ID: $JOB_ID"
if [ -n "${JOB_ID:-}" ] && type notify_submitted >/dev/null 2>&1; then
  notify_submitted "$JOB_ID" "M2_FIX_MED_18K" "normal_imfdfkmq" || true
fi
