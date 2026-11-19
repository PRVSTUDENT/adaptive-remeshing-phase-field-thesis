#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_289_method_c_demo_case"
cd "${RUN_DIR}"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus job=PK_METHOD_C_DEMO_COARSE_JOB1_DC input=PK_METHOD_C_DEMO_COARSE_JOB1.inp user=f42_mixed_uel.for datacheck interactive
echo "DATACHECK_FINISHED_WITH_CODE_$?"
