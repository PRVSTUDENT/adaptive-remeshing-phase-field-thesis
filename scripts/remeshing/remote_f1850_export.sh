#!/bin/bash
set -euo pipefail
source /etc/profile.d/lmod.sh
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python /scratch9/pr21vyci/runs/mode1_pk_f1772_case1_remesh/snapshot_f1850_donor.py /scratch9/pr21vyci/runs/mode1_pk_f1772_case1_remesh/PK_F1772_CASE1_ENVELOPE.odb /scratch9/pr21vyci/runs/mode1_pk_f1772_case1_remesh/f1850_case1_donor.json existing
abaqus python /scratch9/pr21vyci/runs/mode1_pk_f1772_case1_remesh/snapshot_f1850_donor.py /scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_JOB1.odb /scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/f1850_case3_donor.json damage 0.285 1.5 0.03
