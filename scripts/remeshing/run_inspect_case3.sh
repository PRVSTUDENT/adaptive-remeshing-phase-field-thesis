#!/bin/bash
set -e
source /etc/profile.d/lmod.sh
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
cd /scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1
abaqus python inspect_case3_staggered_odb.py
