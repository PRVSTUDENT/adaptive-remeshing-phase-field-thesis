#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

PACKAGE_DIR="/scratch/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/30_stage14_adaptive_candidate_spatial_fine"
cd "${PACKAGE_DIR}" || exit 1

if [ ! -f ./job_notifications.sh ]; then
  echo "[SUBMIT ERROR] job_notifications.sh missing" >&2
  exit 10
fi

source ./job_notifications.sh
notification_load_config || true

echo "=== PRE-SUBMISSION INTEGRITY CHECKS ==="
EXPECTED_INP_SHA="537c8c6617945afd66e135c1df4e2c34211f47fbeeec44e4c145a8551cc1eefd"
EXPECTED_FOR_SHA="ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

ACTUAL_INP_SHA=$(sha256sum PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.inp | awk '{print $1}')
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
echo "Submitting Stage 14U-AM Spatial Fine candidate job to PBS..."
JOB_ID=$(qsub submit_solver.pbs)
echo "SUBMITTED_JOB_ID=${JOB_ID}"

notify_submitted "${JOB_ID}" "PK_M1_14AM_SOLVE" "normal_imfdfkmq" "Gate-6B Stage 14U-AM Controlled Adaptive Spatial-Resolution Convergence Solve" || true
echo "Submission complete: ${JOB_ID}"
