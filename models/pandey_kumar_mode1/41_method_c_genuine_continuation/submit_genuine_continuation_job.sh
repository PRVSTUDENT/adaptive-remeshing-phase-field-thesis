#!/bin/bash
set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_method_c_genuine_continuation"
cd "${RUN_DIR}"

if [ -f "${RUN_DIR}/job_notifications.sh" ]; then
    source "${RUN_DIR}/job_notifications.sh"
    notification_load_config || true
fi

# 1. Cryptographic hash preflight
EXPECTED_INP_SHA="2F2C76B21979DC71EFB9D5D9175AD1522D49E187DEB4931293C4E9A84AE4AE33"
EXPECTED_SUB_SHA="CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_PBS_SHA="4986B6807C5987ECD51A4FC29FB4BAAF3418212DE928CE47D83DF96C410ED456"

ACTUAL_INP_SHA=$(sha256sum M1_MC_GENUINE_CONTINUATION.inp | awk '{print toupper($1)}')
ACTUAL_SUB_SHA=$(sha256sum f42_mixed_uel.for | awk '{print toupper($1)}')
ACTUAL_PBS_SHA=$(sha256sum submit_M1_MC_GENUINE_CONTINUATION.pbs | awk '{print toupper($1)}')

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
        exit 2
    fi
fi

if [ -f "${RUN_DIR}/M1_MC_GENUINE_CONTINUATION.odb" ] || [ -f "${RUN_DIR}/M1_MC_GENUINE_CONTINUATION.lck" ]; then
    echo "[GUARD ERROR] Production simulation artifacts already exist on disk. Refusing duplicate launch." >&2
    exit 2
fi

EXISTING_JOB=$(qstat -u pr21vyci 2>/dev/null | grep -E 'M1_MC_GEN' || true)
if [ -n "${EXISTING_JOB}" ]; then
    echo "[GUARD ERROR] Active or queued job already exists in PBS: ${EXISTING_JOB}" >&2
    exit 2
fi
echo "[GUARD PASS] Zero duplicate PBS jobs or prior submission records detected."

echo "Submitting Method C Genuine Continuation Job to entry_imfdfkmq -> normal_imfdfkmq..."
JOB_ID=$(qsub submit_M1_MC_GENUINE_CONTINUATION.pbs)
echo "Submitted Job ID: ${JOB_ID}"
echo "${JOB_ID}" > "${RUN_DIR}/SUBMITTED_JOB_ID.txt"

if type notify_submitted >/dev/null 2>&1; then
    notify_submitted "${JOB_ID}" "M1_MC_GEN_CONT" "normal_imfdfkmq" "1" "16gb" "04:00:00" || true
fi
