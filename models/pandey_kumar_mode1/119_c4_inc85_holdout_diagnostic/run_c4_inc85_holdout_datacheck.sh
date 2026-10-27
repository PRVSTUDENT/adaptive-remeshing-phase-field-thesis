#!/bin/bash
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus datacheck job=M1_C4_INC85_HOLDOUT_DC input=M1_C4_INC85_HOLDOUT.inp user=f42_unified_12dof_active_set_uel.for interactive
