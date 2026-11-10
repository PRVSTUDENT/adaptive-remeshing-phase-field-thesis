#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_pk_sec43_job2_staggered_f1709"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Running Cluster Abaqus 2023 Datacheck on Section 4.3 Job-2 (Staggered UEL) ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
hostname
which ifort
which abaqus

set +e
abaqus job=M1_PK_SEC43_JOB2_STAGGERED_DATACHECK input=PK_SEC43_JOB2_ADAPTED_PROD.inp user=f42_staggered_variant_uel.for datacheck -interactive
EXIT_CODE=$?
set -e

echo "Cluster datacheck finished with exit code: ${EXIT_CODE}"
date -u +"%Y-%m-%dT%H:%M:%SZ"

if [ -f "M1_PK_SEC43_JOB2_STAGGERED_DATACHECK.dat" ]; then
    echo "Tail of datacheck .dat file:"
    tail -n 35 M1_PK_SEC43_JOB2_STAGGERED_DATACHECK.dat
fi

exit ${EXIT_CODE}
