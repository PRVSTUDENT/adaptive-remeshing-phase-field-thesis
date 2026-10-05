#!/bin/bash
set -euo pipefail

PACKAGE_DIR="/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/32_stage14_remeshing_errortarget_sensitivity"
ODB_PATH="/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/93_mode1_preanalysis_inf_companion_2906/PK_M1_JOB1_INF_COMPANION_2906.odb"

cd "$PACKAGE_DIR" || exit 1

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== STARTING STAGE 14U-AP ERRORTARGET SENSITIVITY REMESHING ==="
echo "ODB: $ODB_PATH"
echo "Package Dir: $PACKAGE_DIR"

abaqus cae noGUI=execute_stage14uap_error_target_sensitivity.py -- "$ODB_PATH" "$PACKAGE_DIR"
EXIT_CODE=$?

echo "=== FINISHED STAGE 14U-AP SENSITIVITY REMESHING (EXIT: $EXIT_CODE) ==="
exit "$EXIT_CODE"
