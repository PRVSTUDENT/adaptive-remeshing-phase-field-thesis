#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for M2REF_ONEEL_FRACFIX_VERIFY
# Protocol version: 1
# Requires explicit prior human chat authorization.

AUTH_FILE="../VERIFICATION_BATCH_SUBMISSION_RECORD.json"

if [ ! -f "$AUTH_FILE" ]; then
    echo "ERROR: Authorization record $AUTH_FILE missing. Direct submission prohibited." >&2
    exit 1
fi

echo "Submitting M2REF_ONEEL_FRACFIX_VERIFY to PBS..."
qsub M2REF_ONEEL_FRACFIX_VERIFY.pbs
