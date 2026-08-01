#!/bin/bash
set -u
ROOT=${1:?runtime root required}
AUTH=${2:?authorization json required}
attempts=0
successes=0
failed=0
job_a=""
job_b=""
python3 - "$AUTH" <<'PY' || exit 20
import json,sys
a=json.load(open(sys.argv[1]))
assert a['execution_authorized'] and a['submission_approved']
assert a['authorized_jobs']==['M2RTLOAD1','M2RMREG1']
assert a['approved_submissions']==2 and a['maximum_jobs_now']==2
assert not a['retry_authorized'] and not a['replacement_authorized']
PY
submit_one() {
  d=$1; pbs=$2
  attempts=$((attempts+1))
  out=$(cd "$d" && qsub -M pr21vyci@tu-freiberg.de -m abe "$pbs" 2>&1)
  rc=$?
  if [ "$rc" -eq 0 ]; then successes=$((successes+1)); printf '%s' "$out"
  else failed=$((failed+1)); printf '%s\n' "$out" >&2; return "$rc"; fi
}
job_a=$(submit_one "$ROOT/runtime_load" M2RTLOAD1.pbs) || true
job_b=$(submit_one "$ROOT/adaptive_region" M2RMREG1.pbs) || true
python3 - "$ROOT/SUBMISSION_RESULT.json" "$attempts" "$successes" "$failed" "$job_a" "$job_b" <<'PY'
import json,sys
out={'qsub_attempts':int(sys.argv[2]),'successful_submissions':int(sys.argv[3]),
     'failed_qsub_attempts':int(sys.argv[4]),'job_a':sys.argv[5],'job_b':sys.argv[6],
     'retries':0,'replacements':0,'direct_qsub':0,'qdel':0,'qmove':0}
json.dump(out,open(sys.argv[1],'w'),indent=2,sort_keys=True); open(sys.argv[1],'a').write('\n')
PY
test "$attempts" -le 2 || exit 21
exit 0
