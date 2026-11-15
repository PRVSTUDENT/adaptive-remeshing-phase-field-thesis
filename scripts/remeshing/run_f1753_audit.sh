#!/bin/bash
# scripts/remeshing/run_f1753_audit.sh
# Execute audit_f1753_continuation_odb.py on cluster via Abaqus Python

set -euo pipefail

source /etc/profile.d/lmod.sh 2>/dev/null || true
module purge || true
module load abaqus/2023 2>/dev/null || module load abaqus 2>/dev/null || true
export PATH="/cluster/application/abaqus/2023/Commands:$PATH"

RUN_DIR="/scratch9/pr21vyci/runs/f1752_case2_continuation"
ODB_PATH="${RUN_DIR}/PK_F1752_CASE_2_CONTINUATION.odb"
DAT_PATH="${RUN_DIR}/PK_F1752_CASE_2_CONTINUATION.dat"
OUT_JSON="${RUN_DIR}/f1753_case2_continuation_audit.json"

cd "$RUN_DIR"
echo "=== Running F1753 Continuation ODB Audit ==="
abaqus python audit_f1753_continuation_odb.py "$ODB_PATH" "$DAT_PATH" "$OUT_JSON"
echo "=== Audit Completed ==="
