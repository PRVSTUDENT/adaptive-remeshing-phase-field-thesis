#!/bin/bash
set -euo pipefail

cd /home/pr21vyci/projects/adaptive-remeshing

WORKTREE_DIR=$(mktemp -d /tmp/f43moderef_vcheck_XXXXXX)
git worktree add --detach "$WORKTREE_DIR" HEAD
cd "$WORKTREE_DIR"

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7
export PYTHONPATH=.

python3 -m unittest discover -v -s tests/unit -p 'test_*.py' 2>&1 | grep -C 5 -E "(FAIL|ERROR):" || true

cd /home/pr21vyci/projects/adaptive-remeshing
git worktree remove --force "$WORKTREE_DIR"
