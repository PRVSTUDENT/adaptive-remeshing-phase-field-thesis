# -*- coding: utf-8 -*-
"""
tests/unit/test_f1796_case2_evolving_native_miseseri.py
Task F1796: Case 2 Evolving Native-MISESERI Causal Indicator Qualification Test Suite.

Verifies:
1. Machine-readable ODB inventory receipt and definitive technical blocker conclusion.
2. Forensic evaluation of existing Case 2 candidate ODBs:
   - PK_HOLE_METHOD_A_PREANALYSIS.odb is the sole authentic prefracture native donor.
   - PK_HOLE_COARSE_JOB1.odb has MISESERI == 0.0 across all frames due to UEL black-box formulation.
   - Disqualification of synthetic envelopes, non-Case-2 files, and auxiliary USDFLD models.
3. Analytical verification of Kirsch solution sign convention under remote vertical tension.
4. Resolution of F1795 errata (physical element count vs IP values, replay log inventory).
5. Governance invariants: frozen UEL hash, framework hash, zero new PBS jobs, cumulative 35,
   and MASTER_GOAL_STATUS = OPEN.
"""

import os
import sys
import json
import math
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine,
    OffAxisHoleMode1Adapter,
    FROZEN_UEL_SHA256
)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


class TestF1796InventoryReceipt:
    """Verifies the machine-readable ODB inventory receipt for Task F1796."""

    @pytest.fixture
    def inventory_receipt(self):
        receipt_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "246_f1796_case2_evolving_native_miseseri" / "PK_F1796_CASE2_ODB_INVENTORY_RECEIPT.json"
        assert receipt_path.exists(), f"Inventory receipt must exist: {receipt_path}"
        with open(receipt_path, "r") as f:
            return json.load(f)

    def test_receipt_metadata_and_governance(self, inventory_receipt):
        assert inventory_receipt["task_id"] == "F1796-CASE2-EVOLVING-NATIVE-MISESERI-CAUSAL-INDICATOR-QUALIFICATION"
        assert inventory_receipt["correlation_id"] == "HND-F1796-EVOLVING-INDICATOR-001"
        gov = inventory_receipt["governance"]
        assert gov["frozen_uel_sha256"] == FROZEN_UEL_SHA256
        assert gov["cumulative_pbs_submissions"] == 35
        assert gov["new_pbs_submissions_under_f1796"] == 0
        assert gov["master_goal_status"] == "OPEN"

    def test_f1795_errata_resolution_metadata(self, inventory_receipt):
        errata = inventory_receipt["f1795_errata_resolution"]
        assert errata["kirsch_sign_convention"] == "CORRECTED_TO_REMOTE_VERTICAL_TENSION"
        assert errata["execution_log_inventory"] == "CORRECTED_TO_ABAQUS_JOURNAL_RPY"
        counts = errata["field_value_vs_element_count"]
        assert counts["num_physical_elements"] == 2906
        assert counts["num_elements_with_indicator"] == 2906
        assert counts["total_integration_point_values"] == 5812

    def test_definitive_technical_blocker_conclusion(self, inventory_receipt):
        conclusion = inventory_receipt["definitive_technical_blocker_conclusion"]
        assert conclusion["later_state_native_miseseri_available"] is False
        assert conclusion["directive_action"] == "STOP_EXPERIMENT_WITHOUT_FABRICATION_OR_METHOD_C_RECONSTRUCTION"
        assert "Abaqus native stress recovery error (MISESERI)" in conclusion["justification"]


class TestF1796ForensicDonorEvaluation:
    """Verifies the forensic status of all inspected Case 2 candidate ODBs."""

    def test_prefracture_native_donor_exists_and_valid(self):
        pre_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_METHOD_A_PREANALYSIS.odb"
        assert pre_path.exists()
        assert pre_path.stat().st_size == 2883480
        assert sha256_file(pre_path) == "C698A4B7AB23761C731BBC73E0F2C00166BF53116BB8CBC31439D89270D38FE4"

    def test_coarse_job1_exists_and_proven_zero_miseseri(self):
        coarse_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_COARSE_JOB1.odb"
        assert coarse_path.exists()
        assert coarse_path.stat().st_size == 518169932

        # Check JSON audit result proving zero MISESERI across all frames
        audit_path = REPO_ROOT / "runs" / "case2_odb_audit_results.json"
        assert audit_path.exists()
        with open(audit_path, "r") as f:
            audit_data = json.load(f)

        found_coarse = False
        for item in audit_data:
            if "PK_HOLE_COARSE_JOB1.odb" in item["path"]:
                found_coarse = True
                probe = item["probe"]
                assert probe["error"] is None
                assert probe["steps"]["Step-1"]["has_any_nonzero_miseseri"] is False
                assert probe["steps"]["Step-2"]["has_any_nonzero_miseseri"] is False
                break
        assert found_coarse, "Coarse Job 1 must be present in audit results"

    def test_synthetic_envelope_disqualification(self):
        audit_path = REPO_ROOT / "runs" / "case2_odb_audit_results.json"
        with open(audit_path, "r") as f:
            audit_data = json.load(f)

        found_env = False
        for item in audit_data:
            if "PK_F1779_CASE2_ENVELOPE.odb" in item["path"]:
                found_env = True
                probe = item["probe"]
                # Synthetic envelope contains artificial frame 9999
                step2 = probe["steps"]["Step-2"]
                frame_ids = [f["frame_id"] for f in step2["frames"]]
                assert 9999 in frame_ids
                break
        assert found_env, "PK_F1779_CASE2_ENVELOPE must be audited"

    def test_non_case2_artifacts_classified(self):
        audit_path = REPO_ROOT / "runs" / "case2_odb_audit_results.json"
        with open(audit_path, "r") as f:
            audit_data = json.load(f)

        for item in audit_data:
            if "SEC43_STATE1_INIT.odb" in item["path"]:
                probe = item["probe"]
                # 3923 elements corresponds to Case 3 (120x65 mm plate), not Case 2 (2906 elements)
                assert probe["steps"]["RECOVERY_STEP"]["frames"][1]["miseseri_stats"]["count"] == 3923


class TestF1796KirschElastomechanics:
    """Verifies the exact analytical Kirsch stress field for remote vertical tension."""

    def test_kirsch_remote_vertical_tension_boundary_conditions(self):
        sigma_0 = 100.0  # remote tensile stress in MPa
        a = 0.10         # hole radius in mm

        # Polar coordinates centered at hole:
        # theta = 0: along positive x-axis (equator, perpendicular to remote tension)
        # theta = pi/2: along positive y-axis (crown, parallel to remote tension)

        def kirsch_stresses(r, theta):
            term1_rr = (sigma_0 / 2.0) * (1.0 - (a / r) ** 2)
            term2_rr = (sigma_0 / 2.0) * (1.0 - 4.0 * (a / r) ** 2 + 3.0 * (a / r) ** 4) * math.cos(2.0 * theta)
            sigma_rr = term1_rr - term2_rr

            term1_tt = (sigma_0 / 2.0) * (1.0 + (a / r) ** 2)
            term2_tt = (sigma_0 / 2.0) * (1.0 + 3.0 * (a / r) ** 4) * math.cos(2.0 * theta)
            sigma_tt = term1_tt + term2_tt

            tau_rt = (sigma_0 / 2.0) * (1.0 + 2.0 * (a / r) ** 2 - 3.0 * (a / r) ** 4) * math.sin(2.0 * theta)
            return sigma_rr, sigma_tt, tau_rt

        # 1. Traction-free hole boundary at r = a
        for theta_deg in [0, 30, 45, 60, 90, 135, 180]:
            th = math.radians(theta_deg)
            s_rr, s_tt, t_rt = kirsch_stresses(a, th)
            assert abs(s_rr) < 1e-10, f"sigma_rr must be zero at r=a (theta={theta_deg})"
            assert abs(t_rt) < 1e-10, f"tau_rt must be zero at r=a (theta={theta_deg})"

        # 2. Stress concentration at hole equator theta = 0 (perpendicular to remote tension)
        s_rr_eq, s_tt_eq, t_rt_eq = kirsch_stresses(a, 0.0)
        assert abs(s_tt_eq - 3.0 * sigma_0) < 1e-10, "Kt must be exactly 3.0 at hole equator"

        # 3. Stress at hole crown theta = pi/2 (parallel to remote tension)
        s_rr_cr, s_tt_cr, t_rt_cr = kirsch_stresses(a, math.pi / 2.0)
        assert abs(s_tt_cr - (-1.0 * sigma_0)) < 1e-10, "sigma_thetatheta must be -sigma_0 (compressive) at hole crown"

        # 4. Algebraic perturbation decay into distal ligament (r = 0.35 mm, theta = 0)
        r_distal = 0.35
        s_rr_dist, s_tt_dist, _ = kirsch_stresses(r_distal, 0.0)
        delta_sigma_tt = s_tt_dist - sigma_0
        expected_perturbation_pct = (delta_sigma_tt / sigma_0) * 100.0
        assert 5.0 <= expected_perturbation_pct <= 5.15, "Perturbation must drop to ~5.08% at r=0.35 mm"


class TestF1796GovernanceAndInvariants:
    """Verifies mandatory research governance invariants for Task F1796."""

    def test_production_uel_bitwise_frozen(self):
        uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
        assert uel_path.exists()
        assert sha256_file(uel_path) == FROZEN_UEL_SHA256

    def test_unified_framework_hash(self):
        fw_path = REPO_ROOT / "scripts" / "remeshing" / "reusable_2d_adaptive_framework.py"
        assert fw_path.exists()
        assert sha256_file(fw_path) == "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D"

    def test_active_task_and_session_governance(self):
        task_path = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
        with open(task_path, "r") as f:
            task = json.load(f)
        assert task["task_id"] in [
            "F1796-CASE2-EVOLVING-NATIVE-MISESERI-CAUSAL-INDICATOR-QUALIFICATION",
            "F1797-CASE2-ALL-FRAME-MISESERI-AND-RECOVERY-PROVENANCE-QUALIFICATION",
            "F1798-CASE3-NATIVE-MISESERI-CAUSAL-BASELINE-REMESHING"
        ]
        assert task["classification"] == "ADAPTIVE_REMESHING_RESEARCH_ONLY"
        assert task["max_new_pbs_submissions"] == 0
        assert task["submissions_consumed"] == 0
        assert task["cumulative_pbs_submissions"] == 35
        assert task["master_goal_status"] == "OPEN"
