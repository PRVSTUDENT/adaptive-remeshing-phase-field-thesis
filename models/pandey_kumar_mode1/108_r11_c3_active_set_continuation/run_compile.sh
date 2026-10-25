#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_c3_active_set_r11_test
if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus make library=f42_unified_12dof_active_set_uel.for