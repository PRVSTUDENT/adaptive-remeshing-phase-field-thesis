#!/bin/bash
# ==============================================================================
# GUARDED PBS SUBMISSION WRAPPER: MODE-I 8-THREAD SHARED-MEMORY (SMP)
# Target: PBS Professional on TU Bergakademie Freiberg HPC Cluster
# Working Directory: MUST BE UNDER /scratch9/pr21vyci/
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ------------------------------------------------------------------------------
# 1. HARD STORAGE-COMPLIANCE GUARD (EXIT 88)
# ------------------------------------------------------------------------------
CURRENT_DIR="$(pwd -P)"
if [[ "$CURRENT_DIR" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is strictly prohibited." >&2
  echo "Heavy simulation packages must reside and execute on /scratch9/pr21vyci/." >&2
  echo "Current directory: $CURRENT_DIR" >&2
  exit 88
fi

# ------------------------------------------------------------------------------
# 2. REQUIRED ARTIFACT EXISTENCE CHECKS
# ------------------------------------------------------------------------------
if [ ! -f ./submit_mode1_8thread_scratch_template.pbs ] && [ ! -f ./submit_solver.pbs ]; then
  echo "[LAUNCHER ERROR] Neither submit_mode1_8thread_scratch_template.pbs nor submit_solver.pbs found." >&2
  exit 10
fi

PBS_SCRIPT="submit_solver.pbs"
if [ ! -f "$PBS_SCRIPT" ]; then
  PBS_SCRIPT="submit_mode1_8thread_scratch_template.pbs"
fi

if [ ! -f ./f42_mixed_uel.for ]; then
  echo "[LAUNCHER ERROR] User subroutine f42_mixed_uel.for missing." >&2
  exit 11
fi

# ------------------------------------------------------------------------------
# 3. DUAL-CHANNEL NOTIFICATION INITIALIZATION
# ------------------------------------------------------------------------------
if [ -f ./job_notifications.sh ]; then
  source ./job_notifications.sh
  notification_load_config || true
fi

# ------------------------------------------------------------------------------
# 4. GUARDED PBS SUBMISSION
# ------------------------------------------------------------------------------
JOB_NAME="${1:-PK_M1_PROD_8T}"
echo "Submitting 8-Thread Shared-Memory Solver Job [$JOB_NAME] to PBS..."

JOB_ID=$(qsub "$PBS_SCRIPT")
echo "Submitted PBS Job ID: $JOB_ID"

# ------------------------------------------------------------------------------
# 5. TELEGRAM SUBMISSION NOTIFICATION
# ------------------------------------------------------------------------------
if type notify_submitted >/dev/null 2>&1; then
  notify_submitted "$JOB_ID" "$JOB_NAME" "8-Thread Shared-Memory Production Job on /scratch9/" || true
fi

echo "Submission completed successfully."
exit 0
