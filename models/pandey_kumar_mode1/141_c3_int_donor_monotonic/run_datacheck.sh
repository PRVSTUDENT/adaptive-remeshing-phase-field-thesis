#!/bin/bash
set -e
cd /scratch9/pr21vyci/runs/mode1_c3_int_donor_monotonic
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
rm -f M1_C3_INT_DONOR_MONOTONIC_DC.*
abaqus job=M1_C3_INT_DONOR_MONOTONIC_DC input=M1_C3_INT_DONOR_MONOTONIC.inp user=f42_mixed_uel.for datacheck interactive
