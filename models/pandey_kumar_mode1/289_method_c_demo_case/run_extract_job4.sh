#!/bin/bash
set -euo pipefail
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load abaqus/2023
abaqus python /scratch9/pr21vyci/runs/mode1_289_method_c_demo_job4/extract_job4_observables.py --run-dir /scratch9/pr21vyci/runs/mode1_289_method_c_demo_job4
