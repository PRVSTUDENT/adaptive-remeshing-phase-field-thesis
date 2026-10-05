#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

CANDIDATE="M2STATE_FRACFIX_RESTART2R10"
PBS_SCRIPT="${CANDIDATE}.pbs"
MANIFEST="PACKAGE_MANIFEST.json"

echo "======================================================================"
echo "Guarded HPC Submission Wrapper: $CANDIDATE"
echo "======================================================================"

if [ ! -f "$PBS_SCRIPT" ]; then
    echo "ERROR: PBS script $PBS_SCRIPT not found!" >&2
    exit 1
fi

if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: Package manifest $MANIFEST not found!" >&2
    exit 1
fi

echo "--> Verifying SHA256 package manifest..."
python3 -c "
import json, hashlib, sys
with open('$MANIFEST') as f:
    m = json.load(f)
for fn, expected in m['file_hashes'].items():
    h = hashlib.sha256(open(fn, 'rb').read()).hexdigest()
    if h != expected:
        print(f'MISMATCH: {fn} actual={h} expected={expected}')
        sys.exit(1)
print('Package integrity verified: 100% SHA256 match.')
"

MODE="${1:---dry-run}"
if [ "$MODE" == "--execute" ]; then
    echo "--> Authorized execution mode detected."
    if [ -f "job_notifications.sh" ]; then
        source "job_notifications.sh"
        load_notification_config
    fi
    
    JOBID=$(qsub "$PBS_SCRIPT")
    echo "SUCCESS: Job submitted with PBS ID: $JOBID"
    if command -v notify_submitted >/dev/null 2>&1; then
        notify_submitted "$JOBID" "$CANDIDATE" "entry_imfdfkmq" "1" "16gb" "24:00:00"
    fi
elif [ "$MODE" == "--dry-run" ]; then
    echo "--> DRY-RUN mode: qsub call count = 0."
    echo "Ready for authorized single-job submission."
else
    echo "ERROR: Unknown mode '$MODE'. Use --dry-run or --execute." >&2
    exit 1
fi
