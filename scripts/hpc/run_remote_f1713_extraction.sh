#!/usr/bin/env bash
set -euo pipefail
# Task F1713: Extract authentic damage field and F-u history from M1_PK_F1713_JOB2_ADAPTED.odb
RUN_DIR="/scratch9/pr21vyci/runs/mode1_pk_f1713_job2_adapted"
cd "$RUN_DIR"

echo "=== Task F1713: Remote ODB Extraction Started at $(date) ==="
module load abaqus/2023 || true

abaqus python extract_f1713_damage.py \
    "$RUN_DIR/M1_PK_F1713_JOB2_ADAPTED.odb" \
    "$RUN_DIR/f1713_job2_damage_field.json"

ls -lh "$RUN_DIR/f1713_job2_damage_field.json"
echo "=== Task F1713: Remote ODB Extraction Finished at $(date) ==="
