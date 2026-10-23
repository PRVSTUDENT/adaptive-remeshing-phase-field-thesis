#!/bin/bash
set -u
if ! type module >/dev/null 2>&1; then
    if [ -f /etc/profile.d/lmod.sh ]; then
        source /etc/profile.d/lmod.sh
    fi
fi

echo "--- Testing module load python/gcc/11.4.0/3.11.7 ---"
module purge || true
module load gcc/11.4.0 python/gcc/11.4.0/3.11.7 || true
which python3 || true
python3 -V || true
python3 -c "import numpy; print('Module Python NumPy:', numpy.__version__)" || echo "Module Python has NO numpy"
python3 -c "import scipy; print('Module Python SciPy:', scipy.__version__)" || echo "Module Python has NO scipy"

echo "--- Testing python3.11 or pip or virtualenv ---"
which pip3 || true
pip3 list || true
