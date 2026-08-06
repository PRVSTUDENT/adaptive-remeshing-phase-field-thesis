#!/bin/bash
# Guarded orchestrator for Stage F40 M2RMBISECT1 Abaqus CAE bisection diagnostic.
# Strict activation and authorization gates; 1 submission call maximum; no retries.
set -Eeuo pipefail

PREP_SHA="${F40_PREPARATION_SHA:?F40_PREPARATION_SHA must be explicitly bound after package review}"

echo "=== Stage F40 M2RMBISECT1 Launcher Bisection Orchestrator ==="

# 1. Activation Gate
if [ "${F40_ALLOW_SUBMISSION:-false}" != "true" ]; then
  echo "HALT: Activation gate F40_ALLOW_SUBMISSION is not 'true'. Refusing submission."
  exit 0
fi

# 2. Authorization Gate
if [ "${F40_AUTHORIZE_M2RMBISECT1:-false}" != "true" ]; then
  echo "HALT: Authorization gate F40_AUTHORIZE_M2RMBISECT1 is not 'true'. Refusing submission."
  exit 0
fi

# 3. Head descendant check
HEAD_SHA=$(git rev-parse HEAD)
if ! git merge-base --is-ancestor "$PREP_SHA" "$HEAD_SHA"; then
  echo "ERROR: HEAD ($HEAD_SHA) is not a descendant of preparation revision ($PREP_SHA)."
  exit 1
fi

# 4. Blob identity check freezing both package directory and submission wrapper
PKG_DIR="models/generated/mode_ii/f40_f38_cae_invocation_model_building_bisect"
WRAPPER_PATH="scripts/hpc/stage_f/submit_stage_f40_cae_bisect.sh"
FREEZE_PATHS=("$PKG_DIR" "$WRAPPER_PATH")

PREP_BLOBS=$(git ls-tree -r "$PREP_SHA" -- "${FREEZE_PATHS[@]}" | awk '{print $3, $4}' | sort)
HEAD_BLOBS=$(git ls-tree -r "$HEAD_SHA" -- "${FREEZE_PATHS[@]}" | awk '{print $3, $4}' | sort)

if [ -z "$PREP_BLOBS" ] || [ -z "$HEAD_BLOBS" ]; then
  echo "ERROR: Package or submission wrapper blob list is empty."
  exit 1
fi

if [ "$PREP_BLOBS" != "$HEAD_BLOBS" ]; then
  echo "ERROR: Package/wrapper blob mismatch between preparation SHA ($PREP_SHA) and HEAD ($HEAD_SHA)."
  exit 1
fi

# 5. Lock file path definition
LOCK_FILE="runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/M2RMBISECT1_SUBMITTED.lock"

# 6. Maximum Submission Audit & Binary Check
if [ "${MAX_SUBMISSIONS:-1}" -ne 1 ]; then
  echo "ERROR: Only 1 submission maximum authorized."
  exit 1
fi

command -v qsub >/dev/null 2>&1 || { echo "ERROR: qsub command not found on PATH." >&2; exit 1; }
command -v qstat >/dev/null 2>&1 || { echo "ERROR: qstat command not found on PATH." >&2; exit 1; }

# 7. Check scheduler queue state for existing M2RMBISECT1 job
USER_NAME=$(id -un 2>/dev/null || echo "${USER:-}")
QSTAT_OUTPUT=$(qstat -u "$USER_NAME" 2>/dev/null || true)
if printf '%s\n' "$QSTAT_OUTPUT" | awk 'NR > 2 && $2 == "M2RMBISECT1" {found=1} END {exit !found}'; then
  echo "HALT: An M2RMBISECT1 job is already present in scheduler state." >&2
  exit 1
fi

# 8. Create atomic submission-attempt lock BEFORE qsub
mkdir -p "$(dirname "$LOCK_FILE")"
if ! (set -o noclobber; printf '%s\n' "submission_attempt_started prep=$PREP_SHA head=$HEAD_SHA" > "$LOCK_FILE") 2>/dev/null; then
  echo "HALT: Submission lock file exists ($LOCK_FILE). Job has already been submitted or submission attempt started." >&2
  exit 1
fi

# Single Guarded Scheduler Invocation
echo "INFO: Submitting M2RMBISECT1..."
EVIDENCE_ROOT="$(pwd)/runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/evidence"
PACKAGE_DIR="$(pwd)/$PKG_DIR"

JOB_ID=$(qsub -v F40_PACKAGE_DIR="$PACKAGE_DIR",F40_EVIDENCE_ROOT="$EVIDENCE_ROOT",F40_GUARDED_WRAPPER_INVOKED=1 "$PACKAGE_DIR/M2RMBISECT1.pbs")

if [ -z "$JOB_ID" ]; then
  echo "ERROR: qsub returned empty Job ID." >&2
  exit 1
fi

echo "SUCCESS: Submitted M2RMBISECT1 with Job ID: $JOB_ID"
echo "$JOB_ID" > "runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/LAST_JOB_ID.txt"

if ! qstat "$JOB_ID" >/dev/null 2>&1; then
  echo "ERROR: Immediate qstat verification failed for Job ID: $JOB_ID" >&2
  exit 1
fi
