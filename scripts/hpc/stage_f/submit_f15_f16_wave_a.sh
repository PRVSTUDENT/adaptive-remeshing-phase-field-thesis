#!/usr/bin/env bash
set -uo pipefail

ROOT=${1:?repository root required}
RUN_DIR=${2:?immutable run directory required}
AUTH="$ROOT/runs/hpc/stage_f/f15_f16_conditional_batch_preparation/BATCH_AUTHORIZATION.json"
PACKAGE="$ROOT/models/generated/infrastructure/f15_dual_channel_notification_smoke"

mkdir -p "$RUN_DIR"
python3 - "$AUTH" <<'PY'
import json,sys
a=json.load(open(sys.argv[1]))
assert a['execution_authorized'] is True
assert a['submission_approved'] is True
assert a['currently_executable_jobs']==['M2NOTIFY1']
assert a['approved_submissions_now']==1 and a['maximum_qsub_attempts_now']==1
assert a['qsub_attempts']==0 and a['successful_submissions']==0
assert a['retry_authorized'] is False and a['replacement_authorized'] is False
assert a['wave_b_gate_satisfied'] is False and a['wave_b_submission_approved'] is False
PY

test "$(sha256sum "$PACKAGE/M2NOTIFY1.pbs" | awk '{print $1}')" = 6afeef49b3d5f408e75804dc2c792c2c314cfb556bf881715ac0655f0a05e804
test "$(sha256sum "$PACKAGE/runtime/job_notifications.sh" | awk '{print $1}')" = e51843b0c3173b0b2ce0aee8add763356e0b273dc55a136d9ec07e8f7f940bfe
cp -a "$PACKAGE/." "$RUN_DIR/"
cd "$RUN_DIR" || exit 20
sha256sum -c SHA256SUMS

attempts=0
successes=0
failures=0
attempts=$((attempts+1))
qsub M2NOTIFY1.pbs >QSUB_JOB_ID.txt 2>QSUB_STDERR.txt
qsub_rc=$?
if [ "$qsub_rc" -eq 0 ]; then successes=1; else failures=1; fi
job_id=""
if [ -s QSUB_JOB_ID.txt ]; then IFS= read -r job_id < QSUB_JOB_ID.txt; fi
python3 - "$qsub_rc" "$attempts" "$successes" "$failures" "$job_id" >SUBMISSION_RESULT.json <<'PY'
import json,sys,datetime
print(json.dumps({'qsub_return_code':int(sys.argv[1]),'qsub_attempts':int(sys.argv[2]),
'successful_submissions':int(sys.argv[3]),'failed_qsub_attempts':int(sys.argv[4]),
'pbs_job_id':sys.argv[5] or None,'execution_authorized':False,'submission_approved':False,
'maximum_jobs_now':0,'approved_submissions_now':0,'wave_b_conditionally_authorized':True,
'wave_b_gate_satisfied':False,'wave_b_submission_approved':False,
'utc':datetime.datetime.utcnow().isoformat()+'Z'},indent=2,sort_keys=True))
PY
exit "$qsub_rc"
