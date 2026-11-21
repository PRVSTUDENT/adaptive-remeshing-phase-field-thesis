#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_290_method_c_case3_c3_job4"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Extracting donor state from Job 4 ODB..."
abaqus python extract_case3_cycle3_donor_fields.py --run-dir "${RUN_DIR}" --out-json "${RUN_DIR}/donor_case3_cycle3_state.json"
echo "Extraction completed successfully."
