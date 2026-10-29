# -*- coding: utf-8 -*-
"""
test_mode1_f1597_h50_reference_consistency.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Hypothesis: H50 - Coupled PDAS Reference Consistency and Physical Validation
Protocol Version: 2

Validates H50 audit deliverables:
1. Verifies authentic Package 143 Frame-77 reference values.
2. Detects and classifies the H49 spurious reference discrepancy (+3.999% in donor E_tot).
3. Evaluates corrected Stage C1-1 continuity: Force Gate PASS (-1.92%), Energy Gate FAIL (+2.23%).
4. Verifies physical energy compensation ratio between elastic relaxation and fracture dissipation.
5. Confirms preservation of master invariants.
"""

import os
import json
import pytest

AUDIT_PATH = os.path.join("results", "validation", "h50_reference_consistency_audit.json")
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


@pytest.fixture(scope="module")
def h50_data():
    assert os.path.isfile(AUDIT_PATH), "Audit file %s does not exist" % AUDIT_PATH
    with open(AUDIT_PATH, "r") as f:
        data = json.load(f)
    return data


def test_schema_and_task(h50_data):
    assert h50_data.get("schema") == 1
    assert h50_data.get("task_id") == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert h50_data.get("classification") == "H50_REFERENCE_MISMATCH_CONFIRMED"


def test_governing_invariants(h50_data):
    invariants = h50_data.get("governing_invariants_preserved", {})
    assert invariants.get("H47_PACKAGE142_C1_1_FAILED") is True
    assert invariants.get("STAGE_C1_2_STEP2_ENERGY_GATE_FAILED") is True
    assert invariants.get("P113_GATE_VALID_FAILURE") is True
    assert invariants.get("H24_REFERENCE_AUDIT_PENDING") is True
    assert invariants.get("FROZEN_UEL_HASH") == FROZEN_UEL_SHA256


def test_authentic_donor_reference(h50_data):
    auth = h50_data.get("donor_comparison", {}).get("authentic_reference", {})
    assert abs(auth["u_rp_mm"] - 0.0018003125442191958) < 1e-12
    assert abs(auth["rf2_n"] - 188.45704197883606) < 1e-6
    assert abs(auth["e_elastic_knmm"] - 0.000169634810) < 1e-9
    assert abs(auth["e_fracture_knmm"] - 0.000039117135) < 1e-9
    assert abs(auth["e_total_knmm"] - 0.000208751950) < 1e-9


def test_spurious_donor_reference_detected(h50_data):
    comp = h50_data.get("donor_comparison", {})
    spur = comp.get("h49_spurious_reference", {})
    discrep = comp.get("reference_discrepancy_pct", {})
    assert abs(spur["e_total_knmm"] - 0.00021710000) < 1e-8
    assert discrep["e_total"] > 3.5  # +3.999% discrepancy in donor total energy


def test_corrected_stage_c1_1_gates(h50_data):
    gates = h50_data.get("stage_c1_1_gate_results", {})
    force_gate = gates.get("force_gate_5pct", {})
    energy_gate = gates.get("total_energy_gate_2pct", {})

    # Force gate PASSES: -1.9214% <= 5.0%
    assert force_gate["status"] == "PASS"
    assert abs(force_gate["error_pct"]) <= 5.0

    # Total energy gate FAILS: +2.2310% > 2.0%
    assert energy_gate["status"] == "FAIL"
    assert energy_gate["error_pct"] > 2.0

    # Overall gate must FAIL
    assert gates.get("overall_gate_pass") is False
    assert h50_data.get("acceptance_overall") is False


def test_energy_compensation_and_invariance(h50_data):
    mech = h50_data.get("coupled_relaxation_mechanics", {})
    # Elastic relaxation must be negative
    assert mech["delta_elas_knmm"] < 0.0
    # Fracture energy must be positive
    assert mech["delta_frac_knmm"] > 0.0
    # Compensation ratio near 1.0 (95.3% compensation)
    assert 0.90 <= mech["compensation_ratio"] <= 1.15
    # Net total energy relaxation during 10 cycles is tiny (< 0.5%)
    assert abs(mech["delta_tot_pct"]) < 0.5
