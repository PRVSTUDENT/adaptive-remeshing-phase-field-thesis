#!/bin/bash
set -uo pipefail
attempts=0; successes=0; failures=0; job_id=""
result(){ printf '{"classification":"%s","qsub_attempts":%d,"successful_submissions":%d,"failed_qsub_attempts":%d,"job_id":"%s","authority_consumed":%s}\n' "$1" "$attempts" "$successes" "$failures" "$job_id" "$([ "$attempts" -gt 0 ]&&printf true||printf false)"; return "$2"; }
fail(){ result "$1" "${2:-1}"; exit "${2:-1}"; }
[ "${F26_ACTIVATE_SUBMISSION:-0}" = 1 ] || fail activation_gate_closed 3
[ "${F26_EXPLICIT_AUTHORIZATION:-0}" = 1 ] || fail explicit_authorization_gate_closed 4
package=${F26_PACKAGE_DIR:-}; evidence=${F26_EVIDENCE_ROOT:-}; pbs="$package/M2RMBUILD1.pbs"
case "$package:$evidence" in /*:/*) ;; *) fail absolute_paths_required 5;; esac
case "$package$evidence" in *$'\n'*|*$'\r'*|*,*) fail unsafe_path 5;; esac
[ -r "$pbs" ] && [ -r "$package/F26_SHA256SUMS" ] && [ -r "$package/SHA256SUMS" ] || fail missing_package 6
(cd "$package" && sha256sum -c F26_SHA256SUMS >/dev/null && sha256sum -c SHA256SUMS >/dev/null) || fail manifest_failed 7
mkdir -p "$evidence" && [ -w "$evidence" ] || fail evidence_unwritable 8
[ "$attempts" -eq 0 ] || fail attempt_cap 9; attempts=1
output=$(qsub -v "F26_PACKAGE_DIR=${package},F26_EVIDENCE_DIR=${evidence}" "$pbs"); rc=$?
[ $rc -eq 0 ] || { failures=1; fail qsub_failed "$rc"; }
[[ "$output" =~ ^[0-9]+(\.[A-Za-z0-9][A-Za-z0-9._-]*)?$ ]] || { failures=1; fail invalid_pbs_id 10; }
successes=1; job_id=$output; result submitted_cae_build_qualification 0
