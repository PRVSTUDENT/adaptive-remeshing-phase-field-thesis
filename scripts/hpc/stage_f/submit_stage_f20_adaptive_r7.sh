#!/bin/bash
# Sole guarded F20 Batch-A qsub call site. Preparation/testing uses a PATH mock.
set -uo pipefail
attempts=0; successes=0; failures=0; adaptive_id=""
account() { printf '{"classification":"%s","qsub_attempts":%d,"successful_submissions":%d,"failed_qsub_attempts":%d,"adaptive_job_id":"%s","authority_consumed":%s}\n' "$1" "$attempts" "$successes" "$failures" "$adaptive_id" "$([ "$attempts" -gt 0 ] && printf true || printf false)"; return "$2"; }
fail() { local c=$1 r=${2:-1}; account "$c" "$r"; exit "$r"; }
[ "${F20_ACTIVATE_SUBMISSION:-0}" = 1 ] || fail activation_gate_closed 3
[ "${F20_EXPLICIT_AUTHORIZATION:-0}" = 1 ] || fail explicit_authorization_gate_closed 4
for name in F20_ADAPTIVE_PACKAGE_DIR F20_EVIDENCE_ROOT; do [ -n "${!name:-}" ] || fail "missing_${name}" 5; done
package=$F20_ADAPTIVE_PACKAGE_DIR; evidence=$F20_EVIDENCE_ROOT; pbs="$package/M2RMREG7.pbs"
case "$package" in /*) ;; *) fail relative_package_path 6;; esac
case "$evidence" in /*) ;; *) fail relative_evidence_path 6;; esac
case "$package$evidence" in *$'\n'*|*$'\r'*|*,*) fail unsafe_path 6;; esac
[ -d "$package" ] && [ -r "$pbs" ] || fail missing_package_or_pbs 7
[ -r "$package/F20_SHA256SUMS" ] && [ -r "$package/SHA256SUMS" ] || fail missing_manifest 7
(cd "$package" && sha256sum -c F20_SHA256SUMS >/dev/null && sha256sum -c SHA256SUMS >/dev/null) || fail manifest_validation_failed 8
mkdir -p "$evidence" || fail evidence_directory_creation_failed 9
[ -w "$evidence" ] || fail evidence_directory_not_writable 9
[ "$attempts" -lt 1 ] || fail qsub_attempt_cap_reached 10
attempts=$((attempts+1))
output=$(qsub -v "F20_PACKAGE_DIR=${package},F20_EVIDENCE_DIR=${evidence}" "$pbs"); rc=$?
if [ "$rc" -ne 0 ]; then failures=$((failures+1)); fail qsub_invocation_failed "$rc"; fi
[[ "$output" =~ ^[0-9]+(\.[A-Za-z0-9][A-Za-z0-9._-]*)?$ ]] || { failures=$((failures+1)); fail invalid_pbs_id 11; }
successes=$((successes+1)); adaptive_id=$output
[ "$attempts" -eq 1 ] && [ "$successes" -eq 1 ] && [ "$failures" -eq 0 ] || fail accounting_invariant_failed 12
account submitted_adaptive_r7 0
