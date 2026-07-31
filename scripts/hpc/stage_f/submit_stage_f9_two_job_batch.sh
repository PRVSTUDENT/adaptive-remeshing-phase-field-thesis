#!/bin/bash
set -u
: "${F9_RUN_ROOT:?}"
: "${F9_AUTHORIZATION:?}"
: "${F9_MAIL:?}"
python3 - "$F9_AUTHORIZATION" <<'PY' || exit 20
import json,sys
a=json.load(open(sys.argv[1]))
assert a["authorization_phrase_received"] is True
assert a["execution_authorized"] is True
assert a["submission_approved"] is True
assert a["authorized_jobs"] == ["M2DKMAT1", "M2RMTYPE1"]
assert a["approved_submissions"] == 2
assert a["maximum_running_jobs"] == 2
assert a["qsub_attempts"] == 0 and a["successful_submissions"] == 0
assert not a["retry_authorized"] and not a["replacement_authorized"]
PY
attempts=0
successes=0
job_a=""
job_b=""
submit_eligible() {
  case_dir="$1"
  pbs="$2"
  attempts=$((attempts+1))
  test "$attempts" -le 2 || return 90
  result=$(cd "$case_dir" && qsub -M "$F9_MAIL" -m abe "$pbs")
  rc=$?
  if [ "$rc" -eq 0 ]; then
    successes=$((successes+1))
    printf '%s' "$result"
  fi
  return "$rc"
}
if python3 -c 'import json,sys;sys.exit(0 if json.load(open(sys.argv[1]))["eligible"] else 1)' \
  "$F9_RUN_ROOT/datacheck_matrix/PREFLIGHT.json"; then
  job_a=$(submit_eligible "$F9_RUN_ROOT/datacheck_matrix" M2DKMAT1.pbs) || true
fi
if python3 -c 'import json,sys;sys.exit(0 if json.load(open(sys.argv[1]))["eligible"] else 1)' \
  "$F9_RUN_ROOT/remesh_type/PREFLIGHT.json"; then
  job_b=$(submit_eligible "$F9_RUN_ROOT/remesh_type" M2RMTYPE1.pbs) || true
fi
printf '{"qsub_attempts":%d,"successful_submissions":%d,"job_a":"%s","job_b":"%s","maximum_running_jobs":2}\n' \
  "$attempts" "$successes" "$job_a" "$job_b" > "$F9_RUN_ROOT/SUBMISSION_RESULT.json"
printf '%s\n%s\n' "$job_a" "$job_b"
