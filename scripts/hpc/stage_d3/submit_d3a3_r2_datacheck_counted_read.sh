#!/bin/bash
set -euo pipefail

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

REVISION="$(git rev-parse HEAD)"

scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name d3a3_r2_datacheck_r2 \
  --message "D3A3-R2 counted runtime-H datacheck; exact 25600-record loader; no full solver execution" \
  -- -q entry_imfdfkmq \
     -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de \
     -m abe \
     -v PROJECT_REVISION="${REVISION}" \
     scripts/hpc/stage_d3/06_d3a3_r2_datacheck_counted_read.pbs
