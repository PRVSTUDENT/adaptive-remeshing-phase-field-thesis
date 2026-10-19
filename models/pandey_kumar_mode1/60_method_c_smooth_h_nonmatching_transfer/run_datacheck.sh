#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_package60_smooth_h_nonmatching_transfer

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Compiler check:"
command -v ifort
ifort --version | head -n 1

echo "Running Abaqus 2023 datacheck for M1_EXP_NONMATCHING_SMOOTH_H_650..."
abaqus datacheck job=M1_EXP_NONMATCHING_SMOOTH_H_650 input=M1_EXP_NONMATCHING_SMOOTH_H_650.inp user=f42_experimental_offset_uel.for interactive
RC=$?

echo "Datacheck finished with exit code: $RC"
exit $RC
