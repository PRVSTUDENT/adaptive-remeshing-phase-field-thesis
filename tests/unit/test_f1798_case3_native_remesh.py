# -*- coding: utf-8 -*-
"""
tests/unit/test_f1798_case3_native_remesh.py
Task F1798: Case 3 Native-MISESERI Causal Baseline Remeshing Test Suite.

Verifies:
1. Authentic Case 3 Initial-State Recovery Donor Qualification Receipt:
   - PK_SEC43_COARSE_RECOVERY.odb (1,498,400 bytes, SHA-256: D3CF03DF...)
   - 3,923 physical elements (CPE3, CPE4) and 4,040 nodes
   - Step: RECOVERY_STEP, procedure *STATIC, frame 1 (t = 1.0 s)
   - Active MISESERI field with all 3,923 elements populated (range: [0.000535, 5.1983] MPa)
   - Status: QUALIFIED_AUTHENTIC_INITIAL_STATE_NATIVE_DONOR
2. Fresh Native Remeshing Execution and Physical Mesh Quality:
   - Physical mesh INP: PK_F1798_CASE_3_ADAPT_PHYS.inp (1,934,333 bytes)
   - Mesh body SHA-256: 13B6770FC30025CBB1D2CC5ACC1D50F98CE6D5F58F5300BB70158A39E232F7B6
   - 26,891 total elements (26,145 quads = 97.23% quad fraction, 746 tris)
   - Positive signed Jacobians: min det(J) = 7.97e-4 > 0, zero negative Jacobians (GATE PASS)
   - Aspect ratio: max AR = 2.706 <= 4.0, median AR = 1.232, 0 violations > 4.0 (GATE PASS)
3. Spatial Resolution and Far-Field Coarsening:
   - Primary corridor (notch to central hole): 5,888 elements, mean h = 0.295 mm, 57.05% <= l0
   - Secondary corridor (hole to boundary): 890 elements, mean h = 0.627 mm, 1.24% <= l0
   - Far-field background: 2,074 elements, mean h = 0.924 mm
   - Far-to-core coarsening ratio: 3.13x >= 2.0x (GATE PASS)
4. Efficiency Comparison against Historical Baselines:
   - Current F1798: 26,891 elements (-7.06% vs historical F1741 explosion of 28,933)
   - Relative to F1780 envelope benchmark (10,064) and literature target (12,168)
5. Governance Invariants:
   - Bitwise frozen production UEL (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6)
   - Single shared framework (99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D)
   - Zero new PBS submissions (cumulative count strictly preserved at 35)
   - MASTER_GOAL_STATUS strictly remains OPEN
"""

import os
import sys
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FRAMEWORK_HASH = "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D"
F1798_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "248_f1798_case3_native_remesh"


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


class TestF1798DonorQualification:
    """Verifies Case 3 authentic initial-state recovery donor qualification."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.receipt_path = F1798_DIR / "PK_F1798_CASE3_DONOR_QUALIFICATION_RECEIPT.json"
        assert self.receipt_path.exists(), f"Missing receipt: {self.receipt_path}"
        with open(self.receipt_path, "r") as f:
            self.data = json.load(f)

    def test_donor_provenance_and_hash(self):
        assert self.data["donor_file"] == "PK_SEC43_COARSE_RECOVERY.odb"
        assert self.data["donor_sha256"] == "D3CF03DF60ECBA928E1D73E1C8EDB30029FB327F2B6503C227F46E458116C20C"
        assert self.data["donor_size_bytes"] == 1498400
        assert self.data["qualification_status"] == "QUALIFIED_AUTHENTIC_INITIAL_STATE_NATIVE_DONOR"

    def test_donor_topology_and_step(self):
        topo = self.data["mesh_topology"]
        assert topo["num_nodes"] == 4040
        assert topo["num_elements"] == 3923
        assert set(topo["element_types"]) == {"CPE3", "CPE4"}
        assert self.data["step_name"] == "RECOVERY_STEP"
        assert self.data["frame_index"] == 1
        assert self.data["frame_time"] == 1.0
        assert self.data["is_causal_preanalysis"] is True

    def test_donor_miseseri_field(self):
        assert self.data["indicator_field"] == "MISESERI"
        assert self.data["num_elements_with_indicator"] == 3923
        stats = self.data["miseseri_stats"]
        assert stats["nonzero_count"] == 3923
        assert pytest.approx(stats["min_mpa"], rel=1e-3) == 0.000535
        assert pytest.approx(stats["max_mpa"], rel=1e-3) == 5.1983
        assert pytest.approx(stats["mean_mpa"], rel=1e-2) == 0.05985


class TestF1798NativeRemeshingReceipt:
    """Verifies fresh native RemeshingRule and adaptiveRemesh() execution results."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.receipt_path = F1798_DIR / "PK_F1798_CASE3_NATIVE_REMESH_RECEIPT.json"
        assert self.receipt_path.exists(), f"Missing receipt: {self.receipt_path}"
        with open(self.receipt_path, "r") as f:
            self.data = json.load(f)

    def test_physical_mesh_file_and_hashes(self):
        phys = self.data["physical_mesh"]
        inp_path = F1798_DIR / phys["filename"]
        assert inp_path.exists()
        assert inp_path.stat().st_size == phys["size_bytes"]
        assert sha256_file(inp_path) == phys["sha256"]
        assert phys["mesh_body_sha256"] == "13B6770FC30025CBB1D2CC5ACC1D50F98CE6D5F58F5300BB70158A39E232F7B6"

    def test_mesh_quality_metrics(self):
        phys = self.data["physical_mesh"]
        assert phys["total_elements"] == 26891
        assert phys["total_nodes"] == 26961
        assert phys["quad_count"] == 26145
        assert phys["tri_count"] == 746
        assert phys["quad_percent"] >= 90.0
        assert pytest.approx(phys["quad_percent"], rel=1e-3) == 97.226
        # Positive Jacobian requirement
        assert phys["min_det_j"] > 0.0
        assert phys["non_positive_jacobians"] == 0
        assert phys["zero_negative_jacobians"] is True
        # Aspect ratio requirement
        assert phys["max_aspect_ratio"] <= 4.0
        assert phys["ar_violations_gt_4"] == 0

    def test_spatial_resolution_and_coarsening(self):
        sp = self.data["spatial_resolution"]
        assert sp["l0_mm"] == 0.285
        # Primary corridor
        p = sp["primary_corridor_notch_to_hole"]
        assert p["count"] == 5888
        assert p["pct_le_l0"] > 50.0  # 57.05%
        # Secondary corridor
        s = sp["secondary_corridor_hole_to_boundary"]
        assert s["count"] == 890
        assert s["pct_le_l0"] < 10.0  # Demonstrates pre-crack state lacks secondary refinement
        # Far field coarsening
        assert sp["far_to_core_coarsening_ratio"] >= 2.0  # 3.13x

    def test_efficiency_metrics(self):
        eff = self.data["efficiency_comparison"]
        assert eff["current_f1798_elements"] == 26891
        assert eff["historical_f1741_explosion"]["elements"] == 28933
        assert eff["historical_f1741_explosion"]["reduction_percent"] > 0.0  # 7.06% reduction
        assert eff["historical_f1780_benchmark"]["elements"] == 10064

    def test_quality_gates(self):
        gates = self.data["quality_gates"]
        assert gates["GATE_01_NATIVE_EXECUTION_EXIT_0"] == "PASS"
        assert gates["GATE_02_QUAD_FRACTION_GE_90_PCT"] == "PASS"
        assert gates["GATE_03_ZERO_NEGATIVE_JACOBIANS"] == "PASS"
        assert gates["GATE_04_ASPECT_RATIO_LE_4"] == "PASS"
        # Scientific finding: Gate 5 fails causally for single-pass initial linear elasticity
        assert gates["GATE_05_PRIMARY_CORRIDOR_RESOLUTION"] == "FAIL"
        assert gates["GATE_06_FAR_FIELD_COARSENING"] == "PASS"
        # Gate 7 fails because single-pass linear recovery unguided element count is 26,891
        assert gates["GATE_07_EFFICIENCY_VS_HISTORICAL_EXPLOSION"] == "FAIL"


class TestF1798GovernanceAndInvariants:
    """Verifies frozen production UEL hash, framework hash, report, and PBS constraints."""

    def test_frozen_production_uel_hash(self):
        uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
        assert uel_path.exists()
        assert sha256_file(uel_path) == FROZEN_UEL_HASH

    def test_framework_source_hash(self):
        fw_path = REPO_ROOT / "scripts" / "remeshing" / "reusable_2d_adaptive_framework.py"
        assert fw_path.exists()
        assert sha256_file(fw_path) == FRAMEWORK_HASH

    def test_report_artifact_exists_and_content(self):
        report_path = REPO_ROOT / "docs" / "validation" / "F1798_CASE3_NATIVE_MISESERI_CAUSAL_REMESHING_REPORT.md"
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "Task F1798" in content
        assert "HND-F1798-CASE3-NATIVE-REMESH-001" in content
        assert "PK_SEC43_COARSE_RECOVERY.odb" in content
        assert "26,891" in content
        assert "97.23%" in content
        assert "MASTER_GOAL_STATUS = OPEN" in content

    def test_zero_new_pbs_submissions_and_governance(self):
        task_json = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
        assert task_json.exists()
        with open(task_json, "r") as f:
            data = json.load(f)
        assert data["task_id"] in (
            "F1797-CASE2-ALL-FRAME-MISESERI-AND-RECOVERY-PROVENANCE-QUALIFICATION",
            "F1798-CASE3-NATIVE-MISESERI-CAUSAL-BASELINE-REMESHING",
            "F1799-CASE3-CAUSAL-CONFIG-AND-PHYSICAL-DONOR-CONTROLLED-REMESH",
            "F1800-CASE3-PRECRITICAL-NATIVE-MISESERI-SCALE-AND-CAUSAL-REMESH-TEST",
            "F1801-CASE3-NATIVE-MISESERI-ERROR-TARGET-EFFICIENCY-TEST",
            "F1802-CASE3-METHOD-A2-EVOLVING-RECOVERY-DONOR-QUALIFICATION-AND-CAUSAL-REMESH",
            "F1803-CASE3-STATE2-DEGRADED-MODULUS-FIDELITY-NATIVE-REMESH",
            "F1804-CASE2-DISTAL-DEGRADED-MODULUS-RECOVERY-REMESH",
            "F1805-CASE2-OUTERMOST-DISTAL-NATIVE-MISESERI-TARGET-SENSITIVITY",
            "F1806-CASE2-OUTERMOST-DISTAL-NATIVE-MISESERI-TARGET-1P8PCT"
        )
        assert data["max_new_pbs_submissions"] == 0
        assert data["submissions_consumed"] == 0
        assert data["cumulative_pbs_submissions"] == 35
        assert data["master_goal_status"] == "OPEN"
