#!/bin/bash
set -euo pipefail

# Environment setup
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

WORKDIR="/scratch9/pr21vyci/test_mode2_compile"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

SRC="/home/pr21vyci/projects/mode2_reproduction_worktree/models/pandey_kumar_mode2/f42_mixed_uel_mode2_miehe.for"
if [ ! -f "$SRC" ]; then
    echo "ERROR: Source file $SRC not found" >&2
    exit 1
fi

cp "$SRC" ./f42_mixed_uel_mode2_miehe.for

echo "=== Testing Abaqus compilation of f42_mixed_uel_mode2_miehe.for ==="
abaqus make library=f42_mixed_uel_mode2_miehe.for

if [ -f "libstandardU.so" ] || [ -f "f42_mixed_uel_mode2_miehe.o" ] || [ -f "f42_mixed_uel_mode2_miehe-std.o" ]; then
    echo "SUCCESS: Library object created successfully."
    ls -l
else
    echo "WARNING: Compilation finished without expected .so or .o output."
    ls -l
fi
