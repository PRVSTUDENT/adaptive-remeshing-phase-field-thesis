#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

TARGET_DIR="/scratch/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/16_energy_qualification_reference_15k"
cd "$TARGET_DIR" || exit 1

echo "================================================================================"
echo "PREFLIGHT VALIDATION: PK_M1_REF15K_ENERGY (15,192 Finite Elements 1-CPU Serial)"
echo "================================================================================"

# 1. Check required files
for req in f42_mixed_uel.for PK_MODE1_REF15K_ENERGY.inp job_notifications.sh submit_solver.pbs; do
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

EXPECTED_INP_HASH="ec560a4c265730647b43dab125d166ebc57cac285d574d38222a498a967535d9"
ACTUAL_INP_HASH=$(sha256sum PK_MODE1_REF15K_ENERGY.inp | awk '{print $1}')
if [ "$EXPECTED_INP_HASH" != "$ACTUAL_INP_HASH" ]; then
  echo "[ERROR] INP Hash mismatch: expected $EXPECTED_INP_HASH, got $ACTUAL_INP_HASH" >&2
  exit 4
fi
echo "[PASS] Input Deck Hash: $ACTUAL_INP_HASH"

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

rm -f PK_M1_REF15K_DC_RUN.* PK_M1_REF15K_ENERGY.lck PK_M1_REF15K_ENERGY.023
abaqus datacheck job=PK_M1_REF15K_DC_RUN user=f42_mixed_uel.for input=PK_MODE1_REF15K_ENERGY.inp cpus=1 memory="8gb" double=both interactive
DC_EXIT=$?

if [ "$DC_EXIT" -ne 0 ]; then
  echo "[FATAL] Datacheck preflight FAILED with exit code $DC_EXIT" >&2
  cat PK_M1_REF15K_DC_RUN.msg 2>/dev/null || true
  exit 5
fi
echo "[PASS] Datacheck preflight PASSED (Exit 0)."

# Archive previous run files if present before fresh launch
if [ -f PK_M1_REF15K_ENERGY.odb ]; then
  echo "Archiving previous run files to job_1409705_archive/..."
  mkdir -p job_1409705_archive
  for f in PK_M1_REF15K_ENERGY.dat PK_M1_REF15K_ENERGY.msg PK_M1_REF15K_ENERGY.odb PK_M1_REF15K_ENERGY.out PK_M1_REF15K_ENERGY.prt PK_M1_REF15K_ENERGY.sta PK_M1_REF15K_ENERGY.err PK_M1_REF15K_ENERGY.com; do
    if [ -f "$f" ]; then
      mv "$f" job_1409705_archive/
    fi
  done
  echo "[PASS] Archived previous run artifacts."
fi

# 5. Guarded PBS Submission
echo "Submitting authorized 1-CPU serial replacement job to normal_imfdfkmq..."
JOB_ID=$(qsub submit_solver.pbs)
echo "SUBMITTED_JOB_ID: $JOB_ID"

# 6. Notify Submission
notify_submitted "PK_M1_REF15K_ENERGY" "$JOB_ID" "15,192 finite elements (1-CPU serial Mode-I energy reference solve with All_elem SDV output and working-dir CSV)" || true

echo "================================================================================"
echo "SUCCESSFULLY SUBMITTED AUTHORITATIVE REPLACEMENT JOB: $JOB_ID"
echo "================================================================================"
