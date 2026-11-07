#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_method_a_hole_propagation
source /etc/profile.d/lmod.sh
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus job=PK_HOLE_METHOD_A_PROP_DC input=PK_HOLE_METHOD_A_PROP.inp user=f42_mixed_uel.for datacheck interactive
