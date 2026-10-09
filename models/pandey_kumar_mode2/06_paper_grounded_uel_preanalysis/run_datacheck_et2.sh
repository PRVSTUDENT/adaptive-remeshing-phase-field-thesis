#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode2_j2_adapted_stabilized_et2

source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

rm -f Job-2_UEL.lck Job-2_UEL.023 2>/dev/null || true
echo "Running Abaqus Datacheck for M2_J2_ADAPT_ET2_STAB..."
abaqus datacheck job=Job-2_UEL user=f42_mixed_uel_mode2_miehe.for input=Job-2_UEL.inp cpus=1 double=both interactive
echo "DATACHECK_EXIT: $?"
