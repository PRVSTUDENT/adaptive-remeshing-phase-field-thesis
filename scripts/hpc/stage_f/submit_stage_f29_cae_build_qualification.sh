#!/bin/bash
set -uo pipefail
attempts=0; successes=0; failures=0; job_id=""
PACKAGE_PREP_SHA="b2a3535742a08961688ee5e65dbe4c8e412e4118"

result(){ printf '{"classification":"%s","qsub_attempts":%d,"successful_submissions":%d,"failed_qsub_attempts":%d,"job_id":"%s","authority_consumed":%s}\n' "$1" "$attempts" "$successes" "$failures" "$job_id" "$([ "$attempts" -gt 0 ]&&printf true||printf false)"; return "$2"; }
fail(){ result "$1" "${2:-1}"; exit "${2:-1}"; }

[ "${F29_ACTIVATE_SUBMISSION:-0}" = 1 ] || fail activation_gate_closed 3
[ "${F29_EXPLICIT_AUTHORIZATION:-0}" = 1 ] || fail explicit_authorization_gate_closed 4

# Check ancestry: PACKAGE_PREP_SHA must be an ancestor of HEAD
git merge-base --is-ancestor "$PACKAGE_PREP_SHA" HEAD 2>/dev/null || fail preparation_sha_not_ancestor 4

package=${F29_PACKAGE_DIR:-}; evidence=${F29_EVIDENCE_ROOT:-}; pbs="$package/M2RMBUILD4.pbs"
case "$package:$evidence" in /*:/*) ;; *) fail absolute_paths_required 5;; esac
case "$package$evidence" in *$'\n'*|*$'\r'*|*,*) fail unsafe_path 5;; esac

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || fail not_in_git_repository 5
tracked_package_dir="$repo_root/models/generated/mode_ii/f29_topology_safe_cae_build"
[ "$package" = "$tracked_package_dir" ] || fail package_path_not_restricted_to_tracked_dir 5

git diff --quiet "$PACKAGE_PREP_SHA" HEAD -- "$package" || fail package_modified_since_prep 4

p_blobs=$(git ls-tree -r "$PACKAGE_PREP_SHA" -- "$package" | awk '{print $3, $4}')
head_blobs=$(git ls-tree -r HEAD -- "$package" | awk '{print $3, $4}')
[ "$p_blobs" = "$head_blobs" ] || fail package_blob_mismatch 4

[ -r "$pbs" ] && [ -r "$package/F29_SHA256SUMS" ] && [ -r "$package/SHA256SUMS" ] || fail missing_package 6
(cd "$package" && sha256sum -c F29_SHA256SUMS >/dev/null && sha256sum -c SHA256SUMS >/dev/null) || fail manifest_failed 7
mkdir -p "$evidence" && [ -w "$evidence" ] || fail evidence_unwritable 8

[ "$attempts" -eq 0 ] || fail attempt_cap 9; attempts=1
output=$(qsub -v "F29_PACKAGE_DIR=${package},F29_EVIDENCE_DIR=${evidence}" "$pbs"); rc=$?
[ $rc -eq 0 ] || { failures=1; fail qsub_failed "$rc"; }
[[ "$output" =~ ^[0-9]+(\.[A-Za-z0-9][A-Za-z0-9._-]*)?$ ]] || { failures=1; fail invalid_pbs_id 10; }
successes=1; job_id=$output; result submitted_cae_build_qualification 0
