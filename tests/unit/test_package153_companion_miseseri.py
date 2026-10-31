#!/usr/bin/env python3
"""
test_package153_companion_miseseri.py
======================================
Unit tests verifying the authentic Package 153 C4 companion continuum solve (Job 1419101.mmaster02),
extracted MISESERI/MISESAVG fields, and refinement candidate marking for Cycle C5.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""

import csv
import json
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG153_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "153_c4_companion_miseseri")
AUDIT_JSON = os.path.join(PKG153_DIR, "c4_package153_miseseri_audit.json")
DIST_CSV = os.path.join(PKG153_DIR, "c4_package153_companion_miseseri_distribution.csv")
MARKING_JSON = os.path.join(REPO_ROOT, "results", "validation", "c4_refinement_candidate_marking.json")


def test_package153_audit_json_integrity():
    assert os.path.isfile(AUDIT_JSON), "Missing c4_package153_miseseri_audit.json"
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)

    assert data["job_name"] == "M1_C4_COMPANION_MISESERI"
    assert data["pbs_job_id"] == "1419101.mmaster02"
    assert data["total_elements"] == 7056
    assert data["loading_state"]["prescribed_u2_mm"] == 0.002

    # Peak MISESERI check
    peak_eri = data["peak_miseseri"]
    assert peak_eri["element_id"] == 3484
    assert pytest.approx(peak_eri["miseseri_kNmm2"], rel=1e-4) == 5.961021
    assert pytest.approx(peak_eri["centroid_mm"]["x"], abs=0.005) == 0.0403
    assert pytest.approx(peak_eri["centroid_mm"]["y"], abs=0.005) == 0.0497

    # Peak relative error check
    peak_eta = data["peak_relative_error"]
    assert peak_eta["element_id"] == 3361
    assert pytest.approx(peak_eta["eta"], rel=1e-4) == 2.103443

    # Refinement metrics
    metrics = data["refinement_metrics"]
    assert metrics["threshold_eta"] == 0.15
    assert metrics["elements_above_threshold"] == 266
    assert pytest.approx(metrics["pct_above_threshold"], rel=1e-3) == 3.7698
    assert metrics["adaptation_recommendation"] == "ADVANCE_CYCLE_C5_REFINEMENT"


def test_package153_distribution_csv_integrity():
    assert os.path.isfile(DIST_CSV), "Missing c4_package153_companion_miseseri_distribution.csv"
    with open(DIST_CSV, "r") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 7056, f"Expected 7056 records, found {len(reader)}"

    element_ids = [int(r["element_id"]) for r in reader]
    assert element_ids == list(range(1, 7057)), "Element IDs must be sequential 1..7056"

    high_err_count = 0
    for r in reader:
        eri = float(r["miseseri_kNmm2"])
        avg = float(r["misesavg_kNmm2"])
        eta = float(r["eta_relative_error"])
        assert eri >= 0.0, "MISESERI must be non-negative"
        assert avg > 0.0, "MISESAVG must be strictly positive"
        assert eta >= 0.0, "eta must be non-negative"
        if eta >= 0.15:
            high_err_count += 1

    assert high_err_count == 266, f"Expected 266 high-error elements, found {high_err_count}"


def test_candidate_marking_artifact_uses_authentic_package153():
    assert os.path.isfile(MARKING_JSON), "Missing c4_refinement_candidate_marking.json"
    with open(MARKING_JSON, "r") as f:
        marking = json.load(f)

    assert marking["schema"] == 1
    assert marking["status"] == "C4_REFINEMENT_MARKING_COMPLETE"
    assert marking["mesh_id"] == "C4_CORRECTED_7056_QUADS"
    assert marking["total_elements"] == 7056
    assert marking["threshold_eta"] == 0.15
    assert marking["refinement_policy"] == "REFINEMENT_ONLY"
    assert marking["coarsening_allowed"] is False
    assert marking["marked_elements_count"] == 266
    assert pytest.approx(marking["marked_percentage"], rel=1e-3) == 3.7698

    # Provenance
    prov = marking["source_provenance"]
    assert prov["indicator_origin"] == "PACKAGE_153_AUTHENTIC_COMPANION_ODB"
    assert prov["companion_job_name"] == "M1_C4_COMPANION_MISESERI"
    assert prov["companion_pbs_job_id"] == "1419101.mmaster02"
    assert prov["companion_status"]["compatible_companion_available"] is True
    assert prov["companion_status"]["missing_prerequisite"] is None

    # Flank topology
    topo = marking["flank_topology"]
    assert topo["duplicate_slit_node_pairs_count"] == 40
    assert topo["ligament_nodes_count"] == 45
    assert topo["slit_y_mm"] == 0.05
    assert topo["crack_tip_x_mm"] == 0.04
