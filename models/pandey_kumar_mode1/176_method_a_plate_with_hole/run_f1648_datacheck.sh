#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_method_a_hole_finer

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running Abaqus 2023 datacheck for PK_HOLE_METHOD_A_FINER..."
abaqus job=PK_HOLE_METHOD_A_FINER_DC input=PK_HOLE_METHOD_A_FINER.inp user=f42_mixed_uel.for datacheck interactive
EXIT_CODE=$?

echo "Datacheck finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
