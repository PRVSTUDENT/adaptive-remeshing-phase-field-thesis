#!/bin/bash
set -euo pipefail
if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

python3 /scratch9/pr21vyci/runs/env_test/test_cluster_pdas_startup.py
