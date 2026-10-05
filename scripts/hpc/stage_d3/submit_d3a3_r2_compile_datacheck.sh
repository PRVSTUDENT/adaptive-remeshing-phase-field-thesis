#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name d3a3_r2_datacheck \
  --message "D3A3-R2 compile/datacheck only: runtime H loader, no full solver continuation; D3D/D3E remain blocked" \
  -- -q entry_imfdfkmq \
     -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de \
     -m abe \
     scripts/hpc/stage_d3/04_d3a3_r2_compile_datacheck.pbs
