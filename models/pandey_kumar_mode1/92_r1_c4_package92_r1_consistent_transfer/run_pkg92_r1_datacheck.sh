#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_package92_r1_c4_consistent_transfer
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
rm -f M1_C4_PACKAGE92_R1_TRANSFER.log M1_C4_PACKAGE92_R1_TRANSFER.dat M1_C4_PACKAGE92_R1_TRANSFER.msg M1_C4_PACKAGE92_R1_TRANSFER.sta
abaqus job=M1_C4_PACKAGE92_R1_TRANSFER input=M1_C4_PACKAGE92_R1_TRANSFER.inp user=f42_mixed_uel.for datacheck interactive
