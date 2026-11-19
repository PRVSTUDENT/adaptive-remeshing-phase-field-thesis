#!/bin/bash
set -euo pipefail
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
cd /scratch9/pr21vyci/runs/mode1_289_method_c_demo_job2
abaqus python extract_job2_observables.py --run-dir /scratch9/pr21vyci/runs/mode1_289_method_c_demo_job2
