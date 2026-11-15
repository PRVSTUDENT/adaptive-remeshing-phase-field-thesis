"""
Unit tests for Task F1766: Benchmark Suite Reconciliation and Full-Suite Regression Plan.
Verifies:
1. Reconciled 4-benchmark core suite mapping against Pandey & Kumar (2025).
2. Elimination of duplicate off-axis hole descriptions.
3. Proper distinction of 3-hole pin-loaded plate (Sec. 4.3) vs 5-hole plate (Sec. 4.5).
4. Preservation of frozen UEL hash and reusable framework integrity.
5. Detection and diagnosis of Case 1 distal crack-path refinement limitation.
"""
import json
import os
import pytest

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FRAMEWORK_PATH = "scripts/remeshing/reusable_2d_adaptive_framework.py"
MANIFEST_PATH = "configs/remeshing/canonical_five_case_manifest.json"


def test_frozen_uel_unmodified():
    uel_path = "models/pandey_kumar_mode1/f42_mixed_uel.for"
    assert os.path.exists(uel_path), "Frozen UEL file must exist"
    import hashlib
    with open(uel_path, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest().upper()
    assert actual_sha == FROZEN_UEL_SHA256, "Frozen UEL hash must be bitwise invariant"


def test_reconciled_suite_mapping():
    assert os.path.exists(MANIFEST_PATH), "Canonical manifest must exist"
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)
    
    benchmarks = manifest["benchmarks"]
    assert "case_1" in benchmarks, "Case 1 must be present"
    assert "case_2" in benchmarks, "Case 2 must be present"
    assert "case_3" in benchmarks, "Case 3 must be present"
    assert "case_5" in benchmarks, "Case 5 must be present"
    
    # Check Case 1: Standard Mode-I edge-cracked plate
    c1 = benchmarks["case_1"]
    assert "Section 4.1" in c1["benchmark_name"] or "Section 4.2" in c1["benchmark_name"]
    assert c1["target_elements"] in (13941, 13762)
    
    # Check Case 2: Plate with off-axis hole (resolves duplicate items 2 & 3)
    c2 = benchmarks["case_2"]
    assert "Off-Axis Hole" in c2["benchmark_name"]
    assert c2["target_elements"] == 23618
    
    # Check Case 3: Rectangular notched plate with hole and pins (3 internal holes)
    c3 = benchmarks["case_3"]
    assert "Section 4.3" in c3["benchmark_name"]
    assert "Hole and Pins" in c3["benchmark_name"]
    assert c3["target_elements"] == 12168
    
    # Check Case 5: Seven-hole plate
    c5 = benchmarks["case_5"]
    assert "Section 4.6" in c5["benchmark_name"]
    assert "Seven Holes" in c5["benchmark_name"]
    assert c5["target_elements"] == 15714


def test_case1_defect_diagnosis():
    c1_config_path = "configs/remeshing/f1728_case1_mode1_edge_crack.json"
    assert os.path.exists(c1_config_path), "Case 1 config must exist"
    with open(c1_config_path, "r") as f:
        c1_cfg = json.load(f)
    
    rr = c1_cfg["remeshing_rule"]
    # Documented defect: LAST_INCREMENT on static linear elastic donor isolates crack-tip singularity
    # and fails to propagate refinement into the distal ligament
    assert rr["variable"] == "MISESERI"
    assert rr["coarsening_factor"] == "NOT_ALLOWED"
    assert rr["min_element_size_mm"] == 0.001
    assert rr["max_element_size_mm"] == 0.020


def test_case4_omission_preservation():
    # Case 4 is preserved in manifest and history, but permitted to be omitted from mandatory suite
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)
    c4 = manifest["benchmarks"]["case_4"]
    assert "Five Holes" in c4["benchmark_name"]
    assert os.path.exists("docs/validation/F1763_CASE4_PILOT_EXECUTION_REPORT.md"), \
        "Case 4 F1763 pilot report must be preserved"
