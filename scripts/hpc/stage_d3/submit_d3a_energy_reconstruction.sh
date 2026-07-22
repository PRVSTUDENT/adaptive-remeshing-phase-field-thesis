#!/bin/bash
# Submit exactly one D3A-E energy-reconstruction job. ODB post-processing only.
set -euo pipefail
PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de}"
JOB_NAME="d3a_energy_reconstruct"

cd "${PROJECT_HOME}"

if [ ! -f docs/decisions/D3A_ENERGY_EVIDENCE_ROUTE.md ]; then
  echo "D3A-E blocked: missing D3A_ENERGY_EVIDENCE_ROUTE.md" >&2
  exit 20
fi
grep -q 'stage_d3a_energy_reconstruction_authorized' docs/decisions/D3A_ENERGY_EVIDENCE_ROUTE.md || {
  echo "D3A-E blocked: energy reconstruction route is not authorized" >&2
  exit 21
}

qstat -q
for q in shortq testq entry_imfdfkmq normal_imfdfkmq; do
  echo "========== ${q} =========="
  qstat -Qf "${q}" 2>/dev/null |
    egrep 'queue_type|enabled|started|state_count|resources_max.walltime|resources_max.mem|resources_max.ncpus|resources_min|acl|route_destinations' || true
done

bash -n scripts/hpc/stage_d3/02_d3a_energy_reconstruction.pbs
python3 -m py_compile \
  scripts/state_transfer/reconstruct_d3_checkpoint_energy.py \
  scripts/validation/validate_d3_reconstructed_energy.py
python3 scripts/hpc/validate_pbs_email_notifications.py \
  --email "${MAIL}" scripts/hpc/stage_d3/02_d3a_energy_reconstruction.pbs

JOB_ID=$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "Stage D3A independent energy reconstruction from existing H0 checkpoint; ODB postprocessing only, no solver" \
  -- -q "${QUEUE}" \
     -M "${MAIL}" \
     -m abe \
     scripts/hpc/stage_d3/02_d3a_energy_reconstruction.pbs)

echo "${JOB_ID}"
