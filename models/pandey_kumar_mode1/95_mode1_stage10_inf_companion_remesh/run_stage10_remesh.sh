#!/bin/bash
set -e

# Load Abaqus 2023
module load abaqus/2023

# Navigate to stage 10 directory
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/95_mode1_stage10_inf_companion_remesh

echo "Running Abaqus CAE noGUI for Stage 10 native adaptive remeshing..."
abaqus cae noGUI=execute_stage10_inf_companion_native_remesh.py -- ../93_mode1_preanalysis_inf_companion_2906/PK_M1_JOB1_INF_COMPANION_2906.odb .
echo "Abaqus CAE execution completed with exit code $?"
