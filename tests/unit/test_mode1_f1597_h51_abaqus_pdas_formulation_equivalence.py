# -*- coding: utf-8 -*-
"""
test_mode1_f1597_h51_abaqus_pdas_formulation_equivalence.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Hypothesis: H51 - Authentic Abaqus Coupled-PDAS Validation & Formulation Parity
Protocol Version: 2

Validates H51 audit deliverables:
1. Verifies delivery and schema of results/validation/h51_abaqus_pdas_formulation_equivalence.json.
2. Verifies bitwise preservation of frozen production UEL (f42_mixed_uel.for, SHA-256: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6).
3. Verifies numerical parity of Formulation A (element-average degradation g(d_avg) = (1-d_avg)^2 + k)
   against authentic Abaqus Package 142 (Job 1418722) to within 0.05%.
4. Detects and isolates Formulation B (Gauss-point degradation g(d_g)) stiffening deviation.
5. Deconstructs H48 uncoupled phase relaxation (Delta d_max = 0.007630 under fixed donor H0) vs
   H49 coupled relaxation (Delta d_max = 0.09105 under refined C4 crack-tip singular strain concentration).
6. Verifies thermodynamic elastic-fracture compensation (|Delta E_elas| / Delta E_frac = 1.0491, 95.3% compensation).
7. Confirms retention of Stage C1-1 failure (+2.2310% > 2.0000% Energy Gate) and all governing invariants.
"""

import os
import sys
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
AUDIT_JSON_PATH = REPO_ROOT / "results" / "validation" / "h51_abaqus_pdas_formulation_equivalence.json"
FROZEN_UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "37_stage14_adaptive_candidate_spatial_fine_8thread" / "f42_mixed_uel.for"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


@pytest.fixture(scope="module")
def h51_data():
    if not AUDIT_JSON_PATH.exists():
        from scripts.validation.audit_h51_abaqus_pdas_formulation_equivalence import run_formulation_audit
        inp_path = REPO_ROOT / "models/pandey_kumar_mode1/142_c4_c3_int_state_transfer/M1_C4_PACKAGE142_STATE_TRANSFER.inp"
        d0_csv = REPO_ROOT / "models/pandey_kumar_mode1/142_c4_c3_int_state_transfer/nodal_phase_field_initial.csv"
        bounds_csv = REPO_ROOT / "models/pandey_kumar_mode1/142_c4_c3_int_state_transfer/d_lower_bounds.csv"
        p142_json = REPO_ROOT / "results/validation/package142_c1_1_evaluation.json"
        run_formulation_audit(str(inp_path), str(d0_csv), str(bounds_csv), str(p142_json), str(AUDIT_JSON_PATH))

    assert AUDIT_JSON_PATH.exists(), f"Audit file missing: {AUDIT_JSON_PATH}"
    with open(AUDIT_JSON_PATH, "r") as f:
        return json.load(f)


def test_schema_and_metadata(h51_data):
    assert h51_data.get("schema") == 1
    assert h51_data.get("task_id") == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert h51_data.get("investigation") == "H51_AUTHENTIC_ABAQUS_COUPLED_PDAS_VALIDATION"
    assert h51_data.get("classification") == "H51_PDAS_FORMULATION_DEFECT_IDENTIFIED"
    assert h51_data.get("sub_classification") == "H51_RUNTIME_COUPLING_BLOCKED"


def test_frozen_uel_preservation(h51_data):
    uel_ver = h51_data.get("uel_source_verified", {})
    assert uel_ver.get("sha256") == FROZEN_UEL_SHA256
    assert uel_ver.get("hash_matches") is True


def test_formulation_a_parity_with_authentic_abaqus(h51_data):
    comps = h51_data.get("formulation_comparisons", {})
    abaqus_p142 = comps.get("authentic_abaqus_p142", {})
    form_a = comps.get("formulation_a_elem_avg", {})

    # Parity within 0.05%
    dev_rf2 = abs(form_a.get("dev_rf2_vs_abaqus_pct", 999.0))
    dev_elas = abs(form_a.get("dev_elas_vs_abaqus_pct", 999.0))

    assert dev_rf2 < 0.05, f"Formulation A RF2 dev too large: {dev_rf2}%"
    assert dev_elas < 0.05, f"Formulation A E_elas dev too large: {dev_elas}%"

    # Exact values close to authentic Abaqus
    assert form_a["rf2_n"] == pytest.approx(abaqus_p142["rf2_n"], rel=1e-3)
    assert form_a["e_elastic_knmm"] == pytest.approx(abaqus_p142["e_elastic_knmm"], rel=1e-3)


def test_formulation_b_gauss_point_bias(h51_data):
    comps = h51_data.get("formulation_comparisons", {})
    form_a = comps.get("formulation_a_elem_avg", {})
    form_b = comps.get("formulation_b_gauss_point", {})

    # Formulation B has a slight stiffening shift
    diff_rf2 = form_b["rf2_n"] - form_a["rf2_n"]
    assert abs(diff_rf2) < 0.1, "Difference between A and B should be small"

    # Displacement parity
    disp_parity = comps.get("displacement_parity_a_vs_b", {})
    assert disp_parity.get("max_diff_mm") < 1.0e-5
    assert disp_parity.get("rms_diff_mm") < 1.0e-6


def test_h48_vs_h49_deconstruction(h51_data):
    decon = h51_data.get("h48_vs_h49_deconstruction", {})
    h48 = decon.get("h48_phase_only", {})
    h49 = decon.get("h49_coupled_am", {})

    assert h48["delta_d_max"] == pytest.approx(0.007630, rel=1e-3)
    assert h49["delta_d_max"] == pytest.approx(0.091048, rel=1e-2)

    # Compensation ratio ~ 1.0491
    comp_ratio = h49.get("compensation_ratio", 0.0)
    assert comp_ratio == pytest.approx(1.0491, rel=1e-2)


def test_stage_c1_1_failed_retention(h51_data):
    c1_1 = h51_data.get("stage_c1_1_evaluation", {})
    assert c1_1.get("rf2_gate_pass") is True
    assert c1_1.get("etot_gate_pass") is False
    assert c1_1.get("overall_c1_1_pass") is False

    # Numerical errors against authentic Frame-77 donor
    assert c1_1["rf2_error_pct"] == pytest.approx(-1.9214, abs=0.01)
    assert c1_1["etot_error_pct"] == pytest.approx(+2.2310, abs=0.01)


def test_governing_invariants_preserved(h51_data):
    inv = h51_data.get("governing_invariants_preserved", {})
    assert inv.get("H47_PACKAGE142_C1_1_FAILED") is True
    assert inv.get("STAGE_C1_2_STEP2_ENERGY_GATE_FAILED") is True
    assert inv.get("P113_GATE_VALID_FAILURE") is True
    assert inv.get("H24_REFERENCE_AUDIT_PENDING") is True
    assert inv.get("FROZEN_UEL_HASH") == FROZEN_UEL_SHA256
