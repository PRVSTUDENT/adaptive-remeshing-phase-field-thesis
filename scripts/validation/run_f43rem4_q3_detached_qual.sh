#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

TARGET_P="da46210cbf2e34f71a545c51b12e3f6351f5502c"
WORKTREE_DIR="/tmp/f43rem4_q3_detached_qual_worktree"

echo "=== STARTING F43REM4-Q3 DETACHED WORKTREE QUALIFICATION AT EXACT P=${TARGET_P} ==="

rm -rf "${WORKTREE_DIR}"
cd "${PROJECT_ROOT}"
git worktree prune
git worktree add --detach "${WORKTREE_DIR}" "${TARGET_P}"

cd "${WORKTREE_DIR}"
git config core.autocrlf false

HEAD_SHA="$(git rev-parse HEAD)"
echo "Detached HEAD SHA: ${HEAD_SHA}"

if [ "${HEAD_SHA}" != "${TARGET_P}" ]; then
  echo "FATAL: Detached HEAD (${HEAD_SHA}) does not match expected target P (${TARGET_P})"
  exit 1
fi

echo "Running full unit test suite in detached worktree..."
python3 -m unittest discover -s tests/unit -p 'test_*.py' 2>&1 | tee /tmp/f43rem4_unittest_run.log

STATUS_OUTPUT="$(git status --porcelain=v1)"
echo "Post-test git status --porcelain=v1:"
echo "${STATUS_OUTPUT}"

if [ -n "${STATUS_OUTPUT}" ]; then
  echo "FATAL: Post-test worktree is dirty!"
  git status
  exit 1
fi

echo "Post-test worktree is naturally clean!"
echo "=== F43REM4-Q3 DETACHED QUALIFICATION SUCCESSFUL ==="

cd "${PROJECT_ROOT}"
git worktree remove --force "${WORKTREE_DIR}" || true
