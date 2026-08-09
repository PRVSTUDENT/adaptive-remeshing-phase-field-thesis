#!/usr/bin/env python3
import subprocess
import sys

target_sha = "ee33659ed675f71485ef9162048f65c2f0ab8727"

remote_script = f"""
set -e
cd /home/pr21vyci/projects/adaptive-remeshing
git checkout -- models/generated/mode_ii/f43_stage_c_bridge/F43REM2_NATIVE_VALIDATION_STATUS.json 2>/dev/null || true
git fetch origin main
git merge --ff-only origin/main

REMOTE_HEAD=$(git rev-parse HEAD)
echo "REMOTE_HEAD_SHA=$REMOTE_HEAD"

if [ "$REMOTE_HEAD" != "{target_sha}" ]; then
    echo "ERROR: Remote HEAD SHA $REMOTE_HEAD does not match expected preparation target {target_sha}"
    exit 1
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== STEP 6: REAL ABAQUS 2023 PREFLIGHTS AT EXACT FINAL2 P ==="

export PBS_O_WORKDIR=/home/pr21vyci/projects/adaptive-remeshing
export F43REM4_PREFLIGHT_ONLY=1

# PK1 PREFLIGHT
echo "--- Running PK1 Preflight ---"
bash models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43REM4_PK1.pbs || PK1_RC=$?
PK1_RC=${{PK1_RC:-0}}
echo "PK1_PREFLIGHT_RC=$PK1_RC"

# PK5 PREFLIGHT
echo "--- Running PK5 Preflight ---"
bash models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43REM4_PK5.pbs || PK5_RC=$?
PK5_RC=${{PK5_RC:-0}}
echo "PK5_PREFLIGHT_RC=$PK5_RC"

# MM PREFLIGHT
echo "--- Running MM Preflight ---"
bash models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43REM4_MM.pbs || MM_RC=$?
MM_RC=${{MM_RC:-0}}
echo "MM_PREFLIGHT_RC=$MM_RC"

echo "=== STEP 7: MANDATORY COMPLETE DETACHED UNIT SUITE ==="

WORKTREE_DIR=$(mktemp -d /tmp/f43rem4_final2_qual_XXXXXX)
echo "WORKTREE_DIR=$WORKTREE_DIR"

git worktree add --detach "$WORKTREE_DIR" "{target_sha}"
cd "$WORKTREE_DIR"

DETACHED_HEAD=$(git rev-parse HEAD)
echo "DETACHED_HEAD=$DETACHED_HEAD"

module load gcc/11.4.0 python/gcc/11.4.0/3.11.7 intel/2024.2.0 abaqus/2023
export PYTHONPATH=.

set +e
python3 -m unittest discover -s tests/unit -p 'test_*.py' > /tmp/full_unittest_discovery.log 2>&1
FULL_SUITE_RC=$?
set -e

echo "FULL_SUITE_RC=$FULL_SUITE_RC"
echo "--- Full Unittest Discovery Output Tail ---"
tail -n 25 /tmp/full_unittest_discovery.log

echo "=== STEP 9: NATURAL CLEANLINESS CHECK ==="
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

echo "=== PREFLIGHT & QUALIFICATION COMPLETE ==="
"""

p = subprocess.run(["ssh", "-F", r"C:\Users\pruth\.ssh\codex_config", "tu_freiberg", remote_script], capture_output=True, text=True)
print("STDOUT:")
print(p.stdout)
print("STDERR:")
print(p.stderr)
sys.exit(p.returncode)
