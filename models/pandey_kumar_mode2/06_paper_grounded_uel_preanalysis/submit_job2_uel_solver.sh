#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f ./job_notifications.sh ]; then
  echo "[SUBMIT ERROR] job_notifications.sh missing" >&2
  exit 10
fi

source ./job_notifications.sh
notification_load_config || true

JOB_ID=$(qsub submit_job2_uel_solver.pbs)
echo "SUBMITTED_JOB_ID: $JOB_ID"
notify_submitted "$JOB_ID" "M2_J2_ADAPT_RETEST" "normal_imfdfkmq" || true
