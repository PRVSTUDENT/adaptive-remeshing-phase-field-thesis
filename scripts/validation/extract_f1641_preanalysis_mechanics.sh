#!/bin/bash
# Read-only existing ODB field extraction, not PBS/solver execution.
set -euo pipefail
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
cd /scratch9/pr21vyci/runs/mode1_hole_method_a_test
abaqus python extract_f1641_preanalysis_mechanics.py
