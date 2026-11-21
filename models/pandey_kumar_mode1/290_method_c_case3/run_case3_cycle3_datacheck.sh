#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_290_method_c_case3_c3_job4"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running Abaqus Datacheck for Case 3 Cycle-3 Refined Deck..."
abaqus job="PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_DC" input="PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp" user="f42_mixed_uel.for" datacheck interactive
echo "Datacheck Finished with Exit Code: $?"
