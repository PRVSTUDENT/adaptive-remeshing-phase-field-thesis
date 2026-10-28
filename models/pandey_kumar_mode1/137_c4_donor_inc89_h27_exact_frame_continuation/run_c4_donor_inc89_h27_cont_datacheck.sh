#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c4_donor_inc89_h27_exact_frame_continuation"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

abaqus job=M1_C4_INC89_H27_CONT_DC input=M1_C4_INC89_H27_CONT.inp user=f42_unified_12dof_active_set_uel.for datacheck interactive
