#!/bin/bash
set -euo pipefail
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module load abaqus/2023
cd /scratch9/pr21vyci/runs/mode1_package96_r2_c5_transfer
abaqus python extract_pkg96_r2_results.py
