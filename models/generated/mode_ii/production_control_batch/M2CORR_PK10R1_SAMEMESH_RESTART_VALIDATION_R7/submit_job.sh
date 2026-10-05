#!/bin/bash
#PBS -N M2R7_VAL
#PBS -q entry_imfdfkmq
#PBS -l nodes=1:ppn=1
#PBS -l mem=16gb
#PBS -l walltime=24:00:00
#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de
#PBS -m abe
#PBS -o M2R7_VAL.out
#PBS -e M2R7_VAL.err

cd "$PBS_O_WORKDIR" || exit 1

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== STARTING M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7 ==="
abaqus job=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7 user=f44_mixed_uel_restart_stateinit.for input=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.inp double=both interactive
ABAQUS_EXIT=$?
echo "=== FINISHED M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7 (EXIT: $ABAQUS_EXIT) ==="

exit $ABAQUS_EXIT
