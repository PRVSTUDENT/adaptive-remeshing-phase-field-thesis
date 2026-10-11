#!/bin/bash
set -euo pipefail

export PROJECT_HOME="/home/pr21vyci/projects/mode2_reproduction_worktree"
WRAPPER="${PROJECT_HOME}/scripts/hpc/qsub_with_submitted_notify.sh"

FINAL_DIR="/scratch9/pr21vyci/runs/mode1_method_b_f1408/final_fracture"

echo "=== SUBMITTING METHOD B FINAL FRACTURE SIMULATION ==="

JOB_ID=$("${WRAPPER}" --job-name "M1_MB_FINAL_1S" --message "Mode-I Method B Final Fracture Adaptive Solve (u=0.0100mm, 6112 FE, 1 CPU, 16GB, walltime 24h)" -- "${FINAL_DIR}/submit_M1_MB_FINAL_1S.pbs")

echo "Submitted M1_MB_FINAL_1S: ${JOB_ID}"
echo "FINAL_JOB_ID=${JOB_ID}"
