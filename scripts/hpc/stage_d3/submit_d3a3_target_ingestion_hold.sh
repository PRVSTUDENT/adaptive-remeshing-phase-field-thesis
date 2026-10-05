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
  --job-name d3a3_target_ingest_r1 \
  --message "Corrected D3A3 full-target ingestion/equilibration/release hold; compiler modules restored; serial; no continuation beyond U=0.003 mm" \
  -- -q entry_imfdfkmq \
     -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de \
     -m abe \
     scripts/hpc/stage_d3/03_d3a3_target_ingestion_hold.pbs
