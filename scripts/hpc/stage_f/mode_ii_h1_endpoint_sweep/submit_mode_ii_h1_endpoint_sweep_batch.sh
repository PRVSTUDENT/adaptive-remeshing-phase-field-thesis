#!/bin/bash
# Stage F Mode-II H1 endpoint sweep guarded batch submit wrapper script.
# Default mode is preflight-only (qsub count = 0).
# Set MODE_II_H1_ENDPOINT_SWEEP_SUBMIT=1 or pass --submit to execute actual submissions.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

AUTH_PATH="${PROJECT_ROOT}/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/MODE_II_H1_ENDPOINT_SWEEP_AUTHORIZATION.json"
PBS_SCRIPT="${SCRIPT_DIR}/mode_ii_h1_endpoint_sweep.pbs"
PRESERVE_SUBMIT_NOTIFY="${PROJECT_ROOT}/scripts/hpc/qsub_with_submitted_notify.sh"

SUBMIT_MODE=0
if [ "${MODE_II_H1_ENDPOINT_SWEEP_SUBMIT:-0}" = "1" ]; then
  SUBMIT_MODE=1
fi

for arg in "$@"; do
  if [ "${arg}" = "--submit" ]; then
    SUBMIT_MODE=1
  fi
done

echo "=========================================================="
echo "Stage-F Mode-II H1 Endpoint Sweep Guarded Batch Wrapper"
echo "=========================================================="
echo "Submit mode: ${SUBMIT_MODE} (1=Submit, 0=Preflight-Only)"
echo "Project Root: ${PROJECT_ROOT}"

# 1. Check required authorization JSON
if [ ! -f "${AUTH_PATH}" ]; then
  echo "Error: Authorization JSON missing at ${AUTH_PATH}" >&2
  exit 10
fi

# Parse authorization parameters using python
AUTH_SUMMARY=$(python3 -c "
import json, sys
with open('${AUTH_PATH}', 'r') as f:
    d = json.load(f)
print(json.dumps({
    'task_id': d.get('task_id'),
    'exec_auth': d.get('execution_authorized', False),
    'sub_approved': d.get('submission_approved', False),
    'max_batch': d.get('maximum_batch_submissions', 0),
    'subs_used': d.get('submissions_used', 0),
    'max_jobs_now': d.get('maximum_jobs_now', 0),
    'retry_auth': d.get('automatic_retry_authorized', False),
    'approved_variants': d.get('approved_variants', []),
    'approved_job_names': d.get('approved_job_names', []),
}))
")

TASK_ID=$(echo "${AUTH_SUMMARY}" | python3 -c "import json, sys; print(json.load(sys.stdin)['task_id'])")
EXEC_AUTH=$(echo "${AUTH_SUMMARY}" | python3 -c "import json, sys; print(json.load(sys.stdin)['exec_auth'])")
SUB_APPROVED=$(echo "${AUTH_SUMMARY}" | python3 -c "import json, sys; print(json.load(sys.stdin)['sub_approved'])")
MAX_BATCH=$(echo "${AUTH_SUMMARY}" | python3 -c "import json, sys; print(json.load(sys.stdin)['max_batch'])")
SUBS_USED=$(echo "${AUTH_SUMMARY}" | python3 -c "import json, sys; print(json.load(sys.stdin)['subs_used'])")
MAX_JOBS_NOW=$(echo "${AUTH_SUMMARY}" | python3 -c "import json, sys; print(json.load(sys.stdin)['max_jobs_now'])")
RETRY_AUTH=$(echo "${AUTH_SUMMARY}" | python3 -c "import json, sys; print(json.load(sys.stdin)['retry_auth'])")

echo "Authorization Task ID: ${TASK_ID}"
echo "Execution Authorized: ${EXEC_AUTH}"
echo "Submission Approved: ${SUB_APPROVED}"
echo "Maximum Batch Submissions: ${MAX_BATCH}"
echo "Submissions Used: ${SUBS_USED}"
echo "Maximum Jobs Now: ${MAX_JOBS_NOW}"

if [ "${TASK_ID}" != "F2-H1-ENDPOINT-SWEEP-BATCH" ]; then
  echo "Error: Authorization task ID mismatch ('${TASK_ID}' != 'F2-H1-ENDPOINT-SWEEP-BATCH')" >&2
  exit 11
fi

if [ "${MAX_BATCH}" -ne 4 ]; then
  echo "Error: maximum_batch_submissions must be 4 (got ${MAX_BATCH})" >&2
  exit 12
fi

if [ "${SUBS_USED}" -ge 4 ]; then
  echo "Error: submissions_used already reached or exceeded ${MAX_BATCH} (got ${SUBS_USED})" >&2
  exit 13
fi

if [ "${RETRY_AUTH}" = "True" ] || [ "${RETRY_AUTH}" = "true" ]; then
  echo "Error: automatic_retry_authorized must be false" >&2
  exit 14
fi

# 2. Check static validations for all 4 variants
SWEEP_DIR="${PROJECT_ROOT}/models/generated/mode_ii/h1_endpoint_sweep"
VARIANTS=("u015" "u020" "u030" "u040")
JOB_NAMES=("m2h1_u015" "m2h1_u020" "m2h1_u030" "m2h1_u040")

for v in "${VARIANTS[@]}"; do
  val_json="${SWEEP_DIR}/${v}/STATIC_VALIDATION.json"
  if [ ! -f "${val_json}" ]; then
    echo "Error: Static validation JSON missing for variant ${v} at ${val_json}" >&2
    exit 15
  fi
  vpass=$(python3 -c "import json; print(json.load(open('${val_json}'))['passed'])")
  if [ "${vpass}" != "True" ] && [ "${vpass}" != "true" ]; then
    echo "Error: Static validation failed for variant ${v}" >&2
    exit 16
  fi
  echo "Variant ${v} static validation: PASS"
done

# 3. Preflight-only report if SUBMIT_MODE == 0
if [ "${SUBMIT_MODE}" -ne 1 ]; then
  echo "=========================================================="
  echo "PREFLIGHT-ONLY CHECK PASSED."
  echo "qsub count = 0 (no jobs submitted)."
  echo "To submit all four jobs, set MODE_II_H1_ENDPOINT_SWEEP_SUBMIT=1 or pass --submit."
  echo "=========================================================="
  exit 0
fi

# 4. Submission mode validation
if [ "${EXEC_AUTH}" != "True" ] && [ "${EXEC_AUTH}" != "true" ]; then
  echo "Error: execution_authorized is false in authorization JSON" >&2
  exit 17
fi

if [ "${SUB_APPROVED}" != "True" ] && [ "${SUB_APPROVED}" != "true" ]; then
  echo "Error: submission_approved is false in authorization JSON" >&2
  exit 18
fi

if [ "${MAX_JOBS_NOW}" -lt 4 ]; then
  echo "Error: maximum_jobs_now must be >= 4 to execute batch submission (got ${MAX_JOBS_NOW})" >&2
  exit 19
fi

# 5. Check cluster working tree revision match
CURRENT_REV=$(git rev-parse HEAD)
echo "Current HEAD revision: ${CURRENT_REV}"

AUTH_REV=$(python3 -c "import json; print(json.load(open('${AUTH_PATH}')).get('approved_base_revision', ''))")
if [ -n "${AUTH_REV}" ] && [ "${CURRENT_REV}" != "${AUTH_REV}" ]; then
  echo "Warning: Current revision (${CURRENT_REV}) differs from approved_base_revision (${AUTH_REV})"
fi

# 6. Duplicate job check on HPC scheduler
echo "Checking for active/queued duplicate jobs..."
if command -v qselect >/dev/null 2>&1; then
  USER_JOBS=$(qselect -u "${USER:-pr21vyci}" 2>/dev/null || true)
  for jid in ${USER_JOBS}; do
    jname=$(qstat -f "${jid}" 2>/dev/null | grep "Job_Name =" | awk '{print $3}' || true)
    for jn in "${JOB_NAMES[@]}"; do
      if [ "${jname}" = "${jn}" ]; then
        echo "Error: Active or queued job '${jn}' already exists (Job ID ${jid})" >&2
        exit 20
      fi
    done
  done
fi

# 7. Execute batch submissions
SUBMISSION_DIR="${PROJECT_ROOT}/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/submission"
mkdir -p "${SUBMISSION_DIR}"

QSUB_COUNT=0
SUBMITTED_MAP="{}"

echo "Starting sequential submission of 4 jobs..."

PRESTAGED_ROOT="${PRESTAGED_ROOT:-${PROJECT_ROOT}}"
PRESTAGED_RUNTIME_ROOT="${PRESTAGED_RUNTIME_ROOT:-${PRESTAGED_ROOT}}"

for idx in "${!VARIANTS[@]}"; do
  v="${VARIANTS[$idx]}"
  jn="${JOB_NAMES[$idx]}"

  echo "Submitting variant ${v} (${jn})..."

  VARS="VARIANT=${v},PROJECT_REVISION=${CURRENT_REV},PRESTAGED_ROOT=${PRESTAGED_ROOT},PRESTAGED_RUNTIME_ROOT=${PRESTAGED_RUNTIME_ROOT}"

  if [ -f "${PRESERVE_SUBMIT_NOTIFY}" ]; then
    JOB_ID=$(bash "${PRESERVE_SUBMIT_NOTIFY}" --job-name "${jn}" --message "Stage-F H1 endpoint sweep ${v} (${jn}) submitted" -- -N "${jn}" -v "${VARS}" "${PBS_SCRIPT}")
  else
    JOB_ID=$(qsub -N "${jn}" -v "${VARS}" "${PBS_SCRIPT}")
  fi

  echo "  Variant ${v} -> Job ID: ${JOB_ID}"
  QSUB_COUNT=$((QSUB_COUNT + 1))

  # Record in map
  SUBMITTED_MAP=$(python3 -c "
import json
m = json.loads('''${SUBMITTED_MAP}''')
m['${v}'] = '${JOB_ID}'
print(json.dumps(m))
")
done

echo "=========================================================="
echo "BATCH SUBMISSION SUCCESSFUL!"
echo "Total qsub count: ${QSUB_COUNT}"
echo "Submitted Map:"
echo "${SUBMITTED_MAP}" | python3 -m json.tool

cat > "${SUBMISSION_DIR}/variant_job_map.json" <<EOF
${SUBMITTED_MAP}
EOF

cat > "${SUBMISSION_DIR}/submission_summary.json" <<EOF
{
  "classification": "stage_f_mode_ii_h1_endpoint_sweep_submitted",
  "task_id": "F2-H1-ENDPOINT-SWEEP-BATCH",
  "qsub_count": ${QSUB_COUNT},
  "submitted_at": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "source_revision": "${CURRENT_REV}",
  "variant_job_map": ${SUBMITTED_MAP}
}
EOF

echo "Saved submission records to ${SUBMISSION_DIR}"
echo "=========================================================="
