#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_method_a_hole_f1685_prod
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "=== Running Pointwise Damage Audit ==="
abaqus python audit_f1685_pointwise_damage.py > damage_audit.log 2>&1
cat damage_audit.log
