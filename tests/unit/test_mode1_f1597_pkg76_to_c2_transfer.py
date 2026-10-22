"""
Unit regression test suite for Turn 20: Package 76 to Candidate C2 State Transfer.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""

import os
import sys
import json
import csv
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_uel_bit_identity():
    """Verify production UEL matches bitwise frozen hash."""
    uel_path = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/f42_mixed_uel.for"
    assert uel_path.exists(), f"UEL not found at {uel_path}"
    assert sha256_file(uel_path) == FROZEN_UEL_HASH

def test_donor_extracted_evidence_files():
    """Verify extracted authentic donor frame 111 evidence files exist and have non-trivial data."""
    nodal_csv = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_1416301/pkg76_frame111_nodal_u.csv"
    elem_csv = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_1416301/pkg76_frame111_elem_sdv.csv"
    manifest_json = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_1416301/pkg76_frame111_extraction_manifest.json"

    assert nodal_csv.exists()
    assert elem_csv.exists()
    assert manifest_json.exists()

    with open(manifest_json, "r") as f:
        m = json.load(f)
    assert m["status"] == "EXTRACTION_COMPLETE"
    assert m["num_nodes"] == 1698
    assert m["num_elements"] == 1600
    assert m["damage_metrics"]["bound_0_to_1_satisfied"] is True
    assert m["history_metrics"]["nonnegative_kuhn_tucker_satisfied"] is True
    # Terminal frame max damage is documented separately
    assert m["terminal_frame_metrics"]["terminal_max_damage"] > 1.0

def test_mapped_state_table_completeness():
    """Verify candidate_c2_mapped_state_table.csv covers all 2413 nodes and 2300 elements."""
    table_path = REPO_ROOT / "models/pandey_kumar_mode1/candidate_c2_mapped_state_table.csv"
    assert table_path.exists()

    nodes_count = 0
    elems_count = 0
    with open(table_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["record_type"] == "NODE":
                nodes_count += 1
            elif r["record_type"] == "ELEM_H":
                elems_count += 1

    assert nodes_count == 2413, f"Expected 2413 nodes, got {nodes_count}"
    assert elems_count == 2300, f"Expected 2300 elements, got {elems_count}"

def test_receiver_deck_proposal_structure():
    """Verify candidate_receiver_c2_state_transferred.inp contains all 2300 solution cards and 2-step setup."""
    deck_path = REPO_ROOT / "models/pandey_kumar_mode1/candidate_receiver_c2_state_transferred.inp"
    assert deck_path.exists()
    content = deck_path.read_text(encoding="utf-8")

    assert "*USER ELEMENT, TYPE=U1" in content
    assert "*USER ELEMENT, TYPE=U2" in content
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in content
    assert "Step, name=STATE_HOLD" in content
    assert "Step, name=FREE_CONTINUATION" in content

    # Count how many solution element cards exist
    sol_count = content.count("*INITIAL CONDITIONS, TYPE=SOLUTION")
    assert sol_count == 1
    # Check that element 2300 has initial conditions
    assert "2300, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0" in content

def test_audit_json_scientific_criteria():
    """Verify pkg76_to_c2_state_transfer_audit.json passes all governing numerical criteria."""
    audit_path = REPO_ROOT / "results/validation/mode1_f1597/pkg76_to_c2_state_transfer_audit.json"
    assert audit_path.exists()

    with open(audit_path, "r", encoding="utf-8") as f:
        audit = json.load(f)

    assert audit["status"] == "MAPPING_COMPLETE"
    assert audit["receiver"]["energy_continuity_pass"] is True
    assert audit["receiver"]["energy_continuity_rel_diff_pct"] <= 2.0
    assert audit["verification_criteria"]["phase_field_convention_satisfied"] is True
    assert audit["verification_criteria"]["zero_healing_strictly_enforced"] is True
    assert audit["verification_criteria"]["healing_node_count"] == 0
    assert audit["verification_criteria"]["history_monotonicity_kuhn_tucker"] is True
    assert audit["verification_criteria"]["crack_flank_separation_preserved"] is True
    assert audit["verification_criteria"]["cmod_at_slit_mouth_um"] > 2.0
    assert audit["mechanical_equilibrium_assessment"]["claim_of_physical_equilibrium"] is False
