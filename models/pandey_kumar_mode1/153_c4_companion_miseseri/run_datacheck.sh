#!/bin/bash
set -euo pipefail
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus datacheck job=M1_C4_COMPANION_MISESERI_DC input=M1_C4_COMPANION_MISESERI.inp interactive
EXIT_CODE=$?
echo "Datacheck exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
