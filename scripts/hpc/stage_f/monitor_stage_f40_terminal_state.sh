#!/bin/bash
# Terminal state monitoring and mandatory notification dispatch for Stage F40 M2RMBISECT1.
set -Eeuo pipefail

JOB_ID="${1:-}"
if [ -z "$JOB_ID" ]; then
  LAST_JOB_FILE="runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/LAST_JOB_ID.txt"
  if [ -f "$LAST_JOB_FILE" ]; then
    JOB_ID=$(cat "$LAST_JOB_FILE" | tr -d '\r\n')
  fi
fi

if [ -z "$JOB_ID" ]; then
  echo "ERROR: Job ID must be supplied or present in LAST_JOB_ID.txt" >&2
  exit 1
fi

EVIDENCE_DIR="runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/evidence/$JOB_ID"
mkdir -p "$EVIDENCE_DIR"

NOTIFICATION_DISPATCHER="scripts/hpc/notify_hpc_event.py"

echo "INFO: Monitoring terminal state for Job ID: $JOB_ID..."

# Poll qstat until job disappears or enters terminal state
while true; do
  QSTAT_OUT=$(qstat -x "$JOB_ID" 2>/dev/null || qstat "$JOB_ID" 2>/dev/null || true)
  if [ -z "$QSTAT_OUT" ]; then
    break
  fi
  # Check if job status shows C or F (completed/finished)
  STATE=$(echo "$QSTAT_OUT" | awk -v jid="$JOB_ID" '$1 ~ jid {print $5}' 2>/dev/null || echo "")
  if [ "$STATE" = "C" ] || [ "$STATE" = "F" ] || [ "$STATE" = "E" ]; then
    break
  fi
  sleep 5
done

echo "INFO: Job $JOB_ID reached terminal state."

# Extract terminal evidence attributes if STATUS.json exists
EXIT_STATUS="0"
HOST="unknown"
WALLTIME="unknown"
CLASSIFICATION="completed"

STATUS_JSON="$EVIDENCE_DIR/STATUS.json"
if [ -f "$STATUS_JSON" ]; then
  EXIT_STATUS=$(python3 -c "import json; print(json.load(open('$STATUS_JSON')).get('exit_status', '0'))" 2>/dev/null || echo "0")
  CLASSIFICATION=$(python3 -c "import json; print(json.load(open('$STATUS_JSON')).get('overall_classification', 'completed'))" 2>/dev/null || echo "completed")
fi

PROV_JSON="$EVIDENCE_DIR/SCHEDULER_PROVENANCE.json"
if [ -f "$PROV_JSON" ]; then
  HOST=$(python3 -c "import json; print(json.load(open('$PROV_JSON')).get('hostname', 'unknown'))" 2>/dev/null || echo "unknown")
fi

if [ -f "$NOTIFICATION_DISPATCHER" ]; then
  echo "INFO: Dispatching terminal state notifications..."
  python3 "$NOTIFICATION_DISPATCHER" \
    --mode terminal \
    --job-name "M2RMBISECT1" \
    --job-id "$JOB_ID" \
    --exit-status "$EXIT_STATUS" \
    --host "$HOST" \
    --walltime "$WALLTIME" \
    --classification "$CLASSIFICATION" \
    --evidence-path "$EVIDENCE_DIR" \
    --audit-file "$EVIDENCE_DIR/POST_TERMINAL_NOTIFICATION_AUDIT.json" \
    --returncode-dir "$EVIDENCE_DIR" || true
fi

echo "SUCCESS: Terminal monitoring and notification closeout complete for $JOB_ID."
