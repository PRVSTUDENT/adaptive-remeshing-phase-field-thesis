#!/bin/bash
set -u
echo "=== CLUSTER ENVIRONMENT INSPECTION ==="
hostname
date

if ! type module >/dev/null 2>&1; then
    if [ -f /etc/profile.d/lmod.sh ]; then
        source /etc/profile.d/lmod.sh
    elif [ -f /etc/profile.d/modules.sh ]; then
        source /etc/profile.d/modules.sh
    fi
fi

echo "--- System python3 ---"
which python3 || echo "No python3 in PATH"
python3 -V || true
python3 -c "import sys; print('Python sys.path:', sys.path)" || true
python3 -c "import numpy; print('NumPy:', numpy.__version__)" || echo "python3 has NO numpy"

echo "--- Module abaqus/2023 ---"
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 || true
which abaqus || echo "No abaqus in PATH"

echo "--- Abaqus Python Inspection ---"
abaqus python -c "import sys; print('sys.executable:', sys.executable); print('sys.version:', sys.version)" || true
abaqus python -c "import numpy; print('Abaqus NumPy version:', numpy.__version__); print('Abaqus NumPy path:', numpy.__file__)" || echo "abaqus python has NO numpy"
abaqus python -c "import scipy; print('Abaqus SciPy version:', scipy.__version__); print('Abaqus SciPy path:', scipy.__file__)" || echo "abaqus python has NO scipy"

echo "--- Available Python Modules on Cluster ---"
module avail python 2>&1 | head -n 30 || true
module avail scipy 2>&1 | head -n 30 || true
module avail anaconda 2>&1 | head -n 30 || true

echo "=== END INSPECTION ==="
