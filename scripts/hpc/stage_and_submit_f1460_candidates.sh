#!/bin/bash
set -euo pipefail

source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

WORKTREE="/home/pr21vyci/projects/mode2_reproduction_worktree"
PKG38="${WORKTREE}/models/pandey_kumar_mode1/38_method_b_native_final_14k"
PKG40="${WORKTREE}/models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k"

EXPECTED_UEL_HASH="CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_DECK38_HASH="39CFD486C87A48A72F145919998E4FE698367DDA452B0F20C2E8F43EA13B0A6D"
EXPECTED_DECK40_HASH="1209F716971719B1A740FF92C8B5503BA9784F10D5EEDD3C5035C81D40A066E9"

echo "=========================================================="
echo "TASK F1460: STAGING, PREFLIGHT & SUBMISSION PIPELINE"
echo "=========================================================="

# -----------------------------------------------------------------------------
# CANDIDATE 1: M1_MB_NATIVE_8T_B (Stage B Determinism Repeat on 14,677 FE mesh)
# -----------------------------------------------------------------------------
DIR1="/scratch9/pr21vyci/runs/mode1_method_b_native_8t_b"
echo ">>> [1/2] Staging Candidate 1: M1_MB_NAT_8TB in ${DIR1}..."
mkdir -p "${DIR1}"
cp -f "${PKG38}/M1_MB_NATIVE_FINAL_1S.inp" "${DIR1}/"
cp -f "${PKG38}/f42_mixed_uel.for" "${DIR1}/"
cp -f "${PKG38}/submit_M1_MB_NATIVE_8T_B.pbs" "${DIR1}/"
cp -f "${WORKTREE}/scripts/hpc/notifications/job_notifications.sh" "${DIR1}/"
chmod +x "${DIR1}/job_notifications.sh" "${DIR1}/submit_M1_MB_NATIVE_8T_B.pbs"

# Hash verification
HASH_DECK1=$(sha256sum "${DIR1}/M1_MB_NATIVE_FINAL_1S.inp" | awk '{print toupper($1)}')
HASH_UEL1=$(sha256sum "${DIR1}/f42_mixed_uel.for" | awk '{print toupper($1)}')
if [ "${HASH_DECK1}" != "${EXPECTED_DECK38_HASH}" ]; then
    echo "[ERROR] Candidate 1 deck hash mismatch: ${HASH_DECK1} != ${EXPECTED_DECK38_HASH}" >&2
    exit 1
fi
if [ "${HASH_UEL1}" != "${EXPECTED_UEL_HASH}" ]; then
    echo "[ERROR] Candidate 1 UEL hash mismatch: ${HASH_UEL1} != ${EXPECTED_UEL_HASH}" >&2
    exit 1
fi
echo "[PASS] Candidate 1 hashes verified bitwise match."

# Datacheck for Candidate 1
cd "${DIR1}"
rm -f M1_MB_NATIVE_8T_B_DC.* 2>/dev/null || true
echo ">>> Executing Abaqus Datacheck for Candidate 1 (8 CPUs, mp_mode=threads)..."
abaqus datacheck job=M1_MB_NATIVE_8T_B_DC \
       user=f42_mixed_uel.for \
       input=M1_MB_NATIVE_FINAL_1S.inp \
       cpus=8 \
       mp_mode=threads \
       memory="24gb" \
       double=both \
       interactive > M1_MB_NATIVE_8T_B_DC.log 2>&1
DC_EXIT1=$?
if [ ${DC_EXIT1} -ne 0 ] || ! grep -q -E "COMPLETED|THE ANALYSIS HAS COMPLETED SUCCESSFULLY" M1_MB_NATIVE_8T_B_DC.log; then
    echo "[ERROR] Candidate 1 datacheck failed with code ${DC_EXIT1}." >&2
    cat M1_MB_NATIVE_8T_B_DC.log >&2 || true
    exit 2
fi
echo "[PASS] Candidate 1 Datacheck qualified successfully (Exit 0)."

# Submit Candidate 1
echo ">>> Submitting Candidate 1 via qsub..."
JOB_ID1=$(qsub submit_M1_MB_NATIVE_8T_B.pbs)
echo "=== SUBMITTED CANDIDATE 1 JOB ID: ${JOB_ID1} ==="
echo "${JOB_ID1}" > "${DIR1}/SUBMITTED_JOB_ID.txt"
echo "[$(date -Iseconds)] Submitted PBS Job ID: ${JOB_ID1} (8 CPUs, 24 GB RAM, walltime 24:00:00, queue normal_imfdfkmq)" >> "${DIR1}/SUBMISSION_HISTORY.log"

if [ -f "${DIR1}/job_notifications.sh" ]; then
    source "${DIR1}/job_notifications.sh"
    notification_load_config || true
    if type notify_submitted >/dev/null 2>&1; then
        notify_submitted "${JOB_ID1}" "M1_MB_NAT_8TB" "normal_imfdfkmq" "8" "24gb" "24:00:00" || true
    fi
fi

# -----------------------------------------------------------------------------
# CANDIDATE 2: M1_MB_CORR_8TA (8-thread SMP Parity on 14,483 FE Corrected Mesh)
# -----------------------------------------------------------------------------
DIR2="/scratch9/pr21vyci/runs/mode1_method_b_corrected_8t_a"
echo ">>> [2/2] Staging Candidate 2: M1_MB_CORR_8TA in ${DIR2}..."
mkdir -p "${DIR2}"
cp -f "${PKG40}/M1_MB_CORRECTED_PROPAGATION_14K.inp" "${DIR2}/"
cp -f "${PKG40}/f42_mixed_uel.for" "${DIR2}/"
cp -f "${PKG40}/submit_M1_MB_CORR_8TA.pbs" "${DIR2}/"
cp -f "${WORKTREE}/scripts/hpc/notifications/job_notifications.sh" "${DIR2}/"
chmod +x "${DIR2}/job_notifications.sh" "${DIR2}/submit_M1_MB_CORR_8TA.pbs"

# Hash verification
HASH_DECK2=$(sha256sum "${DIR2}/M1_MB_CORRECTED_PROPAGATION_14K.inp" | awk '{print toupper($1)}')
HASH_UEL2=$(sha256sum "${DIR2}/f42_mixed_uel.for" | awk '{print toupper($1)}')
if [ "${HASH_DECK2}" != "${EXPECTED_DECK40_HASH}" ]; then
    echo "[ERROR] Candidate 2 deck hash mismatch: ${HASH_DECK2} != ${EXPECTED_DECK40_HASH}" >&2
    exit 3
fi
if [ "${HASH_UEL2}" != "${EXPECTED_UEL_HASH}" ]; then
    echo "[ERROR] Candidate 2 UEL hash mismatch: ${HASH_UEL2} != ${EXPECTED_UEL_HASH}" >&2
    exit 3
fi
echo "[PASS] Candidate 2 hashes verified bitwise match."

# Datacheck for Candidate 2
cd "${DIR2}"
rm -f M1_MB_CORRECTED_8T_A_DC.* 2>/dev/null || true
echo ">>> Executing Abaqus Datacheck for Candidate 2 (8 CPUs, mp_mode=threads)..."
abaqus datacheck job=M1_MB_CORRECTED_8T_A_DC \
       user=f42_mixed_uel.for \
       input=M1_MB_CORRECTED_PROPAGATION_14K.inp \
       cpus=8 \
       mp_mode=threads \
       memory="24gb" \
       double=both \
       interactive > M1_MB_CORRECTED_8T_A_DC.log 2>&1
DC_EXIT2=$?
if [ ${DC_EXIT2} -ne 0 ] || ! grep -q -E "COMPLETED|THE ANALYSIS HAS COMPLETED SUCCESSFULLY" M1_MB_CORRECTED_8T_A_DC.log; then
    echo "[ERROR] Candidate 2 datacheck failed with code ${DC_EXIT2}." >&2
    cat M1_MB_CORRECTED_8T_A_DC.log >&2 || true
    exit 4
fi
echo "[PASS] Candidate 2 Datacheck qualified successfully (Exit 0)."

# Submit Candidate 2
echo ">>> Submitting Candidate 2 via qsub..."
JOB_ID2=$(qsub submit_M1_MB_CORR_8TA.pbs)
echo "=== SUBMITTED CANDIDATE 2 JOB ID: ${JOB_ID2} ==="
echo "${JOB_ID2}" > "${DIR2}/SUBMITTED_JOB_ID.txt"
echo "[$(date -Iseconds)] Submitted PBS Job ID: ${JOB_ID2} (8 CPUs, 24 GB RAM, walltime 24:00:00, queue normal_imfdfkmq)" >> "${DIR2}/SUBMISSION_HISTORY.log"

if [ -f "${DIR2}/job_notifications.sh" ]; then
    source "${DIR2}/job_notifications.sh"
    notification_load_config || true
    if type notify_submitted >/dev/null 2>&1; then
        notify_submitted "${JOB_ID2}" "M1_MB_CORR_8TA" "normal_imfdfkmq" "8" "24gb" "24:00:00" || true
    fi
fi

echo "=========================================================="
echo "ALL CANDIDATES STAGED, DATACHECK-QUALIFIED, AND SUBMITTED"
echo "Candidate 1: ${JOB_ID1} (M1_MB_NAT_8TB)"
echo "Candidate 2: ${JOB_ID2} (M1_MB_CORR_8TA)"
echo "=========================================================="
