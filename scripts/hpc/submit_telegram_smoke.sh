#!/bin/bash
# Submit non-scientific Telegram compute-node smoke test + login SUBMITTED notify.
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi
PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
EMAIL="${EMAIL:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
cd "${PROJECT_HOME}"

python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" \
  scripts/hpc/stage_c2/13_telegram_smoke.pbs

JOB_ID=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -o /scratch/pr21vyci/adaptive-remeshing/pbs_output/telegram_smoke.out \
  scripts/hpc/stage_c2/13_telegram_smoke.pbs)
echo "TELEGRAM_SMOKE=${JOB_ID}"

python3 scripts/hpc/telegram_notify.py \
  --event SUBMITTED \
  --job-id "${JOB_ID}" \
  --job-name tg_smoke \
  --message "Queue: ${QUEUE}; purpose: compute-node Telegram HTTPS smoke; not a scientific job" \
  || true

mkdir -p runs/hpc/notifications
{
  echo "submission_time=$(date -Is)"
  echo "job_id=${JOB_ID}"
  echo "purpose=telegram_compute_smoke"
  echo "queue=${QUEUE}"
} | tee runs/hpc/notifications/TELEGRAM_SMOKE_SUBMISSION.txt
