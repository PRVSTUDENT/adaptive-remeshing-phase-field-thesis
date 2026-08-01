#!/usr/bin/env bash
set -uo pipefail

ROOT=${1:?repository root required}
RUN_DIR=${2:?immutable run directory required}
AUTH="$ROOT/runs/hpc/stage_f/f15_f16_conditional_batch_preparation/BATCH_AUTHORIZATION.json"
CTL="$ROOT/models/generated/mode_ii/f16_controlled_rollback_control"
FORCE="$ROOT/models/generated/mode_ii/f16_controlled_rollback_forced"
REG="$ROOT/models/generated/mode_ii/f16_native_adaptive_region_resolution"

python3 - "$AUTH" <<'PY'
import json,sys
a=json.load(open(sys.argv[1]))
assert a['execution_authorized'] is True and a['submission_approved'] is True
assert a['wave_b_submission_approved'] is True
assert a['wave_b_gate_satisfied_by_user_override'] is True
assert a['currently_executable_jobs']==['M2IRRROLLCTL2','M2IRRROLLFORCE2','M2RMREG2']
assert a['approved_submissions_now']==3 and a['maximum_qsub_attempts_now']==3
assert a['qsub_attempts']==1 and a['successful_submissions']==1
assert a['retry_authorized'] is False and a['replacement_authorized'] is False
PY

test "$(sha256sum "$ROOT/scripts/hpc/notifications/job_notifications.sh" | awk '{print $1}')" = e51843b0c3173b0b2ce0aee8add763356e0b273dc55a136d9ec07e8f7f940bfe
test "$(sha256sum "$CTL/runtime/M2IRR_F16.for" | awk '{print $1}')" = 8d30f10b8c668b9b1e256aeb389e9cf53e38d03fec4e1650bf1e30d975da133a
test "$(sha256sum "$CTL/runtime/M2IRR_F16.inp" | awk '{print $1}')" = a84df34a2bdbfbd55d7f2642082710f1d410cd8480637f9da9aa47c107beed3b
test "$(sha256sum "$CTL/M2IRRROLLCTL2.pbs" | awk '{print $1}')" = 3d909ecc45007672290ea0b35454e4855b5b0f929bac5b29ba18b2eff40860aa
test "$(sha256sum "$FORCE/M2IRRROLLFORCE2.pbs" | awk '{print $1}')" = a2fd83c3f81bed3d22a205336817401e72beefedc8286af6106229ccdaf7b9cf
test "$(sha256sum "$REG/runtime/source_deck.inp" | awk '{print $1}')" = a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2
test "$(sha256sum "$REG/M2RMREG2.pbs" | awk '{print $1}')" = 23c9015ab6231d6288b69c5303c93e2d371ec61b8dd8d9d8712b59e092601950
cmp -s "$CTL/runtime/M2IRR_F16.for" "$FORCE/runtime/M2IRR_F16.for"
cmp -s "$CTL/runtime/M2IRR_F16.inp" "$FORCE/runtime/M2IRR_F16.inp"

mkdir -p "$RUN_DIR/control" "$RUN_DIR/forced" "$RUN_DIR/adaptive_region"
cp -a "$CTL/." "$RUN_DIR/control/"
cp -a "$FORCE/." "$RUN_DIR/forced/"
cp -a "$REG/." "$RUN_DIR/adaptive_region/"

attempts=0; successes=0; failures=0
submit_one() {
  local case_dir=$1 pbs=$2 dependency=${3:-} out_file=$4 err_file=$5
  attempts=$((attempts+1))
  if [ -n "$dependency" ]; then
    (cd "$case_dir" && qsub -W "depend=$dependency" "$pbs" >"$out_file" 2>"$err_file")
  else
    (cd "$case_dir" && qsub "$pbs" >"$out_file" 2>"$err_file")
  fi
  local rc=$?
  if [ "$rc" -eq 0 ]; then successes=$((successes+1)); else failures=$((failures+1)); fi
  return "$rc"
}

submit_one "$RUN_DIR/control" M2IRRROLLCTL2.pbs "" QSUB_JOB_ID.txt QSUB_STDERR.txt; ctl_rc=$?
ctl_id=""; [ -s "$RUN_DIR/control/QSUB_JOB_ID.txt" ] && IFS= read -r ctl_id <"$RUN_DIR/control/QSUB_JOB_ID.txt"
submit_one "$RUN_DIR/forced" M2IRRROLLFORCE2.pbs "" QSUB_JOB_ID.txt QSUB_STDERR.txt; force_rc=$?
force_id=""; [ -s "$RUN_DIR/forced/QSUB_JOB_ID.txt" ] && IFS= read -r force_id <"$RUN_DIR/forced/QSUB_JOB_ID.txt"
dependency=""
if [ "$ctl_rc" -eq 0 ] && [ -n "$ctl_id" ]; then dependency="afterany:$ctl_id"; fi
if [ -n "$dependency" ]; then
  submit_one "$RUN_DIR/adaptive_region" M2RMREG2.pbs "$dependency" QSUB_JOB_ID.txt QSUB_STDERR.txt; reg_rc=$?
else
  attempts=$((attempts+1)); failures=$((failures+1)); reg_rc=125
  printf '%s\n' 'control submission unavailable; concurrency dependency cannot be created' >"$RUN_DIR/adaptive_region/QSUB_STDERR.txt"
fi
reg_id=""; [ -s "$RUN_DIR/adaptive_region/QSUB_JOB_ID.txt" ] && IFS= read -r reg_id <"$RUN_DIR/adaptive_region/QSUB_JOB_ID.txt"

python3 - "$attempts" "$successes" "$failures" "$ctl_rc" "$force_rc" "$reg_rc" "$ctl_id" "$force_id" "$reg_id" "$dependency" >"$RUN_DIR/SUBMISSION_RESULT.json" <<'PY'
import datetime,json,sys
print(json.dumps({'wave_b_qsub_attempts':int(sys.argv[1]),'wave_b_successful_submissions':int(sys.argv[2]),
'wave_b_failed_qsub_attempts':int(sys.argv[3]),'return_codes':{'M2IRRROLLCTL2':int(sys.argv[4]),'M2IRRROLLFORCE2':int(sys.argv[5]),'M2RMREG2':int(sys.argv[6])},
'pbs_job_ids':{'M2IRRROLLCTL2':sys.argv[7] or None,'M2IRRROLLFORCE2':sys.argv[8] or None,'M2RMREG2':sys.argv[9] or None},
'scientific_dependency':'none','scheduler_concurrency_dependency':sys.argv[10] or None,
'execution_authorized':False,'submission_approved':False,'maximum_jobs_now':0,
'utc':datetime.datetime.utcnow().isoformat()+'Z'},indent=2,sort_keys=True))
PY
[ "$attempts" -eq 3 ] || exit 90
[ "$failures" -eq 0 ] || exit 91
