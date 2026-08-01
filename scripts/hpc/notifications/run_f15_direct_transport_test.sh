#!/usr/bin/env bash
set -u

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/job_notifications.sh"

LABEL='F15 PRE-SUBMISSION TRANSPORT TEST — NOT A PBS JOB EVENT'
notification_load_config || exit $?
mkdir -p "$NOTIFICATION_EVIDENCE_DIR"
context=$(notification_context DIRECT_TRANSPORT_TEST)
email_rc=0; telegram_rc=0
notify_email "$LABEL" "$LABEL
$context" "$NOTIFICATION_EVIDENCE_DIR/PRE_SUBMISSION_NOTIFICATION_TEST_EMAIL.json" || email_rc=$?
notify_telegram "$LABEL" "$LABEL
$context" "$NOTIFICATION_EVIDENCE_DIR/PRE_SUBMISSION_NOTIFICATION_TEST_TELEGRAM.json" || telegram_rc=$?
python3 - "$NOTIFICATION_EVIDENCE_DIR" "$email_rc" "$telegram_rc" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
email = json.loads((root / "PRE_SUBMISSION_NOTIFICATION_TEST_EMAIL.json").read_text())
telegram = json.loads((root / "PRE_SUBMISSION_NOTIFICATION_TEST_TELEGRAM.json").read_text())
summary = {
    "label": "F15 PRE-SUBMISSION TRANSPORT TEST — NOT A PBS JOB EVENT",
    "email": email,
    "telegram": telegram,
    "technical_pass": email.get("pass") is True and telegram.get("pass") is True,
    "pbs_job_event": False,
    "qsub_attempts": 0,
}
(root / "PRE_SUBMISSION_NOTIFICATION_TEST.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
PY
[ "$email_rc" -eq 0 ] && [ "$telegram_rc" -eq 0 ]
