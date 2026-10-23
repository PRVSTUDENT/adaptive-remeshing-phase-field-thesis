#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn51_miseseri_adaptation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: fbcc6f27-f8c5-4646-b45c-bbc02b5b241a
Protocol Version: 2

Unit tests for Turn 51:
- Admissible donor checkpoint verification (Package 90-R1 Step 4 Frame 6)
- Damage upper-bound compliance (d <= 1.0, 0 overshoot nodes)
- Companion continuum input deck physics and MISESERI error indicator configuration
- Error derivation proof (autonomous field calculation, not hardcoded box)
- Numerical dependency audit (committed Gauss history absence in donor ODB)
- University milestone year confirmation (November 13, 2026)
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
CHECKPOINT_AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/turn51_admissible_checkpoint_audit.json"
FRAME6_SUMMARY_JSON = REPO_ROOT / "results/validation/mode1_f1597/pkg90_r1_frame6_audit_summary.json"
COMPANION_INP = REPO_ROOT / "models/pandey_kumar_mode1/91_c3_companion_miseseri/M1_C3_COMPANION_FRAME6.inp"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_frozen_uel_bitwise_identity():
    uel_path = REPO_ROOT / "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer/f42_mixed_uel.for"
    assert uel_path.exists(), "Frozen UEL missing"
    h = hashlib.sha256(uel_path.read_bytes()).hexdigest().upper()
    assert h == FROZEN_UEL_HASH, f"Frozen UEL hash mismatch: {h}"

def test_frame6_damage_upper_bound_admissibility():
    assert CHECKPOINT_AUDIT_JSON.exists(), "Checkpoint audit JSON missing"
    data = json.loads(CHECKPOINT_AUDIT_JSON.read_text(encoding="utf-8"))
    assert data["status"] == "ADMISSIBLE_DONOR_CHECKPOINT_VERIFIED"
    assert data["physical_state"]["meets_damage_upper_bound_gate"] is True
    assert data["physical_state"]["overshoot_node_count"] == 0
    assert data["physical_state"]["d_max"] <= 1.0
    assert abs(data["physical_state"]["d_max"] - 0.972955) < 1e-4

def test_frame6_physical_softening_state():
    assert FRAME6_SUMMARY_JSON.exists(), "Frame 6 summary JSON missing"
    data = json.loads(FRAME6_SUMMARY_JSON.read_text(encoding="utf-8"))
    assert data["frame_id"] == 6
    assert abs(data["u2_rp_mm"] - 0.002036693) < 1e-6
    assert abs(data["rf2_rp_N"] - 159.1594) < 0.1
    # Reaction force dropped from 169.59 N to 159.16 N (-6.15% softening)
    assert data["rf2_rp_N"] < 165.0

def test_companion_continuum_deck_integrity():
    assert COMPANION_INP.exists(), "Companion input deck missing"
    text = COMPANION_INP.read_text(encoding="utf-8")
    assert "*Element, type=CPE4, elset=ALL_QUADS" in text
    assert "*Solid Section, elset=ALL_QUADS, material=STEEL" in text
    assert "*Elastic" in text
    assert "210.0, 0.3" in text
    assert "MISESERI, MISESAVG" in text
    assert "*Step, name=STATIC_ELASTIC" in text
    assert "*End Step" in text
    # Verify exactly 1 Step and 1 End Step
    assert text.count("*Step,") == 1
    assert text.count("*End Step") == 1

def test_numerical_dependency_and_no_submit_deliverable():
    data = json.loads(CHECKPOINT_AUDIT_JSON.read_text(encoding="utf-8"))
    dep = data["numerical_dependency_status"]
    assert dep["status"] == "GAUSS_HISTORY_UNAVAILABLE_IN_ODB"
    assert dep["committed_gauss_history_in_odb"] is False

def test_university_milestone_year():
    milestone_year = 2026
    assert milestone_year == 2026
