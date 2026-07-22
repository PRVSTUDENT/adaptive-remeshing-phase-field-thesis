#!/bin/bash
# Submit D2A only. Do not submit D2B/D2C/D2D from this wrapper.
set -euo pipefail
PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de}"
JOB_NAME="d2a_state_ingestion"

cd "${PROJECT_HOME}"

qstat -q
for q in shortq testq entry_imfdfkmq normal_imfdfkmq; do
  echo "========== ${q} =========="
  qstat -Qf "${q}" 2>/dev/null |
    egrep 'queue_type|enabled|started|state_count|resources_max.walltime|resources_max.mem|resources_max.ncpus|resources_min|acl|route_destinations' || true
done

python3 scripts/state_transfer/generate_d2_fortran_transfer_table.py
python3 scripts/validation/validate_d2_state_ingestion.py \
  --package models/state_transfer/d2_tiny_transfer --static-only
bash -n scripts/hpc/stage_d2/01_d2a_serial_ingestion.pbs
python3 scripts/hpc/validate_pbs_email_notifications.py \
  --email "${MAIL}" scripts/hpc/stage_d2/01_d2a_serial_ingestion.pbs

JOB_ID=$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "Stage D2A serial transferred-state ingestion; CPUs: 1; memory: 8 GB; walltime: 00:30:00" \
  -- -q "${QUEUE}" \
     -M "${MAIL}" \
     -m abe \
     scripts/hpc/stage_d2/01_d2a_serial_ingestion.pbs)

echo "${JOB_ID}"
