#!/bin/bash
set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r14"
cd "${RUN_DIR}"

export XDG_RUNTIME_DIR="/tmp/runtime-pr21vyci"
mkdir -p "${XDG_RUNTIME_DIR}" 2>/dev/null || true

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running Abaqus 2023 datacheck for Package 108 Revision 14 (R14)..."
abaqus datacheck job=M1_C3_ACTIVE_SET_R14 input=M1_C3_ACTIVE_SET_R14_CONTINUATION.inp user=f42_unified_12dof_active_set_uel.for interactive
