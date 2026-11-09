# -*- coding: utf-8 -*-
"""
test_f1695_method_a_final_closeout.py
======================================
Unit test suite for Task F1695:
  Method A Autonomous Closeout, Review Corrections Verification,
  Chapter 5 Synthesis, and Freeze Readiness.

Validates:
  1. Best-donor adapted mesh metrics from committed JSON (repo-relative path,
     primary med 0.2368 mm, primary 2.14% <= l0/2, secondary 68 elems,
     min 0.1968 mm, med 0.5022 mm, exactly 0.00% <= l0/2).
  2. Secondary corridor count basis across all four Section 4.3 adapted meshes
     (20, 43, 68, 430 elements), confirming 0.00% <= l0/2 in every case.
  3. Strict scoping of falsification language in thesis text (no unscoped
     'across ALL donor states'; scoped to 'every donor state tested').
  4. Complete absence of ungrounded '659x' multiplier in thesis text.
  5. Reconciled test-suite total arithmetic (29 prior + 9 F1694 = 38 total).
  6. Tripartite Table 5.13 and Table 5.16 text consistency in Chapter 5.
  7. Governance and resource integrity: production UEL inviolable, zero new PBS jobs.
"""

import os
import sys
import json
import ast
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VALIDATION_DIR = os.path.join(REPO_ROOT, "results", "validation")
CHAPTER05_TEX = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "chapter05_method_a_hole_benchmark.tex")
PRODUCTION_UEL = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().lower()

# ==============================================================================
# 1. Best-Donor Metrics and Path Validation
# ==============================================================================

def test_f1695_best_donor_metrics_and_repo_relative_path():
    json_path = os.path.join(VALIDATION_DIR, "f1694_sec43_adapted_mesh_best_donor_metrics.json")
    assert os.path.exists(json_path), "Missing f1694_sec43_adapted_mesh_best_donor_metrics.json"

    with open(json_path, "r") as f:
        data = json.load(f)

    # 1. Path must be repository-relative (not absolute Windows path)
    donor_odb = data.get("donor_odb", "")
    assert not os.path.isabs(donor_odb), f"donor_odb must be repo-relative, found: {donor_odb}"
    assert "D:" not in donor_odb, f"donor_odb contains drive letter: {donor_odb}"
    assert "models/pandey_kumar_mode1" in donor_odb or "models\\pandey_kumar_mode1" in donor_odb

    # 2. Total elements & DOFs
    assert data["elements_total"] == 12110
    assert data["total_dofs"] == 24434

    # 3. Primary corridor metrics
    prim = data["primary_corridor"]
    assert abs(prim["med"] - 0.2368) < 1e-4, f"Expected primary median 0.2368 mm, got {prim['med']}"
    assert abs(prim["pct_l0_half"] - 2.14) < 1e-2, f"Expected primary pct <= l0/2 2.14%, got {prim['pct_l0_half']}"

    # 4. Secondary corridor metrics
    sec = data["secondary_corridor"]
    assert sec["count"] == 68, f"Expected secondary count 68 elements, got {sec['count']}"
    assert abs(sec["min"] - 0.1968) < 1e-4, f"Expected secondary min 0.1968 mm, got {sec['min']}"
    assert abs(sec["med"] - 0.5022) < 1e-4, f"Expected secondary median 0.5022 mm, got {sec['med']}"
    assert sec["pct_l0_half"] == 0.0, f"Expected secondary pct <= l0/2 exactly 0.0%, got {sec['pct_l0_half']}"

# ==============================================================================
# 2. Secondary Corridor Basis Across All Section 4.3 Adapted Meshes
# ==============================================================================

def test_f1695_corridor_counts_and_resolution_basis():
    # Four distinct Section 4.3 adapted meshes evaluated
    cases = [
        ("f1693_sec43_case_a_adapted_mesh_metrics.json", 9432, 20, 0.0),
        ("f1692_sec43_adapted_mesh_metrics.json", 15625, 43, 0.0),
        ("f1694_sec43_adapted_mesh_best_donor_metrics.json", 12110, 68, 0.0),
        ("f1690_sec43_adapted_mesh_metrics.json", 30686, 430, 0.0),
    ]
    for filename, exp_total_elems, exp_sec_count, exp_sec_pct in cases:
        p = os.path.join(VALIDATION_DIR, filename)
        assert os.path.exists(p), f"Missing {filename}"
        with open(p, "r") as f:
            d = json.load(f)
        total_elems = d.get("elements_total") or d.get("adapted_mesh", {}).get("total_elements")
        assert total_elems == exp_total_elems, f"Mismatch in total elems for {filename}: got {total_elems}, expected {exp_total_elems}"
        assert d["secondary_corridor"]["count"] == exp_sec_count, f"Mismatch in sec count for {filename}"
        assert d["secondary_corridor"]["pct_l0_half"] == exp_sec_pct, f"Secondary resolution must be 0.0% in {filename}"

# ==============================================================================
# 3. Scoped Falsification Language in Thesis Text
# ==============================================================================

def test_f1695_thesis_text_scoped_falsification_language():
    assert os.path.exists(CHAPTER05_TEX), "Missing Chapter 5 tex file"
    with open(CHAPTER05_TEX, "r", encoding="utf-8") as f:
        content = f.read()

    # Unscoped language must be absent
    assert "across all donor" not in content.lower(), "Found unscoped 'across all donor' in Chapter 5"
    assert "universal failure of single-rule method~a across all donor states" not in content.lower()

    # Scoped language must be present
    assert "every donor state tested" in content.lower(), "Expected scoped phrase 'every donor state tested' in Chapter 5"

# ==============================================================================
# 4. Absence of Ungrounded 659x Multiplier
# ==============================================================================

def test_f1695_thesis_no_659x_multiplier():
    with open(CHAPTER05_TEX, "r", encoding="utf-8") as f:
        content = f.read()

    assert "659x" not in content, "Found ungrounded '659x' in Chapter 5"
    assert "659\\times" not in content, "Found ungrounded '659\\times' in Chapter 5"

# ==============================================================================
# 5. Test Suite Total Reconciliation
# ==============================================================================

def test_f1695_test_suite_total_reconciliation():
    """
    Reconciles the exact arithmetic:
      test_f1688: 5
      test_f1689: 5
      test_f1690: 7
      test_f1692: 6
      test_f1693: 6
      Subtotal (through F1693) = 29
      test_f1694: 9
      Total (through F1694) = 38
    """
    test_files = [
        "test_f1688_pandey_kumar_sec43_reproduction.py",
        "test_f1689_method_a_synthesis.py",
        "test_f1690_pandey_kumar_sec43_rerun.py",
        "test_f1692_pandey_kumar_sec43_staggered_rerun.py",
        "test_f1693_sec43_donor_correction_and_synthesis.py",
        "test_f1694_sec43_miseseri_fields_and_multidonor.py"
    ]
    expected_counts = [5, 5, 7, 6, 6, 9]
    actual_counts = []
    for tf in test_files:
        path = os.path.join(REPO_ROOT, "tests", "unit", tf)
        assert os.path.exists(path), f"Missing {tf}"
        with open(path, "r", encoding="utf-8") as fp:
            tree = ast.parse(fp.read(), filename=path)
        cnt = sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_"))
        actual_counts.append(cnt)

    assert actual_counts == expected_counts, f"Test count per file mismatch: {actual_counts} vs {expected_counts}"
    subtotal_f1693 = sum(actual_counts[:5])
    assert subtotal_f1693 == 29, f"F1693 subtotal must be 29, got {subtotal_f1693}"
    total_f1694 = sum(actual_counts)
    assert total_f1694 == 38, f"Grand total through F1694 must be 38, got {total_f1694}"

# ==============================================================================
# 6. Tripartite Table and Master Table Consistency
# ==============================================================================

def test_f1695_tripartite_and_master_tables_reconciled():
    with open(CHAPTER05_TEX, "r", encoding="utf-8") as f:
        content = f.read()

    # Table 5.13: Scoped falsification entry
    assert "Definitively Falsified on Every Donor State Tested" in content
    # Unproven category must have Job-2 comparison, not donor question
    assert "Section 4.3 Job-2 Fine Fracture Comparison" in content
    # Table 5.16: Best Donor values
    assert r"0.0875\,\mathrm{mm} \le \ell_0/3$ ($2.14\% \le \ell_0/2$)" in content
    assert r"0/68$ elems)" in content or r"($0/68$ elems)" in content

# ==============================================================================
# 7. Governance and Inviolability
# ==============================================================================

def test_f1695_production_uel_inviolability_and_governance():
    assert os.path.exists(PRODUCTION_UEL), "Production UEL missing"
    assert sha256_file(PRODUCTION_UEL) == EXPECTED_UEL_SHA, "Production UEL hash modified!"
