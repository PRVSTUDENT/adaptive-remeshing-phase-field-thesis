#!/bin/bash
set -euo pipefail

cd /scratch9/pr21vyci/runs/mode1_c4_inc88_h23_underrelaxed_forward_continuation

export XDG_RUNTIME_DIR="/tmp/runtime-pr21vyci"
mkdir -p "${XDG_RUNTIME_DIR}" 2>/dev/null || true

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

abaqus job=M1_C4_INC88_H23_CONT_DC input=M1_C4_INC88_H23_CONT.inp user=f42_unified_12dof_active_set_uel.for datacheck interactive
