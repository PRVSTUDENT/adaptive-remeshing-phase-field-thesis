#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_method_a_hole_f1664_prod

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running time-resolved crack extraction for M1_HOLE_F1664_METHOD_A_PROD.odb..."
abaqus python extract_f1679_time_resolved_crack.py \
    --odb M1_HOLE_F1664_METHOD_A_PROD.odb \
    --inp PK_HOLE_F1664_METHOD_A_PROD.inp \
    --n-phys 20213 \
    --out-summary f1679_time_resolved_crack_summary.json \
    --out-csv f1679_time_resolved_crack_states.csv

EXIT_CODE=$?
echo "Time-resolved crack extraction finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
