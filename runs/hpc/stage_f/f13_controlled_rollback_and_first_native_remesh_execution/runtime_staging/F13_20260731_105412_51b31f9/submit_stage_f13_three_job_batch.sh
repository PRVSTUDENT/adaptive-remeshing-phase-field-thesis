#!/bin/bash
set -u
: "${F13_RUN_ROOT:?}" "${F13_AUTHORIZATION:?}" "${F13_MAIL:?}"
python3 - "$F13_AUTHORIZATION" <<'PY' || exit 20
import json,sys
a=json.load(open(sys.argv[1]))
assert a["execution_authorized"] and a["submission_approved"]
assert a["authorized_jobs"] == ["M2IRRROLLCTL1", "M2IRRROLLFORCE1", "M2RMEXEC1"]
assert a["approved_submissions"] == 3 and a["maximum_running_jobs"] == 2
assert a["qsub_attempts"] == 0 and a["successful_submissions"] == 0
assert not a["retry_authorized"] and not a["replacement_authorized"]
PY
attempts=0; successes=0; failures=0; job_a=""; job_b=""; job_c=""
submit_one() {
  case_dir="$1"; pbs="$2"; attempts=$((attempts+1)); test "$attempts" -le 3 || return 90
  output=$(cd "$case_dir" && qsub -M "$F13_MAIL" -m abe "$pbs"); rc=$?
  if [ "$rc" -eq 0 ]; then successes=$((successes+1)); LAST_JOB="$output"; else failures=$((failures+1)); LAST_JOB=""; fi
  return "$rc"
}
eligible() { python3 -c 'import json,sys;sys.exit(0 if json.load(open(sys.argv[1]))["eligible"] else 1)' "$1"; }
if eligible "$F13_RUN_ROOT/rollback_control/PREFLIGHT.json"; then submit_one "$F13_RUN_ROOT/rollback_control" M2IRRROLLCTL1.pbs || true; job_a="$LAST_JOB"; fi
if eligible "$F13_RUN_ROOT/rollback_forced/PREFLIGHT.json"; then submit_one "$F13_RUN_ROOT/rollback_forced" M2IRRROLLFORCE1.pbs || true; job_b="$LAST_JOB"; fi
if eligible "$F13_RUN_ROOT/native_remesh/PREFLIGHT.json"; then submit_one "$F13_RUN_ROOT/native_remesh" M2RMEXEC1.pbs || true; job_c="$LAST_JOB"; fi
printf '{"qsub_attempts":%d,"successful_submissions":%d,"failed_qsub_attempts":%d,"job_a":"%s","job_b":"%s","job_c":"%s"}\n' "$attempts" "$successes" "$failures" "$job_a" "$job_b" "$job_c" > "$F13_RUN_ROOT/SUBMISSION_RESULT.json"
