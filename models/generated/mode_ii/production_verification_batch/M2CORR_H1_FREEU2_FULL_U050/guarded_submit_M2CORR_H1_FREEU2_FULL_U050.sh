#!/bin/bash
set -euo pipefail

JOB_NAME="M2CORR_H1_FREEU2_FULL_U050"
EXPECTED_MANIFEST_SHA256="ea5c4382e53aca228ca47a162ec64488807701726b49cda5b29ddeb4cc0ec97d"
EXPECTED_UEL_SHA256="ed1586d6427a4b1a01d99f7e219891ec7be9fe911e066d9360724942e7d27720"

echo "=== PRE-SUBMISSION GUARDED VERIFICATION: $JOB_NAME ==="

# 1. Verify UEL SHA256
ACTUAL_UEL_SHA256=$(sha256sum f42_mixed_uel_transactional.for | awk '{print $1}')
if [ "$ACTUAL_UEL_SHA256" != "$EXPECTED_UEL_SHA256" ]; then
    echo "ERROR: UEL SHA256 mismatch! Expected $EXPECTED_UEL_SHA256, got $ACTUAL_UEL_SHA256"
    exit 1
fi

# 2. Verify Manifest SHA256
ACTUAL_MANIFEST_SHA256=$(sha256sum manifest.json | awk '{print $1}')
if [ "$ACTUAL_MANIFEST_SHA256" != "$EXPECTED_MANIFEST_SHA256" ]; then
    echo "ERROR: Manifest SHA256 mismatch! Expected $EXPECTED_MANIFEST_SHA256, got $ACTUAL_MANIFEST_SHA256"
    exit 1
fi

echo "MANIFEST AND UEL VERIFICATION PASSED FOR $JOB_NAME"

# 3. Submit via qsub
SUBMIT_OUTPUT=$(qsub submit_M2CORR_H1_FREEU2_FULL_U050.pbs)
JOB_ID=$(echo "$SUBMIT_OUTPUT" | grep -E '^[0-9]+\.' || echo "$SUBMIT_OUTPUT")
echo "SUBMITTED_JOB_ID=$JOB_ID"

# 4. Trigger Telegram submission notification
if [ -f "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" ]; then
    source "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
    notify_submitted "$JOB_NAME" "$JOB_ID"
fi
