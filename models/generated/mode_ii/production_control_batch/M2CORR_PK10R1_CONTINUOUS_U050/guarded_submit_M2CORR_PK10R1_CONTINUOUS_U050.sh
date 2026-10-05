#!/bin/bash
set -euo pipefail

JOB_NAME="M2CORR_PK10R1_CONTINUOUS_U050"
EXPECTED_MANIFEST_SHA256="352cdf03c9f323be5030b42ce0cfba5c0d70eee49be1cce6b510510deadbb793"
EXPECTED_UEL_SHA256="e3b373253069f9b36085ee426568ce002a7f195a4d5356c6c6a5549c97767138"

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
SUBMIT_OUTPUT=$(qsub submit_M2CORR_PK10R1_CONTINUOUS_U050.pbs)
JOB_ID=$(echo "$SUBMIT_OUTPUT" | grep -E '^[0-9]+\.' || echo "$SUBMIT_OUTPUT")
echo "SUBMITTED_JOB_ID=$JOB_ID"

# 4. Trigger Telegram submission notification
if [ -f "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" ]; then
    source "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
    notify_submitted "$JOB_NAME" "$JOB_ID"
fi
