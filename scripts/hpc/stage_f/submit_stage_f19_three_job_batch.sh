#!/bin/bash
# The sole guarded F19 qsub call site. Preparation/testing uses a PATH mock.
set -uo pipefail

attempts=0
successes=0
failures=0
control_id=""
forced_id=""
adaptive_id=""

account() {
  local classification=$1 rc=$2
  printf '{"classification":"%s","qsub_attempts":%d,"successful_submissions":%d,"failed_qsub_attempts":%d,"control_job_id":"%s","forced_job_id":"%s","adaptive_job_id":"%s","authority_consumed":%s}\n' \
    "$classification" "$attempts" "$successes" "$failures" \
    "$control_id" "$forced_id" "$adaptive_id" \
    "$([ "$attempts" -gt 0 ] && printf true || printf false)"
  return "$rc"
}

fail() {
  local classification=$1 rc=${2:-1}
  account "$classification" "$rc"
  exit "$rc"
}

if [ "${F19_ACTIVATE_SUBMISSION:-0}" != 1 ]; then
  fail activation_gate_closed 3
fi
if [ "${F19_EXPLICIT_AUTHORIZATION:-0}" != 1 ]; then
  fail explicit_authorization_gate_closed 4
fi

for required_name in F19_CONTROL_PACKAGE_DIR F19_FORCED_PACKAGE_DIR F19_ADAPTIVE_PACKAGE_DIR F19_EVIDENCE_ROOT; do
  [ -n "${!required_name:-}" ] || fail "missing_${required_name}" 5
done

validate_path_value() {
  local value=$1 kind=$2
  [ -n "$value" ] || fail "empty_${kind}_path" 6
  case "$value" in /*) ;; *) fail "relative_${kind}_path" 6 ;; esac
  case "$value" in *$'\n'*|*$'\r'*|*,*) fail "unsafe_${kind}_path" 6 ;; esac
}

validate_package() {
  local package_dir=$1 evidence_dir=$2 pbs=$3 expected_name=$4
  validate_path_value "$package_dir" package
  validate_path_value "$evidence_dir" evidence
  validate_path_value "$pbs" pbs
  [ -d "$package_dir" ] || fail missing_package_directory 7
  [ "$pbs" = "$package_dir/$expected_name" ] || fail unexpected_pbs_path 7
  [ -r "$pbs" ] || fail unreadable_pbs_wrapper 7
  [ -r "$package_dir/F19_SHA256SUMS" ] || fail missing_f19_manifest 7
  [ -r "$package_dir/SHA256SUMS" ] || fail missing_legacy_manifest 7
  (cd "$package_dir" && sha256sum -c F19_SHA256SUMS >/dev/null) || fail f19_manifest_validation_failed 8
  (cd "$package_dir" && sha256sum -c SHA256SUMS >/dev/null) || fail legacy_manifest_validation_failed 8
  mkdir -p "$evidence_dir" || fail evidence_directory_creation_failed 9
  [ -d "$evidence_dir" ] && [ -w "$evidence_dir" ] || fail evidence_directory_not_writable 9
}

valid_pbs_id() {
  local value=$1
  [[ "$value" =~ ^[0-9]+(\.[A-Za-z0-9][A-Za-z0-9._-]*)?$ ]]
}

submit_one() {
  local package_dir=$1 evidence_dir=$2 expected_name=$3 dependency=${4:-}
  local pbs="$package_dir/$expected_name" output rc
  local -a qsub_args

  validate_package "$package_dir" "$evidence_dir" "$pbs" "$expected_name"
  qsub_args=(-v "F19_PACKAGE_DIR=${package_dir},F19_EVIDENCE_DIR=${evidence_dir}")
  if [ -n "$dependency" ]; then
    valid_pbs_id "$dependency" || fail invalid_dependency_pbs_id 10
    qsub_args+=(-W "depend=afterany:${dependency}")
  fi
  qsub_args+=("$pbs")

  [ "$attempts" -lt 3 ] || fail qsub_attempt_cap_reached 10
  attempts=$((attempts + 1))
  output=$(qsub "${qsub_args[@]}")
  rc=$?
  if [ "$rc" -ne 0 ]; then
    failures=$((failures + 1))
    fail "qsub_invocation_${attempts}_failed" "$rc"
  fi
  if ! valid_pbs_id "$output"; then
    failures=$((failures + 1))
    fail "qsub_invocation_${attempts}_invalid_pbs_id" 11
  fi
  successes=$((successes + 1))
  SUBMITTED_ID=$output
}

submit_one "$F19_CONTROL_PACKAGE_DIR" "$F19_EVIDENCE_ROOT/control" M2IRRROLLCTL5.pbs
control_id=$SUBMITTED_ID
submit_one "$F19_FORCED_PACKAGE_DIR" "$F19_EVIDENCE_ROOT/forced" M2IRRROLLFORCE5.pbs
forced_id=$SUBMITTED_ID
submit_one "$F19_ADAPTIVE_PACKAGE_DIR" "$F19_EVIDENCE_ROOT/adaptive" M2RMREG6.pbs "$control_id"
adaptive_id=$SUBMITTED_ID

[ "$attempts" -eq 3 ] && [ "$successes" -eq 3 ] && [ "$failures" -eq 0 ] || fail accounting_invariant_failed 12
account submitted_three_job_batch 0
