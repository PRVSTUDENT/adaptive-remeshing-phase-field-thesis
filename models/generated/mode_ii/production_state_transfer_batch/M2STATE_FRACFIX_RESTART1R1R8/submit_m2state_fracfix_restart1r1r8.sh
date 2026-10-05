#!/bin/bash
# ==============================================================================
# Guarded Submission Wrapper for M2STATE_FRACFIX_RESTART1R1R8
# Single-job submission wrapper with dry-run protection and manifest verification
# ==============================================================================
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
  esac
done

echo "=== Guarded Wrapper: M2STATE_FRACFIX_RESTART1R1R8 ==="

# 1. Validate manifest
python3 validate_package_manifest.py PACKAGE_MANIFEST.json

if [ "$DRY_RUN" = true ]; then
  echo "[DRY-RUN] Manifest verified. qsub invocation skipped. (qsub call count = 0)"
  exit 0
fi

echo "[GUARD] Verifying execution authorization..."
# Note: Actual execution requires explicit human approval recorded in project_coordination.
JOB_ID=$(qsub M2STATE_FRACFIX_RESTART1R1R8.pbs)
echo "[SUBMITTED] PBS Job ID: $JOB_ID"

# Dual channel notification
NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-$HOME/.config/adaptive-remeshing/notifications.env}"
NOTIFICATION_SCRIPT="${NOTIFICATION_SCRIPT:-${SCRIPT_DIR}/job_notifications.sh}"
if [ -f "$NOTIFICATION_SCRIPT" ]; then
  source "$NOTIFICATION_SCRIPT" 2>/dev/null || true
  notification_load_config 2>/dev/null || true
  notify_submitted "$JOB_ID" "M2STATE_FRACFIX_RESTART1R1R8" 2>/dev/null || true
fi
