#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

P_SHA="${1:-519186771adf848a91971c612c7c0fc67f6dc592}"
WORKTREE_DIR="/tmp/f43rem4_real_kernel_probe_worktree"

echo "=== STARTING REAL ABAQUS 2023 KERNEL PROBE ON HPC AT P_SHA=${P_SHA} ==="

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

module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Executing real Abaqus 2023 kernel probe inside detached worktree..."
abaqus cae noGUI=scripts/validation/run_real_abaqus_f43rem4_probes.py -- "${WORKTREE_DIR}"

echo "=== REAL ABAQUS 2023 KERNEL PROBE SUCCESSFUL ==="
cd "${PROJECT_ROOT}"
git worktree remove --force "${WORKTREE_DIR}" || true
