#!/bin/bash
set -euo pipefail

# ==============================================================================
# METHOD C1 FORWARD REFINEMENT GUARDED SUBMISSION WRAPPER
# ==============================================================================
# GOVERNANCE STATUS: PREFLIGHT_ONLY - AWAITING 22 OCTOBER 2026 SUPERVISOR SIGNOFF
# ==============================================================================

RUN_DIR="/scratch9/pr21vyci/runs/mode1_method_c1_forward_refinement"
cd "${RUN_DIR}"

# Governance Hold Guard: Prevent accidental un-authorized launch
AUTHORIZED=false
if [ "${AUTHORIZED}" != "true" ]; then
    echo "[GOVERNANCE HOLD] Method C solver jobs are strictly on hold pending formal Gate 6C supervisor review and authorization on 22 October 2026." >&2
    echo "[GOVERNANCE HOLD] Execution aborted cleanly without PBS submission." >&2
    exit 0
fi

# 1. Cryptographic hash preflight
EXPECTED_INP_SHA="614D3955E75105C707EC14D84F8E4ABBFB0A42415DAFAB8977816162DD731985"
EXPECTED_SUB_SHA="CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_PBS_SHA="1642C9B72864BCC06C4602E7CCB7AA7ED83417F377503E3C7C113B92CDE66D9C"

ACTUAL_INP_SHA=$(sha256sum M1_MC_C1_FORWARD_14K.inp | awk '{print toupper($1)}')
ACTUAL_SUB_SHA=$(sha256sum f42_mixed_uel.for | awk '{print toupper($1)}')
ACTUAL_PBS_SHA=$(sha256sum submit_M1_MC_C1_FORWARD_14K.pbs | awk '{print toupper($1)}')

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
echo "[GUARD PASS] Cryptographic hashes verified bitwise match."

# 2. Duplicate submission protection
if [ -f "${RUN_DIR}/SUBMITTED_JOB_ID.txt" ]; then
    PREV_JOB_ID=$(cat "${RUN_DIR}/SUBMITTED_JOB_ID.txt" | tr -d '[:space:]')
    if [ -n "${PREV_JOB_ID}" ]; then
        echo "[GUARD ERROR] Job was already submitted under ID ${PREV_JOB_ID}." >&2
        exit 2
    fi
fi

echo "Submitting Method C1 Forward Refinement Job to entry_imfdfkmq -> normal_imfdfkmq..."
JOB_ID=$(qsub submit_M1_MC_C1_FORWARD_14K.pbs)
echo "Submitted Job ID: ${JOB_ID}"
echo "${JOB_ID}" > "${RUN_DIR}/SUBMITTED_JOB_ID.txt"
