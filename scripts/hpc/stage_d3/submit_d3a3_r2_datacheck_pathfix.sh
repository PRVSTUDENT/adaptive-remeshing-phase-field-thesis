#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

REVISION="$(git rev-parse HEAD)"

scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name d3a3_r2_datacheck_r1 \
  --message "D3A3-R2 corrected datacheck using GETOUTDIR absolute runtime-H path; no full solver execution" \
  -- -q entry_imfdfkmq \
     -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de \
     -m abe \
     -v PROJECT_REVISION="${REVISION}" \
     scripts/hpc/stage_d3/05_d3a3_r2_datacheck_pathfix.pbs
