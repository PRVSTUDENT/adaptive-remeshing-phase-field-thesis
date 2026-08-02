#!/bin/bash
# Guarded F17 parent-shell orchestrator. This is the only authorized qsub call site.
set -uo pipefail
set +x

ROOT="${F17_REPO_ROOT:?F17_REPO_ROOT required}"
RUN_ROOT="${F17_RUN_ROOT:?F17_RUN_ROOT required}"
AUTH="$ROOT/runs/hpc/stage_f/f17_penalty_activation_and_adaptive_region_repair/BATCH_AUTHORIZATION.json"
PROBE="$ROOT/models/generated/mode_ii/f17_penalty_activation_probe"
REGION="$ROOT/models/generated/mode_ii/f17_native_adaptive_region_repair"
mkdir -p "$RUN_ROOT"

python3 - "$AUTH" <<'PY'
import json,sys
a=json.load(open(sys.argv[1]))
assert a['authorization_phrase_received'] is True
assert a['authorized_jobs']==['M2IRRPENACT1','M2RMREG4']
assert a['preparation_commit']=='b4d9fad6b7c155ae60c6af47b44af9b498d43edc'
assert a['queue']=='entry_imfdfkmq'
assert a['execution_authorized'] is True and a['submission_approved'] is True
assert a['approved_submissions_now']==2 and a['maximum_qsub_invocations']==2
assert a['maximum_running_jobs']==2
assert a['qsub_attempts']==0 and a['successful_submissions']==0
for key in ('retry_authorized','replacement_authorized','direct_qsub_authorized','qdel_authorized','qmove_authorized','rerun_authorized'):
    assert a[key] is False
PY

(cd "$PROBE" && sha256sum -c F17_SHA256SUMS)
(cd "$REGION" && sha256sum -c F17_SHA256SUMS)
grep -q '^#PBS -q entry_imfdfkmq$' "$PROBE/M2IRRPENACT1.pbs"
grep -q '^#PBS -q entry_imfdfkmq$' "$REGION/M2RMREG4.pbs"

qstat -u pr21vyci >"$RUN_ROOT/QSTAT_PREFLIGHT.txt"
if grep -E 'M2IRRPENACT1|M2RMREG4' "$RUN_ROOT/QSTAT_PREFLIGHT.txt"; then
  echo 'duplicate F17 job detected; no submission performed' >&2
  exit 30
fi

attempts=0
successes=0
failures=0
probe_id=''
region_id=''

submit_one() {
  name="$1"
  package="$2"
  pbs="$3"
  id_file="$RUN_ROOT/${name}_QSUB_ID.txt"
  err_file="$RUN_ROOT/${name}_QSUB_STDERR.txt"
  evidence="$RUN_ROOT/evidence/${name}"
  runtime="$RUN_ROOT/runtime/${name}"
  mkdir -p "$evidence" "$runtime"
  cp -Rp "$package/." "$runtime/"
  attempts=$((attempts+1))
  (cd "$runtime" && qsub -v "F17_PACKAGE_DIR=$runtime,F17_EVIDENCE_DIR=$evidence" "$pbs" >"$id_file" 2>"$err_file")
  rc=$?
  if [ "$rc" -eq 0 ]; then
    successes=$((successes+1))
  else
    failures=$((failures+1))
  fi
  printf '%s' "$rc" >"$RUN_ROOT/${name}_QSUB_RC.txt"
}

submit_one M2IRRPENACT1 "$PROBE" M2IRRPENACT1.pbs
probe_rc=$(cat "$RUN_ROOT/M2IRRPENACT1_QSUB_RC.txt")
if [ "$probe_rc" -eq 0 ]; then probe_id=$(tr -d '\r\n' <"$RUN_ROOT/M2IRRPENACT1_QSUB_ID.txt"); fi

submit_one M2RMREG4 "$REGION" M2RMREG4.pbs
region_rc=$(cat "$RUN_ROOT/M2RMREG4_QSUB_RC.txt")
if [ "$region_rc" -eq 0 ]; then region_id=$(tr -d '\r\n' <"$RUN_ROOT/M2RMREG4_QSUB_ID.txt"); fi

python3 - "$RUN_ROOT/SUBMISSION_RESULT.json" "$attempts" "$successes" "$failures" "$probe_rc" "$region_rc" "$probe_id" "$region_id" <<'PY'
import json,sys
out={
  'qsub_attempts':int(sys.argv[2]),
  'successful_submissions':int(sys.argv[3]),
  'failed_qsub_attempts':int(sys.argv[4]),
  'qsub_return_codes':{'M2IRRPENACT1':int(sys.argv[5]),'M2RMREG4':int(sys.argv[6])},
  'pbs_ids':{'M2IRRPENACT1':sys.argv[7],'M2RMREG4':sys.argv[8]},
  'retries':0,'replacements':0,'direct_qsub':0,'qdel':0,'qmove':0
}
open(sys.argv[1],'w').write(json.dumps(out,indent=2,sort_keys=True)+'\n')
PY

test "$attempts" -eq 2
test $((successes+failures)) -eq 2
exit 0
