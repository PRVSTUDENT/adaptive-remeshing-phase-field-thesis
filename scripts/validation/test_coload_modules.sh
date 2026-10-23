#!/bin/bash
set -u
if ! type module >/dev/null 2>&1; then
    if [ -f /etc/profile.d/lmod.sh ]; then
        source /etc/profile.d/lmod.sh
    fi
fi

echo "--- Testing co-loading python 3.11 and abaqus 2023 ---"
module purge || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 || true
which python3
python3 -V
python3 -c "import numpy, scipy; print('Python 3 NumPy:', numpy.__version__, 'SciPy:', scipy.__version__)"
which abaqus
abaqus whereami || true
