#!/bin/bash
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python /scratch9/pr21vyci/runs/mode1_candidate_donor_h0025_visual/evaluate_p76_p87_checkpoint_candidates.py
