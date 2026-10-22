#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_candidate_donor_h0025
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh 2>/dev/null || true; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python inspect_odb_frames.py
