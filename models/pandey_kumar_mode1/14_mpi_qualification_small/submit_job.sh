#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
JOB_ID=$(qsub submit_mpi_qualification.pbs)
echo "SUBMITTED_JOB_ID=$JOB_ID"
