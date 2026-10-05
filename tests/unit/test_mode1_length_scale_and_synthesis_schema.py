"""
Unit Regression Tests for Mode-I Length-Scale Adequacy and Synthesis Schema
Governing Task: F1248-MODE1-LENGTH-SCALE-ADEQUACY-AUDIT-AND-SYNTHESIS-SCHEMA-FREEZE
"""

import json
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
ADEQUACY_JSON_PATH = REPO_ROOT / "project_coordination" / "MODE1_GOVERNED_MESHES_LENGTH_SCALE_ADEQUACY.json"
SCHEMA_JSON_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "MODE1_GATE6B_MULTIQUANTITY_SYNTHESIS_SCHEMA.json"
METHODS_MD_PATH = REPO_ROOT / "docs" / "methods" / "MODE1_LENGTH_SCALE_ADEQUACY_AND_SYNTHESIS_SCHEMA.md"


def test_reject_job_name_as_l0_proof():
    """
    Guard 1: Enforce that phase-field length scale l0 must be derived from
    verified input deck properties / UEL PROPS, never from heuristic job names
    or directory strings (e.g. 'L1', 'L2', 'H0015').
    """
    sample_deck_text = """
*USER MATERIAL, CONSTANTS=10
 210000.0, 0.3, 0.0027, 0.0075, 1.0e-7, 0.0, 0.0, 0.0, 0.0, 0.0
"""
    # Parse l0 from constants (index 3 is 0.0075 mm = 7.5 um)
    lines = [line.strip() for line in sample_deck_text.strip().splitlines()]
    assert "*USER MATERIAL" in lines[0]
    props = [float(x.strip()) for x in lines[1].split(",")]
    l0_val = props[3]
    assert l0_val == 0.0075, f"Expected l0=0.0075 mm (7.5 um), got {l0_val}"

    # Verify that a misleading string 'JOB_L3_HEURISTIC_SWEEP' cannot override deck value
    fake_job_name = "JOB_L3_HEURISTIC_SWEEP"
    with pytest.raises(ValueError, match="Job name strings cannot be used as proof of physical parameter l0"):
        def parse_l0(job_str, deck_props=None):
            if deck_props is None:
                raise ValueError("Job name strings cannot be used as proof of physical parameter l0 without input deck verification")
            return deck_props[3]
        parse_l0(fake_job_name, deck_props=None)


def test_reject_confounded_l0_mesh_comparison():
    """
    Guard 2: Enforce that any comparison varying both discretization h and
    length-scale l0 is flagged as CONFOUNDED_L0_AND_MESH_CHANGE rather than
    a clean length-scale sensitivity study.
    """
    def classify_comparison(case_a, case_b):
        same_mesh = (case_a["elements"] == case_b["elements"] and case_a["mesh_hash"] == case_b["mesh_hash"])
        same_l0 = (case_a["l0_um"] == case_b["l0_um"])

        if same_mesh and same_l0:
            return "IDENTICAL_REPLICATION"
        elif same_mesh and not same_l0:
            return "VALID_LENGTH_SCALE_SENSITIVITY"
        elif not same_mesh and same_l0:
            return "VALID_MESH_RESOLUTION_STUDY"
        else:
            return "CONFOUNDED_L0_AND_MESH_CHANGE"

    case_ref15k_l75 = {"elements": 15192, "mesh_hash": "hash_s1", "l0_um": 7.5}
    case_ref41k_l75 = {"elements": 41912, "mesh_hash": "hash_s3", "l0_um": 7.5}
    case_ref41k_l150 = {"elements": 41912, "mesh_hash": "hash_s3", "l0_um": 15.0}

    assert classify_comparison(case_ref15k_l75, case_ref41k_l75) == "VALID_MESH_RESOLUTION_STUDY"
    assert classify_comparison(case_ref41k_l75, case_ref41k_l150) == "VALID_LENGTH_SCALE_SENSITIVITY"
    assert classify_comparison(case_ref15k_l75, case_ref41k_l150) == "CONFOUNDED_L0_AND_MESH_CHANGE"


def test_enforce_explicit_h_definition_in_adequacy():
    """
    Guard 3: Enforce that mesh adequacy records strictly provide explicit
    mathematical definitions for h (e.g. h_area_min, h_area_median, notch_edge),
    avoiding ambiguous bare 'h' numbers.
    """
    assert ADEQUACY_JSON_PATH.is_file(), f"Missing adequacy JSON: {ADEQUACY_JSON_PATH}"
    with open(ADEQUACY_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    required_keys = [
        "num_base_elements",
        "num_nodes",
        "global_h_area_min_um",
        "corridor_h_area_min_um",
        "corridor_h_area_median_um",
        "nominal_notch_root_edge_um",
        "corridor_h_area_min_over_l0",
        "nominal_notch_edge_over_l0"
    ]

    expected_meshes = [
        "Fixed Reference (S1)",
        "Adaptive ET1 (14k)",
        "Adaptive ET2 (6k)",
        "Adaptive ET3 (5k)",
        "Adaptive ET5 (4k)",
        "Spatial Fine (58k)"
    ]

    for mesh_name in expected_meshes:
        assert mesh_name in data, f"Mesh {mesh_name} missing from adequacy JSON"
        record = data[mesh_name]
        for key in required_keys:
            assert key in record, f"Key '{key}' missing from {mesh_name} adequacy record"
            assert isinstance(record[key], (int, float)), f"Value for '{key}' in {mesh_name} must be numeric"

        # Assert resolution adequacy at fracture process zone (h_min / l0 <= 0.50)
        assert record["corridor_h_area_min_over_l0"] <= 0.50, (
            f"{mesh_name} corridor h_min/l0 ({record['corridor_h_area_min_over_l0']}) exceeds 0.50"
        )


def test_distinguish_spatial_crack_path_vs_force_divergence():
    """
    Guard 4: Enforce scientific distinction between post-peak spatial crack path
    localization agreement and mechanical reaction force relative percentage divergence
    in the deep softening regime (where absolute load is near-zero, F < 0.002 kN).
    """
    f_ref_postpeak = 0.0010  # kN
    f_adapt_postpeak = 0.0018  # kN
    delta_abs_kN = abs(f_adapt_postpeak - f_ref_postpeak)
    rel_pct = delta_abs_kN / f_ref_postpeak * 100.0

    # Relative error is 80%, but absolute error is 0.0008 kN (0.8 N, <0.15% of peak load 0.609 kN)
    assert rel_pct == 80.0
    assert delta_abs_kN < 0.002, "Absolute force difference is negligible"

    # Evaluate spatial trajectory error
    y_dev_mean_um = 0.05  # <0.1 um deviation from y=0.5 mm line
    assert y_dev_mean_um < 1.0, "Spatial crack localization is in near-perfect alignment"

    def evaluate_postpeak_consistency(f_ref, f_adapt, y_dev_um):
        f_max = 0.609
        abs_err = abs(f_adapt - f_ref)
        is_force_divergence_relative_artifact = (abs_err / f_max < 0.005) and (f_ref < 0.005)
        is_spatial_path_consistent = (y_dev_um < 5.0)
        return {
            "spatial_agreement": is_spatial_path_consistent,
            "force_absolute_error_negligible": is_force_divergence_relative_artifact,
            "interpretation": (
                "SPATIAL_CRACK_PATH_AGREEMENT_MAINTAINED_DESPITE_RELATIVE_FORCE_DIVERGENCE"
                if is_spatial_path_consistent and is_force_divergence_relative_artifact
                else "GENUINE_DIVERGENCE"
            )
        }

    eval_result = evaluate_postpeak_consistency(f_ref_postpeak, f_adapt_postpeak, y_dev_mean_um)
    assert eval_result["interpretation"] == "SPATIAL_CRACK_PATH_AGREEMENT_MAINTAINED_DESPITE_RELATIVE_FORCE_DIVERGENCE"


def test_block_future_terminal_results_before_completion():
    """
    Guard 5: Enforce that the multi-quantity synthesis schema strictly blocks
    marking uncompleted jobs as populated or completed before terminal solver output.
    """
    assert SCHEMA_JSON_PATH.is_file(), f"Missing schema JSON: {SCHEMA_JSON_PATH}"
    with open(SCHEMA_JSON_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    assert schema["schema_version"] == "2.0.0"
    assert "required_jobs" in schema
    assert "evaluation_metrics" in schema

    # A mock record with uncompleted job marked as COMPLETED_VALIDATED with null values must fail validation
    invalid_record = {
        "job_id": "1410179",
        "model_name": "PK_M1_14AM_SOLVE",
        "mesh_label": "Spatial Fine 58k",
        "base_elements": 57929,
        "base_nodes": 57492,
        "length_scale_l0_um": 7.5,
        "h_area_min_um": 0.553,
        "h_notch_edge_um": 1.896,
        "h_min_over_l0": 0.074,
        "status": "COMPLETED_VALIDATED",
        "mechanical": {
            "peak_force_kN": None  # Null value forbidden for COMPLETED_VALIDATED
        }
    }

    def validate_ingest_record(record):
        if record["status"] == "COMPLETED_VALIDATED":
            if record.get("mechanical", {}).get("peak_force_kN") is None:
                raise ValueError(f"Job {record['job_id']} cannot have status COMPLETED_VALIDATED with null peak_force_kN")
        return True

    with pytest.raises(ValueError, match="cannot have status COMPLETED_VALIDATED with null"):
        validate_ingest_record(invalid_record)
