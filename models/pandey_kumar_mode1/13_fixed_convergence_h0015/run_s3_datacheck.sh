#!/bin/bash
set -eo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/13_fixed_convergence_h0015
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== STARTING DATACHECK S3 (41,912 elements) ==="
rm -f PK_M1_S3_DC.*
abaqus datacheck job=PK_M1_S3_DC user=f42_mixed_uel.for input=PK_MODE1_FIX_H0015_ENERGY.inp cpus=1 memory=16gb double=both interactive
RC=$?
echo "=== DATACHECK S3 FINISHED WITH EXIT CODE: $RC ==="
exit $RC
