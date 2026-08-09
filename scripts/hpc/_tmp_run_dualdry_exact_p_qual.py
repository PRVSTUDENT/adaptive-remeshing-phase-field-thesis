#!/usr/bin/env python3
"""
Detached Exact-P Qualification Runner for P43DUALDRY1 on tu_freiberg
"""

import subprocess
import sys

target_sha = "2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6"





remote_script = f"""
set -euo pipefail

echo "=== Fast-forwarding main repo on cluster ==="
cd /home/pr21vyci/projects/adaptive-remeshing
git fetch origin main
rm -f models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/runtime_*/*.inp
git merge --ff-only origin/main



WORKTREE_DIR=$(mktemp -d /tmp/f43dualdry_qual_XXXXXX)
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
bash -n models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/dry_test_mm/F43DRY_MM.pbs
bash -n models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/dry_test_mm/submit_f43dry_mm.sh
bash -n models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/dry_test_pk5/F43DRY_PK5.pbs
bash -n models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/dry_test_pk5/submit_f43dry_pk5.sh

echo "=== Dry Package Contract Validation ==="
python3 scripts/validation/validate_f43_dualdry_contract.py

echo "=== Focused Dual Dry and Rebuild Unit Tests ==="
python3 -m unittest discover -s tests/unit -p 'test_f43_dualdry_contract.py'
python3 -m unittest discover -s tests/unit -p 'test_f43_dual_candidate_rebuild.py'
python3 -m unittest discover -s tests/unit -p 'test_f43rem4_gate_c1_resolution_coverage.py'
python3 -m unittest discover -s tests/unit -p 'test_f43rem4_gate_c1_localization.py'
python3 -m unittest discover -s tests/unit -p 'test_stage_f42_mixed_uel.py'


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
