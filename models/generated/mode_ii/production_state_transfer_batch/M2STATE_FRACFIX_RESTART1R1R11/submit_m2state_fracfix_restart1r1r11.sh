#!/bin/bash
# Guarded Submission Wrapper for Candidate M2STATE_FRACFIX_RESTART1R1R11
# Max Submissions: 1 (Single Job Batch)
# Automatic Retry: FALSE

set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

CANDIDATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CANDIDATE_DIR"

echo "=== Preflight Verification for M2STATE_FRACFIX_RESTART1R1R11 ==="
python3 validate_package_manifest.py

DRY_RUN=false
if [ "${1:-}" == "--dry-run" ]; then
    DRY_RUN=true
    echo "[INFO] Dry run mode enabled. Submission wrapper verified without qsub."
    exit 0
fi

if [ "${1:-}" != "--execute" ]; then
    echo "Usage: $0 --dry-run | --execute"
    exit 1
fi

echo "=== Submitting Job M2STATE_FRACFIX_RESTART1R1R11 to PBS ==="
JOB_ID=$(qsub M2STATE_FRACFIX_RESTART1R1R11.pbs)
echo "[SUBMISSION] Job submitted successfully: $JOB_ID"

if [ -f "$CANDIDATE_DIR/job_notifications.sh" ]; then
    source "$CANDIDATE_DIR/job_notifications.sh" 2>/dev/null || true
    notification_load_config 2>/dev/null || true
    notify_submitted "$JOB_ID" "M2STATE_FRACFIX_RESTART1R1R11" "entry_imfdfkmq" "1" "16gb" "24:00:00" 2>/dev/null || true
fi
