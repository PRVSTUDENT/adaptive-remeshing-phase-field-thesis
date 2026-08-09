#!/usr/bin/env python3
"""
Detached Exact-P Qualification Runner for P43MODEREF1 on tu_freiberg
Task: F43MODEREF-PREP1
"""

import subprocess
import sys

target_sha = "cf082a32dfa85d114acfe9702731a7a16e457eb8"

remote_script = f"""
set -euo pipefail

echo "=== Fast-forwarding main repo on cluster ==="
cd /home/pr21vyci/projects/adaptive-remeshing
git fetch origin --tags
git merge --ff-only origin/main

WORKTREE_DIR=$(mktemp -d /tmp/f43moderef_qual_XXXXXX)
echo "WORKTREE_DIR=$WORKTREE_DIR"

git worktree add --detach "$WORKTREE_DIR" "{target_sha}"
cd "$WORKTREE_DIR"

DETACHED_HEAD=$(git rev-parse HEAD)
echo "DETACHED_HEAD=$DETACHED_HEAD"
if [ "$DETACHED_HEAD" != "{target_sha}" ]; then
    echo "ERROR: Detached HEAD mismatch! $DETACHED_HEAD != {target_sha}" >&2
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
"""

p = subprocess.run(["ssh", "-F", r"C:\Users\pruth\.ssh\codex_config", "tu_freiberg", remote_script], capture_output=True, text=True)
print("STDOUT:")
print(p.stdout)
print("STDERR:")
print(p.stderr)
sys.exit(p.returncode)
