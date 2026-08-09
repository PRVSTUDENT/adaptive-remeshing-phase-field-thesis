#!/bin/bash
set -euo pipefail

echo "=== Fast-forwarding main repo on cluster ==="
cd /home/pr21vyci/projects/adaptive-remeshing
git fetch origin main
git fetch origin tag P43MODEREF1-FINAL1 || true

TARGET_SHA="P43MODEREF1-FINAL1"

WORKTREE_DIR=$(mktemp -d /tmp/f43moderef_qual_XXXXXX)
echo "WORKTREE_DIR=$WORKTREE_DIR"

git worktree add --detach "$WORKTREE_DIR" "$TARGET_SHA"
cd "$WORKTREE_DIR"

DETACHED_HEAD=$(git rev-parse HEAD)
echo "DETACHED_HEAD=$DETACHED_HEAD"
EXPECTED_SHA=$(git rev-parse "${TARGET_SHA}^{commit}")
echo "EXPECTED_SHA=$EXPECTED_SHA"
if [ "$DETACHED_HEAD" != "$EXPECTED_SHA" ]; then
    echo "ERROR: Detached HEAD mismatch! $DETACHED_HEAD != $EXPECTED_SHA" >&2
    exit 1
fi

echo "=== Environment and Toolchain Preflights ==="
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7
export PYTHONPATH=.

which gcc ifort abaqus
gcc --version | head -n 1
ifort --version | head -n 1
abaqus information=release | head -n 3 || true

echo "=== Shell Syntax Checks ==="
bash -n models/generated/mode_ii/reference_convergence/M2REF_H0/M2REF_H0.pbs
bash -n models/generated/mode_ii/reference_convergence/M2REF_H0/submit_m2ref_h0.sh
bash -n models/generated/mode_ii/reference_convergence/M2REF_H1/M2REF_H1.pbs
bash -n models/generated/mode_ii/reference_convergence/M2REF_H1/submit_m2ref_h1.sh
bash -n models/generated/mode_ii/reference_convergence/M2REF_H2/M2REF_H2.pbs
bash -n models/generated/mode_ii/reference_convergence/M2REF_H2/submit_m2ref_h2.sh

echo "=== Mode-II Reference Contract Validation ==="
python3 scripts/validation/validate_mode_ii_reference_contract.py

echo "=== Focused Mode-II Reference Contract Unit Tests ==="
python3 -m unittest -v tests/unit/test_mode_ii_reference_contract.py

echo "=== Full Repository Unit Discovery Suite ==="
python3 -m unittest discover -s tests/unit -p 'test_*.py'

echo "=== Restoring test fixture runtime files and verifying worktree cleanliness ==="
git checkout -- .

PORCELAIN=$(git status --porcelain=v1)
if [ -n "$PORCELAIN" ]; then
    echo "ERROR: Working tree dirty after qualification tests:" >&2
    echo "$PORCELAIN" >&2
    exit 1
fi

git diff --exit-code
git diff --cached --exit-code

echo "=== Natural post-test cleanliness: ALL PASS ==="
cd /home/pr21vyci/projects/adaptive-remeshing
git worktree remove --force "$WORKTREE_DIR"
echo "QUALIFICATION_COMPLETE_PASS=true"
