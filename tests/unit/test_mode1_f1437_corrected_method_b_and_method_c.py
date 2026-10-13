import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def test_method_c_gate_c1_v2_evidence():
    """Verify completed Method C Gate C1 V2 results committed under evidence_1412464."""
    eval_json = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "39_method_c_transfer_gate_c1",
        "evidence_1412464", "c1_continuation_evaluation.json"
    )
    assert os.path.isfile(eval_json), f"Missing {eval_json}"
    with open(eval_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Solver completion
    telemetry = data["solver_telemetry"]
    assert telemetry["total_increments"] == 5058
    assert telemetry["step1_increments"] == 10
    assert telemetry["step2_increments"] == 5048
    assert telemetry["cutbacks"] == 14
    assert telemetry["final_step"] == 2
    assert telemetry["final_time"] == 2.0

    # 2. Step 1 reload metrics
    reload = data["metrics"]["step1_reload"]
    assert abs(reload["handoff_displacement_mm"] - 0.0050) < 1e-6
    assert abs(reload["handoff_reaction_force_kn"] - 0.65246675) < 1e-4

    # 3. Step boundary continuity (< 5 N threshold)
    boundary = data["metrics"]["step_boundary"]
    assert boundary["boundary_continuous"] is True
    assert boundary["delta_rf_boundary_kn"] < 0.005  # < 5 N
    assert abs(boundary["delta_rf_boundary_kn"] - 9.25e-5) < 1e-6

    # 4. Continuation & Softening
    step2 = data["metrics"]["step2_continuation"]
    assert abs(step2["peak_force_fmax_kn"] - 1.086839) < 1e-4
    assert abs(step2["final_force_kn"] - 0.027694544) < 1e-4


def test_method_b_inflight_evaluation_and_fallback():
    """Verify in-flight Method B telemetry and explicit no-results fallback."""
    brain_dir = r"C:\Users\pruth\.gemini\antigravity-cli\brain\5b3092fe-b3ba-407b-8092-39ee419d35f3"
    inflight_json = os.path.join(brain_dir, "inflight_corrected_b_evaluation.json")
    assert os.path.isfile(inflight_json), f"Missing {inflight_json}"
    with open(inflight_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["job_id"] == "1412465.mmaster02"
    assert data["job_name"] == "M1_MB_CORR_14K"
    assert data["status"] == "RUNNING_STEP1"

    # Elastic stiffness parity
    el = data["elastic_response"]
    assert el["num_elastic_points"] == 400
    assert abs(el["K0_kN_per_mm"] - 137.909558) < 0.01
    assert abs(el["delta_K0_vs_canonical_pct"]) < 0.10  # within 0.1% of reference
    assert el["R2"] > 0.999999

    # Cutbacks
    assert data["solver_telemetry"]["cutbacks"] == 0
    assert data["solver_telemetry"]["completed_increments_sta"] > 1500

    # Explicit fallback structure
    fallback = data["post_peak_evaluation_fallback"]
    assert fallback["status"] == "HELD_PENDING_STEP2_COMPLETION"
    assert "Peak reaction force" in fallback["reason"]
    assert fallback["metrics"]["F_max_kN"] == "PENDING_STEP2"
    assert fallback["metrics"]["terminal_W_ext_mJ"] == "PENDING_STEP2"


def test_comparison_figures_generated():
    """Verify authentic Method B comparison figures exist and are non-empty."""
    fig_dir = os.path.join(REPO_ROOT, "results", "figures", "mode1_method_b_corrected_comparison")
    png_path = os.path.join(fig_dir, "fig_mode1_method_b_corrected_comparison.png")
    pdf_path = os.path.join(fig_dir, "fig_mode1_method_b_corrected_comparison.pdf")

    assert os.path.isfile(png_path), f"Missing PNG {png_path}"
    assert os.path.isfile(pdf_path), f"Missing PDF {pdf_path}"
    assert os.path.getsize(png_path) > 100000, "PNG too small"
    assert os.path.getsize(pdf_path) > 20000, "PDF too small"
