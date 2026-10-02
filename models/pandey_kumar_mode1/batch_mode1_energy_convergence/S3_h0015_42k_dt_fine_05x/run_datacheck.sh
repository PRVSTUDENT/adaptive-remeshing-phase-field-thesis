#!/bin/bash
set -euo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/batch_mode1_energy_convergence/S3_h0015_42k_dt_fine_05x || exit 1
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

rm -f PK_M1_S3_H0015_DTFINE.lck PK_M1_S3_H0015_DTFINE.023
abaqus datacheck job=PK_M1_S3_H0015_DTFINE user=f42_mixed_uel.for input=PK_M1_S3_H0015_DTFINE.inp cpus=4 memory="24gb" double=both interactive
