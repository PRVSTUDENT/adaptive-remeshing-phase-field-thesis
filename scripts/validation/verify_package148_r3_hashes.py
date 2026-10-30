#!/usr/bin/env python3
"""scripts/validation/verify_package148_r3_hashes.py

Computes and verifies SHA-256 hashes of all Package 148 R3 files, dependencies, and test fixtures.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES = [
    'scripts/state_transfer/driver_package146_147_pdas_continuation.py',
    'scripts/validation/extract_package148_iteration.py',
    'scripts/state_transfer/build_package146_147_transfer_deck.py',
    'scripts/state_transfer/c3_int_to_c4_spatial_mapping.py',
    'scripts/hpc/Invoke-Mode1Execution.ps1',
    'scripts/hpc/mode1_execution_gate.py',
    'scripts/hpc/Submit-Mode1Batch.ps1',
    'scripts/hpc/preflight_package49_authorization.py',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/PACKAGE_MANIFEST.json',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/EXECUTION_MANIFEST.json',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/submit_M1_C4_P148_R3.pbs',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/f42_mixed_uel.for',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/job_notifications.sh',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/run_datacheck.sh',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/M1_C4_PACKAGE148_STATE_TRANSFER.inp',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/P148_MECHANICAL_DC.inp',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/P148_PHASE_DC.inp',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/nodal_displacements_initial.csv',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/nodal_phase_field_initial.csv',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/d_lower_bounds.csv',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/active_set_boundary_cards.inc',
    'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/initial_conditions_solution.inc',
    'models/pandey_kumar_mode1/146_c3_fine_donor/M1_C3_FINE_PACKAGE146_DONOR.inp',
    'models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp',
    'tests/fixtures/package146147/146_step1_dat.txt.gz',
    'results/validation/package146147/evaluation.json',
    'tests/unit/test_mode1_f1597_package148_r3_extraction.py',
    'tests/unit/test_mode1_f1597_package148_r3_preflight.py',
    'tests/unit/test_mode1_f1597_package148_py36_compatibility.py',
    'tests/unit/test_mode1_execution_gate.py'
]

def main():
    hashes = {}
    for rel in FILES:
        p = ROOT / rel
        if not p.exists():
            raise FileNotFoundError(f"Missing required file: {rel}")
        h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
        hashes[rel] = h

    out_file = ROOT / 'results/validation/r3_qualification_verification.json'
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    print(f"Verified {len(hashes)} files; wrote {out_file}")

if __name__ == '__main__':
    main()
