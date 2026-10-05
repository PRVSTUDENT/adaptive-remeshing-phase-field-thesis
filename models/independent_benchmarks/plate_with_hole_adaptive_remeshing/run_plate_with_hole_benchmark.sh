#!/bin/bash
set -euo pipefail

PACKAGE_DIR="/home/pr21vyci/projects/adaptive-remeshing/models/independent_benchmarks/plate_with_hole_adaptive_remeshing"

mkdir -p "$PACKAGE_DIR"
cd "$PACKAGE_DIR" || exit 1

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== STARTING PLATE-WITH-HOLE INDEPENDENT BENCHMARK ==="
echo "Package Dir: $PACKAGE_DIR"

abaqus cae noGUI=build_and_run_plate_with_hole_benchmark.py -- "$PACKAGE_DIR"
EXIT_CODE=$?

echo "=== FINISHED PLATE-WITH-HOLE BENCHMARK (EXIT: $EXIT_CODE) ==="
exit "$EXIT_CODE"
