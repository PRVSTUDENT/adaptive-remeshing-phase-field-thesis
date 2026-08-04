#!/bin/bash
# Guarded orchestrator for Stage F30 M2RMBUILD5 CAE build qualification
# Strict activation and authorization gates; 1 qsub call maximum; no retries.
set -Eeuo pipefail

PREP_SHA="${F30_PREPARATION_SHA:-96872b416723899d2b065676ffb4e124915446db}"

echo "=== Stage F30 M2RMBUILD5 Qualification Orchestrator ==="

# 1. Activation Gate
if [ "${F30_ACTIVATE_SUBMISSION:-false}" != "true" ]; then
  echo "INFO: F30_ACTIVATE_SUBMISSION is false. Running read-only preflight."
  READ_ONLY=true
else
  READ_ONLY=false
fi

# 2. Authorization Gate
if [ "${F30_EXPLICIT_AUTHORIZATION:-false}" != "true" ]; then
  echo "INFO: F30_EXPLICIT_AUTHORIZATION is false. Submission disabled."
  SUBMISSION_PERMITTED=false
else
  SUBMISSION_PERMITTED=true
fi

# 3. Repository and Relative Path Validation
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
if [ -z "$REPO_ROOT" ]; then
  echo "ERROR: Not inside a git repository"
  exit 1
fi

PACKAGE_REL_PATH="models/generated/mode_ii/f30_cae_runtime_gate_repair"
PACKAGE_ABS_DIR="$REPO_ROOT/$PACKAGE_REL_PATH"

if [ ! -d "$PACKAGE_ABS_DIR" ]; then
  echo "ERROR: Package directory does not exist: $PACKAGE_ABS_DIR"
  exit 1
fi

# 4. Ancestry and Diff Check against P
if ! git merge-base --is-ancestor "$PREP_SHA" HEAD; then
  echo "ERROR: PREP_SHA $PREP_SHA is not an ancestor of HEAD"
  exit 1
fi

if ! git diff --quiet "$PREP_SHA" HEAD -- "$PACKAGE_REL_PATH"; then
  echo "ERROR: Tracked package path $PACKAGE_REL_PATH has uncommitted changes relative to PREP_SHA $PREP_SHA"
  exit 1
fi

# 5. Repository-Relative Git Blob Comparison against P
prep_blobs=$(git ls-tree -r "$PREP_SHA" "$PACKAGE_REL_PATH" | awk '{print $3, $4}' | sort)
head_blobs=$(git ls-tree -r HEAD "$PACKAGE_REL_PATH" | awk '{print $3, $4}' | sort)

if [ -z "$prep_blobs" ]; then
  echo "ERROR: Preparation blob listing is empty for $PREP_SHA:$PACKAGE_REL_PATH"
  exit 1
fi

if [ -z "$head_blobs" ]; then
  echo "ERROR: HEAD blob listing is empty for HEAD:$PACKAGE_REL_PATH"
  exit 1
fi

if [ "$prep_blobs" != "$head_blobs" ]; then
  echo "ERROR: Package blob listing at HEAD does not match preparation SHA $PREP_SHA"
  exit 1
fi

# 6. Manifest Verification
if [ ! -f "$PACKAGE_ABS_DIR/PACKAGE_MANIFEST.json" ] || [ ! -f "$PACKAGE_ABS_DIR/SHA256SUMS" ]; then
  echo "ERROR: Package manifests missing in $PACKAGE_ABS_DIR"
  exit 1
fi

# 7. Check Submission Boundary
if [ "$READ_ONLY" = true ] || [ "$SUBMISSION_PERMITTED" = false ]; then
  echo "INFO: Preflight passed cleanly. Submission withheld."
  exit 0
fi

# 8. Single Authorized qsub Call Site
RUN_ID="F30_BUILD_$(date -u +%Y%m%d_%H%M%S)"
EVIDENCE_DIR="$REPO_ROOT/runs/hpc/stage_f/f30_cae_runtime_gate_repair/evidence/$RUN_ID"
mkdir -p "$EVIDENCE_DIR"

echo "INFO: Issuing single authorized qsub call for M2RMBUILD5..."
JOB_ID=$(qsub -v "F30_PACKAGE_DIR=$PACKAGE_ABS_DIR,F30_EVIDENCE_DIR=$EVIDENCE_DIR" "$PACKAGE_ABS_DIR/M2RMBUILD5.pbs")
echo "SUCCESS: Submitted job $JOB_ID for M2RMBUILD5"
