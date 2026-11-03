#!/usr/bin/env python3
import hashlib
from pathlib import Path

files = [
    'results/validation/c6_r5_independent_review_remediation_analysis.json',
    'results/validation/c6_r3_falsifiable_damping_hypothesis_offline_evaluation.json',
    'tests/unit/test_package171_r5_c6_coupled_driver_gates.py',
    'tests/unit/test_package171_r5_c6_coupled_driver_readiness.py',
    'tests/unit/test_package171_r5_c6_coupled_driver_integration.py',
    'scripts/state_transfer/driver_package171_r5_c6_coupled_pdas.py',
    'models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration/PACKAGE_MANIFEST.json',
    'models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration/M1_C6_PACKAGE171_R5_AUTHORIZATION.json',
    'models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration/EXECUTION_MANIFEST.json',
    'models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration/submit_M1_C6_P171_R5_C3_0.pbs'
]

for f in files:
    p = Path(f)
    h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    print(f'"{f}": "{h}",')
