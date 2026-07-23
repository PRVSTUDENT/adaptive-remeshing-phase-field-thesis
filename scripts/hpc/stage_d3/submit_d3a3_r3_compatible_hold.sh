#!/bin/bash
set -euo pipefail

cd "${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"

JOB_NAME="d3a3_r3_compat_hold"
PBS="scripts/hpc/stage_d3/09_d3a3_r3_compatible_hold.pbs"
DATACHECK_OK="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r3_compatible_datacheck_r1/D3A3_R3_DATACHECK.ok"
POSTPYTHON_OK="runs/hpc/stage_d3/interrupted_transfer/r3_postpython_environment/D3A3_R3_POSTPYTHON.ok"
RUNTIME_H="models/state_transfer/d3_interrupted_transfer/executable_r3_compatible/d3_transfer_h.dat"
D3A4_OK="runs/hpc/stage_d3/interrupted_transfer/compatibility_projection_d3a4/D3A4.ok"
PACKAGE_OK="runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1/D3_PACKAGE_COMPATIBLE_R1.ok"
MAIL="Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"

git ls-files --error-unmatch "${DATACHECK_OK}" >/dev/null
grep -q "stage_d3a3_r3_compatible_datacheck_pass" "${DATACHECK_OK}"
git ls-files --error-unmatch "${POSTPYTHON_OK}" >/dev/null
grep -q "stage_d3a3_r3_postpython_environment_pass" "${POSTPYTHON_OK}"
git ls-files --error-unmatch "${RUNTIME_H}" >/dev/null
git ls-files --error-unmatch "${D3A4_OK}" >/dev/null
git ls-files --error-unmatch "${PACKAGE_OK}" >/dev/null
bash -n "${PBS}"
! grep -Eq "cp .*d3_transfer_table[.]inc" "${PBS}"
# ODB must not be listed as a repository copy_evidence pattern (scratch only).
! grep -Eq '^[[:space:]]*"D3A3_R3_compatible_hold[.]odb"' "${PBS}"
grep -q 'D3A3_R3_ODB_LOCATION.json' "${PBS}"
grep -q 'write_odb_location' "${PBS}"
grep -q 'python/gcc/11.4.0/3.11.7' "${PBS}"
grep -q 'D3A3_R3_POSTPYTHON_PIPELINE.log' "${PBS}"

REVISION="$(git rev-parse HEAD)"

scripts/hpc/qsub_with_submitted_notify.sh \
  --job-name "${JOB_NAME}" \
  --message "D3A3-R3 compatible active-set release hold; serial CPU1/16GB/02:00; gated by committed datacheck + postpython markers" \
  -- -q entry_imfdfkmq \
     -M "${MAIL}" \
     -m abe \
     -v PROJECT_REVISION="${REVISION}" \
     "${PBS}"
