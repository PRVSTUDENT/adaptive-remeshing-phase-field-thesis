#!/bin/bash
set -euo pipefail

source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

WORKTREE="/home/pr21vyci/projects/mode2_reproduction_worktree"
PKG40="${WORKTREE}/models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k"

EXPECTED_UEL_HASH="CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_DECK40_HASH="1209F716971719B1A740FF92C8B5503BA9784F10D5EEDD3C5035C81D40A066E9"

echo "=========================================================="
echo "TASK F1471: STAGING, PREFLIGHT & SUBMISSION PIPELINE"
echo "TARGET: M1_MB_CORR_8TB (Stage B 8-Thread Determinism Repeat)"
echo "=========================================================="

DIR="/scratch9/pr21vyci/runs/mode1_method_b_corrected_8t_b"
echo ">>> Staging Candidate: M1_MB_CORR_8TB in ${DIR}..."
mkdir -p "${DIR}"
cp -f "${PKG40}/M1_MB_CORRECTED_PROPAGATION_14K.inp" "${DIR}/"
cp -f "${PKG40}/f42_mixed_uel.for" "${DIR}/"
cp -f "${PKG40}/submit_M1_MB_CORR_8TB.pbs" "${DIR}/"
cp -f "${WORKTREE}/scripts/hpc/notifications/job_notifications.sh" "${DIR}/"
chmod +x "${DIR}/job_notifications.sh" "${DIR}/submit_M1_MB_CORR_8TB.pbs"

# 1. Cryptographic Hash verification
HASH_DECK=$(sha256sum "${DIR}/M1_MB_CORRECTED_PROPAGATION_14K.inp" | awk '{print toupper($1)}')
HASH_UEL=$(sha256sum "${DIR}/f42_mixed_uel.for" | awk '{print toupper($1)}')
if [ "${HASH_DECK}" != "${EXPECTED_DECK40_HASH}" ]; then
    echo "[GUARD ERROR] Deck hash mismatch: ${HASH_DECK} != ${EXPECTED_DECK40_HASH}" >&2
    exit 1
fi
if [ "${HASH_UEL}" != "${EXPECTED_UEL_HASH}" ]; then
    echo "[GUARD ERROR] UEL hash mismatch: ${HASH_UEL} != ${EXPECTED_UEL_HASH}" >&2
    exit 1
fi
echo "[GUARD PASS] Cryptographic hashes verified bitwise match."

# 2. Duplicate submission protection
if [ -f "${DIR}/SUBMITTED_JOB_ID.txt" ]; then
    PREV_JOB_ID=$(cat "${DIR}/SUBMITTED_JOB_ID.txt" | tr -d '[:space:]')
    if [ -n "${PREV_JOB_ID}" ]; then
        echo "[GUARD ERROR] Job was already submitted under ID ${PREV_JOB_ID} in ${DIR}." >&2
        exit 2
    fi
fi

EXISTING_JOB=$(qstat -u pr21vyci 2>/dev/null | grep -E 'M1_MB_CORR_8TB' || true)
if [ -n "${EXISTING_JOB}" ]; then
    echo "[GUARD ERROR] Active or queued M1_MB_CORR_8TB job already exists in PBS: ${EXISTING_JOB}" >&2
    exit 2
fi
echo "[GUARD PASS] Zero duplicate PBS jobs or prior submission records detected."

# 3. FlexNet license check
LMUTIL_PATH="/cluster/application/abaqus/2023/linux_a64/code/bin/lmutil"
LICENSE_SERVER="25000@license4.imfd.tu-freiberg.de"
LMSTAT_OUT=$("${LMUTIL_PATH}" lmstat -c "${LICENSE_SERVER}" -f standard 2>/dev/null || true)
TOKENS_IN_USE=$(echo "${LMSTAT_OUT}" | grep -o 'Total of [0-9]* licenses in use' | grep -o '[0-9]*' || echo "300")
TOKENS_TOTAL=$(echo "${LMSTAT_OUT}" | grep -o 'Total of [0-9]* licenses issued' | grep -o '[0-9]*' || echo "300")
TOKENS_FREE=$((TOKENS_TOTAL - TOKENS_IN_USE))
echo "License status: ${TOKENS_IN_USE}/${TOKENS_TOTAL} in use (${TOKENS_FREE} free, minimum 5 required)."

if [ "${TOKENS_FREE}" -lt 5 ]; then
    echo "[LICENSE GATE BLOCKED] Insufficient floating licenses (${TOKENS_FREE} free < 5 required). Cannot run datacheck." >&2
    exit 3
fi

# 4. Execute Abaqus 2023 datacheck
cd "${DIR}"
rm -f M1_MB_CORRECTED_8T_B_DC.* 2>/dev/null || true
echo ">>> Executing Abaqus Datacheck for M1_MB_CORR_8TB (8 CPUs, mp_mode=threads)..."
abaqus datacheck job=M1_MB_CORRECTED_8T_B_DC \
       user=f42_mixed_uel.for \
       input=M1_MB_CORRECTED_PROPAGATION_14K.inp \
       cpus=8 \
       mp_mode=threads \
       memory="24gb" \
       double=both \
       interactive > M1_MB_CORRECTED_8T_B_DC.log 2>&1

DC_EXIT=$?
if [ ${DC_EXIT} -ne 0 ] || ! grep -q -E "COMPLETED|THE ANALYSIS HAS COMPLETED SUCCESSFULLY" M1_MB_CORRECTED_8T_B_DC.log; then
    echo "[DATACHECK FATAL] Datacheck failed with code ${DC_EXIT}." >&2
    cat M1_MB_CORRECTED_8T_B_DC.log >&2 || true
    exit 4
fi
echo "[DATACHECK PASS] Datacheck qualified successfully (Exit 0)."

# 5. Submit authorized PBS job via entry_imfdfkmq
echo ">>> Submitting M1_MB_CORR_8TB via qsub (entry_imfdfkmq -> normal_imfdfkmq)..."
JOB_ID=$(qsub submit_M1_MB_CORR_8TB.pbs)
echo "=== SUBMITTED PBS JOB ID: ${JOB_ID} ==="
echo "${JOB_ID}" > "${DIR}/SUBMITTED_JOB_ID.txt"
echo "[$(date -Iseconds)] Submitted PBS Job ID: ${JOB_ID} (8 CPUs, 24 GB RAM, walltime 24:00:00, queue entry_imfdfkmq -> normal_imfdfkmq)" >> "${DIR}/SUBMISSION_HISTORY.log"

if [ -f "${DIR}/job_notifications.sh" ]; then
    source "${DIR}/job_notifications.sh"
    notification_load_config || true
    if type notify_submitted >/dev/null 2>&1; then
        notify_submitted "${JOB_ID}" "M1_MB_CORR_8TB" "entry_imfdfkmq" "8" "24gb" "24:00:00" || true
    fi
fi

echo "TASK F1471 SUBMISSION COMPLETE: ${JOB_ID}"
