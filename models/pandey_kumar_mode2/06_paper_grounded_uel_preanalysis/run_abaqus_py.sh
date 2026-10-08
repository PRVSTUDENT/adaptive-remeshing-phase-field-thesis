#!/bin/bash
module purge 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 2>/dev/null || true
abaqus python "$@"
