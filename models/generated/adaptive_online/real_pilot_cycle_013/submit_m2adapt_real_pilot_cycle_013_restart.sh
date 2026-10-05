#!/bin/bash
# Guarded submit wrapper for M2ADAPT_REAL_PILOT_CYCLE_013_RESTART (Step 3 & Step 4 Relaxed Controls)
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

EXPECTED_INP_SHA="27d11cb923902f580c9c640237d085c8d8253d098b2bf50f940b0fd7f55eceb8"
EXPECTED_UEL_SHA="942003c5882b5598e81b471d87840e0dce2a639179cc24c87662dcf53eaef946"
EXPECTED_PBS_SHA="73a484a344c4ec46fe4565ddbc3c00deac9976e2783ef4d46be0eea16a46a951"

ACTUAL_INP_SHA=$(sha256sum M2ADAPT_REAL_PILOT_CYCLE_013_RESTART.inp | awk '{print $1}')
ACTUAL_UEL_SHA=$(sha256sum f44_mixed_uel_restart_stateinit.for | awk '{print $1}')
ACTUAL_PBS_SHA=$(sha256sum M2ADAPT_REAL_PILOT_CYCLE_013_RESTART.pbs | awk '{print $1}')

if [ "$ACTUAL_INP_SHA" != "$EXPECTED_INP_SHA" ]; then echo "ERROR: INP SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_UEL_SHA" != "$EXPECTED_UEL_SHA" ]; then echo "ERROR: UEL SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_PBS_SHA" != "$EXPECTED_PBS_SHA" ]; then echo "ERROR: PBS SHA mismatch!"; exit 1; fi

echo "Preflight check PASS. Submitting to PBS authorized."
JOB_ID=$(qsub M2ADAPT_REAL_PILOT_CYCLE_013_RESTART.pbs)
echo "Submitted Job ID: $JOB_ID"
NOTIF_SCRIPT=""
for cand in \
  "scripts/hpc/notifications/job_notifications.sh" \
  "../../../../scripts/hpc/notifications/job_notifications.sh" \
  "/scratch/pr21vyci/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" \
  "${HOME}/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"; do
  if [ -f "$cand" ]; then
    NOTIF_SCRIPT="$cand"
    break
  fi
done
if [ -n "$NOTIF_SCRIPT" ]; then
  source "$NOTIF_SCRIPT"
  notify_submitted "$JOB_ID" "M2ADAPT_REAL_PILOT_CYCLE_013_RESTART" "Submitted to queue entry_imfdfkmq" || true
fi
