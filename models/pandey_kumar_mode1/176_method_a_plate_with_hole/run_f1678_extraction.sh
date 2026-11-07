#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_method_a_hole_f1664_prod

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running extraction for M1_HOLE_F1664_METHOD_A_PROD.odb..."
abaqus python extract_f1678_prod_results.py \
    --odb M1_HOLE_F1664_METHOD_A_PROD.odb \
    --energy-csv uel_energy_balance.csv \
    --n-phys 20213 \
    --out-summary f1678_prod_summary.json \
    --out-rf-csv f1678_prod_rf_u.csv \
    --out-crack-csv f1678_prod_crack_path.csv

EXIT_CODE=$?
echo "Extraction finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
