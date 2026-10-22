#!/bin/bash
set -euo pipefail
cd "${1:-.}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running Abaqus Datacheck on M1_DONOR_SAMEPROCESS_STAGGERED.inp..."
abaqus datacheck job=M1_DONOR_SAMEPROCESS_STAGGERED_DC input=M1_DONOR_SAMEPROCESS_STAGGERED.inp user=f42_mixed_uel.for interactive
DC_EXIT=$?
echo "Datacheck finished with Exit Code: ${DC_EXIT}"
exit ${DC_EXIT}
