#!/bin/bash
set -u
AUTH="${1:?authorization json required}"
JOB_A_DIR="${2:?job A directory required}"
JOB_B_DIR="${3:?job B directory required}"
: "${F7_RUN_ID:?F7_RUN_ID required}"
python3 - "$AUTH" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p))
assert d["execution_authorized"] and d["submission_approved"]
assert d["authorized_jobs"] == ["M2H2IRR1","M2RMAPI2"]
assert d["qsub_attempts"] == 0 and d["approved_submissions"] == 2
assert not d["retry_authorized"] and not d["replacement_authorized"]
PY
attempts=0; successes=0; failures=0; job_a=""; job_b=""; LAST_JOB_ID=""
submit_one() {
  dir="$1"; script="$2"
  attempts=$((attempts+1))
  if jid=$(cd "$dir" && qsub -v "F7_RUN_ID=${F7_RUN_ID}" -M pr21vyci@mailserver.tu-freiberg.de -m abe "$script"); then
    successes=$((successes+1)); LAST_JOB_ID="$jid"; return 0
  else
    failures=$((failures+1)); LAST_JOB_ID=""; return 1
  fi
}
submit_one "$JOB_A_DIR" M2H2IRR1.pbs || true; job_a="$LAST_JOB_ID"
submit_one "$JOB_B_DIR" M2RMAPI2.pbs || true; job_b="$LAST_JOB_ID"
python3 - "$AUTH" "$attempts" "$successes" "$failures" "$job_a" "$job_b" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p))
d.update(execution_authorized=False,submission_approved=False,
 postprocessing_authorized_job_a=False,preprocessing_authorized_job_b=False,
 solver_authorized_job_a=False,solver_authorized_job_b=False,
 retry_authorized=False,replacement_authorized=False,
 automatic_retry_authorized=False,maximum_jobs_now=0,
 qsub_attempts=int(sys.argv[2]),submissions_used=int(sys.argv[2]),
 successful_submissions=int(sys.argv[3]),failed_qsub_attempts=int(sys.argv[4]),
 job_a_id=sys.argv[5],job_b_id=sys.argv[6],status="consumed_monitoring")
open(p,"w").write(json.dumps(d,indent=2,sort_keys=True)+"\n")
PY
printf 'JOB_A=%s\nJOB_B=%s\nATTEMPTS=%s\nSUCCESSES=%s\nFAILURES=%s\n' "$job_a" "$job_b" "$attempts" "$successes" "$failures"
