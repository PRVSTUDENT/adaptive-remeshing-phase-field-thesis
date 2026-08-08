#!/bin/bash
# Linux-Git detached worktree qualification script for P43PRE3-R2
set -euo pipefail

TARGET_P="${1:-P43PRE3-R2}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

WORKTREE_DIR="/tmp/f43pre3_r2_qual_worktree"
SCRATCH_DIR="/tmp/f43pre3_r2_qual_scratch"

echo "=== F43PRE3-R2 DETACHED QUALIFICATION STARTING ==="
echo "Target P: ${TARGET_P}"

rm -rf "${WORKTREE_DIR}" "${SCRATCH_DIR}"
mkdir -p "${SCRATCH_DIR}"

git -C "${REPO_ROOT}" worktree add --detach "${WORKTREE_DIR}" "${TARGET_P}"
git -C "${WORKTREE_DIR}" config core.autocrlf false

DETACHED_HEAD=$(git -C "${WORKTREE_DIR}" rev-parse HEAD)
echo "Detached HEAD: ${DETACHED_HEAD}"

# Resolve target SHA if branch/tag passed
TARGET_FULL_SHA=$(git -C "${REPO_ROOT}" rev-parse "${TARGET_P}")

if [ "${DETACHED_HEAD}" != "${TARGET_FULL_SHA}" ]; then
    echo "FATAL: Detached HEAD mismatch! Target=${TARGET_FULL_SHA}, Actual=${DETACHED_HEAD}" >&2
    git -C "${REPO_ROOT}" worktree remove --force "${WORKTREE_DIR}"
    exit 1
fi

echo "Step 1: Running full unit test discovery in detached worktree..."
cd "${WORKTREE_DIR}"
export F38_DIAGNOSTIC_MATRIX="${SCRATCH_DIR}/CAE_PHASE_DIAGNOSTIC_MATRIX.json"
python3 -m unittest discover -s "${WORKTREE_DIR}/tests/unit" -p 'test_*.py'

echo "Step 2: Running static runtime validator in detached worktree..."
python3 "${WORKTREE_DIR}/models/generated/mode_ii/f43_stage_c_bridge/validate_f43pre3_geom_runtime.py" "${WORKTREE_DIR}/models/generated/mode_ii/f43_stage_c_bridge"

echo "Step 3: Running semantic equivalence validator in detached worktree..."
python3 "${WORKTREE_DIR}/scripts/validation/validate_f43pre3_semantic_equivalence.py" "${WORKTREE_DIR}/models/generated/mode_ii/f43_stage_c_bridge/F43PRE2_GEOM.inp" "${WORKTREE_DIR}/models/generated/mode_ii/f43_stage_c_bridge/F43PRE3_GEOM.inp"

echo "Step 4: Verifying git status and diff cleanliness in detached worktree..."
STATUS_OUT=$(git -C "${WORKTREE_DIR}" status --porcelain=v1)
if [ -n "${STATUS_OUT}" ]; then
    echo "FATAL: Worktree is dirty after tests!" >&2
    echo "${STATUS_OUT}"
    git -C "${REPO_ROOT}" worktree remove --force "${WORKTREE_DIR}"
    exit 1
fi

git -C "${WORKTREE_DIR}" diff --exit-code
git -C "${WORKTREE_DIR}" diff --cached --exit-code

echo "F43PRE3_R2_DETACHED_QUALIFICATION_SUCCESS"
echo "Cleaning up detached worktree..."
git -C "${REPO_ROOT}" worktree remove --force "${WORKTREE_DIR}"
rm -rf "${SCRATCH_DIR}"
