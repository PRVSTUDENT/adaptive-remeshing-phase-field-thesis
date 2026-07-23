#!/bin/bash
set -euo pipefail

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name d3a3_target_ingest \
  --message "D3A3 full nonmatching-target d/H ingestion, checkpoint equilibration, and phase-release hold; serial; no continuation beyond U=0.003 mm" \
  -- -q entry_imfdfkmq \
     -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de \
     -m abe \
     scripts/hpc/stage_d3/03_d3a3_target_ingestion_hold.pbs
