#!/usr/bin/env bash
set -uo pipefail

ROOT=${1:?repository root required}
RUN_DIR=${2:?immutable run directory required}
AUTH="$ROOT/runs/hpc/stage_f/f16_queue_access_qualification_and_wave_b_r3_preparation/F16_R3_AUTHORIZATION.json"
CTL="$ROOT/models/generated/mode_ii/f16_controlled_rollback_control_r3"
FORCE="$ROOT/models/generated/mode_ii/f16_controlled_rollback_forced_r3"
REG="$ROOT/models/generated/mode_ii/f16_native_adaptive_region_resolution_r3"

mkdir -p "$RUN_DIR"
attempts=0
successes=0
failures=0
withheld=0
ctl_id=""
force_id=""
reg_id=""
ctl_rc=null
force_rc=null
reg_rc=null
dependency=""

write_result() {
  local classification=$1
  python3 - "$classification" "$attempts" "$successes" "$failures" "$withheld" \
    "$ctl_rc" "$force_rc" "$reg_rc" "$ctl_id" "$force_id" "$reg_id" "$dependency" \
    >"$RUN_DIR/SUBMISSION_RESULT.json" <<'PY'
import datetime,json,sys
def rc(v): return None if v == 'null' else int(v)
print(json.dumps({
  'classification':sys.argv[1],
  'actual_qsub_attempts':int(sys.argv[2]),
  'successful_submissions':int(sys.argv[3]),
  'failed_qsub_attempts':int(sys.argv[4]),
  'withheld_lanes':int(sys.argv[5]),
  'return_codes':{'M2IRRROLLCTL3':rc(sys.argv[6]),'M2IRRROLLFORCE3':rc(sys.argv[7]),'M2RMREG3':rc(sys.argv[8])},
  'pbs_job_ids':{'M2IRRROLLCTL3':sys.argv[9] or None,'M2IRRROLLFORCE3':sys.argv[10] or None,'M2RMREG3':sys.argv[11] or None},
  'scientific_dependency':'none',
  'scheduler_concurrency_dependency':sys.argv[12] or None,
  'execution_authorized':False,'submission_approved':False,'maximum_jobs_now':0,
  'retry_performed':False,'same_session_replacement_performed':False,
  'utc':datetime.datetime.utcnow().isoformat()+'Z'
},indent=2,sort_keys=True))
PY
}

fail_preflight() {
  write_result "$1"
  exit "$2"
}

[ -f "$AUTH" ] || fail_preflight authorization_missing 20
python3 - "$AUTH" <<'PY' || fail_preflight authorization_invalid 21
import json,sys
a=json.load(open(sys.argv[1]))
assert a['execution_authorized'] is True and a['submission_approved'] is True
assert a['authorized_jobs']==['M2IRRROLLCTL3','M2IRRROLLFORCE3','M2RMREG3']
assert a['maximum_qsub_attempts']==3 and a['maximum_running_jobs']==2
assert a['retry_authorized'] is False and a['same_session_replacement_authorized'] is False
assert a['direct_qsub_authorized'] is False and a['qdel_authorized'] is False and a['qmove_authorized'] is False
PY

test "$(sha256sum "$CTL/runtime/M2IRR_F16.for" | awk '{print $1}')" = 8d30f10b8c668b9b1e256aeb389e9cf53e38d03fec4e1650bf1e30d975da133a || fail_preflight hash_mismatch 22
test "$(sha256sum "$CTL/runtime/M2IRR_F16.inp" | awk '{print $1}')" = a84df34a2bdbfbd55d7f2642082710f1d410cd8480637f9da9aa47c107beed3b || fail_preflight hash_mismatch 22
test "$(sha256sum "$REG/runtime/source_deck.inp" | awk '{print $1}')" = a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2 || fail_preflight hash_mismatch 22
test "$(sha256sum "$CTL/M2IRRROLLCTL3.pbs" | awk '{print $1}')" = 32b2813bd0eda812853b654be84b939e9f21ed988a57d3b2a23882f847e6f2aa || fail_preflight hash_mismatch 22
test "$(sha256sum "$FORCE/M2IRRROLLFORCE3.pbs" | awk '{print $1}')" = 1916a80b6938fddca5a4a87466b35b0d54dfc0366ffe741841599e2990e7a210 || fail_preflight hash_mismatch 22
test "$(sha256sum "$REG/M2RMREG3.pbs" | awk '{print $1}')" = dcca83868e894c1e7226487d7560cfdf20ddf6906964943aa12437ab6e51bbe1 || fail_preflight hash_mismatch 22
cmp -s "$CTL/runtime/M2IRR_F16.for" "$FORCE/runtime/M2IRR_F16.for" || fail_preflight scientific_identity_mismatch 23
cmp -s "$CTL/runtime/M2IRR_F16.inp" "$FORCE/runtime/M2IRR_F16.inp" || fail_preflight scientific_identity_mismatch 23

qstat -u "$(id -un)" >"$RUN_DIR/QSTAT_PRE_SUBMISSION.txt" || fail_preflight qstat_failed 24
if grep -E 'M2IRRROLLCTL3|M2IRRROLLFORCE3|M2RMREG3' "$RUN_DIR/QSTAT_PRE_SUBMISSION.txt" >/dev/null; then
  fail_preflight duplicate_job_name_detected 25
fi

mkdir -p "$RUN_DIR/control" "$RUN_DIR/forced" "$RUN_DIR/adaptive_region"
cp -a "$CTL/." "$RUN_DIR/control/"
cp -a "$FORCE/." "$RUN_DIR/forced/"
cp -a "$REG/." "$RUN_DIR/adaptive_region/"

submit_one() {
  local case_dir=$1 pbs=$2 dependency_arg=${3:-} id_file=$4 err_file=$5
  attempts=$((attempts+1))
  if [ -n "$dependency_arg" ]; then
    (cd "$case_dir" && qsub -W "depend=$dependency_arg" "$pbs" >"$id_file" 2>"$err_file")
  else
    (cd "$case_dir" && qsub "$pbs" >"$id_file" 2>"$err_file")
  fi
  local qrc=$?
  if [ "$qrc" -eq 0 ]; then successes=$((successes+1)); else failures=$((failures+1)); fi
  return "$qrc"
}

submit_one "$RUN_DIR/control" M2IRRROLLCTL3.pbs "" QSUB_JOB_ID.txt QSUB_STDERR.txt
ctl_rc=$?
[ -s "$RUN_DIR/control/QSUB_JOB_ID.txt" ] && IFS= read -r ctl_id <"$RUN_DIR/control/QSUB_JOB_ID.txt"

submit_one "$RUN_DIR/forced" M2IRRROLLFORCE3.pbs "" QSUB_JOB_ID.txt QSUB_STDERR.txt
force_rc=$?
[ -s "$RUN_DIR/forced/QSUB_JOB_ID.txt" ] && IFS= read -r force_id <"$RUN_DIR/forced/QSUB_JOB_ID.txt"

if [ "$ctl_rc" -eq 0 ] && printf '%s\n' "$ctl_id" | grep -Eq '^[0-9]+\.[A-Za-z0-9._-]+$'; then
  dependency="afterany:$ctl_id"
  submit_one "$RUN_DIR/adaptive_region" M2RMREG3.pbs "$dependency" QSUB_JOB_ID.txt QSUB_STDERR.txt
  reg_rc=$?
  [ -s "$RUN_DIR/adaptive_region/QSUB_JOB_ID.txt" ] && IFS= read -r reg_id <"$RUN_DIR/adaptive_region/QSUB_JOB_ID.txt"
else
  withheld=$((withheld+1))
  printf '%s\n' 'withheld: valid M2IRRROLLCTL3 PBS ID unavailable' >"$RUN_DIR/adaptive_region/WITHHELD.txt"
fi

if [ "$failures" -eq 0 ] && [ "$attempts" -eq 3 ]; then
  write_result three_submissions_accepted
  exit 0
fi
write_result submission_sequence_incomplete_no_retry
exit 91
