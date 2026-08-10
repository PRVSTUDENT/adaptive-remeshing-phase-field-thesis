#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for M2ADAPT_MM_FRACFIX_PROD
# Protocol version: 1
# Requires explicit prior human chat authorization.

AUTH_FILE="../M2ADAPT_BATCH_SUBMISSION_RECORD.json"

if [ ! -f "$AUTH_FILE" ]; then
    echo "ERROR: Authorization record $AUTH_FILE missing. Direct submission prohibited." >&2
    exit 1
fi

echo "Submitting M2ADAPT_MM_FRACFIX_PROD to PBS..."
qsub M2ADAPT_MM_FRACFIX_PROD.pbs
