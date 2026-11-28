#!/bin/bash
set -euo pipefail
cd /scratchtemp/pr21vyci/runs/cost_analysis/case1_normal
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus job=PK_COST_CASE1_NORMAL_DATACHECK input=PK_COST_CASE1_NORMAL.inp user=f42_mixed_uel.for cpus=1 datacheck interactive
