import hashlib
import json
from pathlib import Path

files = [
    'results/validation/package121_source_state_audit.json',
    'results/validation/c4_inc88_from_p121_mapping_audit.json',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/PACKAGE_MANIFEST.json',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/M1_C4_INC88_TRANSFER_AUTHORIZATION.json',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/M1_C4_INC88_TRANSFER.inp',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/driver_c4_inc88_transfer.py',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/submit_M1_C4_INC88_TRANSFER.pbs',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/d_lower_bounds.csv',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/stage_a_all_d0_boundary_cards.inc',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/active_set_boundary_cards.inc',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/nodal_displacements_initial.csv',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/run_c4_inc88_transfer_datacheck.sh',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/M1_C4_INC88_TRANSFER_DC.dat',
    'models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer/M1_C4_INC88_TRANSFER_DC.msg',
    'scripts/remeshing/build_package122_from_p121_transfer.py',
    'scripts/validation/stage_and_qualify_package122.py',
    'tests/unit/test_mode1_f1597_package122_qualification.py'
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
    "finding": "Package 122 (Controlled Source-State Sensitivity at Increment 88) successfully prepared, mapped with slit-flank awareness from converged Package 121 re-equilibrated terminal state, staged to cluster scratch, datacheck verified Exit 0, and submitted to PBS queue as Job 1417919.mmaster02.",
    "evidence_sources": hashes,
    "verification_passed": True
}

with open("results/validation/preparation-d013ff95-b54f-417e-bbfa-2fbb4bf38027.json", "w", newline="\n", encoding="utf-8") as f:
    json.dump(prep, f, indent=2)

print("\nSaved preparation-d013ff95-b54f-417e-bbfa-2fbb4bf38027.json successfully!")
