#!/bin/bash
set -euo pipefail
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
extract_script="${1:-/scratch9/pr21vyci/runs/f1859_suite/extract_adaptive_damage_contours.py}"
if [ "$#" -gt 0 ]; then shift; fi
/cluster/application/abaqus/2023/Commands/abaqus python "$extract_script" "$@"
