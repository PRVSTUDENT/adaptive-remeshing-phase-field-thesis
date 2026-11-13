#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_method_a_hole_coarse

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running nodal U extraction for PK_HOLE_COARSE_JOB1.odb..."
abaqus python extract_case2_nodal_u.py
EXIT_CODE=$?

echo "Extraction finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
