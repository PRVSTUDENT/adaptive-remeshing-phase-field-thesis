#!/bin/bash
# Read-only ODB extraction, not PBS execution or a solver job.
set -euo pipefail
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
cd /scratch9/pr21vyci/runs/mode1_hole_method_a_test
abaqus python extract_method_a_hole_indicator.py /scratch9/pr21vyci/runs/mode1_hole_method_a_test/PK_HOLE_METHOD_A_PREANALYSIS.odb
