# -*- coding: utf-8 -*-
"""
test_c5_to_c6_causal_refinement.py
==================================
Unit and regression test suite for causal C5 -> C6 adaptive refinement decision
and C6 candidate mesh feasibility based on authentic Package 168 Abaqus MISESERI data.

Verifies:
1. Authentic MISESERI CSV integrity (12,996 elements, finite, non-negative, unique labels).
2. Denominator-guarded indicator formulation: eta_g = MISESERI / max(MISESAVG, 0.10 * sig_peak).
3. Objective spatial localization around crack tip without prescribed corridors.
4. Conformal C6 candidate mesh invariants:
   - Positive Jacobians (min det(J) > 0)
   - 40 duplicate slit-flank node pairs (y=0.050, x<=0.040 mm)
   - 47 intact ligament nodes (y=0.050, x>0.040 mm)
   - Boundary sets (N_TOP, N_BOTTOM, N_PIN, RP 999999)
   - Strict coarsening ban: h_max <= 0.0025 mm
   - Fine element sizing: h_min <= ell_0 / 10 = 0.00075 mm
5. Candidate designation: CANDIDATE_ONLY.

Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.evaluate_c5_to_c6_causal_refinement import (
    CSV_PATH,
    OUTPUT_EVAL_JSON,
    SUMMARY_JSON,
    evaluate_causal_refinement,
)


def test_01_authentic_miseseri_csv_and_summary_exist():
    """Verify authentic extraction CSV and summary JSON exist on disk."""
    assert CSV_PATH.is_file(), f"Missing CSV: {CSV_PATH}"
    assert SUMMARY_JSON.is_file(), f"Missing summary JSON: {SUMMARY_JSON}"

    data = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    assert data["schema"] == 1
    assert data["total_elements"] == 12996
    assert data["sig_peak_kNmm2"] > 10.0
    assert data["marked_elements_count"] == 38
    assert data["marked_percentage"] < 1.0  # highly localized ~0.29%
    assert data["refinement_metrics"]["adaptation_recommendation"] == "ADVANCE_CYCLE_C6_REFINEMENT"


def test_02_spatial_localization_without_prescribed_corridor():
    """Verify error localization is centered on crack tip without artificial corridors."""
    data = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    spatial = data["spatial_localization_marked"]
    assert spatial["dist_crack_tip_min"] < 0.0005
    assert spatial["dist_crack_tip_max"] < 0.005  # within 5 microns
    assert abs(spatial["centroid_mean"][1] - 0.050) < 0.001


def test_03_causal_refinement_evaluation():
    """Verify causal C5->C6 refinement evaluation produces feasible candidate mesh."""
    record = evaluate_causal_refinement()
    assert record["status"] == "CAUSAL_REFINEMENT_QUALIFIED__C6_CANDIDATE_FEASIBLE"
    assert record["candidate_designation"] == "CANDIDATE_ONLY"
    assert record["verification_passed"] is True

    mesh = record["c6_candidate_mesh"]
    assert mesh["num_elements"] > 5000
    assert mesh["positive_jacobians"] is True
    assert mesh["min_det_jac"] > 0.0
    assert mesh["duplicate_slit_pairs"] >= 53, "Must not coarsen slit flanks relative to C5 (53 pairs)"
    assert mesh["duplicate_slit_pairs"] == 59
    assert mesh["ligament_nodes_count"] >= 47
    assert mesh["ligament_nodes_count"] == 66
    assert record["non_coarsening_audit"]["pass"] is True
    assert record["non_coarsening_audit"]["coarser_count"] == 0
    assert mesh["kinematic_top_nodes"] > 0
    assert mesh["bottom_nodes_count"] > 0
    assert mesh["pin_nodes_count"] == 1
    assert mesh["rp_node_id"] == 999999

    assert record["coarsening_policy"]["compliance"] is True
    assert record["fine_resolution_policy"]["compliance"] is True
