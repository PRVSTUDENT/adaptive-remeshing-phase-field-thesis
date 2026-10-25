#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${USER}}"
mkdir -p "${XDG_RUNTIME_DIR}"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python extract_r6_odb.py
