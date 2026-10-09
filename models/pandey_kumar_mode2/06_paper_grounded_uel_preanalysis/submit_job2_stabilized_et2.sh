#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode2_j2_adapted_stabilized_et2

if [ -f ./job_notifications.sh ]; then
  source ./job_notifications.sh
  notification_load_config || true
fi

JOB_ID=$(qsub /scratch9/pr21vyci/runs/mode2_j2_adapted_stabilized_et2/submit_job2_stabilized_et2.pbs)
echo "SUBMITTED_JOB_ID: $JOB_ID"
if [ -n "${JOB_ID:-}" ] && type notify_submitted >/dev/null 2>&1; then
  notify_submitted "$JOB_ID" "M2_J2_ADAPT_ET2_STAB" "normal_imfdfkmq" || true
fi
