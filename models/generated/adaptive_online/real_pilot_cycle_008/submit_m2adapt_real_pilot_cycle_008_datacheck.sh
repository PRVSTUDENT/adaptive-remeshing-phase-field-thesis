#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi
cd "$(dirname "$0")"

echo "=== PREFLIGHT NOTIFICATION CHECK FOR M2ADAPT_REAL_PILOT_CYCLE_008_DATACHECK ==="

# Resolve notification helper
NOTIF_SCRIPT="/scratch/pr21vyci/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
if [ -f "$NOTIF_SCRIPT" ]; then
  source "$NOTIF_SCRIPT"
  notification_load_config
  echo "  [OK] Dual-channel notification system loaded."
else
  echo "ERROR: Notification helper not found: $NOTIF_SCRIPT"
  exit 1
fi

REQUIRED_FILES=(
  "M2ADAPT_REAL_PILOT_CYCLE_008_RESTART.inp"
  "M2ADAPT_REAL_PILOT_CYCLE_008_DATACHECK.pbs"
  "f44_mixed_uel_restart_stateinit.for"
  "MODE_STAGED.flag"
  "STAGE_D_COMMITTED_STATE.bin"
  "TARGET_REAL_PILOT_CYCLE_008_STATE_INSTALL_BOUNDARY.inp"
  "TARGET_REAL_PILOT_CYCLE_008_U3_ONLY_BOUNDARY.inp"
)

for req in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$req" ]; then
    echo "ERROR: Missing required artifact: $req"
    exit 1
  fi
  echo "  [OK] $req exists ($(stat -c%s "$req") bytes)"
done

echo "Submitting PBS Datacheck job: qsub M2ADAPT_REAL_PILOT_CYCLE_008_DATACHECK.pbs"
JOB_ID=$(qsub M2ADAPT_REAL_PILOT_CYCLE_008_DATACHECK.pbs)
echo "Submitted successfully: $JOB_ID"

# Send submission notification
notify_submitted "$JOB_ID" "M2ADAPT_REAL_PILOT_CYCLE_008_DATACHECK" "Cycle-008 Mandatory Datacheck Submitted" || true

echo "JOB_ID=$JOB_ID"
