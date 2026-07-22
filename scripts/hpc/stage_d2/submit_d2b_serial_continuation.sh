#!/bin/bash
# Submit D2B only. Do not submit D2C/D2D from this wrapper.
set -euo pipefail
PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de}"
JOB_NAME="d2b_serial_cont_r1"

cd "${PROJECT_HOME}"

qstat -q
for q in shortq testq entry_imfdfkmq normal_imfdfkmq; do
  echo "========== ${q} =========="
  qstat -Qf "${q}" 2>/dev/null |
    egrep 'queue_type|enabled|started|state_count|resources_max.walltime|resources_max.mem|resources_max.ncpus|resources_min|acl|route_destinations' || true
done

if [ ! -f runs/hpc/stage_d2/d2a_serial_ingestion/D2A.ok ]; then
  echo "D2B blocked: missing runs/hpc/stage_d2/d2a_serial_ingestion/D2A.ok" >&2
  exit 20
fi

python3 scripts/state_transfer/generate_d2_fortran_transfer_table.py
python3 scripts/validation/validate_d2_state_ingestion.py \
  --package models/state_transfer/d2_tiny_transfer --static-only
bash -n scripts/hpc/stage_d2/02_d2b_serial_continuation.pbs
python3 scripts/hpc/validate_pbs_email_notifications.py \
  --email "${MAIL}" scripts/hpc/stage_d2/02_d2b_serial_continuation.pbs

JOB_ID=$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "Corrected Stage D2B serial continuation; only maximum increments changed from 2 to 50; CPUs: 1; memory: 8 GB; walltime: 00:30:00" \
  -- -q "${QUEUE}" \
     -M "${MAIL}" \
     -m abe \
     scripts/hpc/stage_d2/02_d2b_serial_continuation.pbs)

echo "${JOB_ID}"
