#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_method_a_hole_f1705_prod

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Running Abaqus Python Damage Extraction ==="
abaqus python extract_f1705_e10_damage.py
echo "=== Damage Extraction Completed ==="
ls -lh f1705_e10_damage_field.json
