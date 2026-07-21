#!/bin/bash
# Fair H1 baseline: same serial H1 deck, cpus=4 mp_mode=threads.
# For apples-to-apples walltime vs C2F-v3 (also 4 threads).
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
EMAIL="${EMAIL:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
PBS_SCRIPT="scripts/hpc/stage_c2/12_h1_threads4_baseline.pbs"
PBS_OUT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"

cd "${PROJECT_HOME}"
mkdir -p "${PBS_OUT}"

python3 scripts/hpc/validate_pbs_email_notifications.py --email "Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de" \
  "${PBS_SCRIPT}"

# Pass both recipients to qsub -M (comma-separated). Do not put commas in -v.
J=$(qsub -q "${QUEUE}" \
  -M "${EMAIL}" \
  -m abe \
  -o "${PBS_OUT}/h1_threads4_baseline.out" \
  "${PBS_SCRIPT}")

echo "H1_THREADS4=${J}"
# Primary: Telegram SUBMITTED (never pass token via qsub -v)
python3 scripts/hpc/telegram_notify.py \
  --event SUBMITTED \
  --job-id "${J}" \
  --job-name h1_thr4_base \
  --message "Queue: ${QUEUE}; cpus=4; mp_mode=threads; fair H1 baseline vs C2F-v3 1376480; mail secondary: ${EMAIL}" \
  || true

mkdir -p runs/hpc/stage_c2/recovery
{
  echo "submission_time=$(date -Is)"
  echo "job_id=${J}"
  echo "purpose=fair_4thread_H1_baseline_vs_C2F_v3"
  echo "deck=models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025"
  echo "cpus=4"
  echo "mp_mode=threads"
  echo "mail=${EMAIL}"
  echo "telegram=primary"
  echo "email=secondary_best_effort"
  echo "compare_to_serial_H1=peak_RF_0.2pct_prepeak_NRMSE_0.2pct"
  echo "compare_to_C2F_v3_walltime=1376480.mmaster02"
} | tee runs/hpc/stage_c2/recovery/H1_THREADS4_SUBMISSION_RECORD.txt
qstat -u "${USER}" | head -15 || true
