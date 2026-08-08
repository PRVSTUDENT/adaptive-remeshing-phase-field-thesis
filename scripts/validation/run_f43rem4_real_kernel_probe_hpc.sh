#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

P_SHA="${1:-9e095f56b6c1c3c44fa7f32cbca7e7d50a0b505a}"
WORKTREE_DIR="/tmp/f43rem4_real_kernel_probe_worktree"

echo "=== STARTING REAL ABAQUS 2023 KERNEL PROBE ON HPC AT P_SHA=${P_SHA} ==="

rm -rf "${WORKTREE_DIR}"
cd "${PROJECT_ROOT}"
git worktree prune
git worktree add --detach "${WORKTREE_DIR}" "${P_SHA}"

# Copy untracked pre-built source CAE file from main repository into detached worktree
if [ -f "${PROJECT_ROOT}/models/generated/mode_ii/f43_stage_c_bridge/ModeII_Geometry_Source_Abaqus2023.cae" ]; then
  cp "${PROJECT_ROOT}/models/generated/mode_ii/f43_stage_c_bridge/ModeII_Geometry_Source_Abaqus2023.cae" "${WORKTREE_DIR}/models/generated/mode_ii/f43_stage_c_bridge/"
fi

cd "${WORKTREE_DIR}"
HEAD_SHA="$(git rev-parse HEAD)"
echo "Detached HEAD SHA: ${HEAD_SHA}"

if [ "${HEAD_SHA}" != "${P_SHA}" ]; then
  echo "FATAL: Detached HEAD (${HEAD_SHA}) does not match expected P SHA (${P_SHA})"
  exit 1
fi

module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Executing real Abaqus 2023 kernel probe inside detached worktree..."
abaqus cae noGUI=scripts/validation/run_real_abaqus_f43rem4_probes.py -- "${WORKTREE_DIR}"

if [ -f "${WORKTREE_DIR}/models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43REM4_REAL_ABAQUS2023_PROBE_EVIDENCE.json" ]; then
  cp "${WORKTREE_DIR}/models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43REM4_REAL_ABAQUS2023_PROBE_EVIDENCE.json" \
     "${PROJECT_ROOT}/models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/"
fi

echo "=== REAL ABAQUS 2023 KERNEL PROBE SUCCESSFUL ==="
cd "${PROJECT_ROOT}"
git worktree remove --force "${WORKTREE_DIR}" || true
