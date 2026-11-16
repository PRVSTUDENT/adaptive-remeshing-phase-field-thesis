# -*- coding: utf-8 -*-
"""
tests/unit/test_f1797_case2_all_frame_and_provenance.py
Task F1797: Case 2 All-Frame MISESERI and Recovery Provenance Qualification Test Suite.

Verifies:
1. All-frame scan receipt of PK_HOLE_COARSE_JOB1.odb:
   - Exactly 338 frames in Step-2 scanned elementwise.
   - 0 nonzero values found across all frames (min = 0.0, max = 0.0).
2. Direct element-label and integration-point multiplicity receipt:
   - 2,906 unique element labels.
   - Multiplicity exactly 2 across all elements (WHOLE_ELEMENT section evaluation).
   - Identical bitwise blocks (100.000% parity).
3. Nonzero recovery donor provenance receipt:
   - 10 candidates audited.
   - All use 2,935 elements (incompatible with 2,906-element production mesh).
   - All disqualified from Method A later-donor status.
4. Comprehensive 39-candidate catalog:
   - 39 records with existence, size, SHA-256, classification, and scientific rationale.
   - Complete breakdown matching evidentiary report.
5. Governance invariants: frozen UEL hash, framework hash, zero new PBS submissions (cumulative 35),
   and report existence.
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
F1797_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "247_f1797_case2_all_frame_provenance"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


class TestF1797AllFrameScan:
    """Verifies all-frame scan receipt for PK_HOLE_COARSE_JOB1.odb."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.receipt_path = F1797_DIR / "PK_F1797_CASE2_COARSE_JOB1_ALL_FRAME_SCAN.json"
        assert self.receipt_path.exists(), f"Receipt missing: {self.receipt_path}"
        with open(self.receipt_path, "r") as f:
            self.data = json.load(f)

    def test_all_frame_scan_integrity(self):
        assert self.data["step_name"] == "Step-2"
        assert self.data["total_frames_audited"] == 338
        assert self.data["all_frames_identically_zero"] is True
        assert self.data["total_nonzero_values_across_all_frames"] == 0

    def test_per_frame_records(self):
        records = self.data["frame_records"]
        assert len(records) == 338
        for r in records:
            assert r["has_miseseri"] is True
            assert r["total_values"] == 2906
            assert r["finite_count"] == 2906
            assert r["nonfinite_count"] == 0
            assert r["nonzero_count"] == 0
            assert r["min"] == 0.0
            assert r["max"] == 0.0


class TestF1797MultiplicityReceipt:
    """Verifies integration-point and element-label multiplicity proof."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.receipt_path = F1797_DIR / "PK_F1797_CASE2_PREANALYSIS_MULTIPLICITY_RECEIPT.json"
        assert self.receipt_path.exists(), f"Receipt missing: {self.receipt_path}"
        with open(self.receipt_path, "r") as f:
            self.data = json.load(f)

    def test_multiplicity_structure(self):
        assert self.data["step_name"] == "Step-1"
        assert self.data["frame_index"] == 10
        assert self.data["variable"] == "MISESERI"
        res = self.data["results"]
        assert res["total_field_values"] == 5812
        assert res["unique_element_labels_count"] == 2906
        assert res["multiplicity_distribution"] == {"2": 2906}
        assert res["all_blocks_identical"] is True

    def test_sample_multiplicity_details(self):
        details = self.data["results"]["sample_multiplicity_details"]
        assert details["elem_min_label"] == 1
        assert details["elem_max_label"] == 2906
        assert "WHOLE_ELEMENT" in details["position_types"]


class TestF1797RecoveryProvenanceReceipt:
    """Verifies provenance, ancestry, and mesh compatibility of candidate recovery ODBs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.receipt_path = F1797_DIR / "PK_F1797_CASE2_RECOVERY_DONOR_PROVENANCE_RECEIPT.json"
        assert self.receipt_path.exists(), f"Receipt missing: {self.receipt_path}"
        with open(self.receipt_path, "r") as f:
            self.data = json.load(f)

    def test_provenance_records_count_and_admissibility(self):
        assert len(self.data) == 10
        for rec in self.data:
            assert rec["admissible_as_method_a_later_donor"] is False
            assert len(rec["exclusion_reason"]) > 20
            # All audited recovery candidates use the non-standard 2,935-element mesh
            assert rec["probe_info"]["num_elements"] == 2935

    def test_usdfld_and_historical_classifications(self):
        assessments = {r["path"]: r["assessment"] for r in self.data}
        assert assessments["runs/f1683_recovery_candidate_b/PK_HOLE_RECOVERY_B.odb"] == "AUXILIARY_USDFLD_DEGRADED_ELASTIC"
        assert assessments["runs/f1684_multistep_recovery/PK_HOLE_MULTISTEP_RECOVERY.odb"] == "AUXILIARY_USDFLD_DEGRADED_ELASTIC"
        assert assessments["PK_HOLE_COUPLED_RECOVERY.odb"] == "HISTORICAL_OCT_STAGE_RECOVERY_EXPERIMENT"
        assert assessments["PK_HOLE_RECOVERY_SOLVE.odb"] == "PREFRACTURE_LINEAR_ELASTIC_AUXILIARY"


class TestF1797ComprehensiveCatalog:
    """Verifies complete 39-candidate catalog with individual rationales."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.receipt_path = F1797_DIR / "PK_F1797_CASE2_39_CANDIDATE_FULL_CATALOG.json"
        assert self.receipt_path.exists(), f"Receipt missing: {self.receipt_path}"
        with open(self.receipt_path, "r") as f:
            self.data = json.load(f)

    def test_catalog_completeness(self):
        assert len(self.data) == 39
        for rec in self.data:
            assert "path" in rec
            assert "exists" in rec
            assert "size_bytes" in rec
            assert "sha256" in rec
            assert "classification_status" in rec
            assert len(rec["accept_reject_rationale"]) > 10

    def test_catalog_category_counts(self):
        statuses = [r["classification_status"] for r in self.data]
        from collections import Counter
        counts = Counter(statuses)
        assert counts["ACCEPTED_AS_PREFRACTURE_NATIVE_DONOR"] == 1
        assert counts["REJECTED_ZERO_MISESERI_IN_ALL_FRAMES"] == 1
        assert counts["REJECTED_SYNTHETIC_DAMAGE_ENVELOPE"] == 1
        assert counts["REJECTED_NON_CASE2_BENCHMARK"] == 15
        assert counts["REJECTED_MISSING_ON_DISK"] == 11
        assert counts["REJECTED_HISTORICAL_NONSTANDARD_MESH"] == 4
        assert counts["REJECTED_AUXILIARY_USDFLD_MODEL"] == 4
        assert counts["REJECTED_DUPLICATE_PREFRACTURE_ELASTIC"] == 2
        assert sum(counts.values()) == 39


class TestF1797GovernanceAndInvariants:
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
        report_path = REPO_ROOT / "docs" / "validation" / "F1797_CASE2_ALL_FRAME_MISESERI_AND_PROVENANCE_REPORT.md"
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "Task F1797" in content
        assert "HND-F1797-ALL-FRAME-PROVENANCE-001" in content
        assert "338" in content
        assert "2,906" in content
        assert "5,812" in content
        assert "Table 3: Exhaustive 39-Candidate ODB Audit Catalog" in content
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
            "F1803-CASE3-STATE2-DEGRADED-MODULUS-FIDELITY-NATIVE-REMESH"
        )
        assert data["max_new_pbs_submissions"] == 0
        assert data["submissions_consumed"] == 0
        assert data["cumulative_pbs_submissions"] == 35
        assert data["master_goal_status"] == "OPEN"
