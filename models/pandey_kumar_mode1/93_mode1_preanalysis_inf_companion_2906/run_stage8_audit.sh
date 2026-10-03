#!/bin/bash
set -euo pipefail

WORKDIR="/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/93_mode1_preanalysis_inf_companion_2906"
cd "${WORKDIR}"

if [ -f /etc/profile.d/modules.sh ]; then
    source /etc/profile.d/modules.sh
fi

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== EXECUTING STAGE 8 INF COMPANION AUDIT SCRIPT ==="
abaqus python stage8_inf_companion_audit.py
echo "=== STAGE 8 INF COMPANION AUDIT COMPLETED ==="
