#!/usr/bin/env python3
import subprocess
import sys

target_sha = "60fd58aa63aada7a73ccf29edb5fca2c619bb93d"

remote_script = f"""
set -e
cd /home/pr21vyci/projects/adaptive-remeshing
git fetch origin main
git merge --ff-only origin/main

WORKTREE_DIR=$(mktemp -d /tmp/f43rem4_fullqual_XXXXXX)
echo "WORKTREE_DIR=$WORKTREE_DIR"

git worktree add --detach "$WORKTREE_DIR" "{target_sha}"
cd "$WORKTREE_DIR"

DETACHED_HEAD=$(git rev-parse HEAD)
echo "DETACHED_HEAD=$DETACHED_HEAD"

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
export PYTHONPATH=.

echo "=== RUNNING FULL PROJECT UNIT SUITE IN DETACHED WORKTREE ==="
python3 -m unittest discover -s tests/unit -p 'test_*.py' > /tmp/f43rem4_full_unittest.log 2>&1 || QUAL_RC=$?
QUAL_RC=${{QUAL_RC:-0}}
echo "QUAL_TEST_RC=$QUAL_RC"

cat /tmp/f43rem4_full_unittest.log | tail -n 40

PORCELAIN_STATUS=$(git status --porcelain=v1)
PORCELAIN_STATUS_LEN=${{#PORCELAIN_STATUS}}
echo "PORCELAIN_STATUS_LEN=$PORCELAIN_STATUS_LEN"

git diff --exit-code || DIFF_RC=$?
DIFF_RC=${{DIFF_RC:-0}}
echo "DIFF_RC=$DIFF_RC"

git diff --cached --exit-code || CACHED_DIFF_RC=$?
CACHED_DIFF_RC=${{CACHED_DIFF_RC:-0}}
echo "CACHED_DIFF_RC=$CACHED_DIFF_RC"

cd /home/pr21vyci/projects/adaptive-remeshing
git worktree remove --force "$WORKTREE_DIR"

if [ "$QUAL_RC" -ne 0 ] || [ "$PORCELAIN_STATUS_LEN" -ne 0 ] || [ "$DIFF_RC" -ne 0 ] || [ "$CACHED_DIFF_RC" -ne 0 ]; then
    echo "ERROR: Full qualification failed! QUAL_RC=$QUAL_RC, PORCELAIN_LEN=$PORCELAIN_STATUS_LEN, DIFF_RC=$DIFF_RC, CACHED_DIFF_RC=$CACHED_DIFF_RC"
    exit 1
fi

echo "FULL_QUALIFICATION_SUCCESS=true"
"""

p = subprocess.run(["ssh", "-F", r"C:\Users\pruth\.ssh\codex_config", "tu_freiberg", remote_script], capture_output=True, text=True)
print("STDOUT:")
print(p.stdout)
print("STDERR:")
print(p.stderr)
sys.exit(p.returncode)
