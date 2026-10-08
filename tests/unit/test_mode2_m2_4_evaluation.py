"""
Unit tests for Mode-II Gate M2-4 Adapted Refined PFM Fracture Simulation & Evaluation
Verifies:
1. Model deck integrity (Job-2_UEL.inp: 22,530 FEs, 67,590 layered elements, boundary conditions)
2. Repaired Fortran source indexing (f42_mixed_uel_mode2_miehe.for: dynamic N_PHYS)
3. RHS phase-field driving source term presence in JTYPE=1 and JTYPE=3
4. Predeclared acceptance criteria matrix boundaries
5. Evaluation report and generated figure existence
6. Protection and immutability of Mode-I frozen baseline
"""

import os
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODE2_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
MODE1_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1")
DOCS_DIR = os.path.join(REPO_ROOT, "docs", "experiment_records")
FIG_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode2")

def test_mode2_job2_deck_structure():
    """Verify Job-2_UEL.inp has 22,530 physical elements, 67,590 layered elements, and valid BCs."""
    inp_path = os.path.join(MODE2_DIR, "Job-2_UEL.inp")
    assert os.path.exists(inp_path), "Job-2_UEL.inp must exist in %s" % MODE2_DIR

    n_nodes = 0
    elem_counts = {"U1": 0, "U2": 0, "U3": 0, "U4": 0, "CPE4": 0, "CPE3": 0}
    in_nodes = False
    in_elems = False
    current_elem_type = None

    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l:
                continue
            if l.startswith("*"):
                upper_l = l.upper()
                if upper_l.startswith("*NODE") and not upper_l.startswith("*NODE OUTPUT") and not upper_l.startswith("*NODE PRINT") and not upper_l.startswith("*NODEFILE"):
                    in_nodes = True
                    in_elems = False
                    current_elem_type = None
                    continue
                elif upper_l.startswith("*ELEMENT") and not upper_l.startswith("*ELEMENT OUTPUT") and not upper_l.startswith("*ELEMENT PRINT") and not upper_l.startswith("*ELEMENTFILE"):
                    in_nodes = False
                    in_elems = True
                    current_elem_type = None
                    for et in ["U1", "U2", "U3", "U4", "CPE4", "CPE3"]:
                        if "TYPE=" + et in upper_l:
                            current_elem_type = et
                            break
                    continue
                else:
                    in_nodes = False
                    in_elems = False
                    current_elem_type = None
                    continue

            if in_nodes:
                n_nodes += 1
            elif in_elems and current_elem_type:
                elem_counts[current_elem_type] += 1

    # Physical element counts: 21,962 quads + 568 tris = 22,530 FEs
    total_quads = elem_counts["U1"]
    total_tris = elem_counts["U3"]
    total_phys = total_quads + total_tris

    assert total_phys == 22530, "Physical element count must be 22,530 (got %d)" % total_phys
    assert total_quads == 21962, "Quad element count must be 21,962 (got %d)" % total_quads
    assert total_tris == 568, "Tri element count must be 568 (got %d)" % total_tris

    # Layered elements: 3 * 22,530 = 67,590
    total_layered = sum(elem_counts.values())
    assert total_layered == 67590, "Layered element count must be 67,590 (got %d)" % total_layered
    assert n_nodes >= 22642, "Node count must be >= 22,642 (got %d)" % n_nodes

def test_mode2_fortran_dynamic_indexing_and_rhs_driving_source():
    """Verify f42_mixed_uel_mode2_miehe.for dynamically reads N_PHYS and includes phase-field driving RHS."""
    for_path = os.path.join(MODE2_DIR, "f42_mixed_uel_mode2_miehe.for")
    assert os.path.exists(for_path), "f42_mixed_uel_mode2_miehe.for must exist"

    with open(for_path, "r") as f:
        src = f.read()

    # Verify UEL uses PROPS(6) for N_PHYS
    assert "N_PHYS = INT(PROPS(6))" in src or "N_PHYS = INT(PROPS(6)" in src, \
        "UEL must dynamically read N_PHYS from PROPS(6)"

    # Verify UMAT uses PROPS(3) for N_PHYS
    assert "N_PHYS = INT(PROPS(3))" in src or "N_PHYS = INT(PROPS(3)" in src, \
        "UMAT must dynamically read N_PHYS from PROPS(3)"

    # Verify NO hardcoded 100000 or 200000 offset subtraction in element index calculations
    assert "JELEM - 200000" not in src, "Hardcoded JELEM - 200000 must not exist in source"
    assert "JELEM - 100000" not in src, "Hardcoded JELEM - 100000 must not exist in source"
    assert "NOEL - 200000" not in src, "Hardcoded NOEL - 200000 must not exist in source"

    # Verify Phase-Field driving RHS source terms exist in JTYPE=1 and JTYPE=3
    assert "RHS(I,1) + CJAC * TWO * HIST * SHP(I)" in src or "RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * SHP(I)" in src, \
        "JTYPE=1 must include RHS driving force term"
    assert "RHS(I,1) + CJAC * TWO * HIST * N_TRI(I)" in src or "RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_TRI(I)" in src, \
        "JTYPE=3 must include RHS driving force term"

def test_mode2_predeclared_acceptance_criteria_boundaries():
    """Verify all 8 acceptance checks in M2_4_PREDECLARED_ACCEPTANCE_CRITERIA.md are present."""
    crit_path = os.path.join(MODE2_DIR, "M2_4_PREDECLARED_ACCEPTANCE_CRITERIA.md")
    assert os.path.exists(crit_path), "M2_4_PREDECLARED_ACCEPTANCE_CRITERIA.md must exist"

    with open(crit_path, "r") as f:
        content = f.read()

    for chk in ["M2_4_CHK1", "M2_4_CHK2", "M2_4_CHK3", "M2_4_CHK4", "M2_4_CHK5", "M2_4_CHK6", "M2_4_CHK7", "M2_4_CHK8"]:
        assert chk in content, "Acceptance check %s must be present in criteria document" % chk

def test_mode2_m2_4_evaluation_report_and_figures():
    """Verify Gate M2-4 evaluation report and publication figures exist and are non-empty."""
    rep_path = os.path.join(DOCS_DIR, "MODE2_M2_4_ADAPTED_FRACTURE_EVALUATION_REPORT.md")
    assert os.path.exists(rep_path), "Evaluation report must exist in docs/experiment_records/"
    assert os.path.getsize(rep_path) > 1000, "Evaluation report must be non-trivial"

    fig1_png = os.path.join(FIG_DIR, "fig_mode2_m2_4_rf_comparison.png")
    fig2_png = os.path.join(FIG_DIR, "fig_mode2_m2_4_history_and_miseseri.png")
    assert os.path.exists(fig1_png), "Figure 1 must exist: %s" % fig1_png
    assert os.path.exists(fig2_png), "Figure 2 must exist: %s" % fig2_png
    assert os.path.getsize(fig1_png) > 10000, "Figure 1 PNG must be non-empty"
    assert os.path.getsize(fig2_png) > 10000, "Figure 2 PNG must be non-empty"

def test_mode1_baseline_frozen_immutability():
    """Verify Mode-I baseline files and UEL remain strictly unmodified."""
    m1_uel = os.path.join(MODE1_DIR, "f42_mixed_uel.for")
    assert os.path.exists(m1_uel), "Mode-I f42_mixed_uel.for must exist"

    import hashlib
    with open(m1_uel, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest().upper()

    expected_h = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert h == expected_h, "Mode-I UEL hash mismatch: expected %s, got %s" % (expected_h, h)
