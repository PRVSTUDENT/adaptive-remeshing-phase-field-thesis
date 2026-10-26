#!/bin/bash
set -euo pipefail
if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
cd /scratch9/pr21vyci/runs/mode1_c4_am_dynamic_continuation
abaqus python extract_and_audit_am_cycles.py
