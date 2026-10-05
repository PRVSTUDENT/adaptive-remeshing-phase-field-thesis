#!/bin/bash
# Guarded submit wrapper for M2ADAPT_REAL_PILOT_CYCLE_004_RESTART
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

EXPECTED_INP_SHA="c4bb5925ed4e38594452d420ba4d37bf54b503b29f2a831ca3db4dc4f24f272b"
EXPECTED_UEL_SHA="62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab"
EXPECTED_PBS_SHA="a1ad4078bf2cb423e056a589c2dd86203cc6ccabeb2fb2a80950b96430823e07"

ACTUAL_INP_SHA=$(sha256sum M2ADAPT_REAL_PILOT_CYCLE_004_RESTART.inp | awk '{print $1}')
ACTUAL_UEL_SHA=$(sha256sum f44_mixed_uel_restart_stateinit.for | awk '{print $1}')
ACTUAL_PBS_SHA=$(sha256sum M2ADAPT_REAL_PILOT_CYCLE_004_RESTART.pbs | awk '{print $1}')

if [ "$ACTUAL_INP_SHA" != "$EXPECTED_INP_SHA" ]; then echo "ERROR: INP SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_UEL_SHA" != "$EXPECTED_UEL_SHA" ]; then echo "ERROR: UEL SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_PBS_SHA" != "$EXPECTED_PBS_SHA" ]; then echo "ERROR: PBS SHA mismatch!"; exit 1; fi

echo "Preflight check PASS. Submitting M2ADAPT_REAL_PILOT_CYCLE_004_RESTART to PBS..."
JOB_ID=$(qsub M2ADAPT_REAL_PILOT_CYCLE_004_RESTART.pbs)
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
  notify_submitted "$JOB_ID" "M2ADAPT_REAL_PILOT_CYCLE_004_RESTART" "Submitted to queue entry_imfdfkmq" || true
fi
