#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
from pathlib import Path

files = [
    "models/pandey_kumar_mode1/98_r1_c5_pdas_chatter_repair_pilot/M1_C5_PACKAGE98_R1_PDAS_PILOT_AUTHORIZATION.json",
    "models/pandey_kumar_mode1/98_r1_c5_pdas_chatter_repair_pilot/M1_C5_PACKAGE98_R1_PDAS_PILOT_PREFLIGHT_REPORT.json",
    "models/pandey_kumar_mode1/98_r1_c5_pdas_chatter_repair_pilot/PACKAGE_MANIFEST.json",
    "models/pandey_kumar_mode1/98_r1_c5_pdas_chatter_repair_pilot/pdas_cluster_execution_adapter.py",
    "models/pandey_kumar_mode1/98_r1_c5_pdas_chatter_repair_pilot/submit_M1_C5_PACKAGE98_R1_PDAS_PILOT.pbs",
    "tests/unit/test_mode1_f1597_package98_r1_adapter.py",
    "tests/unit/test_mode1_f1597_turn79_pdas_chatter_repair.py"
]

for f in files:
    p = Path(f)
    if p.exists():
        h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
        print(f'"{f}": "{h}",')
    else:
        print(f"MISSING: {f}")
