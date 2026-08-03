#!/bin/bash
set -euo pipefail
if [ "${F19_ACTIVATE_SUBMISSION:-0}" != 1 ]; then
  echo "F19 preparation only: submission is not authorized" >&2
  exit 3
fi
if [ "${F19_EXPLICIT_AUTHORIZATION:-0}" != 1 ]; then
  echo "fresh exact F19 authorization is required" >&2
  exit 4
fi
: "${F19_CONTROL_PACKAGE_DIR:?required}"
: "${F19_FORCED_PACKAGE_DIR:?required}"
: "${F19_ADAPTIVE_PACKAGE_DIR:?required}"
: "${F19_EVIDENCE_ROOT:?required}"
attempts=0
successes=0
submit_one() {
  package_dir=$1
  evidence_dir=$2
  pbs=$3
  dependency=${4:-}
  attempts=$((attempts + 1))
  if [ -n "$dependency" ]; then
    output=$(F19_PACKAGE_DIR="$package_dir" F19_EVIDENCE_DIR="$evidence_dir" qsub -W "depend=afterany:$dependency" "$pbs") || return $?
  else
    output=$(F19_PACKAGE_DIR="$package_dir" F19_EVIDENCE_DIR="$evidence_dir" qsub "$pbs") || return $?
  fi
  successes=$((successes + 1))
  SUBMITTED_ID=$output
}
test $attempts -lt 3 && submit_one "$F19_CONTROL_PACKAGE_DIR" "$F19_EVIDENCE_ROOT/control" "$F19_CONTROL_PACKAGE_DIR/M2IRRROLLCTL5.pbs"
control_id=$SUBMITTED_ID
test $attempts -lt 3 && submit_one "$F19_FORCED_PACKAGE_DIR" "$F19_EVIDENCE_ROOT/forced" "$F19_FORCED_PACKAGE_DIR/M2IRRROLLFORCE5.pbs"
forced_id=$SUBMITTED_ID
test $attempts -lt 3 && submit_one "$F19_ADAPTIVE_PACKAGE_DIR" "$F19_EVIDENCE_ROOT/adaptive" "$F19_ADAPTIVE_PACKAGE_DIR/M2RMREG6.pbs" "$control_id"
adaptive_id=$SUBMITTED_ID
test $attempts -eq 3 && test $successes -eq 3
printf 'control=%s\nforced=%s\nadaptive=%s\n' "$control_id" "$forced_id" "$adaptive_id"
