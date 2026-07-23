#!/bin/bash
set -euo pipefail

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

JOB_NAME="d3a3_r3_postpy"
PBS="scripts/hpc/stage_d3/11_d3a3_r3_postpython_smoke.pbs"
MAIL="Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"
PACKAGE_H="runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1/D3_TRANSFERRED_IP_H.csv"
ASSEMBLY_SMOKE="scripts/validation/smoke_d3a3_r3_postpython_assembly.py"

git ls-files --error-unmatch \
  "runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1/D3_PACKAGE_COMPATIBLE_R1.ok" >/dev/null
git ls-files --error-unmatch "${PACKAGE_H}" >/dev/null
git ls-files --error-unmatch "${PBS}" >/dev/null
git ls-files --error-unmatch "${ASSEMBLY_SMOKE}" >/dev/null
git ls-files --error-unmatch \
  "scripts/validation/analyze_d3a3_r3_fixed_state_kkt.py" >/dev/null
git ls-files --error-unmatch \
  "scripts/validation/validate_d3a3_r3_compatible_hold.py" >/dev/null
git ls-files --error-unmatch \
  "scripts/validation/test_validate_d3a3_r3_compatible_hold.py" >/dev/null
bash -n "${PBS}"
! grep -Eq "abaqus job=" "${PBS}"
! grep -Eq "datacheck" "${PBS}"

REVISION="$(git rev-parse HEAD)"

scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "D3A3-R3 postpython environment smoke; CPU1/4GB/00:10; no Abaqus solve; qualify Python 3.11+NumPy/SciPy" \
  -- -q entry_imfdfkmq \
     -M "${MAIL}" \
     -m abe \
     -v PROJECT_REVISION="${REVISION}" \
     "${PBS}"
