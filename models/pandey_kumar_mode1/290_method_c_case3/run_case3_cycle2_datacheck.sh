#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_290_method_c_case3_c2_job3"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running Abaqus Datacheck for Case 3 Cycle-2 Refined Deck..."
abaqus job="PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3" input="PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp" user="f42_mixed_uel.for" datacheck interactive
echo "Datacheck Finished with Exit Code: $?"
