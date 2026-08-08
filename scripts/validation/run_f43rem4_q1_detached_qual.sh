#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

P_SHA="${1:-700fb4f7b6def50fadd8b075d8d4c492cea380dd}"
WORKTREE_DIR="/tmp/f43rem4_q1_detached_qual_worktree"

echo "=== STARTING F43REM4-Q1 DETACHED QUALIFICATION AT P_SHA=${P_SHA} ==="

rm -rf "${WORKTREE_DIR}"
cd "${PROJECT_ROOT}"
git worktree prune
git worktree add --detach "${WORKTREE_DIR}" "${P_SHA}"

cd "${WORKTREE_DIR}"
HEAD_SHA="$(git rev-parse HEAD)"
echo "Detached HEAD SHA: ${HEAD_SHA}"

if [ "${HEAD_SHA}" != "${P_SHA}" ]; then
  echo "FATAL: Detached HEAD (${HEAD_SHA}) does not match expected P SHA (${P_SHA})"
  exit 1
fi

echo "--- Running Unit Test Discovery ---"
python3 -m unittest discover -s tests/unit -p 'test_*.py'

echo "--- Running Batch Rule Probes ---"
python3 scripts/validation/probe_f43rem4_batch_rules.py --out-dir /tmp

# Clean transient test artifacts created by test suites in execution directory
rm -f CAE_PHASE_DIAGNOSTIC_MATRIX.json

echo "--- Checking Post-Test Worktree Cleanliness ---"
STATUS="$(git status --porcelain=v1)"
if [ -n "${STATUS}" ]; then
  echo "FATAL: Post-test worktree dirty:"
  echo "${STATUS}"
  exit 1
fi

echo "F43REM4_Q1_DETACHED_QUALIFICATION_SUCCESS"
cd "${PROJECT_ROOT}"
git worktree remove --force "${WORKTREE_DIR}" || true
echo "=== DETACHED QUALIFICATION COMPLETE ==="
