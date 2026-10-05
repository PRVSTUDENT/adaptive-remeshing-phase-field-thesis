#!/bin/bash
set -euo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis || exit 1

module load abaqus/2023
echo "=== EXECUTING MODE-II NATIVE REMESHING SWEEP AGAINST Job-1_UEL.odb ==="
abaqus cae noGUI=execute_mode2_native_remesh_suite.py -- Job-1_UEL.odb .
EXIT_CODE=$?
echo "=== FINISHED REMESHING SWEEP (EXIT: $EXIT_CODE) ==="
exit "$EXIT_CODE"
