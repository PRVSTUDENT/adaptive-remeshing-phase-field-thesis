#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_290_method_c_case3_c4_job5"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running spatial crack extraction for Case 3 Cycle 4 Job 5..."
abaqus python extract_case3_job5_spatial_crack.py \
    "${RUN_DIR}/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.odb" \
    "${RUN_DIR}/PK_METHOD_C_CASE3_CYCLE4_PHYS.inp" \
    "${RUN_DIR}/job5_spatial_crack.json"

echo "Spatial crack extraction finished with exit code $?"
ls -lh "${RUN_DIR}/job5_spatial_crack.json"
