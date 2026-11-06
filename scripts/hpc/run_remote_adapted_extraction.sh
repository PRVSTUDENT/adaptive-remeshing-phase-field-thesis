#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_method_a_hole_adapted
source /etc/profile.d/lmod.sh
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python extract_method_a_hole_adapted.py --odb PK_HOLE_METHOD_A_ADAPT.odb --out-dir . --n-phys 52447
