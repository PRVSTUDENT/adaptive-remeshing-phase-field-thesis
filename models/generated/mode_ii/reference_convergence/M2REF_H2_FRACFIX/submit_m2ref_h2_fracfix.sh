#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for M2REF_H2_FRACFIX
# Protocol version: 1
# Requires explicit prior human chat authorization.

AUTH_FILE="../M2REF_BATCH_SUBMISSION_RECORD.json"

if [ ! -f "$AUTH_FILE" ]; then
    echo "ERROR: Authorization record $AUTH_FILE missing. Direct submission prohibited." >&2
    exit 1
fi

echo "Submitting M2REF_H2_FRACFIX to PBS..."
qsub M2REF_H2_FRACFIX.pbs
