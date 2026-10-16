#!/bin/bash
set -e
source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
cd /scratch9/pr21vyci/runs/mode1_stage_c1_1_nonmatching_transfer
rm -f M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD_DC.*
abaqus job=M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD_DC input=M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD.inp user=f42_mixed_uel.for datacheck interactive
EXIT_CODE=$?
echo "Datacheck finished with exit code: $EXIT_CODE"
exit $EXIT_CODE
