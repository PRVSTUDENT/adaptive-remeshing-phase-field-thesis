#!/usr/bin/env bash
# Guarded batch submission orchestrator for Stage F4 two-job batch:
# Job A: ModeII_H2_u020_postpeak
# Job B: ModeII_MISESERI_corrected_pbs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

REPO_ROOT="${PROJECT_ROOT_OVERRIDE:-${DEFAULT_REPO_ROOT}}"

PKG_A="${REPO_ROOT}/models/generated/mode_ii/h2_uniform_serial_u020_postpeak"
PKG_B="${REPO_ROOT}/models/generated/mode_ii/miseseri_preanalysis_corrected_pbs"

AUTH_FILE="${REPO_ROOT}/runs/hpc/stage_f/MODE_II_STAGE_F4_AUTHORIZATION_PROPOSAL.json"
STATUS_OUT="${REPO_ROOT}/runs/hpc/stage_f/STAGE_F4_BATCH_SUBMISSION_STATUS.json"
ACTIVE_TASK_FILE="${REPO_ROOT}/project_coordination/ACTIVE_TASK.json"

PBS_A="${SCRIPT_DIR}/05_mode_ii_h2_u020_postpeak.pbs"
PBS_B="${SCRIPT_DIR}/06_mode_ii_miseseri_corrected_pbs.pbs"

EXPECTED_H2_DECK_SHA="fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf"
EXPECTED_H2_FOR_SHA="49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37"
EXPECTED_MISESERI_DECK_SHA="a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2"
EXPECTED_EXECUTION_GIT_SHA="e66ba37dc4c639e0b61865cbb28893371a8f2149"

JOBNAME_A="ModeII_H2_u020_postpeak"
JOBNAME_B="ModeII_MISESERI_corrected_pbs"

# Test environment overrides
QSTAT_CMD="${QSTAT_CMD:-qstat}"
QSELECT_CMD="${QSELECT_CMD:-qselect}"
QSUB_CMD="${QSUB_CMD:-qsub}"

PYTHON_CMD="${PYTHON_CMD:-}"
if [[ -z "${PYTHON_CMD}" ]]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    elif command -v py >/dev/null 2>&1; then
        PYTHON_CMD="py"
    elif command -v abaqus >/dev/null 2>&1; then
        PYTHON_CMD="abaqus python"
    else
        PYTHON_CMD="python"
    fi
fi

PREFLIGHT_ONLY=true
if [[ "${1:-}" == "--execute" ]]; then
    PREFLIGHT_ONLY=false
fi

echo "=== STAGE F4 TWO-JOB BATCH ORCHESTRATOR PREFLIGHT CHECK ==="
echo "Repository root: ${REPO_ROOT}"

# 1. Verify Git revision of repository
CURRENT_GIT_SHA=$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo "unknown")
echo "Current Git revision: ${CURRENT_GIT_SHA}"
echo "Expected execution SHA: ${EXPECTED_EXECUTION_GIT_SHA}"

if [[ "${CURRENT_GIT_SHA}" != "${EXPECTED_EXECUTION_GIT_SHA}" ]]; then
    echo "ERROR: Execution Git revision mismatch! Expected ${EXPECTED_EXECUTION_GIT_SHA}, got ${CURRENT_GIT_SHA}"
    exit 1
fi

# 2. Verify existence of package files
if [[ ! -f "${PKG_A}/ModeII_H2_uniform_serial.inp" || ! -f "${PKG_A}/ModeII_H2_uniform_serial.for" ]]; then
    echo "ERROR: Package A files missing under ${PKG_A}"
    exit 1
fi

if [[ ! -f "${PKG_B}/ModeII_MISESERI_preanalysis.inp" ]]; then
    echo "ERROR: Package B files missing under ${PKG_B}"
    exit 1
fi

# 3. Verify deck and Fortran hashes
DECK_A_SHA=$(sha256sum "${PKG_A}/ModeII_H2_uniform_serial.inp" | awk '{print $1}' | tr -d '\\')
FOR_A_SHA=$(sha256sum "${PKG_A}/ModeII_H2_uniform_serial.for" | awk '{print $1}' | tr -d '\\')
DECK_B_SHA=$(sha256sum "${PKG_B}/ModeII_MISESERI_preanalysis.inp" | awk '{print $1}' | tr -d '\\')

if [[ "${DECK_A_SHA}" != "${EXPECTED_H2_DECK_SHA}" ]]; then
    echo "ERROR: Job A deck SHA mismatch! Expected ${EXPECTED_H2_DECK_SHA}, got ${DECK_A_SHA}"
    exit 1
fi

if [[ "${FOR_A_SHA}" != "${EXPECTED_H2_FOR_SHA}" ]]; then
    echo "ERROR: Job A Fortran SHA mismatch! Expected ${EXPECTED_H2_FOR_SHA}, got ${FOR_A_SHA}"
    exit 1
fi

if [[ "${DECK_B_SHA}" != "${EXPECTED_MISESERI_DECK_SHA}" ]]; then
    echo "ERROR: Job B deck SHA mismatch! Expected ${EXPECTED_MISESERI_DECK_SHA}, got ${DECK_B_SHA}"
    exit 1
fi

# 4. Verify step endpoint audit for Job A
if [[ -f "${PKG_A}/STEP_ENDPOINT_AUDIT.json" ]]; then
    AUDIT_PASS=$("${PYTHON_CMD}" -c "import json; d=json.load(open('${PKG_A}/STEP_ENDPOINT_AUDIT.json')); print(str(d.get('pass', False)).lower())")
    if [[ "${AUDIT_PASS}" != "true" ]]; then
        echo "ERROR: Step endpoint audit failed for Package A!"
        exit 1
    fi
else
    echo "ERROR: STEP_ENDPOINT_AUDIT.json missing in Package A"
    exit 1
fi

# 5. Duplicate detection using qselect + qstat -f and coordination state
echo "Checking duplicate status..."
if command -v "${QSELECT_CMD}" >/dev/null 2>&1; then
    USER_JOBS=$("${QSELECT_CMD}" -u "${USER:-$LOGNAME}" 2>/dev/null || true)
    for job_id in ${USER_JOBS}; do
        if [[ -n "${job_id}" ]]; then
            JOB_FULL_INFO=$("${QSTAT_CMD}" -f "${job_id}" 2>/dev/null || true)
            if echo "${JOB_FULL_INFO}" | grep -q "Job_Name = ${JOBNAME_A}"; then
                echo "ERROR: Duplicate detected! Job A (${JOBNAME_A}) is already active (${job_id})"
                exit 1
            fi
            if echo "${JOB_FULL_INFO}" | grep -q "Job_Name = ${JOBNAME_B}"; then
                echo "ERROR: Duplicate detected! Job B (${JOBNAME_B}) is already active (${job_id})"
                exit 1
            fi
        fi
    done
fi

if [[ -f "${ACTIVE_TASK_FILE}" ]]; then
    ACTIVE_JOBS=$("${PYTHON_CMD}" -c "import json; d=json.load(open('${ACTIVE_TASK_FILE}')); print(' '.join(d.get('active_job_ids', [])))" 2>/dev/null || true)
    if [[ -n "${ACTIVE_JOBS}" ]]; then
        echo "ERROR: Duplicate detected! ACTIVE_TASK.json has active jobs: ${ACTIVE_JOBS}"
        exit 1
    fi
fi

# Generate immutable Run ID
UTC_TS=$(date -u +"%Y%m%d_%H%M%S")
SHORT_SHA="${EXPECTED_EXECUTION_GIT_SHA:0:8}"
RUN_ID="${RUN_ID_OVERRIDE:-F4_${UTC_TS}_${SHORT_SHA}}"

SCRATCH_BASE="/scratch/pr21vyci/adaptive-remeshing/runs/stage_f4/${RUN_ID}"
SCRATCH_A="${SCRATCH_BASE}/h2_u020"
SCRATCH_B="${SCRATCH_BASE}/miseseri_corrected"

# Check if execution directory already exists
if [[ -d "${SCRATCH_A}" || -d "${SCRATCH_B}" ]]; then
    echo "ERROR: Immutable execution directory already exists! ${SCRATCH_BASE}"
    exit 1
fi

echo "Preflight check PASSED cleanly for both jobs. Run ID: ${RUN_ID}"

if [[ "${PREFLIGHT_ONLY}" == "true" ]]; then
    STATUS_JSON="{
  \"batch_status\": \"preflight_passed_zero_submitted\",
  \"qsub_attempts\": 0,
  \"successful_submissions\": 0,
  \"failed_qsub_attempts\": 0,
  \"job_a_id\": null,
  \"job_b_id\": null,
  \"run_id\": \"${RUN_ID}\"
}"
    echo "${STATUS_JSON}" > "${STATUS_OUT}"
    echo "Preflight mode complete. Zero jobs submitted."
    exit 0
fi

# 6. Verify single authorization proposal once
if [[ ! -f "${AUTH_FILE}" ]]; then
    echo "ERROR: Authorization proposal file missing: ${AUTH_FILE}"
    exit 1
fi

EXEC_AUTH=$("${PYTHON_CMD}" -c "import json; d=json.load(open('${AUTH_FILE}')); print(str(d.get('execution_authorized', False)).lower())")
SUB_APPROVED=$("${PYTHON_CMD}" -c "import json; d=json.load(open('${AUTH_FILE}')); print(str(d.get('submission_approved', False)).lower())")
APPROVED_SUBS=$("${PYTHON_CMD}" -c "import json; d=json.load(open('${AUTH_FILE}')); print(d.get('approved_submissions', 0))")
USED_SUBS=$("${PYTHON_CMD}" -c "import json; d=json.load(open('${AUTH_FILE}')); print(d.get('submissions_used', 0))")

if [[ "${EXEC_AUTH}" != "true" || "${SUB_APPROVED}" != "true" ]]; then
    echo "ERROR: Execution is NOT authorized in ${AUTH_FILE}"
    exit 1
fi

if [[ "${APPROVED_SUBS}" -ne 2 || "${USED_SUBS}" -ne 0 ]]; then
    echo "ERROR: Authorization proposal state invalid! approved_submissions=${APPROVED_SUBS}, submissions_used=${USED_SUBS}"
    exit 1
fi

# 7. Execute submission sequence
echo "=== SUBMITTING STAGE F4 TWO-JOB BATCH ==="
QSUB_ATTEMPTS=0
SUCCESSFUL_SUBS=0
FAILED_SUBS=0
JOB_A_ID=""
JOB_B_ID=""

# Stage and submit Job A
mkdir -p "${SCRATCH_A}"
cp "${PKG_A}/ModeII_H2_uniform_serial.inp" "${SCRATCH_A}/"
cp "${PKG_A}/ModeII_H2_uniform_serial.for" "${SCRATCH_A}/"
cp "${PBS_A}" "${SCRATCH_A}/"

cd "${SCRATCH_A}"
echo "Attempting qsub for Job A (${JOBNAME_A})..."
((QSUB_ATTEMPTS++))
if JOB_A_ID=$("${QSUB_CMD}" "$(basename "${PBS_A}")"); then
    ((SUCCESSFUL_SUBS++))
    echo "Job A submitted successfully: ${JOB_A_ID}"
else
    ((FAILED_SUBS++))
    echo "ERROR: Job A qsub failed!"
fi

# Stage and submit Job B if Job A succeeded
if [[ "${SUCCESSFUL_SUBS}" -eq 1 ]]; then
    mkdir -p "${SCRATCH_B}"
    cp "${PKG_B}/ModeII_MISESERI_preanalysis.inp" "${SCRATCH_B}/"
    cp "${PBS_B}" "${SCRATCH_B}/"

    cd "${SCRATCH_B}"
    echo "Attempting qsub for Job B (${JOBNAME_B})..."
    ((QSUB_ATTEMPTS++))
    if JOB_B_ID=$("${QSUB_CMD}" "$(basename "${PBS_B}")"); then
        ((SUCCESSFUL_SUBS++))
        echo "Job B submitted successfully: ${JOB_B_ID}"
    else
        ((FAILED_SUBS++))
        echo "WARNING: Job B qsub failed! Partial batch submission occurred."
    fi
fi

# Determine batch status semantics
BATCH_STATUS="zero_submitted"
if [[ "${SUCCESSFUL_SUBS}" -eq 2 ]]; then
    BATCH_STATUS="full_batch_submitted"
elif [[ "${SUCCESSFUL_SUBS}" -eq 1 ]]; then
    BATCH_STATUS="partial_batch_submitted"
fi

# 8. Consume authorization ONCE after submission sequence
"${PYTHON_CMD}" -c "
import json
d = json.load(open('${AUTH_FILE}'))
d['execution_authorized'] = False
d['submission_approved'] = False
d['solver_authorized'] = False
d['automatic_retry_authorized'] = False
d['retry_authorized'] = False
d['maximum_jobs_now'] = 0
d['submissions_used'] = ${SUCCESSFUL_SUBS}
d['actual_qsub_calls'] = ${QSUB_ATTEMPTS}
json.dump(d, open('${AUTH_FILE}', 'w'), indent=2)
"

STATUS_JSON="{
  \"batch_status\": \"${BATCH_STATUS}\",
  \"qsub_attempts\": ${QSUB_ATTEMPTS},
  \"successful_submissions\": ${SUCCESSFUL_SUBS},
  \"failed_qsub_attempts\": ${FAILED_SUBS},
  \"job_a_id\": \"${JOB_A_ID}\",
  \"job_b_id\": \"${JOB_B_ID}\",
  \"run_id\": \"${RUN_ID}\"
}"

echo "${STATUS_JSON}" > "${STATUS_OUT}"
echo "Saved batch submission status to ${STATUS_OUT}"

if [[ "${BATCH_STATUS}" == "full_batch_submitted" ]]; then
    echo "SUCCESS: Both jobs submitted cleanly."
    exit 0
else
    echo "BATCH FAILURE / PARTIAL WARNING: Batch status is ${BATCH_STATUS} (${SUCCESSFUL_SUBS} of 2 submitted)."
    exit 1
fi
