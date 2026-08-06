#!/bin/bash
# Guarded orchestrator for Stage F40 M2RMBISECT1 Abaqus CAE bisection diagnostic.
# Strict activation and authorization gates; 1 submission call maximum; no retries.
set -Eeuo pipefail

PREP_SHA="${F40_PREPARATION_SHA:?F40_PREPARATION_SHA must be explicitly bound after package review}"

echo "=== Stage F40 M2RMBISECT1 Launcher Bisection Orchestrator ==="

# 1. Activation Gate
if [ "${F40_ALLOW_SUBMISSION:-false}" != "true" ]; then
  echo "HALT: Activation gate F40_ALLOW_SUBMISSION is not 'true'. Refusing submission."
  exit 0
fi

# 2. Authorization Gate
if [ "${F40_AUTHORIZE_M2RMBISECT1:-false}" != "true" ]; then
  echo "HALT: Authorization gate F40_AUTHORIZE_M2RMBISECT1 is not 'true'. Refusing submission."
  exit 0
fi

# 3. Head descendant check
HEAD_SHA=$(git rev-parse HEAD)
if ! git merge-base --is-ancestor "$PREP_SHA" "$HEAD_SHA"; then
  echo "ERROR: HEAD ($HEAD_SHA) is not a descendant of preparation revision ($PREP_SHA)."
  exit 1
fi

# 4. Blob identity check freezing package directory, submission wrapper, dispatcher, and monitor
PKG_DIR="models/generated/mode_ii/f40_f38_cae_invocation_model_building_bisect"
WRAPPER_PATH="scripts/hpc/stage_f/submit_stage_f40_cae_bisect.sh"
NOTIFY_PATH="scripts/hpc/notify_hpc_event.py"
MONITOR_PATH="scripts/hpc/stage_f/monitor_stage_f40_terminal_state.py"
FREEZE_PATHS=("$PKG_DIR" "$WRAPPER_PATH" "$NOTIFY_PATH" "$MONITOR_PATH")

PREP_BLOBS=$(git ls-tree -r "$PREP_SHA" -- "${FREEZE_PATHS[@]}" | awk '{print $3, $4}' | sort)
HEAD_BLOBS=$(git ls-tree -r "$HEAD_SHA" -- "${FREEZE_PATHS[@]}" | awk '{print $3, $4}' | sort)

if [ -z "$PREP_BLOBS" ] || [ -z "$HEAD_BLOBS" ]; then
  echo "ERROR: Package or submission wrapper blob list is empty."
  exit 1
fi

if [ "$PREP_BLOBS" != "$HEAD_BLOBS" ]; then
  echo "ERROR: Package/wrapper blob mismatch between preparation SHA ($PREP_SHA) and HEAD ($HEAD_SHA)."
  exit 1
fi

# 5. Lock file path definition
LOCK_FILE="runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/M2RMBISECT1_SUBMITTED.lock"

# 6. Maximum Submission Audit & Binary Check
if [ "${MAX_SUBMISSIONS:-1}" -ne 1 ]; then
  echo "ERROR: Only 1 submission maximum authorized."
  exit 1
fi

command -v qsub >/dev/null 2>&1 || { echo "ERROR: qsub command not found on PATH." >&2; exit 1; }
command -v qstat >/dev/null 2>&1 || { echo "ERROR: qstat command not found on PATH." >&2; exit 1; }

# 7. Check scheduler queue state for existing M2RMBISECT1 job (fail closed)
USER_NAME=$(id -un 2>/dev/null || echo "${USER:-}")
QSTAT_U_DIR="$(pwd)/runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/evidence"
mkdir -p "$QSTAT_U_DIR"

set +e
QSTAT_U_RAW=$(qstat -u "$USER_NAME" 2>&1)
QSTAT_U_RC=$?
set -e

printf '%s\n' "$QSTAT_U_RAW" > "$QSTAT_U_DIR/QSTAT_U_PRECHECK.stdout"
printf '' > "$QSTAT_U_DIR/QSTAT_U_PRECHECK.stderr"

if [ $QSTAT_U_RC -ne 0 ]; then
  echo "FATAL: qstat -u query failed with return code $QSTAT_U_RC. Aborting before lock creation or qsub." >&2
  exit 1
fi

python3 -c "
import sys, subprocess, json, os

qstat_u = sys.argv[1]
lines = [l.strip() for l in qstat_u.splitlines() if l.strip()]
job_ids = []
for l in lines[2:]:
    parts = l.split()
    if parts and parts[0]:
        job_ids.append(parts[0])

audit = []
duplicate_found = False
for jid in job_ids:
    proc = subprocess.run(['qstat', '-f', jid], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    data = {'job_id': jid, 'rc': proc.returncode, 'job_name': 'unknown', 'job_state': 'unknown', 'job_owner': 'unknown'}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if '=' in line:
            parts_kv = line.split('=', 1)
            k, v = parts_kv[0].strip(), parts_kv[1].strip()
            if k == 'Job_Name': data['job_name'] = v
            elif k == 'job_state': data['job_state'] = v
            elif k == 'Job_Owner': data['job_owner'] = v
    audit.append(data)
    if data['job_name'] == 'M2RMBISECT1':
        duplicate_found = True

audit_file = sys.argv[2]
with open(audit_file, 'w') as f:
    json.dump({'active_jobs': audit, 'duplicate_found': duplicate_found}, f, indent=2)

if duplicate_found:
    print('HALT: Active or queued M2RMBISECT1 job detected in scheduler state.', file=sys.stderr)
    sys.exit(1)
" "$QSTAT_U_RAW" "$QSTAT_U_DIR/QSTAT_EXISTING_JOB_AUDIT.json"

# 8. Mandatory Recipient Environment Validation and Preflight Test Channel Check
PBS_MAIL_REC="${F40_PBS_MAIL_RECIPIENT:-}"
NOTIF_EMAIL_RECS="${F40_NOTIFICATION_EMAIL_RECIPIENTS:-}"

if [ "$PBS_MAIL_REC" != "pr21vyci@mailserver.tu-freiberg.de" ]; then
  echo "FATAL: F40_PBS_MAIL_RECIPIENT must equal exact expected address 'pr21vyci@mailserver.tu-freiberg.de'." >&2
  exit 1
fi

IFS=',' read -ra ADDR_ARRAY <<< "$NOTIF_EMAIL_RECS"
if [ "${#ADDR_ARRAY[@]}" -ne 2 ]; then
  echo "FATAL: F40_NOTIFICATION_EMAIL_RECIPIENTS must contain exactly 2 comma-separated addresses." >&2
  exit 1
fi

HAS_MAILSERVER=0
HAS_STUDENT=0
for addr in "${ADDR_ARRAY[@]}"; do
  trimmed=$(echo "$addr" | tr -d '[:space:]')
  if [ "$trimmed" = "pr21vyci@mailserver.tu-freiberg.de" ]; then
    HAS_MAILSERVER=1
  elif [ "$trimmed" = "Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de" ]; then
    HAS_STUDENT=1
  fi
done

if [ "$HAS_MAILSERVER" -ne 1 ] || [ "$HAS_STUDENT" -ne 1 ]; then
  echo "FATAL: F40_NOTIFICATION_EMAIL_RECIPIENTS must equal exact expected set {pr21vyci@mailserver.tu-freiberg.de, Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de}." >&2
  exit 1
fi

if [[ "$NOTIF_EMAIL_RECS" == *"pruthvi.patel@student.tu-freiberg.de"* ]]; then
  echo "FATAL: Obsolete email address pruthvi.patel@student.tu-freiberg.de detected." >&2
  exit 1
fi

NOTIFICATION_DISPATCHER="scripts/hpc/notify_hpc_event.py"
if [ -f "$NOTIFICATION_DISPATCHER" ]; then
  PREFLIGHT_TEST_DIR="$(pwd)/runs/hpc/stage_f/f40_notification_live_test/$(date -u +%Y%m%d_%H%M%S)"
  mkdir -p "$PREFLIGHT_TEST_DIR"
  echo "INFO: Running pre-submission test notification check over Email and Telegram..."
  python3 "$NOTIFICATION_DISPATCHER" \
    --mode test \
    --job-name "M2RMBISECT1" \
    --audit-file "$PREFLIGHT_TEST_DIR/NOTIFICATION_AUDIT.json" \
    --returncode-dir "$PREFLIGHT_TEST_DIR" || {
    echo "FATAL: Pre-submission notification channel test failed. Aborting before qsub." >&2
    exit 1
  }
fi

# 9. Create atomic submission-attempt lock BEFORE qsub
mkdir -p "$(dirname "$LOCK_FILE")"
if ! (set -o noclobber; printf '%s\n' "submission_attempt_started prep=$PREP_SHA head=$HEAD_SHA" > "$LOCK_FILE") 2>/dev/null; then
  echo "HALT: Submission lock file exists ($LOCK_FILE). Job has already been submitted or submission attempt started." >&2
  exit 1
fi

# Single Guarded Scheduler Invocation
echo "INFO: Submitting M2RMBISECT1..."
EVIDENCE_ROOT="$(pwd)/runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/evidence"
PACKAGE_DIR="$(pwd)/$PKG_DIR"

set +e
JOB_ID=$(qsub -M "$PBS_MAIL_REC" -m abe -v F40_PACKAGE_DIR="$PACKAGE_DIR",F40_EVIDENCE_ROOT="$EVIDENCE_ROOT",F40_GUARDED_WRAPPER_INVOKED=1 "$PACKAGE_DIR/M2RMBISECT1.pbs" 2> "$EVIDENCE_ROOT/QSUB_OUTPUT.stderr")
QSUB_RC=$?
set -e
printf '%s\n' "$JOB_ID" > "$EVIDENCE_ROOT/QSUB_OUTPUT.stdout"
printf '%d\n' "$QSUB_RC" > "$EVIDENCE_ROOT/QSUB_RETURNCODE.txt"

JOB_ID=$(echo "$JOB_ID" | tr -d '[:space:]')

if [ $QSUB_RC -ne 0 ] || [ -z "$JOB_ID" ]; then
  echo "ERROR: qsub failed (rc=$QSUB_RC) or returned empty Job ID." >&2
  exit 1
fi

echo "SUCCESS: Submitted M2RMBISECT1 with Job ID: $JOB_ID"
echo "$JOB_ID" > "runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/LAST_JOB_ID.txt"

JOB_EVID_DIR="$EVIDENCE_ROOT/$JOB_ID"
mkdir -p "$JOB_EVID_DIR"

# 10. Mandatory Post-Submission Notification Dispatch (Attempted immediately after qsub returns Job ID)
QUAL_SHA="${F40_QUALIFICATION_SHA:-$HEAD_SHA}"
if [ -f "$NOTIFICATION_DISPATCHER" ]; then
  echo "INFO: Dispatching post-submission notifications..."
  python3 "$NOTIFICATION_DISPATCHER" \
    --mode submission \
    --job-name "M2RMBISECT1" \
    --job-id "$JOB_ID" \
    --queue "entry_imfdfkmq" \
    --resources "1 CPU, 8GB RAM, 30m walltime" \
    --prep-commit "$PREP_SHA" \
    --qual-commit "$QUAL_SHA" \
    --audit-file "$JOB_EVID_DIR/NOTIFICATION_AUDIT.json" \
    --returncode-dir "$JOB_EVID_DIR" || true
fi

# 11. Capture & Verify qstat -f mail settings
set +e
QSTAT_F_OUT=$(qstat -f "$JOB_ID" 2> "$JOB_EVID_DIR/QSTAT_F_RECORD.stderr")
QSTAT_F_RC=$?
set -e
printf '%s\n' "$QSTAT_F_OUT" > "$JOB_EVID_DIR/QSTAT_F_RECORD.txt"
printf '%d\n' "$QSTAT_F_RC" > "$JOB_EVID_DIR/QSTAT_F_RETURNCODE.txt"

VERIF_MAIL_USERS=$(echo "$QSTAT_F_OUT" | grep "Mail_Users" | cut -d'=' -f2 | tr -d '[:space:]' || echo "missing")
VERIF_MAIL_POINTS=$(echo "$QSTAT_F_OUT" | grep "Mail_Points" | cut -d'=' -f2 | tr -d '[:space:]' || echo "missing")
VERIF_JOB_NAME=$(echo "$QSTAT_F_OUT" | grep "Job_Name" | cut -d'=' -f2 | tr -d '[:space:]' || echo "missing")

VERIF_OK="true"
if [ "$VERIF_MAIL_USERS" != "pr21vyci@mailserver.tu-freiberg.de" ]; then VERIF_OK="false"; fi
if [[ "$VERIF_MAIL_POINTS" != *"a"* ]] || [[ "$VERIF_MAIL_POINTS" != *"b"* ]] || [[ "$VERIF_MAIL_POINTS" != *"e"* ]]; then VERIF_OK="false"; fi
if [ "$VERIF_JOB_NAME" != "M2RMBISECT1" ]; then VERIF_OK="false"; fi

python3 -c "
import json, sys
job_id, mail_users, mail_points, job_name, verif_ok, out_file = sys.argv[1:7]
data = {
    'job_id': job_id,
    'mail_users': mail_users,
    'mail_points': mail_points,
    'job_name': job_name,
    'verification_passed': (verif_ok == 'true')
}
with open(out_file, 'w') as f:
    json.dump(data, f, indent=2)
" "$JOB_ID" "$VERIF_MAIL_USERS" "$VERIF_MAIL_POINTS" "$VERIF_JOB_NAME" "$VERIF_OK" "$JOB_EVID_DIR/QSTAT_F_VERIFICATION.json"

if [ "$VERIF_OK" != "true" ] || [ $QSTAT_F_RC -ne 0 ]; then
  echo "WARNING: qstat -f verification failed for Job ID: $JOB_ID. Submission was completed and authorization consumed; no retry will occur." >&2
fi

