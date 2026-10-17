#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_stage_c1_2_propagation_stage2_fine_dt
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus job=M1_MC_PROP_S2_FINE_DT_DC input=M1_MC_PROP_S2_FINE_DT.inp user=f42_mixed_uel.for datacheck interactive
echo "DATACHECK_EXIT=$?"
grep -E "ERROR|COMPLETED|SUCCESSFUL" M1_MC_PROP_S2_FINE_DT_DC.log M1_MC_PROP_S2_FINE_DT_DC.dat || true
