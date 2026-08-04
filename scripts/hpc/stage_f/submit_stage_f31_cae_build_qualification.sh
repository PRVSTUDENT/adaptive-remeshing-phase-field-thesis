#!/bin/bash
# Guarded orchestrator for Stage F31 M2RMBUILD6 qualification submission.
# Strict activation and authorization gates; 1 qsub call maximum; no retries.
set -Eeuo pipefail

PREP_SHA="${F31_PREPARATION_SHA:-f084e8d0adaf049f8e3bb3f2fc223bf3d50ce603}"

echo "=== Stage F31 M2RMBUILD6 Qualification Orchestrator ==="

# 1. Activation Gate
if [ "${F31_ALLOW_SUBMISSION:-false}" != "true" ]; then
  echo "HALT: Activation gate F31_ALLOW_SUBMISSION is not 'true'. Refusing submission."
  exit 0
fi

# 2. Authorization Gate
if [ "${F31_AUTHORIZE_M2RMBUILD6:-false}" != "true" ]; then
  echo "HALT: Authorization gate F31_AUTHORIZE_M2RMBUILD6 is not 'true'. Refusing submission."
  exit 0
fi

# 3. Head descendant check
HEAD_SHA=$(git rev-parse HEAD)
if ! git merge-base --is-ancestor "$PREP_SHA" "$HEAD_SHA"; then
  echo "ERROR: HEAD ($HEAD_SHA) is not a descendant of preparation revision ($PREP_SHA)."
  exit 1
fi

# 4. Blob identity check using repository-relative pathspecs
PKG_DIR="models/generated/mode_ii/f31_cae_runtime_gate_repair"
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
LOCK_FILE="runs/hpc/stage_f/f31_m2rmbuild6_static_gate/M2RMBUILD6_SUBMITTED.lock"
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
echo "INFO: Submitting M2RMBUILD6..."
EVIDENCE_DIR="$(pwd)/runs/hpc/stage_f/f31_m2rmbuild6_static_gate/evidence"
PACKAGE_DIR="$(pwd)/$PKG_DIR"

JOB_ID=$(qsub -v F31_PACKAGE_DIR="$PACKAGE_DIR",F31_EVIDENCE_DIR="$EVIDENCE_DIR" "$PACKAGE_DIR/M2RMBUILD6.pbs")

echo "SUCCESS: Submitted M2RMBUILD6 with Job ID: $JOB_ID"
touch "$LOCK_FILE"
echo "$JOB_ID" > "runs/hpc/stage_f/f31_m2rmbuild6_static_gate/LAST_JOB_ID.txt"
