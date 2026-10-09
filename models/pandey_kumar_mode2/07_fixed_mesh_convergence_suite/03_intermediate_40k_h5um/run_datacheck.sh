#!/bin/bash
set -euo pipefail
cd "/scratch9/pr21vyci/runs/mode2_fixed_convergence/03_intermediate_40k_h5um"

source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

rm -f "M2_FIX_INT_40K.lck" "M2_FIX_INT_40K.023" 2>/dev/null || true
echo "Running Abaqus Datacheck for M2_FIX_INT_40K..."
abaqus datacheck job="M2_FIX_INT_40K" user="f42_mixed_uel_mode2_miehe.for" input="M2_FIX_INT_40K.inp" cpus=1 double=both interactive
echo "DATACHECK_EXIT: $?"
