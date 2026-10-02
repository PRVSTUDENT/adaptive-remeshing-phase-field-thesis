#!/bin/bash
# Guarded submission wrapper for 2.0% Task-5 Production Solver
set -euo pipefail

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PACKAGE_DIR"

echo "================================================================================"
echo "SUBMISSION WRAPPER: 2.0% TASK-5 PANDEY & KUMAR PRODUCTION SOLVE"
echo "================================================================================"
echo "Package Directory: $PACKAGE_DIR"

# 1. Verify files exist
if [ ! -f "PK_MODE1_PROPOSED_PFM.inp" ]; then
  echo "[ERROR] PK_MODE1_PROPOSED_PFM.inp not found!" >&2
  exit 1
fi
if [ ! -f "f42_mixed_uel.for" ]; then
  echo "[ERROR] f42_mixed_uel.for not found!" >&2
  exit 2
fi
if [ ! -f "submit_solver.pbs" ]; then
  echo "[ERROR] submit_solver.pbs not found!" >&2
  exit 3
fi

# 2. Check current queue for duplicates
EXISTING_JOB=$(qstat -u "$USER" 2>/dev/null | grep "PK_MODE1_P_SOLVE" || true)
if [ -n "$EXISTING_JOB" ]; then
  echo "[ERROR] A job named PK_MODE1_P_SOLVE is already active or queued:" >&2
  echo "$EXISTING_JOB" >&2
  exit 4
fi

# 3. Source notification helper
if [ -f "./job_notifications.sh" ]; then
  source ./job_notifications.sh
  notification_load_config || true
fi

# 4. Submit PBS Job
echo "Submitting submit_solver.pbs via qsub ..."
JOB_ID=$(qsub submit_solver.pbs)
echo "SUBMITTED_JOB_ID: $JOB_ID"

# 5. Dual-channel notification (Telegram submitted notify)
if type notify_submitted >/dev/null 2>&1; then
  notify_submitted "$JOB_ID" "PK_MODE1_P_SOLVE" "2.0% Task-5 Proposed Adaptive Refinement Production Solve" || true
fi

echo "================================================================================"
echo "PRODUCTION SOLVE SUBMISSION SUCCESSFUL: $JOB_ID"
echo "================================================================================"
