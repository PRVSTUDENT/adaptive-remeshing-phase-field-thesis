#!/bin/bash
set -euo pipefail

PACKAGE_DIR="/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/26_stage14_temporal_refined_candidate_2x"
cd "${PACKAGE_DIR}" || exit 1

if [ ! -f ./job_notifications.sh ]; then
  echo "[SUBMIT ERROR] job_notifications.sh missing" >&2
  exit 10
fi

source ./job_notifications.sh
notification_load_config || true

echo "=== PRE-SUBMISSION INTEGRITY CHECKS ==="
EXPECTED_INP_SHA="9ac284e6a65e59042e9588db628f9b15d5cbe345d62d164b477304d4813bc526"
EXPECTED_FOR_SHA="ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

ACTUAL_INP_SHA=$(sha256sum PK_MODE1_STAGE14_ADAPT_14K_TEMPORAL_2X.inp | awk '{print $1}')
ACTUAL_FOR_SHA=$(sha256sum f42_mixed_uel.for | awk '{print $1}')

if [ "${ACTUAL_INP_SHA}" != "${EXPECTED_INP_SHA}" ]; then
  echo "[FATAL] Input deck SHA mismatch: expected ${EXPECTED_INP_SHA}, got ${ACTUAL_INP_SHA}" >&2
  exit 1
fi

if [ "${ACTUAL_FOR_SHA}" != "${EXPECTED_FOR_SHA}" ]; then
  echo "[FATAL] Fortran subroutine SHA mismatch: expected ${EXPECTED_FOR_SHA}, got ${ACTUAL_FOR_SHA}" >&2
  exit 1
fi

echo "Hash verification: PASS"
echo "Submitting 2x temporal refinement diagnostic job to PBS (normal_imfdfkmq)..."
JOB_ID=$(qsub submit_solver.pbs)
echo "SUBMITTED_JOB_ID=${JOB_ID}"

notify_submitted "${JOB_ID}" "PK_M1_ADAPT_14K_T2X" "normal_imfdfkmq" "Gate-6B Stage 14U-AG 2x temporal refinement diagnostic for Stage-14 Adaptive 14k Fracture" || true
echo "Submission complete: ${JOB_ID}"
