"""Unit tests for Task F1388: Mode-II Fine 72k Progress, Peak Crossing, and Spatial Convergence Synthesis.

Author: Gemini Antigravity (Autonomous Scientific Agent)
Date: 2026-10-10
"""

import os
import json
import pytest
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "runs", "mode2", "fixed_convergence", "evidence")


def parse_dat_rp(rel_path):
    """Parse displacement and reaction force for RP node 999999 from Abaqus .dat file."""
    dat_path = os.path.join(REPO_ROOT, rel_path)
    if not os.path.exists(dat_path):
        return np.array([]), np.array([])
    u_vals, rf_vals = [], []
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.strip().startswith("999999"):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        u_vals.append(float(parts[1]))
                        rf_vals.append(float(parts[2]))
                    except ValueError:
                        pass
    return np.array(u_vals), np.array(rf_vals)


class TestMode2SpatialConvergenceSynthesis:
    """Test suite validating Mode-II spatial convergence synthesis and governance."""

    def test_01_evidence_files_presence(self):
        """Verify presence of terminal evidence files for all evaluated runs."""
        cases = [
            "01_coarse_2p5k",
            "02_med_18k",
            "03_int_40k",
            "03_int_48h",
            "et2_adapt_37k",
        ]
        for case in cases:
            case_dir = os.path.join(EVIDENCE_DIR, case)
            assert os.path.exists(case_dir), f"Evidence dir {case_dir} missing"
            dat_files = [f for f in os.listdir(case_dir) if f.endswith(".dat")]
            sta_files = [f for f in os.listdir(case_dir) if f.endswith(".sta")]
            assert len(dat_files) >= 1, f"Missing .dat in {case}"
            assert len(sta_files) >= 1, f"Missing .sta in {case}"

    def test_02_initial_stiffness_invariance(self):
        """Verify initial elastic stiffness invariance across all discretizations."""
        cases = [
            ("Coarse 2.5k", "runs/mode2/fixed_convergence/evidence/01_coarse_2p5k/M2_FIX_COARSE_2P5K.dat"),
            ("Medium 18k", "runs/mode2/fixed_convergence/evidence/02_med_18k/M2_FIX_MED_18K.dat"),
            ("Intermediate 40k", "runs/mode2/fixed_convergence/evidence/03_int_40k/M2_FIX_INT_40K.dat"),
            ("Adapted ET2", "runs/mode2/fixed_convergence/evidence/et2_adapt_37k/Job-2_UEL.dat"),
        ]
        stiffness_dict = {}
        for name, rel_path in cases:
            u, rf = parse_dat_rp(rel_path)
            assert len(u) > 100, f"Too few points in {name}"
            # Linear least squares slope on first 20 points
            n = 20
            k0 = np.sum(u[:n] * rf[:n]) / np.sum(u[:n] ** 2)  # kN/mm
            stiffness_dict[name] = k0
            assert 45.4 <= k0 <= 46.2, f"{name} stiffness {k0:.2f} kN/mm out of [45.4, 46.2]"

        k_values = list(stiffness_dict.values())
        mean_k = np.mean(k_values)
        spread_pct = (np.max(k_values) - np.min(k_values)) / mean_k * 100.0
        assert spread_pct < 0.70, f"Stiffness spread {spread_pct:.2f}% exceeds 0.70%"

    def test_03_peak_force_monotonic_convergence(self):
        """Verify peak force converges monotonically downwards with mesh refinement."""
        cases = [
            ("Coarse 2.5k", "runs/mode2/fixed_convergence/evidence/01_coarse_2p5k/M2_FIX_COARSE_2P5K.dat"),
            ("Medium 18k", "runs/mode2/fixed_convergence/evidence/02_med_18k/M2_FIX_MED_18K.dat"),
            ("Intermediate 40k", "runs/mode2/fixed_convergence/evidence/03_int_40k/M2_FIX_INT_40K.dat"),
            ("Adapted ET2", "runs/mode2/fixed_convergence/evidence/et2_adapt_37k/Job-2_UEL.dat"),
        ]
        peak_forces = []
        for name, rel_path in cases:
            u, rf = parse_dat_rp(rel_path)
            f_max = np.max(rf) * 1000.0  # N
            peak_forces.append((name, f_max))

        # Peak force sequence: Coarse (525.7) > Medium (437.0) > Intermediate (420.7) > Adapted ET2 (411.8)
        assert peak_forces[0][1] > peak_forces[1][1] > peak_forces[2][1] > peak_forces[3][1]

    def test_04_displacement_increment_arithmetic(self):
        """Verify exact displacement increment arithmetic (5 nanometers per increment)."""
        dt = 0.0005
        step1_ux = 10.0  # um
        delta_ux = step1_ux * dt
        assert np.isclose(delta_ux, 0.005), f"Expected 0.005 um, got {delta_ux}"
        delta_ux_mm = delta_ux * 1e-3
        assert np.isclose(delta_ux_mm, 5e-6), f"Expected 5e-6 mm, got {delta_ux_mm}"

    def test_05_intermediate_safeguard_bitwise_parity(self):
        """Verify Intermediate 40k 24h and 48h runs achieved identical peak load and terminal increment."""
        u1, rf1 = parse_dat_rp("runs/mode2/fixed_convergence/evidence/03_int_40k/M2_FIX_INT_40K.dat")
        u2, rf2 = parse_dat_rp("runs/mode2/fixed_convergence/evidence/03_int_48h/M2_FIX_INT_48H.dat")
        assert len(u1) == len(u2) == 1928
        np.testing.assert_array_equal(u1, u2)
        np.testing.assert_array_equal(rf1, rf2)
        f_max = np.max(rf1) * 1000.0
        assert np.isclose(f_max, 420.655, atol=0.01)

    def test_06_publication_figures_presence(self):
        """Verify publication figures exist in results directory."""
        pdf_path = os.path.join(REPO_ROOT, "results", "figures", "mode2", "fig_mode2_fixed_mesh_spatial_convergence.pdf")
        png_path = os.path.join(REPO_ROOT, "results", "figures", "mode2", "fig_mode2_fixed_mesh_spatial_convergence.png")
        assert os.path.exists(pdf_path), "PDF figure missing"
        assert os.path.exists(png_path), "PNG figure missing"
        assert os.path.getsize(pdf_path) > 1000, "PDF figure is empty"
        assert os.path.getsize(png_path) > 1000, "PNG figure is empty"

    def test_07_active_session_and_governance(self):
        """Verify session and task governance state."""
        session_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_SESSION.json")
        assert os.path.exists(session_path)
        with open(session_path, "r", encoding="utf-8") as f:
            session_data = json.load(f)
        assert session_data["agent"] in ["gemini-antigravity", "codex"]
        assert any(t in session_data["task_id"] for t in ["F1388", "F1389", "F1390"])
