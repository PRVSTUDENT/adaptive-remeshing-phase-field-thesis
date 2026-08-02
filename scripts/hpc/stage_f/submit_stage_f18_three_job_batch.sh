#!/bin/bash
set -uo pipefail
set +x
: "${F18_AUTHORIZED:?F18_AUTHORIZED required}"
test "$F18_AUTHORIZED" = 1 || exit 2
: "${F18_CTL_PACKAGE:?}" "${F18_FORCE_PACKAGE:?}" "${F18_REG_PACKAGE:?}" "${F18_RUN_ROOT:?}"
mkdir -p "$F18_RUN_ROOT" || exit 3
record="$F18_RUN_ROOT/SUBMISSION_RECORD.json"
attempts=0; successes=0
fail(){ printf '{"qsub_attempts":%s,"successful_submissions":%s,"classification":"%s","authority_consumed":true}\n' "$attempts" "$successes" "$1" > "$record"; exit 1; }
test "$(qstat -u "$USER" 2>/dev/null | awk '$4 ~ /M2IRRROLLCTL4|M2IRRROLLFORCE4|M2RMREG5/{n++} END{print n+0}')" = 0 || fail duplicate_job_name
attempts=$((attempts+1)); ctl=$(qsub -v F18_PACKAGE_DIR="$F18_CTL_PACKAGE",F18_EVIDENCE_DIR="$F18_RUN_ROOT/control" "$F18_CTL_PACKAGE/M2IRRROLLCTL4.pbs") || fail control_submission_failed
successes=$((successes+1)); case "$ctl" in [0-9]*.*) ;; *) fail invalid_control_pbs_id;; esac
attempts=$((attempts+1)); force=$(qsub -v F18_PACKAGE_DIR="$F18_FORCE_PACKAGE",F18_EVIDENCE_DIR="$F18_RUN_ROOT/forced" "$F18_FORCE_PACKAGE/M2IRRROLLFORCE4.pbs") || fail forced_submission_failed
successes=$((successes+1))
attempts=$((attempts+1)); reg=$(qsub -W depend=afterany:"$ctl" -v F18_PACKAGE_DIR="$F18_REG_PACKAGE",F18_EVIDENCE_DIR="$F18_RUN_ROOT/adaptive" "$F18_REG_PACKAGE/M2RMREG5.pbs") || fail adaptive_submission_failed
successes=$((successes+1))
printf '{"qsub_attempts":3,"successful_submissions":3,"control_job_id":"%s","forced_job_id":"%s","adaptive_job_id":"%s","adaptive_dependency":"afterany:%s","authority_consumed":true}\n' "$ctl" "$force" "$reg" "$ctl" > "$record"
