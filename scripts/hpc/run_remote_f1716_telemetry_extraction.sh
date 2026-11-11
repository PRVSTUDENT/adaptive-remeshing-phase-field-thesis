#!/bin/bash
set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_pk_f1716_five_hole_production"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Extracting F1716 Five-Hole Telemetry from M1_PK_F1716_JOB2_ADAPTED.odb ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"

if [ -f "M1_PK_F1716_JOB2_ADAPTED.lck" ]; then
    echo "Notice: Active lock file M1_PK_F1716_JOB2_ADAPTED.lck present. Solver is currently writing to ODB."
fi

abaqus python extract_f1716_five_hole_telemetry.py M1_PK_F1716_JOB2_ADAPTED.odb f1716_five_hole_telemetry.json

echo "=== Telemetry Extraction Finished ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
ls -lh f1716_five_hole_telemetry.json
