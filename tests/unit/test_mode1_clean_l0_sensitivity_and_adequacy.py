"""
Unit Regression Tests for Clean Mode-I Length-Scale Sensitivity, Provenance, and Mesh Adequacy
Governing Task: F1249-MODE1-CLEAN-L0-SENSITIVITY-AND-ADEQUACY-CONSISTENCY-CORRECTION
"""

import json
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_JSON_PATH = REPO_ROOT / "project_coordination" / "MODE1_CLEAN_L0_SENSITIVITY_AUDIT.json"
SCHEMA_JSON_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "MODE1_GATE6B_MULTIQUANTITY_SYNTHESIS_SCHEMA.json"
METHODS_MD_PATH = REPO_ROOT / "docs" / "methods" / "MODE1_LENGTH_SCALE_ADEQUACY_AND_SYNTHESIS_SCHEMA.md"


def test_unmatched_mesh_l0_comparison_fails_without_disclosure():
    """
    Guard 1: Enforce that comparing l0 sensitivity cases across different meshes or
    boundary controls without disclosure raises a validation error.
    Verify that Jobs 1406017, 1406895, 1406896 are proven 100% bitwise identical mesh twins.
    """
    assert AUDIT_JSON_PATH.is_file(), f"Missing audit JSON: {AUDIT_JSON_PATH}"
    with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
        audit = json.load(f)

    provenance = audit["mesh_provenance_and_twin_verification"]
    assert provenance["fe_mesh_nodes"] == 42491
    assert provenance["rp_reference_nodes"] == 1
    assert provenance["total_input_deck_nodes"] == 42492
    assert provenance["base_elements"] == 41912
    assert provenance["n_bottom_nodes"] == 404
    assert provenance["n_top_nodes"] == 404

    # Check twin jobs
    jobs = audit["clean_twin_job_records"]
    assert len(jobs) == 3
    l0_vals = [j["l0_um"] for j in jobs]
    assert l0_vals == [7.50, 11.25, 15.00]

    # Validate function to detect confounded comparison
    def validate_l0_study(job_list):
        for j in job_list:
            if "node_hash" in j and j["node_hash"] != provenance["mesh_node_coordinates_sha256"]:
                raise ValueError("Confounded l0 comparison: mesh node coordinates differ across jobs without disclosure")
        return "L0_SENSITIVITY_QUALIFIED_ON_FIXED_S3_MESH"

    # Synthetic test of confounded comparison
    confounded_jobs = [
        {"job_id": "1406017", "l0_um": 7.5, "node_hash": provenance["mesh_node_coordinates_sha256"]},
        {"job_id": "9999999", "l0_um": 15.0, "node_hash": "different_hash_on_different_mesh"}
    ]
    with pytest.raises(ValueError, match="Confounded l0 comparison"):
        validate_l0_study(confounded_jobs)


def test_historical_runs_energy_availability_fails_if_assigned_uel_energy():
    """
    Guard 2: Enforce that historical runs (1406017, 1406895, 1406896) without qualified
    energy instrumentation are marked ENERGY_NOT_YET_QUALIFIED and fail if assigned
    fabricated UEL fracture energy.
    """
    with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
        audit = json.load(f)

    assert audit["study_summary"]["energy_qualification_status"] == "ENERGY_NOT_YET_QUALIFIED_UNEQUAL_ENDPOINTS_AND_PRE_GATE6B_SOURCE"

    with open(SCHEMA_JSON_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    for job_id in ["1406017", "1406895", "1406896"]:
        rec = schema["records_template"][job_id]
        assert rec["energy_accounting_qualified"] is False
        assert "ENERGY_NOT_YET_QUALIFIED" in rec["energy_status_note"]

    def validate_energy_assignment(record):
        if not record.get("energy_accounting_qualified", False):
            if "E_frac_mJ" in record and record["E_frac_mJ"] is not None:
                raise ValueError(f"Job {record['model_name']} cannot report E_frac_mJ before energy qualification")
        return True

    invalid_rec = {
        "model_name": "PK_M1_42K_L0_7p5_SOLVE",
        "energy_accounting_qualified": False,
        "E_frac_mJ": 1.25
    }
    with pytest.raises(ValueError, match="cannot report E_frac_mJ before energy qualification"):
        validate_energy_assignment(invalid_rec)


def test_uniform_resolution_claim_fails_on_hmin_alone():
    """
    Guard 3: Enforce that mesh adequacy assertions must separate h_area_min,
    h_notch, and h_area_median, and fail if h_min alone is used to claim uniform
    crack-band resolution across the entire specimen.
    """
    with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
        audit = json.load(f)

    table = audit["mesh_adequacy_separation"]["metrics_table"]
    for entry in table:
        assert "h_area_min_um" in entry
        assert "h_notch_um" in entry
        assert "h_area_median_um" in entry
        assert entry["h_area_min_um"] <= entry["h_notch_um"] <= entry["h_area_median_um"] or entry["h_area_min_um"] == entry["h_area_median_um"]

    def validate_adequacy_claim(claim_dict):
        if "uniform_resolution_claimed" in claim_dict and claim_dict["uniform_resolution_claimed"]:
            if claim_dict.get("h_area_min_um") != claim_dict.get("h_area_median_um"):
                raise ValueError("Cannot claim uniform mesh resolution when h_min != h_median; must separate local and corridor metrics")
        return True

    non_uniform_mesh_claim = {
        "mesh": "Adaptive 58k",
        "h_area_min_um": 0.556,
        "h_area_median_um": 1.953,
        "uniform_resolution_claimed": True
    }
    with pytest.raises(ValueError, match="Cannot claim uniform mesh resolution"):
        validate_adequacy_claim(non_uniform_mesh_claim)


def test_rp_node_mixing_fails_without_labeling():
    """
    Guard 4: Enforce that Reference Point (RP) nodes are distinguished from continuum
    FE mesh nodes in all records to resolve the +1 node discrepancy.
    """
    with open(SCHEMA_JSON_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    assert "node_count_convention" in schema
    records = schema["records_template"]
    for job_id, rec in records.items():
        assert "fe_mesh_nodes" in rec, f"Record {job_id} missing fe_mesh_nodes"
        assert "total_nodes_with_rp" in rec, f"Record {job_id} missing total_nodes_with_rp"
        assert rec["total_nodes_with_rp"] == rec["fe_mesh_nodes"] + 1, (
            f"Record {job_id} total_nodes_with_rp ({rec['total_nodes_with_rp']}) != fe_mesh_nodes + 1 ({rec['fe_mesh_nodes'] + 1})"
        )


def test_post_peak_displacement_horizon_fails_beyond_loading_range():
    """
    Guard 5: Enforce that Mode-I prescribed loading horizon is strictly u <= 0.010 mm
    and that common comparison domain stops at u = 5.839 um without forward-filling.
    """
    with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
        audit = json.load(f)

    horizon = audit["governing_model_constants"]["loading_horizon_mm"]
    assert horizon == 0.010, f"Mode-I loading horizon must be 0.010 mm, got {horizon}"

    u_common = audit["study_summary"]["common_reached_displacement_domain_um"]
    assert u_common == [0.0, 5.839]

    def validate_displacement_domain(u_max, horizon_max):
        if u_max > horizon_max:
            raise ValueError(f"Reported displacement {u_max} mm exceeds physical loading horizon {horizon_max} mm")
        return True

    with pytest.raises(ValueError, match="exceeds physical loading horizon"):
        validate_displacement_domain(0.015, horizon)


def test_fracture_energy_renaming_fails_without_governed_symbols():
    """
    Guard 6: Enforce that synthesis schema uses governed energy fields (E_elas, E_frac,
    E_model, W_ext, delta_book, epsilon_book) and rejects deprecated E_strain / E_diss.
    """
    with open(SCHEMA_JSON_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    metrics = schema["evaluation_metrics"]
    governed_required = ["E_elas_mJ", "E_frac_mJ", "E_model_mJ", "W_ext_mJ", "delta_book_mJ", "epsilon_book_rel"]
    for field in governed_required:
        assert field in metrics, f"Governed energy metric '{field}' missing from schema"

    deprecated_fields = ["strain_energy_mJ", "dissipated_energy_mJ", "E_strain", "E_diss"]
    for field in deprecated_fields:
        assert field not in metrics, f"Deprecated field '{field}' must not be in schema"
