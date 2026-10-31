import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = REPO_ROOT / "results/validation/r4_walltime_and_checkpoint_feasibility.json"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


@pytest.fixture(scope="module")
def audit_data():
    assert ARTIFACT_PATH.is_file(), f"Artifact not found: {ARTIFACT_PATH}"
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_audit_artifact_schema_and_status(audit_data):
    assert audit_data["schema"] == 1
    assert audit_data["status"] == "AUDIT_COMPLETE"
    assert audit_data["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"


def test_r4_job_evidence(audit_data):
    job_ev = audit_data["r4_job_evidence"]
    assert job_ev["pbs_job_id"] == "1419147.mmaster02"
    assert job_ev["exit_status"] == "SUBDIVISION_LIMIT_REACHED"
    assert job_ev["substep_1_result"]["outers_executed"] == 50
    assert job_ev["substep_1_result"]["status"] == "REJECTED"
    assert job_ev["substep_2_result"]["outers_executed"] == 50
    assert job_ev["substep_2_result"]["status"] == "REJECTED"


def test_convergence_rate_diagnostics(audit_data):
    conv = audit_data["convergence_rate_diagnostics"]
    assert 0.864 <= conv["asymptotic_contraction_ratio_rho_H"] <= 0.866
    assert conv["additional_outers_needed"] == 24
    assert conv["total_outers_to_converge"] == 74
    assert conv["single_step_converges_within_100_outers"] is True
    assert conv["single_step_converges_within_120_outers"] is True


def test_timing_measurements(audit_data):
    timing = audit_data["authentic_timing_measurements"]
    assert 15.0 <= timing["mechanical_subproblem_mean_s"] <= 20.0
    assert 15.0 <= timing["phase_subproblem_mean_s"] <= 22.0
    assert timing["converged_substep_duration_min"] < 60.0
    assert timing["converged_substep_duration_hours"] < 1.0


def test_schedule_walltime_feasibility(audit_data):
    sched = audit_data["schedule_walltime_feasibility"]
    assert sched["nominal_substeps"] == 15
    assert sched["pbs_walltime_limit_hours"] == 8.0
    assert sched["ideal_full_schedule_hours"] > 8.0
    assert sched["full_schedule_with_bisections_hours"] > 8.0
    assert sched["fits_in_single_8h_pbs_job"] is False
    assert sched["verdict"] == "SINGLE_PBS_JOB_INFEASIBLE_SEGMENTATION_MANDATORY"


def test_segmented_execution_strategy(audit_data):
    seg = audit_data["segmented_execution_strategy"]
    assert seg["recommended_max_outer"] == 100
    assert seg["safety_margin_outers"] == 26
    assert seg["recommended_substeps_per_segment"] == 5
    assert seg["total_segments_required"] == 3
    assert seg["segment_budget_hours"] <= 7.5


def test_checkpoint_preservation_contract(audit_data):
    chk = audit_data["checkpoint_preservation_contract"]
    assert chk["nodal_count"] == 7265
    assert chk["quad_element_count"] == 7056
    assert chk["integration_point_count"] == 28224
    assert "displacement_ux_uy" in chk["preservation_fields"]
    assert "damage_d" in chk["preservation_fields"]
    assert "history_variable_H" in chk["preservation_fields"]


def test_evidence_sources_hashes(audit_data):
    for rel_path, expected_hash in audit_data["evidence_sources"].items():
        full_path = REPO_ROOT / rel_path
        assert full_path.is_file(), f"Missing evidence file: {full_path}"
        actual_hash = compute_sha256(full_path)
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"
