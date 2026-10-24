#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
from pathlib import Path

files = [
    "results/validation/mode1_f1597/pkg98_r1_pdas_trial_evaluation.json",
    "results/validation/mode1_f1597/pkg98_r1_pdas_subproblem_ledger.json",
    "results/validation/mode1_f1597/pkg98_r1_uel_energy_balance.csv",
    "results/validation/mode1_f1597/pkg98_r1_pbs_execution.log",
    "scripts/validation/evaluate_package98_r1_pdas_telemetry.py",
    "scripts/validation/diagnose_pkg98_r1_healing_nodes.py",
    "scripts/validation/inspect_iter15_free_healing.py"
]

for f in files:
    p = Path(f)
    if p.exists():
        h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
        print(f'"{f}": "{h}",')
    else:
        print(f"MISSING: {f}")
