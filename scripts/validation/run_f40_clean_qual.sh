#!/bin/bash
set -euo pipefail

COMMIT_SHA="${1:-daea0e0134266ecaa70de68f14c19ab9348d91fe}"
QUAL_DIR="/tmp/f40_clean_qual_${COMMIT_SHA:0:7}"

git worktree prune || true
rm -rf "$QUAL_DIR"

echo "=== 1. Checking out commit $COMMIT_SHA to detached clean-Linux worktree $QUAL_DIR ==="
git -C '/mnt/d/Master thesis/Adaptive remeshing' worktree add --detach "$QUAL_DIR" "$COMMIT_SHA"
cd "$QUAL_DIR"

echo "=== 2. Running unit tests ==="
python3 -m unittest tests/unit/test_stage_f40_batch.py

echo "=== 3. Running static gate validator ==="
python3 scripts/validation/validate_f40_cae_bisect_gate.py

echo "=== 4. Checking PBS bash syntax ==="
bash -n models/generated/mode_ii/f40_f38_cae_invocation_model_building_bisect/M2RMBISECT1.pbs

echo "=== 5. Compiling Python runtime scripts ==="
python3 -m py_compile models/generated/mode_ii/f40_f38_cae_invocation_model_building_bisect/runtime/*.py

echo "=== 6. Verifying SHA256 package manifests ==="
(cd models/generated/mode_ii/f40_f38_cae_invocation_model_building_bisect && sha256sum -c SHA256SUMS && sha256sum -c F40_SHA256SUMS)

echo "=== 7. Scanning for prohibited operations and __file__ in runner ==="
! grep -rn "__file__" models/generated/mode_ii/f40_f38_cae_invocation_model_building_bisect/runtime/f40_cae_bisection_runner.py
for kw in "abaqus datacheck" "abaqus job" "submit()" "remesh" "state_transfer" "qsub "; do
    ! grep -rn "$kw" models/generated/mode_ii/f40_f38_cae_invocation_model_building_bisect/ --exclude="SHA256SUMS" --exclude="F40_SHA256SUMS" --exclude="PACKAGE_MANIFEST.json"
done

echo "=== Clean Linux Qualification PASSED for commit $COMMIT_SHA ==="
