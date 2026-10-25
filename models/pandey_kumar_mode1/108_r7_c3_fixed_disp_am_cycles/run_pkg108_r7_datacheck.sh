#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r7

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

abaqus job=M1_C3_STAGGERED_R7 input=M1_C3_STAGGERED_R7_CONTINUATION.inp user=f42_experimental_irreversible_uel.for datacheck interactive
