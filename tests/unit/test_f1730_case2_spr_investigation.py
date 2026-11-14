# -*- coding: utf-8 -*-
# tests/unit/test_f1730_case2_spr_investigation.py
# Unit regression tests for Task F1730 Case 2 Targeted SPR Recovery Domain & Interface Investigation

import json
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INVESTIGATION_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1730_case2_spr_interface_investigation.json")
REPORT_MD = os.path.join(REPO_ROOT, "docs", "validation", "F1730_CASE2_SPR_DOMAIN_INVESTIGATION_REPORT.md")
SCRIPT_PY = os.path.join(REPO_ROOT, "scripts", "remeshing", "investigate_case2_spr_interfaces.py")

def test_f1730_spr_investigation_artifacts_exist():
    assert os.path.isfile(SCRIPT_PY), f"Script not found: {SCRIPT_PY}"
    assert os.path.isfile(INVESTIGATION_JSON), f"JSON not found: {INVESTIGATION_JSON}"
    assert os.path.isfile(REPORT_MD), f"Report not found: {REPORT_MD}"

def test_f1730_spr_investigation_mesh_inventory():
    with open(INVESTIGATION_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    inv = data["mesh_inventory"]
    assert inv["total_elements"] == 2906
    assert inv["total_nodes"] == 3010
    assert inv["total_material_sections"] == 13
    assert inv["interface_elements_count"] == 433
    assert inv["interior_elements_count"] == 2473

def test_f1730_spr_investigation_subset_statistics():
    with open(INVESTIGATION_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    stats = data["statistics"]
    
    # 1. Primary component (37 elements)
    p_comp = stats["primary_damage_component"]
    assert p_comp["count"] == 37
    assert abs(p_comp["mean"] - 245.53) < 1.0
    assert abs(p_comp["max"] - 1357.85) < 0.1
    
    # 2. All 48 damaged elements
    dmg = stats["all_damaged_elements"]
    assert dmg["count"] == 48
    assert abs(dmg["mean"] - 210.68) < 1.0
    
    # 3. 6 Boundary ligament elements
    bnd_lig = stats["hole_boundary_ligament"]
    assert bnd_lig["count"] == 6
    assert abs(bnd_lig["mean"] - 141.25) < 1.0
    
    # 4. Uncracked corridor (42 elements)
    uncracked = stats["uncracked_ligament_corridor"]
    assert uncracked["count"] == 42
    assert abs(uncracked["mean"] - 127.27) < 1.0
    
    # 5. Bulk interface elements (385 elements)
    b_int = stats["bulk_interface_elements"]
    assert b_int["count"] == 385
    assert abs(b_int["mean"] - 53.34) < 1.0
    
    # 6. Pure intact bulk (1,516 elements)
    pure_bulk = stats["pure_homogeneous_intact_bulk"]
    assert pure_bulk["count"] == 1516
    assert abs(pure_bulk["mean"] - 10.10) < 0.5
    assert pure_bulk["median"] < 6.5

def test_f1730_spr_investigation_contrasts_and_correlations():
    with open(INVESTIGATION_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    stats = data["statistics"]
    corr = data["correlations"]
    
    # Contrast ratios
    damaged_vs_pure_bulk = stats["all_damaged_elements"]["mean"] / stats["pure_homogeneous_intact_bulk"]["mean"]
    assert damaged_vs_pure_bulk > 20.0  # actual is ~20.86x
    
    damaged_vs_bulk_int = stats["all_damaged_elements"]["mean"] / stats["bulk_interface_elements"]["mean"]
    assert damaged_vs_bulk_int > 3.5  # actual is ~3.95x
    
    uncracked_vs_pure_bulk = stats["uncracked_ligament_corridor"]["mean"] / stats["pure_homogeneous_intact_bulk"]["mean"]
    assert uncracked_vs_pure_bulk > 12.0  # actual is ~12.60x
    
    # Correlations
    assert corr["r_miseseri_vs_damage_d"] > 0.80  # actual is 0.8555
    assert corr["r_miseseri_vs_modulus_jump_bulk"] > 0.60  # actual is 0.6317

def test_f1730_spr_investigation_report_content():
    with open(REPORT_MD, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "F1730-R01" in content
    assert "Superconvergent Patch Recovery" in content
    assert "Zienkiewicz" in content
    assert ("1,357.85" in content or "1357.85" in content)
    assert "210.68" in content
    assert "141.25" in content
    assert "53.34" in content
    assert "10.10" in content
    assert "0.8555" in content
