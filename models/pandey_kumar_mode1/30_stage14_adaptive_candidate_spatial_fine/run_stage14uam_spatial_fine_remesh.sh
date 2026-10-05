#!/bin/bash
set -e

# Load Abaqus 2023
module load abaqus/2023

# Navigate to stage directory
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/30_stage14_adaptive_candidate_spatial_fine

echo "Running Abaqus CAE noGUI for Stage 14U-AM native adaptive remeshing (minElementSize=0.0005 mm)..."
abaqus cae noGUI=execute_stage14uam_spatial_fine_remesh.py -- ../93_mode1_preanalysis_inf_companion_2906/PK_M1_JOB1_INF_COMPANION_2906.odb .
echo "Abaqus CAE execution completed with exit code $?"
