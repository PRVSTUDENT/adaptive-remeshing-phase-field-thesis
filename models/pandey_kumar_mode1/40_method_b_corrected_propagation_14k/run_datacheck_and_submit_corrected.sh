#!/bin/bash
set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_method_b_corrected_propagation_14k"
cd "${RUN_DIR}"

source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

if [ -f "${RUN_DIR}/job_notifications.sh" ]; then
    source "${RUN_DIR}/job_notifications.sh"
    notification_load_config || true
fi

# 1. Cryptographic hash preflight (Model Deck, Subroutine, PBS Directives)
EXPECTED_INP_SHA="1209F716971719B1A740FF92C8B5503BA9784F10D5EEDD3C5035C81D40A066E9"
EXPECTED_SUB_SHA="CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_PBS_SHA="06DE87F62676D9CA35B8B69106881004D2F6B48459966405779EC04E2FC66172"

ACTUAL_INP_SHA=$(sha256sum M1_MB_CORRECTED_PROPAGATION_14K.inp | awk '{print toupper($1)}')
ACTUAL_SUB_SHA=$(sha256sum f42_mixed_uel.for | awk '{print toupper($1)}')
ACTUAL_PBS_SHA=$(sha256sum submit_M1_MB_CORRECTED_14K.pbs | awk '{print toupper($1)}')

if [ "${ACTUAL_INP_SHA}" != "${EXPECTED_INP_SHA}" ]; then
    echo "[GUARD ERROR] Input deck SHA-256 mismatch: ${ACTUAL_INP_SHA} != ${EXPECTED_INP_SHA}" >&2
    exit 1
fi

if [ "${ACTUAL_SUB_SHA}" != "${EXPECTED_SUB_SHA}" ]; then
    echo "[GUARD ERROR] Subroutine SHA-256 mismatch: ${ACTUAL_SUB_SHA} != ${EXPECTED_SUB_SHA}" >&2
    exit 1
fi

if [ "${ACTUAL_PBS_SHA}" != "${EXPECTED_PBS_SHA}" ]; then
    echo "[GUARD ERROR] PBS script SHA-256 mismatch: ${ACTUAL_PBS_SHA} != ${EXPECTED_PBS_SHA}" >&2
    exit 1
fi
echo "[GUARD PASS] Cryptographic hashes verified bitwise match (deck, subroutine, PBS directives)."

# 2. Durable duplicate submission protection
if [ -f "${RUN_DIR}/SUBMITTED_JOB_ID.txt" ]; then
    PREV_JOB_ID=$(cat "${RUN_DIR}/SUBMITTED_JOB_ID.txt" | tr -d '[:space:]')
    if [ -n "${PREV_JOB_ID}" ]; then
        echo "[GUARD ERROR] Job was already submitted under ID ${PREV_JOB_ID} (recorded in SUBMITTED_JOB_ID.txt)." >&2
        echo "Refusing duplicate submission. Inspect previous job or explicitly clear marker if authorized." >&2
        exit 2
    fi
fi

if [ -f "${RUN_DIR}/M1_MB_CORRECTED_PROPAGATION_14K.odb" ] || [ -f "${RUN_DIR}/M1_MB_CORRECTED_PROPAGATION_14K.lck" ]; then
    echo "[GUARD ERROR] Production simulation artifacts already exist on disk. Refusing duplicate launch." >&2
    exit 2
fi

EXISTING_JOB=$(qstat -u pr21vyci 2>/dev/null | grep -E 'M1_MB_CORR|M1_MB_CORRECTED' || true)
if [ -n "${EXISTING_JOB}" ]; then
    echo "[GUARD ERROR] Active or queued Method B job already exists in PBS: ${EXISTING_JOB}" >&2
    exit 2
fi
echo "[GUARD PASS] Zero duplicate PBS jobs or prior submission records detected."

# 3. FlexNet license readiness & Method C priority check
LMUTIL_PATH="/cluster/application/abaqus/2023/linux_a64/code/bin/lmutil"
LICENSE_SERVER="25000@license4.imfd.tu-freiberg.de"
LMSTAT_OUT=$("${LMUTIL_PATH}" lmstat -c "${LICENSE_SERVER}" -f standard 2>/dev/null || true)
TOKENS_IN_USE=$(echo "${LMSTAT_OUT}" | grep -o 'Total of [0-9]* licenses in use' | grep -o '[0-9]*' || echo "300")
TOKENS_TOTAL=$(echo "${LMSTAT_OUT}" | grep -o 'Total of [0-9]* licenses issued' | grep -o '[0-9]*' || echo "300")
TOKENS_FREE=$((TOKENS_TOTAL - TOKENS_IN_USE))

echo "License status: ${TOKENS_IN_USE}/${TOKENS_TOTAL} in use (${TOKENS_FREE} free, minimum 5 required)."

# Check if Method C datacheck (PID 1657700) is actively waiting
METHOD_C_PID=1657700
if ps -p ${METHOD_C_PID} >/dev/null 2>&1; then
    echo "[LICENSE PRIORITY] Method C datacheck (PID ${METHOD_C_PID}) is actively queued in FlexNet."
    if [ "${TOKENS_FREE}" -lt 10 ]; then
        echo "[LICENSE GATE DEFERRED] Method C datacheck has queue priority. Requiring Method C completion or >= 10 free tokens."
        echo "Currently free tokens: ${TOKENS_FREE} < 10. Deferring Method B datacheck to protect Method C."
        exit 3
    fi
else
    if [ "${TOKENS_FREE}" -lt 5 ]; then
        echo "[LICENSE GATE BLOCKED] Insufficient floating licenses (${TOKENS_FREE} free < 5 required). Cannot run datacheck."
        exit 3
    fi
fi

# 4. Execute Abaqus 2023 datacheck
JOB_NAME="M1_MB_CORRECTED_14K_DC"
INP_NAME="M1_MB_CORRECTED_PROPAGATION_14K.inp"
USER_SUB="f42_mixed_uel.for"

rm -f "${JOB_NAME}.lck" "${JOB_NAME}.023" "${JOB_NAME}.log" "${JOB_NAME}.dat" "${JOB_NAME}.msg" "${JOB_NAME}.prt" "${JOB_NAME}.sta" 2>/dev/null || true

echo "=== EXECUTING ABAQUS 2023 DATACHECK: ${JOB_NAME} ==="
abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" datacheck interactive > "${JOB_NAME}.log" 2>&1

DC_EXIT=$?
if [ ${DC_EXIT} -ne 0 ]; then
    echo "[DATACHECK FATAL] Datacheck exited with non-zero exit code: ${DC_EXIT}" >&2
    cat "${JOB_NAME}.log" >&2 || true
    exit ${DC_EXIT}
fi

if [ ! -f "${JOB_NAME}.log" ]; then
    echo "[DATACHECK FATAL] Log file ${JOB_NAME}.log was not produced." >&2
    exit 4
fi

if [ ! -f "${JOB_NAME}.dat" ]; then
    echo "[DATACHECK FATAL] Dat file ${JOB_NAME}.dat was not produced." >&2
    exit 4
fi

if ! grep -q -E "COMPLETED|THE ANALYSIS HAS COMPLETED SUCCESSFULLY" "${JOB_NAME}.log" 2>/dev/null; then
    echo "[DATACHECK FATAL] Log does not contain successful completion message." >&2
    exit 4
fi

if grep -q "\*\*\*ERROR" "${JOB_NAME}.dat" 2>/dev/null; then
    echo "[DATACHECK FATAL] Errors detected in .dat file." >&2
    exit 5
fi

if grep -q "\*\*\*ERROR" "${JOB_NAME}.log" 2>/dev/null; then
    echo "[DATACHECK FATAL] Errors detected in .log file." >&2
    exit 5
fi

echo "=== DATACHECK QUALIFIED WITH ZERO ERRORS (EXIT 0) ==="

# 5. Submit authorized PBS job and record provenance durably
echo "Submitting authorized PBS job: submit_M1_MB_CORRECTED_14K.pbs..."
JOB_ID=$(qsub submit_M1_MB_CORRECTED_14K.pbs)
echo "=== SUBMITTED PBS JOB ID: ${JOB_ID} ==="

echo "${JOB_ID}" > "${RUN_DIR}/SUBMITTED_JOB_ID.txt"
echo "[$(date -Iseconds)] Submitted PBS Job ID: ${JOB_ID} (1 CPU, 16 GB RAM, walltime 24:00:00, queue entry_imfdfkmq)" >> "${RUN_DIR}/SUBMISSION_HISTORY.log"

if type notify_submitted >/dev/null 2>&1; then
    notify_submitted "${JOB_ID}" "M1_MB_CORR_14K" "entry_imfdfkmq" "1" "16gb" "24:00:00" || true
fi
