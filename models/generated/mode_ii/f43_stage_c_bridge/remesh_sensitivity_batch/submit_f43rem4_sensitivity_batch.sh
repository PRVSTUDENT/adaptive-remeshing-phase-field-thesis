#!/bin/bash
# Guarded submission wrapper for F43REM4_SENSITIVITY_BATCH (PK1, PK5, MM)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

EXPECTED_PREP_SHA="cd361ae6fae6a1c2673e23bfca92df362e76cfd8"
EXPECTED_QUAL_SHA="cc752de6d5514a26d84b740e4878aaf231b16087"
EXPECTED_CAE_SHA="0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa"
EXPECTED_PRED_ODB_SHA="9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1"

AUTH_JSON="${SCRIPT_DIR}/F43REM4_BATCH_AUTHORIZATION.json"

echo "[F43REM4 Batch Wrapper] Pre-flight verification..."

if [ ! -f "${AUTH_JSON}" ]; then
    echo "FATAL ERROR: Authorization JSON file missing: ${AUTH_JSON}" >&2
    exit 1
fi

if ! command -v jq >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
    echo "FATAL ERROR: Neither jq nor python3 available for JSON verification" >&2
    exit 1
fi

EXEC_AUTH=$(python3 -c "import json; print(json.load(open('${AUTH_JSON}'))['execution_authorized'])")
SUB_APP=$(python3 -c "import json; print(json.load(open('${AUTH_JSON}'))['submission_approved'])")
MAX_JOBS_NOW=$(python3 -c "import json; print(json.load(open('${AUTH_JSON}'))['maximum_jobs_now'])")
MAX_JOBS_AUTH=$(python3 -c "import json; print(json.load(open('${AUTH_JSON}'))['maximum_jobs_authorized'])")
AUTO_RETRY=$(python3 -c "import json; print(str(json.load(open('${AUTH_JSON}'))['automatic_retry']).lower())")

if [ "${EXEC_AUTH}" != "True" ] || [ "${SUB_APP}" != "True" ]; then
    echo "FATAL ERROR: F43REM4_SENSITIVITY_BATCH submission not authorized! execution_authorized=${EXEC_AUTH}, submission_approved=${SUB_APP}" >&2
    exit 1
fi

if [ "${MAX_JOBS_NOW}" -ne 3 ] || [ "${MAX_JOBS_AUTH}" -ne 3 ]; then
    echo "FATAL ERROR: Authorized job count mismatch! maximum_jobs_now=${MAX_JOBS_NOW}, maximum_jobs_authorized=${MAX_JOBS_AUTH}" >&2
    exit 1
fi

if [ "${AUTO_RETRY}" = "true" ]; then
    echo "FATAL ERROR: Automatic retry is strictly prohibited!" >&2
    exit 1
fi

# Verify local required PBS files
for job_name in "F43REM4_PK1" "F43REM4_PK5" "F43REM4_MM"; do
    if [ ! -f "${SCRIPT_DIR}/${job_name}.pbs" ]; then
        echo "FATAL ERROR: PBS script ${job_name}.pbs missing in ${SCRIPT_DIR}!" >&2
        exit 1
    fi
done

# Verify predecessor ODB SHA if present
PRED_ODB_PATH="${SCRIPT_DIR}/../evidence/1385461.mmaster02/F43PRE3_GEOM.odb"
if [ -f "${PRED_ODB_PATH}" ]; then
    ACTUAL_PRED_ODB_SHA=$(sha256sum "${PRED_ODB_PATH}" | awk '{print $1}')
    if [ "${ACTUAL_PRED_ODB_SHA}" != "${EXPECTED_PRED_ODB_SHA}" ]; then
        echo "FATAL ERROR: Predecessor ODB SHA mismatch! Expected ${EXPECTED_PRED_ODB_SHA}, got ${ACTUAL_PRED_ODB_SHA}" >&2
        exit 1
    fi
fi

# Determine email recipients for PBS mail options
EMAIL_RECIPIENTS="pr21vyci@mailserver.tu-freiberg.de,Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"

# Verify qstat capacity
if ! qstat_out=$(qstat -u "${USER:-${USERNAME:-pr21vyci}}" 2>&1); then
    echo "FATAL ERROR: qstat check failed!" >&2
    exit 1
fi

for job_name in "F43REM4_PK1" "F43REM4_PK5" "F43REM4_MM"; do
    if echo "$qstat_out" | grep -q "${job_name}"; then
        echo "FATAL ERROR: ${job_name} job is already running or queued in qstat!" >&2
        exit 1
    fi
done

echo "[F43REM4 Batch Wrapper] All pre-flight checks passed."

cd "${SCRIPT_DIR}"

if [ "${DRY_RUN:-0}" -eq 1 ]; then
    echo "[F43REM4 Batch Wrapper] DRY_RUN=1: qsub calls skipped."
    exit 0
fi

# Submit all 3 authorized independent jobs together
echo "[F43REM4 Batch Wrapper] Submitting 3 authorized jobs..."

JOB1_ID=$(qsub -m abe -M "${EMAIL_RECIPIENTS}" "${SCRIPT_DIR}/F43REM4_PK1.pbs")
echo "[F43REM4 Batch Wrapper] Submitted F43REM4_PK1 job ID: ${JOB1_ID}"

JOB2_ID=$(qsub -m abe -M "${EMAIL_RECIPIENTS}" "${SCRIPT_DIR}/F43REM4_PK5.pbs")
echo "[F43REM4 Batch Wrapper] Submitted F43REM4_PK5 job ID: ${JOB2_ID}"

JOB3_ID=$(qsub -W depend=afterany:"${JOB1_ID}" -m abe -M "${EMAIL_RECIPIENTS}" "${SCRIPT_DIR}/F43REM4_MM.pbs")
echo "[F43REM4 Batch Wrapper] Submitted F43REM4_MM job ID: ${JOB3_ID} (dependent on ${JOB1_ID})"

SUBMISSION_RECORD_JSON="${SCRIPT_DIR}/F43REM4_BATCH_SUBMISSION_RECORD.json"
cat <<EOF > "${SUBMISSION_RECORD_JSON}"
{
  "batch_id": "F43REM4_SENSITIVITY_BATCH",
  "submission_timestamp_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "preparation_sha256": "${EXPECTED_PREP_SHA}",
  "qualification_sha256": "${EXPECTED_QUAL_SHA}",
  "submitted_jobs": {
    "F43REM4_PK1": "${JOB1_ID}",
    "F43REM4_PK5": "${JOB2_ID}",
    "F43REM4_MM": "${JOB3_ID}"
  }
}
EOF

echo "[F43REM4 Batch Wrapper] Recorded submission IDs to ${SUBMISSION_RECORD_JSON}"
echo "[F43REM4 Batch Wrapper] Batch submission complete!"
