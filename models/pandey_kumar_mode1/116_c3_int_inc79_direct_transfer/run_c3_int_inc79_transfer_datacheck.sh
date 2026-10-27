#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c3_int_inc79_direct_transfer"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

abaqus job=M1_C3_INT_XFER_DC input=M1_C3_INT_INC79_DIRECT_TRANSFER.inp user=f42_unified_12dof_active_set_uel.for datacheck interactive
