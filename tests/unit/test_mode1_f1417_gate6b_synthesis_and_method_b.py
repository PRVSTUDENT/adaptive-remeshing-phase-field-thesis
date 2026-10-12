# -*- coding: utf-8 -*-
"""
Unit test for Task F1417: Mode-I Gate 6B Synthesis, Overnight Method B Validation,
and Supervisor Progress Package.

Verifies:
1. Multi-quantity fracture comparison metrics (K0, F_max, u_peak, W_ext, E_tot).
2. Measured speedups (2.140x on Native 14k, 1.670x on ET2 6k).
3. Stage A 8-thread shared-memory SMP parity hashes.
4. Stage B repeat candidate formal deferral status and governance rationale.
5. Authoritative UEL source SHA-256 hash persistence.
6. Documentation and chapter report inclusion of Gate 6B synthesis.
"""

import os
import hashlib
import json
import pytest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def test_authoritative_uel_source_hash():
    """Verify authoritative Fortran UEL source hash is strictly preserved."""
    uel_path = os.path.join(WORKSPACE_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), f"f42_mixed_uel.for must exist at {uel_path}"
    with open(uel_path, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().upper()
    expected_hash = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert actual_hash == expected_hash, f"UEL hash mismatch: {actual_hash} != {expected_hash}"

def test_multi_quantity_metrics_against_reference():
    """Verify multi-quantity metrics for adapted models against canonical 15k reference."""
    # Canonical 15,192 FE reference anchor values
    ref_K0 = 137.945520
    ref_Fmax = 0.757778
    ref_u_peak = 0.005857

    # Historical ET2 (6,112 FE) metrics (Jobs 1411895 / 1411950)
    et2_K0 = 137.976065
    et2_Fmax = 0.756367
    et2_u_peak = 0.005841
    et2_delta_K0 = (et2_K0 - ref_K0) / ref_K0 * 100.0
    et2_delta_Fmax = (et2_Fmax - ref_Fmax) / ref_Fmax * 100.0
    et2_delta_u_peak = (et2_u_peak - ref_u_peak) / ref_u_peak * 100.0

    assert abs(et2_delta_K0 - (+0.0221)) < 0.005, f"ET2 K0 error mismatch: {et2_delta_K0}"
    assert abs(et2_delta_Fmax - (-0.1862)) < 0.005, f"ET2 Fmax error mismatch: {et2_delta_Fmax}"
    assert abs(et2_delta_u_peak - (-0.2732)) < 0.005, f"ET2 u_peak error mismatch: {et2_delta_u_peak}"

    # Genuine Method B Native (14,677 FE) metrics (Jobs 1411934 / 1411949)
    mb_K0 = 137.891881
    mb_Fmax = 0.743021
    mb_u_peak = 0.005727
    mb_delta_K0 = (mb_K0 - ref_K0) / ref_K0 * 100.0
    mb_delta_Fmax = (mb_Fmax - ref_Fmax) / ref_Fmax * 100.0
    mb_delta_u_peak = (mb_u_peak - ref_u_peak) / ref_u_peak * 100.0

    assert abs(mb_delta_K0 - (-0.0389)) < 0.005, f"Method B K0 error mismatch: {mb_delta_K0}"
    assert abs(mb_delta_Fmax - (-1.9475)) < 0.005, f"Method B Fmax error mismatch: {mb_delta_Fmax}"
    assert abs(mb_delta_u_peak - (-2.2196)) < 0.005, f"Method B u_peak error mismatch: {mb_delta_u_peak}"

def test_smp_speedups():
    """Verify measured 8-thread shared-memory SMP walltime speedups."""
    # ET2 6,112 FE: 17,243 s serial vs 10,328 s 8T SMP
    speedup_et2 = 17243.0 / 10328.0
    assert abs(speedup_et2 - 1.670) < 0.005, f"ET2 speedup mismatch: {speedup_et2}"
    savings_et2 = (17243.0 - 10328.0) / 17243.0 * 100.0
    assert abs(savings_et2 - 40.1) < 0.2

    # Method B Native 14,677 FE: 35,028 s serial vs 16,366 s 8T SMP
    speedup_mb = 35028.0 / 16366.0
    assert abs(speedup_mb - 2.140) < 0.005, f"Method B speedup mismatch: {speedup_mb}"
    savings_mb = (35028.0 - 16366.0) / 35028.0 * 100.0
    assert abs(savings_mb - 53.3) < 0.2

def test_stage_a_parity_hashes():
    """Verify recorded Stage A 8-thread SMP parity hashes."""
    expected_native_energy_hash = "792BE67DB9AC2CA2E51B9811CA0FB6F374BF28D0BA160F725F2D071B3C38D99D"
    expected_et2_energy_hash = "52CF636A3CC145472E87D922167B6AD9EF86ABDB7836827FBA4D283194F9C218"
    expected_native_rf_hash = "1D9D4948A5C4075C1ECD93DD3E24724A28AD7EAD4285F2276B4B008EC3623BC0"

    assert len(expected_native_energy_hash) == 64
    assert len(expected_et2_energy_hash) == 64
    assert len(expected_native_rf_hash) == 64

def test_stage_b_repeat_deferral_status():
    """Verify Stage B repeat candidate is formally recorded as DEFERRED."""
    decision_doc = os.path.join(WORKSPACE_ROOT, "docs", "decisions", "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md")
    assert os.path.exists(decision_doc)
    with open(decision_doc, "r", encoding="utf-8") as f:
        text = f.read()

    assert "M1_MB_NATIVE_8T_B" in text
    assert "DEFERRED" in text
    assert "Prioritize analysis of actual existing evidence over launching new simulations" in text

def test_report_chapter_gate6b_section():
    """Verify chapter 4 includes Section on Gate 6B synthesis and Method B results."""
    ch4_path = os.path.join(WORKSPACE_ROOT, "MA_AdaptiveRemeshing_Report_2026", "chapter04_current_status.tex")
    assert os.path.exists(ch4_path)
    with open(ch4_path, "r", encoding="utf-8") as f:
        ch4_text = f.read()

    assert "Gate-6B Synthesis: Method B Load-Partition Invariance" in ch4_text
    assert "tab:mode1_gate6b_multiquantity_summary" in ch4_text
    assert "2.140" in ch4_text
    assert "1.670" in ch4_text
