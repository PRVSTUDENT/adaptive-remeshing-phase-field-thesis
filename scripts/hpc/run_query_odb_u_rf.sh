#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_pk_f1714_five_hole

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load abaqus/2023

abaqus python query_odb_frames_early.py
