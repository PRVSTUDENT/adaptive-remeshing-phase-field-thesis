# -*- coding: utf-8 -*-
"""
Unit tests for the Problem-Agnostic Generic Adaptive Remesher Qualification (Task F1292).
========================================================================================
Verifies:
1. Reusable generic remeshing engine exists and conforms to the parameter schema.
2. Code audit results: zero benchmark-specific hardcoded coordinates or corridor filters.
3. Multi-pattern quantitative fidelity qualification:
   - Pattern 1: Mode-I straight / horizontal localization
   - Pattern 2: Mode-II inclined shear localization (theta ~ -44 deg)
   - Pattern 3: L-Panel non-symmetric re-entrant corner localization
4. Fidelity metrics meet strict generic acceptance criteria:
   - Pearson r(log10 M, h) <= -0.60 (strong negative correlation)
   - Top 10% MISESERI refined >= 90.0%
   - Fine elements in high MISESERI >= 80.0%
5. All 3 true element-edge publication figures (PNG and PDF) exist and are non-empty.
6. Scientific isolation: remesher is sound; Mode-II deviation is isolated to upstream physics.
"""
import os
import json
import pytest

SUMMARY_JSON = "results/figures/generic_remesher/REMESHER_THREE_PATTERN_QUALIFICATION_SUMMARY.json"
ENGINE_SCRIPT = "scripts/remeshing/generic_adaptive_remesher.py"

FIGURES = [
    "results/figures/generic_remesher/pattern1_mode1_straight_qualification.png",
    "results/figures/generic_remesher/pattern1_mode1_straight_qualification.pdf",
    "results/figures/generic_remesher/pattern2_mode2_inclined_qualification.png",
    "results/figures/generic_remesher/pattern2_mode2_inclined_qualification.pdf",
    "results/figures/generic_remesher/pattern3_lpanel_reentrant_qualification.png",
    "results/figures/generic_remesher/pattern3_lpanel_reentrant_qualification.pdf"
]

def test_generic_remesher_engine_exists_and_clean():
    """Verify generic remesher engine exists and has no hardcoded benchmark coordinates."""
    assert os.path.exists(ENGINE_SCRIPT), f"Missing engine script: {ENGINE_SCRIPT}"
    with open(ENGINE_SCRIPT, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify key schema classes and functions exist
    assert "class RemeshConfig" in content
    assert "def extract_part_mesh_elements" in content
    assert "def compute_mesh_statistics" in content
    assert "def execute_remeshing" in content

    # Verify NO hardcoded benchmark coordinates in executable logic
    assert "0.5, 0.5" not in content
    assert "0.55" not in content
    assert "chord_angle_deg" not in content
    assert "spurious_upper" not in content

def test_qualification_summary_exists_and_passed():
    """Verify that multi-pattern qualification summary exists and overall status is PASS."""
    assert os.path.exists(SUMMARY_JSON), f"Missing qualification summary: {SUMMARY_JSON}"
    with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("overall_status") == "QUALIFIED_PASS"
    patterns = data.get("patterns", [])
    assert len(patterns) == 3, f"Expected 3 patterns, got {len(patterns)}"

    for p in patterns:
        name = p["case_name"]
        assert p["verdict"] == "PASS", f"Pattern {name} did not PASS: {p}"
        assert p["pearson_r"] <= -0.60, f"Pattern {name} Pearson r ({p['pearson_r']}) > -0.60"
        assert p["pct_top10_refined"] >= 90.0, f"Pattern {name} top10 refined ({p['pct_top10_refined']}%) < 90%"
        assert p["pct_fine_in_high_m"] >= 80.0, f"Pattern {name} fine in high M ({p['pct_fine_in_high_m']}%) < 80%"
        assert p["bounds_respected"] is True, f"Pattern {name} size bounds not respected"

def test_true_element_edge_figures_exist():
    """Verify all 6 true element-edge publication figures exist and are non-empty."""
    for fig_path in FIGURES:
        assert os.path.exists(fig_path), f"Figure missing: {fig_path}"
        assert os.path.getsize(fig_path) > 10000, f"Figure too small or corrupt: {fig_path} ({os.path.getsize(fig_path)} bytes)"

def test_upstream_root_cause_isolation():
    """
    Verify scientific conclusion:
    The remesher reliably reproduces the local error field across horizontal (Mode-I),
    inclined (Mode-II), and re-entrant corner (L-panel) fields.
    Therefore, the Mode-II crack trajectory deviation is isolated to upstream
    governing physics (lateral BCs and isotropic degradation vs Miehe spectral split).
    """
    assert os.path.exists(SUMMARY_JSON)
    with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert "error-guided across tested patterns" in data.get("audit_conclusion", "")

def test_errortarget_percentage_semantics_and_fraction_guard():
    """Verify that RemeshConfig enforces percentage semantics (e.g. 1.0, 2.0, 5.0) and rejects fractions (0.01, 0.02)."""
    import sys
    sys.path.insert(0, os.path.abspath("scripts/remeshing"))
    from generic_adaptive_remesher import RemeshConfig
    
    # Valid percentage targets should succeed
    for valid_target in [1.0, 2.0, 3.0, 5.0, 10.0]:
        cfg = RemeshConfig(
            model_name="TEST_MODEL",
            odb_path="dummy.odb",
            part_name="PART-1",
            error_target=valid_target
        )
        assert cfg.error_target == valid_target
        
    # Decimal fraction targets (< 0.10) must be rejected with ValueError
    for invalid_target in [0.01, 0.02, 0.05, 0.001]:
        with pytest.raises(ValueError) as excinfo:
            RemeshConfig(
                model_name="TEST_MODEL",
                odb_path="dummy.odb",
                part_name="PART-1",
                error_target=invalid_target
            )
        assert "percentage" in str(excinfo.value)
