#!/bin/bash
set -euo pipefail

ROOT_DIR="/home/pr21vyci/projects/adaptive-remeshing"
WORKTREE_DIR="/home/pr21vyci/projects/qual_worktree_p8_final2"

cd "$ROOT_DIR"
git fetch origin --tags

# Remove previous worktree if exists
if [ -d "$WORKTREE_DIR" ]; then
    git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || rm -rf "$WORKTREE_DIR"
fi

# 1. Create fresh isolated worktree at P43MODEREF8-FINAL2
git worktree add --detach "$WORKTREE_DIR" P43MODEREF8-FINAL2

cd "$WORKTREE_DIR"

echo "=== Step 1: Worktree Verification ==="
HEAD_SHA=$(git rev-parse HEAD)
echo "Worktree HEAD SHA: $HEAD_SHA"

echo "=== Step 2: Pre-test Cleanliness Check ==="
PRE_STAT=$(git status --porcelain=v1)
echo "Pre-test status length: ${#PRE_STAT}"
if [ -n "$PRE_STAT" ]; then
    echo "ERROR: Pre-test worktree status is not empty!"
    exit 1
fi

module purge 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "=== Host Environment ==="
hostname
whoami
gcc --version | head -n 1
ifort -V 2>&1 | head -n 1 || true
python3 --version

echo "=== Step 3: Authoritative Full Unit Suite ==="
python3 -m unittest discover -s tests/unit -p 'test_*.py'

echo "=== Step 4: Focused Qualification ==="
python3 scripts/validation/validate_nphys_producer_consumer_contract.py

bash -n models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/submit_m2ref_h0_nphysfix_repro.sh
bash -n models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/M2REF_H0_NPHYSFIX_REPRO.pbs
bash -n models/generated/mode_ii/reference_convergence/M2REF_H1/submit_m2ref_h1.sh
bash -n models/generated/mode_ii/reference_convergence/M2REF_H1/M2REF_H1.pbs
bash -n models/generated/mode_ii/reference_convergence/M2REF_H2/submit_m2ref_h2.sh
bash -n models/generated/mode_ii/reference_convergence/M2REF_H2/M2REF_H2.pbs

echo "=== Step 5: True Natural Cleanliness Check ==="
POST_STAT=$(git status --porcelain=v1)
git diff --exit-code
DIFF_RC=$?
git diff --cached --exit-code
CACHED_RC=$?

echo "Post-test status length: ${#POST_STAT}"
echo "git diff exit code: $DIFF_RC"
echo "git diff --cached exit code: $CACHED_RC"

# Clean up worktree
cd "$ROOT_DIR"
git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || rm -rf "$WORKTREE_DIR"

if [ -z "$POST_STAT" ] && [ $DIFF_RC -eq 0 ] && [ $CACHED_RC -eq 0 ]; then
    echo "=== QUALIFICATION PASSED 100% ==="
    exit 0
else
    echo "=== QUALIFICATION FAILED ==="
    exit 1
fi
