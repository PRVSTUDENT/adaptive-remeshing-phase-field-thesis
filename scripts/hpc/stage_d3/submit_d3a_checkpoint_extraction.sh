#!/bin/bash
# Submit exactly one D3A checkpoint-extraction job. ODB post-processing only.
set -euo pipefail
PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de}"
JOB_NAME="d3a_checkpoint_extract"

cd "${PROJECT_HOME}"

if [ ! -f runs/hpc/stage_d3/interrupted_transfer/source_audit/D3A0_SOURCE_ELIGIBILITY.json ]; then
  echo "D3A blocked: missing D3A0_SOURCE_ELIGIBILITY.json" >&2
  exit 20
fi
grep -q 'stage_d3a0_existing_h0_source_eligible' \
  runs/hpc/stage_d3/interrupted_transfer/source_audit/D3A0_SOURCE_ELIGIBILITY.json || {
  echo "D3A blocked: H0 ODB source is not eligible" >&2
  exit 21
}

qstat -q
for q in shortq testq entry_imfdfkmq normal_imfdfkmq; do
  echo "========== ${q} =========="
  qstat -Qf "${q}" 2>/dev/null |
    egrep 'queue_type|enabled|started|state_count|resources_max.walltime|resources_max.mem|resources_max.ncpus|resources_min|acl|route_destinations' || true
done

bash -n scripts/hpc/stage_d3/01_d3a_checkpoint_extraction.pbs
python3 -m py_compile scripts/validation/validate_d3_checkpoint.py
python3 scripts/hpc/validate_pbs_email_notifications.py \
  --email "${MAIL}" scripts/hpc/stage_d3/01_d3a_checkpoint_extraction.pbs

JOB_ID=$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "Stage D3A existing-H0 checkpoint extraction at U approx 0.003 mm; ODB postprocessing only, no solver" \
  -- -q "${QUEUE}" \
     -M "${MAIL}" \
     -m abe \
     scripts/hpc/stage_d3/01_d3a_checkpoint_extraction.pbs)

echo "${JOB_ID}"
