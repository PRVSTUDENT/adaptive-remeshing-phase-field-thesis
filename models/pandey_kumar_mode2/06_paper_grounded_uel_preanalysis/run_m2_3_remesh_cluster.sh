#!/bin/bash
set -eo pipefail

WORKDIR="/scratch9/pr21vyci/runs/mode2_j1_miehe_horizon/m2_3_remesh"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Initialize module environment safely
export HISTCONTROL="${HISTCONTROL:-}"
export HISTSIZE="${HISTSIZE:-}"
source /etc/profile || true
module purge || true
module load abaqus/2023

echo "=== STARTING MODE-II GATE M2-3 NATIVE ADAPTIVE REMESHING SUITE ==="
echo "Workdir: $WORKDIR"
echo "Abaqus: $(which abaqus)"

cp -u /home/pr21vyci/projects/mode2_reproduction_worktree/models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/execute_mode2_m2_3_remesh_reproduction.py .

abaqus cae noGUI=execute_mode2_m2_3_remesh_reproduction.py -- /scratch9/pr21vyci/runs/mode2_j1_miehe_horizon/Job-1_UEL_paper_horizon.odb "$WORKDIR"
EXIT_CODE=$?

echo "=== FINISHED MODE-II GATE M2-3 NATIVE ADAPTIVE REMESHING SUITE (EXIT: $EXIT_CODE) ==="
exit "$EXIT_CODE"
