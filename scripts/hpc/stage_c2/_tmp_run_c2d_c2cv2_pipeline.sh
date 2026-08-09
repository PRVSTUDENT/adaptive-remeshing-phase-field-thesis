#!/bin/bash
# Login-node pipeline: C2D requalify + C2C v1 review + C2C-v2 + optional C2E/F submit.
set -euo pipefail
PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
cd "${PROJECT_HOME}"
git pull --ff-only origin main
git rev-parse HEAD

echo "=== C2C v1 efficiency review ==="
python3 scripts/hpc/stage_c2/write_c2c_v1_efficiency_review.py | tee runs/hpc/stage_c2/recovery/c2c_v1_efficiency_stdout.log

echo "=== C2D postprocess-only requalification ==="
bash scripts/hpc/stage_c2/requalify_c2d_postprocess.sh

echo "=== C2C-v2 offline remesh+rebuild+validate ==="
bash scripts/hpc/stage_c2/build_and_validate_c2c_v2.sh

echo "=== markers ==="
ls -la runs/hpc/stage_c2/chain_state/
test -f runs/hpc/stage_c2/chain_state/C2D.ok
test -f runs/hpc/stage_c2/chain_state/C2C_V2.ok

echo "=== submit C2E-v2 / C2F-v2 ==="
# Need clean tree — if only untracked generated decks, ok; tracked changes block submit
if [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "WARNING: tracked changes present; submit will fail until commit" >&2
  git status --short --untracked-files=no
  exit 0
fi
bash scripts/hpc/stage_c2/submit_c2e_c2f_v2.sh
echo "PIPELINE_DONE"
