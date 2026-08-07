#!/bin/bash
set -euo pipefail

echo "== Stage F41 Detached Clean-Linux Qualification =="

python3 -m unittest tests/unit/test_stage_f41_batch.py -v
python3 -m unittest tests/unit/test_stage_f40_batch.py -v
python3 scripts/validation/validate_f41_cae_reconstruction_gate.py

EXEC_AUTH=$(python3 -c "import json; data=json.load(open('project_coordination/ACTIVE_TASK.json')); print(str(data.get('execution_authorized', False)).lower())")

if [ "${EXEC_AUTH}" == "true" ]; then
    echo "ERROR: execution_authorized is true (must be false)" >&2
    exit 1
fi

echo "F41_QUALIFICATION_SUCCESS"
exit 0
