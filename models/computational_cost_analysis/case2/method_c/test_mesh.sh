#!/bin/bash
source /etc/profile.d/lmod.sh
module load abaqus/2023
abaqus cae noGUI=/scratchtemp/pr21vyci/runs/cost_analysis/case2_method_c/generate_case2_adaptive_corridor_mesh.py -- /scratchtemp/pr21vyci/runs/cost_analysis/case2_method_c/PK_METHOD_C_CASE2_CYCLE1_PHYS.inp 0.5000 0.5000
