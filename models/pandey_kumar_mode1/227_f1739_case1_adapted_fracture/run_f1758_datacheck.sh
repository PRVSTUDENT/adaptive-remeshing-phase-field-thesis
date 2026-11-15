#!/bin/bash
set -euo pipefail

cd /scratch9/pr21vyci/runs/mode1_pk_f1758_case1_preflight

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Running Abaqus Datacheck for PK_F1758_CASE_1_DC ==="
abaqus job=PK_F1758_CASE_1_DC input=PK_F1758_CASE_1_PROD.inp user=f42_mixed_uel.for datacheck -interactive
echo "=== Datacheck Finished with Exit Code $? ==="
