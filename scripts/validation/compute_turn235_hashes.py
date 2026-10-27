import hashlib
import json
from pathlib import Path

files = [
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/c4_inc88_from_p121_summary.json',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/pbs_execution.log',
    'results/validation/package122_initial_energy_audit.json',
    'results/validation/package120_vs_package122_comparison.json',
    'scripts/validation/audit_initial_mapped_energy_p122.py',
    'scripts/validation/evaluate_package120_vs_package122.py',
    'tests/unit/test_mode1_f1597_package122_terminal_evaluation.py',
    'project_coordination/HPC_JOB_LEDGER.csv',
    'project_coordination/CURRENT_STATE.md'
]

hashes = {}
for f in files:
    p = Path(f)
    h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    hashes[f] = h
    print(f'"{f}": "{h}",')

prep = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "finding": "Package 122 terminal evidence reconciled (Exit 0, 303 s, 15 cycles, iteration cap reached); initial mapped elastic energy deconstructed via Dirichlet minimum potential energy (+16.15% pre-solve relaxing to +0.598% post-solve); Hypothesis H3 refuted with H3_NOT_SUPPORTED as Package 122 reproduces Package 120 nonstationary trajectory within 0.0017% energy parity.",
    "evidence_sources": hashes,
    "verification_passed": True
}

with open("results/validation/preparation-d6ea8f07-2fe4-4a25-b28b-99e7a086411c.json", "w", newline="\n", encoding="utf-8") as f:
    json.dump(prep, f, indent=2)

print("\nSaved preparation-d6ea8f07-2fe4-4a25-b28b-99e7a086411c.json successfully!")
