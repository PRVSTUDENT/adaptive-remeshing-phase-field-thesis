#!/bin/bash
set -euo pipefail

PACKAGE_DIR="/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/26_stage14_adaptive_candidate_14k_4thread"
cd "${PACKAGE_DIR}" || exit 1

if [ ! -f ./job_notifications.sh ]; then
  echo "[SUBMIT ERROR] job_notifications.sh missing" >&2
  exit 10
fi

source ./job_notifications.sh
notification_load_config || true

echo "=== PRE-SUBMISSION INTEGRITY CHECKS ==="
EXPECTED_INP_SHA="26d873fb2e68055c80550d1dd981766bcaf46e13d3d0a7ba6411b63d9c382d35"
EXPECTED_FOR_SHA="ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

ACTUAL_INP_SHA=$(sha256sum PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp | awk '{print $1}')
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
echo "Submitting 4-thread Stage-A qualification job to PBS..."
JOB_ID=$(qsub submit_solver.pbs)
echo "SUBMITTED_JOB_ID=${JOB_ID}"

notify_submitted "${JOB_ID}" "PK_M1_14K_4T" "normal_imfdfkmq" "4-thread Stage-A shared-memory qualification for Stage-14 Adaptive 14k Fracture" || true
echo "Submission complete: ${JOB_ID}"
