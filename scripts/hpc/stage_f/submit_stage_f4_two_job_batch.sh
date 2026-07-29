#!/usr/bin/env bash
# Guarded batch orchestrator for Stage F4 two-job batch:
# Job A: ModeII_H2_u020_postpeak
# Job B: ModeII_MISESERI_corrected_pbs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

PKG_A="${REPO_ROOT}/models/generated/mode_ii/h2_uniform_serial_u020_postpeak"
PKG_B="${REPO_ROOT}/models/generated/mode_ii/miseseri_preanalysis_corrected_pbs"

AUTH_FILE="${REPO_ROOT}/runs/hpc/stage_f/MODE_II_STAGE_F4_AUTHORIZATION_PROPOSAL.json"
STATUS_OUT="${REPO_ROOT}/runs/hpc/stage_f/STAGE_F4_BATCH_SUBMISSION_STATUS.json"

PBS_A="${SCRIPT_DIR}/05_mode_ii_h2_u020_postpeak.pbs"
PBS_B="${SCRIPT_DIR}/06_mode_ii_miseseri_corrected_pbs.pbs"

EXPECTED_H2_DECK_SHA="fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf"
EXPECTED_H2_FOR_SHA="49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37"
EXPECTED_MISESERI_DECK_SHA="a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2"

JOBNAME_A="ModeII_H2_u020_postpeak"
JOBNAME_B="ModeII_MISESERI_corrected_pbs"

SCRATCH_A="/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h2_u020_postpeak"
SCRATCH_B="/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_miseseri_pbs"

PREFLIGHT_ONLY=true
if [[ "${1:-}" == "--execute" ]]; then
    PREFLIGHT_ONLY=false
fi

echo "=== STAGE F4 TWO-JOB BATCH ORCHESTRATOR PREFLIGHT CHECK ==="
echo "Package A: ${PKG_A}"
echo "Package B: ${PKG_B}"

# 1. Verify existence of package files
if [[ ! -f "${PKG_A}/ModeII_H2_uniform_serial.inp" || ! -f "${PKG_A}/ModeII_H2_uniform_serial.for" ]]; then
    echo "ERROR: Package A files missing under ${PKG_A}"
    exit 1
fi

if [[ ! -f "${PKG_B}/ModeII_MISESERI_preanalysis.inp" ]]; then
    echo "ERROR: Package B files missing under ${PKG_B}"
    exit 1
fi

# 2. Verify deck and Fortran hashes
DECK_A_SHA=$(sha256sum "${PKG_A}/ModeII_H2_uniform_serial.inp" | awk '{print $1}')
FOR_A_SHA=$(sha256sum "${PKG_A}/ModeII_H2_uniform_serial.for" | awk '{print $1}')
DECK_B_SHA=$(sha256sum "${PKG_B}/ModeII_MISESERI_preanalysis.inp" | awk '{print $1}')

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

# 3. Verify endpoint audit for Job A
if [[ -f "${PKG_A}/STEP_ENDPOINT_AUDIT.json" ]]; then
    AUDIT_PASS=$(python3 -c "import json; d=json.load(open('${PKG_A}/STEP_ENDPOINT_AUDIT.json')); print(str(d.get('pass', False)).lower())")
    if [[ "${AUDIT_PASS}" != "true" ]]; then
        echo "ERROR: Step endpoint audit failed for Package A!"
        exit 1
    fi
else
    echo "ERROR: STEP_ENDPOINT_AUDIT.json missing in Package A"
    exit 1
fi

# 4. Duplicate detection via qstat
if command -v qstat >/dev/null 2>&1; then
    QSTAT_OUT=$(qstat -u "$USER" 2>/dev/null || true)
    if echo "${QSTAT_OUT}" | grep -q "${JOBNAME_A}"; then
        echo "ERROR: Duplicate detection! Job A (${JOBNAME_A}) is already queued/running in qstat."
        exit 1
    fi
    if echo "${QSTAT_OUT}" | grep -q "${JOBNAME_B}"; then
        echo "ERROR: Duplicate detection! Job B (${JOBNAME_B}) is already queued/running in qstat."
        exit 1
    fi
fi

echo "Preflight check PASSED cleanly for both jobs."

if [[ "${PREFLIGHT_ONLY}" == "true" ]]; then
    echo "Preflight mode complete. Zero jobs submitted. Pass --execute to submit if authorized."
    exit 0
fi

# 5. Check single authorization proposal once
if [[ ! -f "${AUTH_FILE}" ]]; then
    echo "ERROR: Authorization proposal file missing: ${AUTH_FILE}"
    exit 1
fi

EXEC_AUTH=$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(str(d.get('execution_authorized', False)).lower())")
SUB_APPROVED=$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(str(d.get('submission_approved', False)).lower())")
APPROVED_SUBS=$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(d.get('approved_submissions', 0))")
USED_SUBS=$(python3 -c "import json; d=json.load(open('${AUTH_FILE}')); print(d.get('submissions_used', 0))")

if [[ "${EXEC_AUTH}" != "true" || "${SUB_APPROVED}" != "true" ]]; then
    echo "ERROR: Execution is NOT authorized in ${AUTH_FILE}"
    exit 1
fi

if [[ "${APPROVED_SUBS}" -ne 2 || "${USED_SUBS}" -ne 0 ]]; then
    echo "ERROR: Authorization proposal state invalid! approved_submissions=${APPROVED_SUBS}, submissions_used=${USED_SUBS}"
    exit 1
fi

# 6. Execute submission sequence
echo "=== SUBMITTING STAGE F4 TWO-JOB BATCH ==="
JOB_A_ID=""
JOB_B_ID=""
JOB_A_SUBMITTED=false
JOB_B_SUBMITTED=false

# Stage Job A
mkdir -p "${SCRATCH_A}"
cp "${PKG_A}/ModeII_H2_uniform_serial.inp" "${SCRATCH_A}/"
cp "${PKG_A}/ModeII_H2_uniform_serial.for" "${SCRATCH_A}/"
cp "${PBS_A}" "${SCRATCH_A}/"

cd "${SCRATCH_A}"
echo "Submitting Job A (${JOBNAME_A})..."
if JOB_A_ID=$(qsub "$(basename "${PBS_A}")"); then
    JOB_A_SUBMITTED=true
    echo "Job A submitted successfully: ${JOB_A_ID}"
else
    echo "ERROR: Job A submission failed!"
    exit 1
fi

# Stage Job B
mkdir -p "${SCRATCH_B}"
cp "${PKG_B}/ModeII_MISESERI_preanalysis.inp" "${SCRATCH_B}/"
cp "${PBS_B}" "${SCRATCH_B}/"

cd "${SCRATCH_B}"
echo "Submitting Job B (${JOBNAME_B})..."
if JOB_B_ID=$(qsub "$(basename "${PBS_B}")"); then
    JOB_B_SUBMITTED=true
    echo "Job B submitted successfully: ${JOB_B_ID}"
else
    echo "WARNING: Job B submission failed! Partial batch submission occurred."
fi

# 7. Consume authorization ONCE after submission sequence
N_SUBMITTED=0
if [[ "${JOB_A_SUBMITTED}" == "true" ]]; then ((N_SUBMITTED++)) || true; fi
if [[ "${JOB_B_SUBMITTED}" == "true" ]]; then ((N_SUBMITTED++)) || true; fi

python3 -c "
import json
d = json.load(open('${AUTH_FILE}'))
d['execution_authorized'] = False
d['submission_approved'] = False
d['solver_authorized'] = False
d['automatic_retry_authorized'] = False
d['retry_authorized'] = False
d['maximum_jobs_now'] = 0
d['submissions_used'] = ${N_SUBMITTED}
d['actual_qsub_calls'] = ${N_SUBMITTED}
json.dump(d, open('${AUTH_FILE}', 'w'), indent=2)
"

STATUS_JSON="{
  \"batch_submission_completed\": true,
  \"job_a_submitted\": ${JOB_A_SUBMITTED},
  \"job_a_id\": \"${JOB_A_ID}\",
  \"job_b_submitted\": ${JOB_B_SUBMITTED},
  \"job_b_id\": \"${JOB_B_ID}\",
  \"partial_batch\": $(if [[ "${JOB_A_SUBMITTED}" == "true" && "${JOB_B_SUBMITTED}" == "false" ]]; then echo "true"; else echo "false"; fi),
  \"actual_qsub_calls\": ${N_SUBMITTED}
}"

echo "${STATUS_JSON}" > "${STATUS_OUT}"
echo "Saved batch submission status to ${STATUS_OUT}"

if [[ "${JOB_A_SUBMITTED}" == "true" && "${JOB_B_SUBMITTED}" == "true" ]]; then
    echo "SUCCESS: Both jobs submitted cleanly."
    exit 0
else
    echo "PARTIAL SUBMISSION WARNING: Job A submitted (${JOB_A_ID}), Job B NOT submitted."
    exit 1
fi
