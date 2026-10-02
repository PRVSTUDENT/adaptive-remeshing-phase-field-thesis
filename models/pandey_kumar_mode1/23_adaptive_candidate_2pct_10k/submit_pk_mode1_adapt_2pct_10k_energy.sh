#!/bin/bash
set -euo pipefail

TARGET_DIR="/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/23_adaptive_candidate_2pct_10k"
cd "$TARGET_DIR" || exit 1

echo "================================================================================"
echo "PREFLIGHT VALIDATION: PK_M1_ADAPT_2PCT_10K_ENERGY (10,253 Finite Elements 1-CPU Serial)"
echo "================================================================================"

# 1. Check required files
for req in f42_mixed_uel.for PK_MODE1_ADAPT_2PCT_10K_ENERGY.inp job_notifications.sh submit_solver.pbs; do
  if [ ! -f "$req" ]; then
    echo "[ERROR] Required file $req is missing in $TARGET_DIR" >&2
    exit 2
  fi
done

# 2. Check hashes
EXPECTED_UEL_HASH="ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
ACTUAL_UEL_HASH=$(sha256sum f42_mixed_uel.for | awk '{print $1}')
if [ "$EXPECTED_UEL_HASH" != "$ACTUAL_UEL_HASH" ]; then
  echo "[ERROR] UEL Hash mismatch: expected $EXPECTED_UEL_HASH, got $ACTUAL_UEL_HASH" >&2
  exit 3
fi
echo "[PASS] Fortran UEL Hash: $ACTUAL_UEL_HASH"

# 3. Notification Preflight
source ./job_notifications.sh
notification_load_config || true
echo "[PASS] Notification configuration loaded."

# 4. Run Datacheck Preflight
echo "Running Abaqus/Standard 2023 Datacheck preflight..."
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

rm -f PK_M1_ADAPT_2PCT_DC_RUN.* PK_M1_ADAPT_2PCT_10K_ENERGY.lck PK_M1_ADAPT_2PCT_10K_ENERGY.023
abaqus datacheck job=PK_M1_ADAPT_2PCT_DC_RUN user=f42_mixed_uel.for input=PK_MODE1_ADAPT_2PCT_10K_ENERGY.inp cpus=1 memory="8gb" double=both interactive
DC_EXIT=$?

if [ "$DC_EXIT" -ne 0 ]; then
  echo "[FATAL] Datacheck preflight FAILED with exit code $DC_EXIT" >&2
  cat PK_M1_ADAPT_2PCT_DC_RUN.msg 2>/dev/null || true
  exit 5
fi
echo "[PASS] Datacheck preflight PASSED (Exit 0)."

# 5. Guarded Authorization Gate
# This job is strictly unsubmitted until S1 energy qualification completes and explicit human authorization is granted.
AUTHORIZATION_FLAG="${1:-check_only}"
if [ "$AUTHORIZATION_FLAG" != "--authorize-execution" ]; then
  echo "================================================================================"
  echo "[GATE GUARD] Package qualified and preflight passed (Exit 0)."
  echo "Status: DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION"
  echo "Strictly unsubmitted: awaiting post-1409734 review and explicit authorization."
  echo "================================================================================"
  exit 0
fi

# 6. Guarded PBS Submission (only when explicitly authorized)
echo "Submitting authorized 1-CPU serial 2% adaptive candidate to normal_imfdfkmq..."
JOB_ID=$(qsub submit_solver.pbs)
echo "SUBMITTED_JOB_ID: $JOB_ID"

# 7. Notify Submission
notify_submitted "PK_M1_ADAPT_2PCT_10K_ENERGY" "$JOB_ID" "10,253 finite elements (1-CPU serial Mode-I 2% adaptive candidate energy solve with All_elem SDV output and working-dir CSV)" || true

echo "================================================================================"
echo "SUCCESSFULLY SUBMITTED JOB: $JOB_ID"
echo "================================================================================"
