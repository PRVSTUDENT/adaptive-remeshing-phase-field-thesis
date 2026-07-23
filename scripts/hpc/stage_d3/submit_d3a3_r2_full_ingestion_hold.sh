#!/bin/bash
set -euo pipefail

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

JOB_NAME="d3a3_target_ingest_r2"
PBS="scripts/hpc/stage_d3/07_d3a3_r2_full_ingestion_hold.pbs"
COMPILE_OK="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r2_replay/D3A3_R2_COMPILE.ok"
MAIL="Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"

git ls-files --error-unmatch "${COMPILE_OK}" >/dev/null
grep -q "stage_d3a3_r2_compile_datacheck_pass_postcheck_replay" "${COMPILE_OK}"
grep -q "D3A3_R2_COMPILE.ok" "${PBS}"
! grep -Eq "cp .*d3_transfer_table[.]inc" "${PBS}"
grep -q "d3_transfer_h.dat" "${PBS}"
bash -n "${PBS}"
python3 - <<'PY'
import json
from pathlib import Path

path = Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r2/D3A3_STATIC_VALIDATION.json")
data = json.loads(path.read_text(encoding="utf-8"))
if data.get("classification") != "stage_d3a3_static_validation_pass":
    raise SystemExit("D3A3 static validation is not pass")
PY

REVISION="$(git rev-parse HEAD)"

scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "D3A3-R2 full serial ingestion/equilibration/release hold after replay-closed compile/datacheck gate" \
  -- -q entry_imfdfkmq \
     -M "${MAIL}" \
     -m abe \
     -v PROJECT_REVISION="${REVISION}" \
     "${PBS}"
