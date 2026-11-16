# -*- coding: utf-8 -*-
"""
tests/unit/test_f1813_unified_synthesis.py
=========================================
Task F1813: Unit and regression tests for Method A / A.2 Unified Framework Synthesis
and Comprehensive Benchmark Assessment across Cases 1, 2, 3, and 5.
"""

import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_OUT_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "262_f1813_unified_synthesis"
RECEIPT_PATH = BASE_OUT_DIR / "PK_F1813_UNIFIED_SYNTHESIS_RECEIPT.json"
PROGRESSION_PATH = BASE_OUT_DIR / "campaign_progression_summary.json"
REPORT_PATH = REPO_ROOT / "docs" / "validation" / "F1813_UNIFIED_FRAMEWORK_SYNTHESIS_REPORT.md"
UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FRAMEWORK_PATH = REPO_ROOT / "scripts" / "remeshing" / "reusable_2d_adaptive_framework.py"

FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FRAMEWORK_SHA = "4276A5DC1AF22A6A117102D8C24492789E8AA4EBFD4AF079C58EE86DBEEC7C8B"

PHYSICAL_MESHES = {
    "case_1": {
        "path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_F1812_CASE_1_ADAPT_PHYS.inp",
        "file_sha256": "A138FF1DDC54E7F113784980D5B9D4E3365766C95ED5AD0A8F3AA926D8C74CBE",
        "body_sha256": "50CB4E3C826D66C7BDAB7FEBEADF5254CDEE33B709B214E9714CD776B3CE379E",
        "elements": 25461,
        "quads": 24770,
        "tris": 691
    },
    "case_2": {
        "path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case2/PK_F1812_CASE_2_ADAPT_PHYS.inp",
        "file_sha256": "FF6F61C307DA2202B1F798E50E42778F30B7872E680EE9232AB79DB801C47E37",
        "body_sha256": "5C7DD6B52DBBE716C823462E2EFBA37EAF3DF884862F2CAA4533F80FB7FFBFE1",
        "elements": 41438,
        "quads": 40432,
        "tris": 1006
    },
    "case_3": {
        "path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case3/PK_F1812_CASE_3_ADAPT_PHYS.inp",
        "file_sha256": "7DB1BB4B7911D604C78DA450B93EF5E47C306FB0DD2E1FC9CF9C15876D5CF095",
        "body_sha256": "08FA694A09033EC1F6BDE1C9150F539B3379BE7DF75CAAAD5DED3D42937FA2B4",
        "elements": 77779,
        "quads": 75708,
        "tris": 2071
    },
    "case_5": {
        "path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case5/PK_F1812_CASE_5_ADAPT_PHYS.inp",
        "file_sha256": "182B185B13B5EBBB2A19B8200D3CCA1344F64104EB10B2A6CFE20883ACEA3842",
        "body_sha256": "78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065",
        "elements": 15466,
        "quads": 15141,
        "tris": 325
    }
}


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def sha256_mesh_body(filepath):
    h = hashlib.sha256()
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip().startswith("**"):
                h.update(line.strip().encode("utf-8") + b"\n")
    return h.hexdigest().upper()


@pytest.fixture(scope="module")
def master_receipt():
    assert RECEIPT_PATH.exists(), "Missing master receipt: %s" % RECEIPT_PATH
    with open(RECEIPT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def progression_summary():
    assert PROGRESSION_PATH.exists(), "Missing progression summary: %s" % PROGRESSION_PATH
    with open(PROGRESSION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class TestF1813GovernanceInvariants:
    """Verifies frozen code invariants, zero new PBS submissions, and persistent master goal."""

    def test_frozen_uel_invariance(self):
        assert UEL_PATH.exists()
        assert sha256_file(UEL_PATH) == FROZEN_UEL_SHA

    def test_frozen_framework_invariance(self):
        assert FRAMEWORK_PATH.exists()
        assert sha256_file(FRAMEWORK_PATH) == FROZEN_FRAMEWORK_SHA

    def test_cumulative_pbs_submissions_preserved(self, master_receipt):
        assert master_receipt["cumulative_pbs_submissions"] == 35
        assert master_receipt["new_pbs_submissions"] == 0

    def test_master_goal_status_open(self, master_receipt):
        assert master_receipt["master_goal_status"] == "OPEN"

    def test_receipt_repo_relative_paths(self, master_receipt):
        for fig_key, fig_data in master_receipt["published_figures"].items():
            rel_p = fig_data["relative_path"]
            assert not rel_p.startswith("D:"), "Path must be repo-relative: %s" % rel_p
            assert not rel_p.startswith("C:"), "Path must be repo-relative: %s" % rel_p
            assert (REPO_ROOT / rel_p).exists(), "Figure not found at repo-relative path: %s" % rel_p


class TestF1813PhysicalMeshIntegrity:
    """Verifies existence, element counts, and cryptographic hashes of all 4 adapted physical meshes."""

    @pytest.mark.parametrize("case_id,info", PHYSICAL_MESHES.items())
    def test_physical_mesh_file_and_body_hashes(self, case_id, info):
        mesh_path = REPO_ROOT / info["path"]
        assert mesh_path.exists(), f"Missing physical mesh for {case_id}: {mesh_path}"
        actual_file_sha = sha256_file(mesh_path)
        assert actual_file_sha == info["file_sha256"], (
            f"File hash mismatch on {case_id}: expected {info['file_sha256']}, got {actual_file_sha}"
        )
        actual_body_sha = sha256_mesh_body(mesh_path)
        assert actual_body_sha == info["body_sha256"], (
            f"Body hash mismatch on {case_id}: expected {info['body_sha256']}, got {actual_body_sha}"
        )

    @pytest.mark.parametrize("case_id,info", PHYSICAL_MESHES.items())
    def test_physical_mesh_element_counts(self, case_id, info):
        mesh_path = REPO_ROOT / info["path"]
        quad_elements = 0
        tri_elements = 0
        in_elements = False
        with open(mesh_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith("**"):
                    continue
                if l.startswith("*"):
                    upline = l.upper()
                    in_elements = upline.startswith("*ELEMENT") and "OUTPUT" not in upline
                    continue
                if in_elements:
                    parts = [p.strip() for p in l.split(",") if p.strip()]
                    try:
                        [int(p) for p in parts]
                    except ValueError:
                        continue
                    if len(parts) == 5:
                        quad_elements += 1
                    elif len(parts) == 4:
                        tri_elements += 1

        total_elements = quad_elements + tri_elements
        assert total_elements == info["elements"], (
            f"Element count mismatch for {case_id}: expected {info['elements']}, counted {total_elements}"
        )
        assert quad_elements == info["quads"], (
            f"Quad count mismatch for {case_id}: expected {info['quads']}, counted {quad_elements}"
        )
        assert tri_elements == info["tris"], (
            f"Tri count mismatch for {case_id}: expected {info['tris']}, counted {tri_elements}"
        )


class TestF1813ScientificGateCompliance:
    """Verifies that all 4 scientific resolution gates evaluate to PASS and meet quality metrics."""

    def test_all_four_scientific_gates_pass(self, master_receipt):
        summary = master_receipt["scientific_gates_summary"]
        assert summary["all_four_scientific_gates_pass"] is True

    def test_case1_gate_compliance(self, master_receipt):
        c1 = master_receipt["scientific_gates_summary"]["case_1"]
        assert c1["elements"] == 25461
        assert c1["elements"] <= 30000
        assert c1["quad_fraction_pct"] >= 90.0
        assert c1["max_aspect_ratio"] <= 4.0
        assert c1["min_signed_jacobian"] > 0.0
        assert c1["coarsening_ratio"] >= 2.0
        assert c1["scientific_gate"] == "PASS"

    def test_case2_gate_compliance(self, master_receipt):
        c2 = master_receipt["scientific_gates_summary"]["case_2"]
        assert c2["elements"] == 41438
        assert c2["elements"] <= 80000
        assert c2["quad_fraction_pct"] >= 90.0
        assert c2["max_aspect_ratio"] <= 4.0
        assert c2["min_signed_jacobian"] > 0.0
        assert c2["scientific_gate"] == "PASS"

    def test_case3_gate_compliance(self, master_receipt):
        c3 = master_receipt["scientific_gates_summary"]["case_3"]
        assert c3["elements"] == 77779
        assert c3["elements"] <= 80000
        assert c3["quad_fraction_pct"] >= 90.0
        assert c3["max_aspect_ratio"] <= 4.0
        assert c3["min_signed_jacobian"] > 0.0
        assert c3["scientific_gate"] == "PASS"

    def test_case5_gate_compliance(self, master_receipt):
        c5 = master_receipt["scientific_gates_summary"]["case_5"]
        assert c5["elements"] == 15466
        assert c5["elements"] <= 30000
        assert c5["quad_fraction_pct"] >= 90.0
        assert c5["max_aspect_ratio"] <= 4.0
        assert c5["min_signed_jacobian"] > 0.0
        assert c5["coarsening_ratio"] >= 2.0
        assert c5["scientific_gate"] == "PASS"


class TestF1813GapAnalysisDocumentation:
    """Verifies that all 4 declared gaps are present and transparently structured in the receipt."""

    def test_gap_analysis_count_and_structure(self, master_receipt):
        gaps = master_receipt["gap_analysis"]
        assert len(gaps) == 4
        gap_ids = [g["gap_id"] for g in gaps]
        assert "GAP_01_GATE06_COARSENING_SHORTFALL" in gap_ids
        assert "GAP_02_GATE07_BUDGET_REDEFINITION" in gap_ids
        assert "GAP_03_LARGE_DONOR_ODB_PROVENANCE" in gap_ids
        assert "GAP_04_UNEXECUTED_COUPLED_FRACTURE_VALIDATION" in gap_ids

    def test_gap_analysis_provenance_and_scratch(self, master_receipt):
        gaps = {g["gap_id"]: g for g in master_receipt["gap_analysis"]}
        g3 = gaps["GAP_03_LARGE_DONOR_ODB_PROVENANCE"]
        assert "scratch_location" in g3
        assert "/scratch9/pr21vyci/" in g3["scratch_location"]


class TestF1813CampaignProgressionSummary:
    """Verifies that the campaign progression across F1808 -> F1809 -> F1811 -> F1812 is complete."""

    def test_campaign_progression_cases_and_stages(self, progression_summary):
        cases = ["case_1", "case_2", "case_3", "case_5"]
        stages = ["F1808", "F1809", "F1811", "F1812"]
        for cid in cases:
            assert cid in progression_summary
            stage_names = [s["task"] for s in progression_summary[cid]]
            assert stage_names == stages


class TestF1813PublicationFiguresAndReports:
    """Verifies that all published synthesis figures and reports exist with non-trivial size."""

    def test_published_figures_exist_and_sizes(self, master_receipt):
        for fig_key, fig_data in master_receipt["published_figures"].items():
            fig_path = REPO_ROOT / fig_data["relative_path"]
            assert fig_path.exists(), "Missing published figure: %s" % fig_path
            actual_size = fig_path.stat().st_size
            assert actual_size > 10000, f"Figure {fig_path} unexpectedly small: {actual_size} bytes"
            actual_sha = sha256_file(fig_path)
            assert actual_sha == fig_data["sha256"], (
                f"Hash mismatch on figure {fig_key}: expected {fig_data['sha256']}, got {actual_sha}"
            )

    def test_report_exists_and_size(self):
        assert REPORT_PATH.exists()
        assert REPORT_PATH.stat().st_size > 15000
