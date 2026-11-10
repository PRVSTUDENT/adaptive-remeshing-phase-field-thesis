#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_pk_sec43_job2_staggered_f1709"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Running Abaqus Python Damage Extraction for Job-2 Staggered ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"

abaqus python "${RUN_DIR}/extract_f1709_job2_damage.py" \
    "${RUN_DIR}/M1_PK_SEC43_JOB2_STAGGERED.odb" \
    "${RUN_DIR}/f1709_job2_damage_field.json"

echo "Extraction finished successfully!"
ls -lh "${RUN_DIR}/f1709_job2_damage_field.json"
