#!/bin/bash
set -euo pipefail

PREP_SHA="${1:-$(git rev-parse HEAD)}"
PROJECT_ROOT="$(pwd)"
WORKTREE_DIR="${PROJECT_ROOT}/models/generated/mode_ii/f43_stage_c_bridge/detached_qual_worktree"

echo "== Stage F43REM2-R5 Detached Clean-Linux Qualification =="
echo "Preparation SHA: ${PREP_SHA}"

if [ -d "${WORKTREE_DIR}" ]; then
    git worktree remove --force "${WORKTREE_DIR}" 2>/dev/null || rm -rf "${WORKTREE_DIR}"
fi

git worktree add --detach "${WORKTREE_DIR}" "${PREP_SHA}"

cleanup() {
    echo "Cleaning up detached worktree..."
    cd "${PROJECT_ROOT}"
    git worktree remove --force "${WORKTREE_DIR}" 2>/dev/null || rm -rf "${WORKTREE_DIR}"
}
trap cleanup EXIT

cd "${WORKTREE_DIR}"
git config core.autocrlf false
git checkout HEAD

echo "Step 1: Running full unit test discovery in detached worktree..."
python3 -m unittest discover -s tests/unit -p "test_*.py"

echo "Step 2: Running static validator in detached worktree..."
python3 models/generated/mode_ii/f43_stage_c_bridge/validate_f43rem2_native.py models/generated/mode_ii/f43_stage_c_bridge/

echo "Step 3: Verifying git status and diff cleanliness in detached worktree..."
git status --porcelain=v1
git diff --exit-code
git diff --cached --exit-code

echo "F43REM2_R5_DETACHED_QUALIFICATION_SUCCESS"
exit 0
