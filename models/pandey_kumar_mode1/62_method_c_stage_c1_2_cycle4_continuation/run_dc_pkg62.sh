#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_stage_c1_2_cycle4_continuation
source /etc/profile.d/lmod.sh 2>/dev/null || true
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus job=M1_MC_STAGE_C1_2_CYCLE4_CONT_DC input=M1_MC_STAGE_C1_2_CYCLE4_CONT.inp user=f42_mixed_uel.for datacheck interactive
echo "DATACHECK_EXIT=$?"
