"""
Unit test suite for Task F1810: Method A.2 Evidence Completion and Verification Freeze.
Validates existence and cryptographic SHA-256 integrity of:
1. Four physical adapted meshes (.inp)
2. Two multi-state recovery donor ODBs (.odb)
3. All 14 published images and vector PDFs
4. Case 2 outer ligament resolution and min-size clamping audit
5. Case 3 dual-corridor resolution
6. Bitwise governance invariants (UEL, framework, PBS count, goal status)
"""

import hashlib
import json
import os
import pytest

TOP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FRAMEWORK_SHA = "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D"

EXPECTED_MESH_HASHES = {
    "case1": {
        "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case1/PK_F1809_CASE_1_ADAPT_PHYS.inp",
        "size": 1011306,
        "sha256": "B18339EA2B4D69932851CAE66483779D258711CB9961D752598D2155A72C57A3",
    },
    "case2": {
        "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_F1809_CASE_2_ADAPT_PHYS.inp",
        "size": 9082011,
        "sha256": "DFC5F4DA3026BFCF0F17F09A958A30481E3AEB1F57ADBF7311DD387E1BC6DA7A",
    },
    "case3": {
        "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/PK_F1809_CASE_3_ADAPT_PHYS.inp",
        "size": 5572384,
        "sha256": "4B1E5F42BA7899D33473DB6960AA0C1FBEF86742233629B00BA3BC5AE5AAA6DD",
    },
    "case5": {
        "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case5/PK_F1809_CASE_5_ADAPT_PHYS.inp",
        "size": 1127961,
        "sha256": "686A61C21ABBC97B550236A6A6ACA7FFCC2DE6B4E1BC66B7CF3F68DEB8345D5A",
    },
}

EXPECTED_DONOR_ODBS = {
    "case2": {
        "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_HOLE_MULTISTATE_RECOVERY.odb",
        "size": 7499592,
        "sha256": "87E100CB40BD35B8844E29D4A5961BB7A3EC527AE0B2A5E1D807174903654EAD",
    },
    "case3": {
        "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/SEC43_MULTISTATE_RECOVERY.odb",
        "size": 10043772,
        "sha256": "C67C0DEE132B31B53FDF7C2DF4C1D232AD92D42E9AFB29F5CD8313C269CF9780",
    },
}

EXPECTED_IMAGE_HASHES = {
    "case_1_mesh_full.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_1_mesh_full.png",
        "F3776225878985899E60B1E2D2BB4C6714899279D71210B27091C1D63B32BB72",
    ),
    "case_1_h_over_l0.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_1_h_over_l0.png",
        "4E31856F4E8C09B062C1289A61F163A4FC55B296253A3339F1BED83D2D6F80FA",
    ),
    "case_1_mesh_closeup.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_1_mesh_closeup.png",
        "24051BF8A8DE58FE3012E13BBF6ED6D0A15BF258FF6856F785A3905C98E8D2C9",
    ),
    "case_2_mesh_full.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_2_mesh_full.png",
        "CCC416E9DF25DF6B6E1C5DBDF2A3F446C76B0B87A1F380C96B6B03B589F76CA1",
    ),
    "case_2_h_over_l0.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_2_h_over_l0.png",
        "3BB4BD4700467D1BD7DF30DC429F7B12ABD20119E5227D3E55BC8DF61295E15F",
    ),
    "case_2_mesh_closeup.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_2_mesh_closeup.png",
        "C38297837AE0D386447AAA0EF9CDF32F683AB54E41268B7CC324115F18F21D3C",
    ),
    "case_3_mesh_full.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_3_mesh_full.png",
        "EEDA01A3BCB9812078840B9133BCA98A146DF706673E69839BAE234EBD6AB031",
    ),
    "case_3_h_over_l0.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_3_h_over_l0.png",
        "514A197A619D511B5300B40D4181F0E7B43654BA9CAD43E8C3D8B0BEB4F90797",
    ),
    "case_3_mesh_closeup.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_3_mesh_closeup.png",
        "E4075725AC5B5A0558529B21CCC0473DF69C3E8B156579210DCFAF3EFAA6F321",
    ),
    "case_5_mesh_full.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_5_mesh_full.png",
        "EA9DD53FF38ED3EB2E98E6966503E7FFB55B08C9170DD141328961E57B69683E",
    ),
    "case_5_h_over_l0.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_5_h_over_l0.png",
        "814339B3528999EDFCED752325BFC8D34691D0BC73E7B423265D431CB96C09AD",
    ),
    "case_5_mesh_closeup.png": (
        "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_5_mesh_closeup.png",
        "F19274745C3927EAEAA9455C733E15AE1B90E74112C3ED20CD29F444395E802A",
    ),
    "fig_f1809_synthesis.png": (
        "results/figures/fig_f1809_four_benchmark_multistate_synthesis.png",
        "1B837E8C71B9B0F1E4A2EB5BCFE00222F368A44A0AAABECB5A0E953541344877",
    ),
    "fig_f1809_synthesis.pdf": (
        "results/figures/fig_f1809_four_benchmark_multistate_synthesis.pdf",
        "B172934659A86CBC63328046760DDEF904A2212D49571280A2ABCC4356B0DE8E",
    ),
}

def sha256_of_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


class TestF1810GovernanceInvariants:
    def test_frozen_uel_invariance(self):
        uel_path = os.path.join(TOP_DIR, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
        assert os.path.isfile(uel_path)
        assert sha256_of_file(uel_path) == FROZEN_UEL_SHA

    def test_frozen_framework_invariance(self):
        fw_path = os.path.join(TOP_DIR, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
        assert os.path.isfile(fw_path)
        assert sha256_of_file(fw_path) == FROZEN_FRAMEWORK_SHA

    def test_pbs_and_goal_invariants(self):
        active_task_path = os.path.join(TOP_DIR, "project_coordination", "ACTIVE_TASK.json")
        with open(active_task_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["task_id"] in ["F1810-EVIDENCE-COMPLETION-AND-REVERIFICATION", "F1811-ERROR-TARGET-EFFICIENCY-CALIBRATION"] or data.get("predecessor_task", {}).get("task_id") == "F1810-EVIDENCE-COMPLETION-AND-REVERIFICATION"
        assert data["master_goal_status"] == "OPEN"
        assert data["max_new_pbs_submissions"] == 0
        assert data["cumulative_pbs_submissions"] == 35


class TestF1810PhysicalMeshes:
    @pytest.mark.parametrize("case_key,info", EXPECTED_MESH_HASHES.items())
    def test_mesh_exists_and_hash_matches(self, case_key, info):
        full_path = os.path.join(TOP_DIR, info["path"])
        assert os.path.isfile(full_path), f"Missing mesh file: {full_path}"
        assert os.path.getsize(full_path) == info["size"]
        assert sha256_of_file(full_path) == info["sha256"]


class TestF1810MultiStateDonors:
    @pytest.mark.parametrize("case_key,info", EXPECTED_DONOR_ODBS.items())
    def test_donor_odb_exists_and_hash_matches(self, case_key, info):
        full_path = os.path.join(TOP_DIR, info["path"])
        assert os.path.isfile(full_path), f"Missing donor ODB: {full_path}"
        assert os.path.getsize(full_path) == info["size"]
        assert sha256_of_file(full_path) == info["sha256"]


class TestF1810ImageManifest:
    @pytest.mark.parametrize("name,pair", EXPECTED_IMAGE_HASHES.items())
    def test_image_exists_and_hash_matches(self, name, pair):
        rel_path, expected_hash = pair
        full_path = os.path.join(TOP_DIR, rel_path)
        assert os.path.isfile(full_path), f"Missing image file: {full_path}"
        assert sha256_of_file(full_path) == expected_hash, f"Hash mismatch for {name}"


class TestF1810Case2Audit:
    def test_case2_outer_ligament_resolution(self):
        receipt_path = os.path.join(
            TOP_DIR, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery",
            "PK_F1809_MULTISTATE_SEQUENTIAL_RECEIPT.json"
        )
        with open(receipt_path, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        c2 = receipt["cases"]["case_2"]
        assert c2["audit"]["total_physical_elements"] == 118640
        assert c2["critical_metrics"]["combined_outer_ligament_count"] == 6138
        assert c2["critical_metrics"]["combined_outer_ligament_pct_le_l0_half"] == 100.0
        assert c2["gates"]["SCIENTIFIC_GATE_OUTER_DISTAL"] == "PASS"


class TestF1810Case3Audit:
    def test_case3_secondary_corridor_resolution(self):
        receipt_path = os.path.join(
            TOP_DIR, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery",
            "PK_F1809_MULTISTATE_SEQUENTIAL_RECEIPT.json"
        )
        with open(receipt_path, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        c3 = receipt["cases"]["case_3"]
        assert c3["audit"]["total_physical_elements"] == 77779
        assert c3["critical_metrics"]["secondary_corridor_elements"] == 12638
        assert c3["critical_metrics"]["secondary_pct_le_l0"] > 93.8
        assert c3["gates"]["SCIENTIFIC_GATE_SECONDARY_CORRIDOR"] == "PASS"
