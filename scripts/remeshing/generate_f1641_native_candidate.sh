#!/bin/bash
# One CAE-only adaptive mesh. No PBS, datacheck or solver execution.
set -euo pipefail
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
cd /scratch9/pr21vyci/runs/mode1_hole_method_a_f1641
test ! -e PK_HOLE_F1641_1PCT_PROD_PHYS.inp
abaqus cae noGUI=generate_plate_with_hole_method_a.py -- --reuse-preanalysis-odb /scratch9/pr21vyci/runs/mode1_hole_method_a_test/PK_HOLE_METHOD_A_PREANALYSIS.odb --preanalysis-sha256 0A108C6A8404F1AF9D8F5DDC03223E9D8D051AB08587F841D9F5799970AE93B1 --error-target 1.0 --coarse-h 0.02 --min-h 0.001 --max-h 0.02 --job-prefix PK_HOLE_F1641_1PCT --output-dir .
