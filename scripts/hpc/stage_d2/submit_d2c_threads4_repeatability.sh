#!/bin/bash
# Submit exactly one D2C four-thread repeatability job.
set -euo pipefail
PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
MAIL="${MAIL:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de}"
JOB_NAME="d2c_threads4"

cd "${PROJECT_HOME}"

qstat -q
for q in shortq testq entry_imfdfkmq normal_imfdfkmq; do
  echo "========== ${q} =========="
  qstat -Qf "${q}" 2>/dev/null |
    egrep 'queue_type|enabled|started|state_count|resources_max.walltime|resources_max.mem|resources_max.ncpus|resources_min|acl|route_destinations' || true
done

if [ ! -f runs/hpc/stage_d2/d2b_serial_continuation/D2B.ok ]; then
  echo "D2C blocked: missing runs/hpc/stage_d2/d2b_serial_continuation/D2B.ok" >&2
  exit 20
fi
if ! grep -q 'accepted_rerun_job_id=1376825.mmaster02' runs/hpc/stage_d2/d2b_serial_continuation/D2B.ok; then
  echo "D2C blocked: canonical D2B.ok does not reference 1376825.mmaster02" >&2
  exit 21
fi

bash -n scripts/hpc/stage_d2/03_d2c_threads4_repeatability.pbs
python3 -m py_compile \
  scripts/postprocessing/extract_d2c_threads4_state.py \
  scripts/validation/validate_d2c_thread_repeatability.py
python3 scripts/hpc/validate_pbs_email_notifications.py \
  --email "${MAIL}" scripts/hpc/stage_d2/03_d2c_threads4_repeatability.pbs
git diff --check

JOB_ID=$(scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "Stage D2C four-thread transferred-state repeatability; reference D2B job 1376825; 1 MPI rank x 4 threads" \
  -- -q "${QUEUE}" \
     -M "${MAIL}" \
     -m abe \
     scripts/hpc/stage_d2/03_d2c_threads4_repeatability.pbs)

echo "${JOB_ID}"
