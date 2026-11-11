#!/usr/bin/env bash
set -euo pipefail
# Task F1714: Extract authentic five-hole telemetry from M1_PK_F1714_JOB2_ADAPTED.odb
RUN_DIR="/scratch9/pr21vyci/runs/mode1_pk_f1714_five_hole"
cd "$RUN_DIR"

echo "=== Task F1714: Remote ODB Telemetry Extraction Started at $(date) ==="
source /etc/profile.d/lmod.sh 2>/dev/null || true
module load abaqus/2023 2>/dev/null || true

# Guard check: Ensure .lck file is gone
if [ -f "$RUN_DIR/M1_PK_F1714_JOB2_ADAPTED.lck" ]; then
    echo "ERROR: ODB is still locked by active Abaqus solver process."
    exit 1
fi

abaqus python extract_f1714_five_hole_telemetry.py \
    "$RUN_DIR/M1_PK_F1714_JOB2_ADAPTED.odb" \
    "$RUN_DIR/f1714_five_hole_telemetry.json"

ls -lh "$RUN_DIR/f1714_five_hole_telemetry.json"
echo "=== Task F1714: Remote ODB Telemetry Extraction Finished at $(date) ==="
