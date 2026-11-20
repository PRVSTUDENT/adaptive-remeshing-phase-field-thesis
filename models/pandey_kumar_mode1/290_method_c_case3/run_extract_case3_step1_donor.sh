#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_290_method_c_case3"
cd "${RUN_DIR}"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python extract_case3_step1_donor_fields.py --run-dir "${RUN_DIR}"
echo "EXTRACTION_COMPLETE"
