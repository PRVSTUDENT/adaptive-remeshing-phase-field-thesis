#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "./job_notifications.sh" ]; then
    source ./job_notifications.sh
    notification_load_config || true
fi

echo "Submitting 4-Thread Shared-Memory Stage-B Determinism Repeat Job to PBS..."
JOB_ID=$(qsub submit_solver.pbs)
echo "Submitted PBS Job ID: $JOB_ID"

if type notify_submitted >/dev/null 2>&1; then
    notify_submitted "$JOB_ID" "PK_M1_14K_4T_STAGE_B" "4-Thread Shared-Memory Stage-B Determinism Repeat"
fi
