#!/bin/bash
set -e
cd /scratch9/pr21vyci/runs/mode1_c4_package145_continuous_reference
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
rm -f M1_C4_PACKAGE145_CONTINUOUS_REFERENCE_DC.*
abaqus job=M1_C4_PACKAGE145_CONTINUOUS_REFERENCE_DC input=M1_C4_PACKAGE145_CONTINUOUS_REFERENCE.inp user=f42_mixed_uel.for datacheck interactive
