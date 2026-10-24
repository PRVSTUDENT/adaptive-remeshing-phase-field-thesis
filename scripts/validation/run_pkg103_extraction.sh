#!/bin/bash
set -e
export XDG_RUNTIME_DIR=/tmp/xdg_runtime_${USER}
source /etc/profile.d/lmod.sh
module load abaqus/2023
cd /scratch9/pr21vyci/runs/mode1_package103_c5_h1_pilot
abaqus python remote_extract_pkg103.py
