#!/bin/bash
# Linux-Git detached worktree qualification script for P43REM3-R1 / Q43REM3-R1
set -euo pipefail

TARGET_P_SHA="${1:-P43REM3-R1}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=== F43REM3-R1 DETACHED WORKTREE QUALIFICATION ==="
echo "Target P SHA: ${TARGET_P_SHA}"

WORKTREE_DIR="$(mktemp -d /tmp/f43rem3_r1_qual_XXXXXX)"
cleanup() {
    echo "Cleaning up worktree ${WORKTREE_DIR}..."
    git -C "${REPO_ROOT}" worktree remove --force "${WORKTREE_DIR}" 2>/dev/null || true
    rm -rf "${WORKTREE_DIR}"
}
trap cleanup EXIT

git -C "${REPO_ROOT}" worktree add --detach "${WORKTREE_DIR}" "${TARGET_P_SHA}"

cd "${WORKTREE_DIR}"
git config core.autocrlf false

echo "Running full unit test suite at exact target P..."
python3 -m unittest discover -s tests/unit -p 'test_*.py'

echo "Running F43REM3 static package validator..."
python3 models/generated/mode_ii/f43_stage_c_bridge/validate_f43rem3_native.py models/generated/mode_ii/f43_stage_c_bridge

echo "Checking natural post-test worktree cleanliness..."
if [ -n "$(git status --porcelain=v1)" ]; then
    echo "FATAL ERROR: Worktree is dirty after tests!" >&2
    git status
    exit 1
fi

echo "=== F43REM3-R1 DETACHED QUALIFICATION SUCCESS ==="
