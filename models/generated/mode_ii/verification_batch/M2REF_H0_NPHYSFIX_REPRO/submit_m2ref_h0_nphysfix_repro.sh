#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

JOB_ID=$(qsub M2REF_H0_NPHYSFIX_REPRO.pbs)
echo "Submitted M2REF_H0_NPHYSFIX_REPRO under Job ID: $JOB_ID"
