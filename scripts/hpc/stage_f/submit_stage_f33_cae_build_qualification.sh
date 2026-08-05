#!/bin/bash
# Guarded orchestrator for Stage F33 M2RMBUILD8 qualification submission.
# Strict activation and authorization gates; 1 qsub call maximum; no retries.
set -Eeuo pipefail

PREP_SHA="${F33_PREPARATION_SHA:?F33_PREPARATION_SHA must be explicitly bound after package review}"

echo "=== Stage F33 M2RMBUILD8 Qualification Orchestrator ==="

# 1. Activation Gate
if [ "${F33_ALLOW_SUBMISSION:-false}" != "true" ]; then
  echo "HALT: Activation gate F33_ALLOW_SUBMISSION is not 'true'. Refusing submission."
  exit 0
fi

# 2. Authorization Gate
if [ "${F33_AUTHORIZE_M2RMBUILD8:-false}" != "true" ]; then
  echo "HALT: Authorization gate F33_AUTHORIZE_M2RMBUILD8 is not 'true'. Refusing submission."
  exit 0
fi

# 3. Head descendant check
HEAD_SHA=$(git rev-parse HEAD)
if ! git merge-base --is-ancestor "$PREP_SHA" "$HEAD_SHA"; then
  echo "ERROR: HEAD ($HEAD_SHA) is not a descendant of preparation revision ($PREP_SHA)."
  exit 1
fi

# 4. Blob identity check using repository-relative pathspecs
PKG_DIR="models/generated/mode_ii/f33_cae_runtime_gate_repair"
PREP_BLOBS=$(git ls-tree -r "$PREP_SHA" -- "$PKG_DIR" | awk '{print $3, $4}' | sort)
HEAD_BLOBS=$(git ls-tree -r "$HEAD_SHA" -- "$PKG_DIR" | awk '{print $3, $4}' | sort)

if [ -z "$PREP_BLOBS" ] || [ -z "$HEAD_BLOBS" ]; then
  echo "ERROR: Package blob list is empty."
  exit 1
fi

if [ "$PREP_BLOBS" != "$HEAD_BLOBS" ]; then
  echo "ERROR: Package blob mismatch between preparation SHA ($PREP_SHA) and HEAD ($HEAD_SHA)."
  exit 1
fi

# 5. Lock file check
LOCK_FILE="runs/hpc/stage_f/f33_m2rmbuild8_static_gate/M2RMBUILD8_SUBMITTED.lock"
if [ -f "$LOCK_FILE" ]; then
  echo "HALT: Submission lock file exists ($LOCK_FILE). Job has already been submitted."
  exit 0
fi

# 6. Maximum Submission Audit
if [ "${MAX_SUBMISSIONS:-1}" -ne 1 ]; then
  echo "ERROR: Only 1 submission maximum authorized."
  exit 1
fi

# Single Guarded qsub Call
echo "INFO: Submitting M2RMBUILD8..."
EVIDENCE_DIR="$(pwd)/runs/hpc/stage_f/f33_m2rmbuild8_static_gate/evidence"
PACKAGE_DIR="$(pwd)/$PKG_DIR"

JOB_ID=$(qsub -v F33_PACKAGE_DIR="$PACKAGE_DIR",F33_EVIDENCE_DIR="$EVIDENCE_DIR" "$PACKAGE_DIR/M2RMBUILD8.pbs")

echo "SUCCESS: Submitted M2RMBUILD8 with Job ID: $JOB_ID"
touch "$LOCK_FILE"
echo "$JOB_ID" > "runs/hpc/stage_f/f33_m2rmbuild8_static_gate/LAST_JOB_ID.txt"
