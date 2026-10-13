"""
Unit test suite for Mode-I Method C Gate C1 V2 Continuation Results and Visualization
Task: F1436-MODE1-SOLVER-MONITORING-AND-EVALUATION
Protocol Version: 2
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "39_method_c_transfer_gate_c1" / "evidence_1412464"
EVAL_JSON = EVIDENCE_DIR / "c1_continuation_evaluation.json"
FU_CSV = EVIDENCE_DIR / "c1_load_displacement.csv"
STA_FILE = EVIDENCE_DIR / "M1_RECIP_2906_CONTINUATION.sta"
PBS_LOG = EVIDENCE_DIR / "pbs_execution.log"
ENERGY_CSV = EVIDENCE_DIR / "uel_energy_balance.csv"

FIG_DIR = REPO_ROOT / "results" / "figures" / "mode1_method_c_gate_c1"
FIG_PNG = FIG_DIR / "fig_mode1_method_c_gate_c1_fu_and_energy.png"
FIG_PDF = FIG_DIR / "fig_mode1_method_c_gate_c1_fu_and_energy.pdf"


class TestMode1C1V2Results:
    def test_01_evidence_files_exist_and_non_empty(self):
        """Verify all lightweight evidence files for Job 1412464 exist and have content."""
        for p in [EVAL_JSON, FU_CSV, STA_FILE, PBS_LOG, ENERGY_CSV]:
            assert p.exists(), f"Missing evidence file: {p}"
            assert p.stat().st_size > 500, f"Evidence file too small: {p} ({p.stat().st_size} bytes)"

    def test_02_solver_telemetry_metrics(self):
        """Verify solver telemetry and convergence parameters from evaluation JSON."""
        with open(EVAL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        telemetry = data["solver_telemetry"]
        assert telemetry["status"] == "PARSED"
        assert telemetry["total_increments"] == 5058
        assert telemetry["step1_increments"] == 10
        assert telemetry["step2_increments"] == 5048
        assert telemetry["cutbacks"] == 14
        assert telemetry["severe_discontinuities"] == 0
        assert telemetry["final_step"] == 2
        assert telemetry["final_time"] == 2.0

    def test_03_handoff_and_boundary_continuity(self):
        """Verify step 1 reload metrics and seamless force continuity across handoff boundary."""
        with open(EVAL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        s1 = data["metrics"]["step1_reload"]
        assert s1["num_points"] == 10
        assert pytest.approx(s1["handoff_displacement_mm"], abs=1e-6) == 0.0050
        assert pytest.approx(s1["handoff_reaction_force_kn"], abs=1e-4) == 0.6525
        assert pytest.approx(s1["effective_reload_stiffness_k0_kn_per_mm"], abs=0.5) == 130.49

        boundary = data["metrics"]["step_boundary"]
        assert boundary["boundary_continuous"] is True
        assert boundary["delta_rf_boundary_kn"] < 0.0001
        assert boundary["delta_rf_boundary_kn"] <= boundary["criterion_max_delta_rf_kn"]

    def test_04_continuation_softening_and_energy(self):
        """Verify continuation peak, complete load drop, and global energy balance."""
        with open(EVAL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        s2 = data["metrics"]["step2_continuation"]
        assert s2["num_points"] == 5048
        assert pytest.approx(s2["peak_force_fmax_kn"], abs=1e-3) == 1.087
        assert pytest.approx(s2["displacement_at_peak_mm"], abs=1e-4) == 0.009234
        assert pytest.approx(s2["final_force_kn"], abs=1e-4) == 0.0277

        energy = data["metrics"]["energy_balance"]
        assert energy["num_records"] == 5058
        assert energy["final_fracture_energy_knmm"] > 0.0045
        assert energy["final_elastic_energy_knmm"] < 0.0002

    def test_05_figures_generated_and_valid(self):
        """Verify publication figure pairs exist with non-trivial size."""
        assert FIG_PNG.exists(), f"Missing PNG: {FIG_PNG}"
        assert FIG_PDF.exists(), f"Missing PDF: {FIG_PDF}"
        assert FIG_PNG.stat().st_size > 100000, f"PNG unexpectedly small: {FIG_PNG.stat().st_size} bytes"
        assert FIG_PDF.stat().st_size > 20000, f"PDF unexpectedly small: {FIG_PDF.stat().st_size} bytes"
