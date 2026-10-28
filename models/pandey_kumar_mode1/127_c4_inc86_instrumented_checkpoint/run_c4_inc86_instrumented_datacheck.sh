#!/bin/bash
cd /scratch9/pr21vyci/runs/mode1_c4_inc86_instrumented_checkpoint
export XDG_RUNTIME_DIR="/tmp/runtime-pr21vyci"
mkdir -p "${XDG_RUNTIME_DIR}" 2>/dev/null || true
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus datacheck job=M1_C4_INC86_INSTRUMENTED_DC input=M1_C4_INC86_INSTRUMENTED.inp user=f42_unified_12dof_active_set_uel.for interactive
