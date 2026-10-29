# -*- coding: utf-8 -*-
"""
test_mode1_f1597_h53_c4_reference_decomposition.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Hypothesis: H53 - Continuous C4 Reference Verification and Mesh-Transfer Error Decomposition
Protocol Version: 2

Tests and verifies:
1. Package 145 execution authentication: PBS Job 1418732.mmaster02 completed Exit 0.
2. Deliverable presence and schema conformance of results/validation/h53_c4_reference_mesh_bias_audit.json.
3. Kinematic enforcement: target displacement u_RP = 0.001800312544 mm reached with zero error.
4. Physical phase-field qualification: unconstrained DOF 3 evolved from virgin state (d=0) to d_max=0.4991 at Step 1 Inc 76,
   localizing at crack-tip Node 2278 (x=0.0414 mm, y=0.0500 mm).
5. Controlled three-way comparison:
   A (Package 143 C3 Donor):     RF2 = 188.457042 N, E_tot = 0.208751950 mJ
   B (Package 145 C4 Reference): RF2 = 187.684400 N, E_tot = 0.213256680 mJ
   C (Package 142 C4 Transf):    RF2 = 194.121346 N, E_tot = 0.213832940 mJ
6. Energy error decomposition:
   Delta_mesh     = +2.1579% (+0.004505 mJ, 88.66% of total shift)
   Delta_transfer = +0.2702% (+0.000576 mJ, 11.34% of total shift)
   Delta_total    = +2.4340% (+0.005081 mJ, 100.00%)
7. Exact absolute energy identity:
   (E_C - E_A) == (E_B - E_A) + (E_C - E_B) within floating point epsilon (< 1e-12 mJ).
8. Classification and governance invariants strictly preserved:
   H53_C4_REFERENCE_QUALIFIED_MESH_BIAS_QUANTIFIED
   H47_PACKAGE142_C1_1_FAILED preserved (raw gate remains FAIL).
"""

import sys
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
AUDIT_JSON_PATH = REPO_ROOT / "results" / "validation" / "h53_c4_reference_mesh_bias_audit.json"


@pytest.fixture(scope="module")
def audit_data():
    if not AUDIT_JSON_PATH.exists():
        # Run generator
        from scripts.validation.evaluate_package145_h53_decomposition import main as gen_main
        gen_main()
    assert AUDIT_JSON_PATH.exists(), f"Audit JSON missing: {AUDIT_JSON_PATH}"
    with open(AUDIT_JSON_PATH, "r") as f:
        return json.load(f)


def test_schema_and_classification(audit_data):
    assert audit_data.get("schema") == 1
    assert audit_data.get("hypothesis") == "H53"
    assert audit_data.get("classification") == "H53_C4_REFERENCE_QUALIFIED_MESH_BIAS_QUANTIFIED"
    assert audit_data.get("package_145_authenticated") is True


def test_pbs_execution_receipt(audit_data):
    pbs = audit_data.get("pbs_execution", {})
    assert pbs.get("pbs_job_id") == "1418732.mmaster02"
    assert pbs.get("exit_code") == 0
    assert pbs.get("abaqus_completed") is True
    assert pbs.get("queue") == "normal_imfdfkmq"


def test_phase_field_physical_qualification(audit_data):
    pf = audit_data.get("phase_field_physical_qualification", {})
    assert pf.get("status") == "PASS"
    assert pf.get("unconstrained_dof3") is True
    assert pf.get("dof3_initial") == 0.0
    assert pf.get("dof3_max_step1") == pytest.approx(0.4991, abs=1e-4)
    assert pf.get("dof3_max_node_step1") == 2278
    assert pf.get("damage_monotonic_growth") is True
    assert pf.get("coupled_history_updates") is True


def test_target_kinematics(audit_data):
    comp = audit_data.get("three_way_comparison", {})
    ref_b = comp.get("reference_B_package145", {})
    target_u = comp.get("target_u_rp_mm")
    assert target_u == pytest.approx(0.0018003125442191958, rel=1e-9)
    assert ref_b.get("u_rp_mm") == pytest.approx(target_u, rel=1e-6)


def test_three_way_energetics_values(audit_data):
    comp = audit_data.get("three_way_comparison", {})
    A = comp.get("donor_A_package143", {})
    B = comp.get("reference_B_package145", {})
    C = comp.get("receiver_C_package142", {})

    # A: Package 143 Frame 77
    assert A.get("rf2_n") == pytest.approx(188.457042, rel=1e-5)
    assert A.get("e_elastic_mj") == pytest.approx(0.169634810, rel=1e-6)
    assert A.get("e_fracture_mj") == pytest.approx(0.039117135, rel=1e-6)
    assert A.get("e_total_mj") == pytest.approx(0.208751950, rel=1e-6)

    # B: Package 145 C4 Continuous Reference
    assert B.get("rf2_n") == pytest.approx(187.684400, rel=1e-5)
    assert B.get("e_elastic_mj") == pytest.approx(0.168943250, rel=1e-6)
    assert B.get("e_fracture_mj") == pytest.approx(0.044313430, rel=1e-6)
    assert B.get("e_total_mj") == pytest.approx(0.213256680, rel=1e-6)

    # C: Package 142 C4 Transferred
    assert C.get("rf2_n") == pytest.approx(194.121346, rel=1e-5)
    assert C.get("e_elastic_mj") == pytest.approx(0.174739550, rel=1e-6)
    assert C.get("e_fracture_mj") == pytest.approx(0.039093387, rel=1e-6)
    assert C.get("e_total_mj") == pytest.approx(0.213832940, rel=1e-6)


def test_energy_decomposition_and_identity(audit_data):
    dec = audit_data.get("decomposition", {})
    # Shifts
    assert dec.get("delta_mesh_pct") == pytest.approx(2.15793433, rel=1e-4)
    assert dec.get("delta_transfer_pct") == pytest.approx(0.27021897, rel=1e-4)
    assert dec.get("delta_total_pct") == pytest.approx(2.43398445, rel=1e-4)

    # Shares of total shift
    assert dec.get("mesh_share_of_total_shift_pct") == pytest.approx(88.6585, rel=1e-3)
    assert dec.get("transfer_share_of_total_shift_pct") == pytest.approx(11.3415, rel=1e-3)

    # Exact absolute identity: (E_B - E_A) + (E_C - E_B) == (E_C - E_A)
    assert dec.get("identity_passed") is True
    assert dec.get("identity_error_mj") < 1e-12


def test_governance_invariants(audit_data):
    gov = audit_data.get("governance_invariants", {})
    assert gov.get("H47_PACKAGE142_C1_1_FAILED") == "PRESERVED"
    assert gov.get("P113_GATE_VALID_FAILURE") == "PRESERVED"
    assert gov.get("STAGE_C1_2_STEP2_ENERGY_GATE_FAILED") == "PRESERVED"
    assert gov.get("H24_REFERENCE_AUDIT_PENDING") == "PRESERVED"
    assert gov.get("original_raw_gate_binding") is True
    assert gov.get("next_job_ready") is False
