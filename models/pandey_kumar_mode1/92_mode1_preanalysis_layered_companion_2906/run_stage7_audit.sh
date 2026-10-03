#!/bin/bash
set -e
if [ -f /etc/profile.d/modules.sh ]; then
    source /etc/profile.d/modules.sh
fi
module load abaqus/2023
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/92_mode1_preanalysis_layered_companion_2906
echo "Running Stage 7 Layered Companion Fidelity Audit..."
abaqus python stage7_companion_fidelity_audit.py
echo "Stage 7 Audit finished successfully."
