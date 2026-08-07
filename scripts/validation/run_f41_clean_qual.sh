#!/bin/bash
set -euo pipefail

PREP_SHA="${1:-$(git rev-parse HEAD)}"
PROJECT_ROOT="$(pwd)"
WORKTREE_DIR="${PROJECT_ROOT}/runs/hpc/stage_f/f41_crack_geometry_reconstruction/detached_qual_worktree"

echo "== Stage F41R1 Detached Clean-Linux Qualification =="
echo "Preparation SHA: ${PREP_SHA}"

# Remove stale worktree if present
if [ -d "${WORKTREE_DIR}" ]; then
    git worktree remove --force "${WORKTREE_DIR}" 2>/dev/null || rm -rf "${WORKTREE_DIR}"
fi

# Create temporary detached Git worktree at PREP_SHA
git worktree add --detach "${WORKTREE_DIR}" "${PREP_SHA}"

cleanup() {
    echo "Cleaning up detached worktree..."
    cd "${PROJECT_ROOT}"
    git worktree remove --force "${WORKTREE_DIR}" 2>/dev/null || rm -rf "${WORKTREE_DIR}"
}
trap cleanup EXIT

# Step 1: Run unit tests inside detached worktree
echo "Running unit tests in detached worktree..."
cd "${WORKTREE_DIR}"
python3 -m unittest tests/unit/test_stage_f41_batch.py -v
python3 -m unittest tests/unit/test_stage_f40_batch.py -v
UNIT_TEST_RESULT="passed"

# Step 2: Run static gate validator inside detached worktree
echo "Running static gate in detached worktree..."
python3 scripts/validation/validate_f41_cae_reconstruction_gate.py
STATIC_GATE_RESULT="passed"

# Step 3: Verify package SHA256 manifests inside detached worktree
echo "Verifying SHA256 manifests in detached worktree..."
python3 scripts/validation/generate_f41_sha256sums.py
MANIFEST_RESULT="passed"

# Step 4: Verify authority false/zero inside detached worktree
echo "Verifying submission authority flags..."
EXEC_AUTH=$(python3 -c "import json; data=json.load(open('project_coordination/ACTIVE_TASK.json')); print(str(data.get('execution_authorized', False)).lower())")

if [ "${EXEC_AUTH}" == "true" ]; then
    echo "ERROR: execution_authorized is true (must be false)" >&2
    exit 1
fi

QUAL_JSON_PATH="${PROJECT_ROOT}/runs/hpc/stage_f/f41_crack_geometry_reconstruction/F41_CLEAN_LINUX_QUALIFICATION.json"
mkdir -p "$(dirname "${QUAL_JSON_PATH}")"

cat <<EOF > "${QUAL_JSON_PATH}"
{
  "protocol_version": 1,
  "preparation_commit": "${PREP_SHA}",
  "qualification_environment": "detached_git_worktree_clean_linux",
  "detached_worktree": "${WORKTREE_DIR}",
  "unit_test_result": "${UNIT_TEST_RESULT}",
  "static_gate_result": "${STATIC_GATE_RESULT}",
  "manifest_result": "${MANIFEST_RESULT}",
  "qualification_status": "qualified_not_authorized"
}
EOF

echo "Qualification JSON written to ${QUAL_JSON_PATH}"
echo "F41_QUALIFICATION_SUCCESS"
exit 0
