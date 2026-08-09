#!/usr/bin/env python3
import subprocess
import json
import os
import sys

target_sha = "60fd58aa63aada7a73ccf29edb5fca2c619bb93d"
target_tag = "P43REM4-BATCH4"

remote_preflight_script = f"""
set -e
cd /home/pr21vyci/projects/adaptive-remeshing
git fetch origin main
git merge --ff-only origin/main
REMOTE_HEAD_SHA=$(git rev-parse HEAD)
echo "REMOTE_HEAD_SHA=$REMOTE_HEAD_SHA"

if [ "$REMOTE_HEAD_SHA" != "{target_sha}" ]; then
    echo "ERROR: Remote SHA mismatch! Expected {target_sha}, got $REMOTE_HEAD_SHA"
    exit 1
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

cd /home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch
export F43REM4_PREFLIGHT_ONLY=1
export PBS_O_WORKDIR="/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch"

echo "=== RUNNING TRACKED PBS PREFLIGHT: F43REM4_PK1.pbs ==="
bash F43REM4_PK1.pbs

echo "=== RUNNING TRACKED PBS PREFLIGHT: F43REM4_PK5.pbs ==="
bash F43REM4_PK5.pbs

echo "=== RUNNING TRACKED PBS PREFLIGHT: F43REM4_MM.pbs ==="
bash F43REM4_MM.pbs

echo "=== AUDITING PREFLIGHT RESULTS AND SINGLE-RULE CONTRACT ==="
cat runtime_pk1/*PREFLIGHT_STATUS.json
echo ""
cat runtime_pk1/F43REM4_ACTIVE_RULE_AUDIT.json
echo ""
cat runtime_pk5/*PREFLIGHT_STATUS.json
echo ""
cat runtime_pk5/F43REM4_ACTIVE_RULE_AUDIT.json
echo ""
cat runtime_mm/*PREFLIGHT_STATUS.json
echo ""
cat runtime_mm/F43REM4_ACTIVE_RULE_AUDIT.json
"""

print("--- Step 1: Executing SSH Preflights on tu_freiberg ---")
p = subprocess.run(["ssh", "-F", r"C:\Users\pruth\.ssh\codex_config", "tu_freiberg", remote_preflight_script], capture_output=True, text=True)
print("PREFLIGHT STDOUT:")
print(p.stdout)
print("PREFLIGHT STDERR:")
print(p.stderr)

if p.returncode != 0:
    print(f"Preflights failed with exit code {p.returncode}")
    sys.exit(p.returncode)

print("\n--- Step 2: Executing Fresh Detached Linux-Git Qualification ---")
remote_qual_script = f"""
set -e
cd /home/pr21vyci/projects/adaptive-remeshing

WORKTREE_DIR=$(mktemp -d /tmp/f43rem4_qual_XXXXXX)
echo "WORKTREE_DIR=$WORKTREE_DIR"

git worktree add --detach "$WORKTREE_DIR" "{target_sha}"
cd "$WORKTREE_DIR"

DETACHED_HEAD=$(git rev-parse HEAD)
echo "DETACHED_HEAD=$DETACHED_HEAD"

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== RUNNING UNIT TEST SUITE IN DETACHED WORKTREE ==="
export PYTHONPATH=.
python3 -m unittest discover -s tests/unit -p 'test_f43rem4_*.py' > /tmp/f43rem4_unittest.log 2>&1 || QUAL_RC1=$?
python3 -m unittest discover -s tests/unit -p 'test_f43pre3_*.py' >> /tmp/f43rem4_unittest.log 2>&1 || QUAL_RC2=$?
python3 -m unittest discover -s tests/unit -p 'test_fake_qsub_*.py' >> /tmp/f43rem4_unittest.log 2>&1 || QUAL_RC3=$?
QUAL_RC1=${{QUAL_RC1:-0}}
QUAL_RC2=${{QUAL_RC2:-0}}
QUAL_RC3=${{QUAL_RC3:-0}}
QUAL_RC=$((QUAL_RC1 + QUAL_RC2 + QUAL_RC3))
echo "QUAL_TEST_RC=$QUAL_RC"
cat /tmp/f43rem4_unittest.log | tail -n 35

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
    echo "ERROR: Qualification failed! QUAL_RC=$QUAL_RC, PORCELAIN_LEN=$PORCELAIN_STATUS_LEN, DIFF_RC=$DIFF_RC, CACHED_DIFF_RC=$CACHED_DIFF_RC"
    exit 1
fi

echo "QUALIFICATION_SUCCESS=true"
"""

p_qual = subprocess.run(["ssh", "-F", r"C:\Users\pruth\.ssh\codex_config", "tu_freiberg", remote_qual_script], capture_output=True, text=True)
print("QUALIFICATION STDOUT:")
print(p_qual.stdout)
print("QUALIFICATION STDERR:")
print(p_qual.stderr)
sys.exit(p_qual.returncode)
