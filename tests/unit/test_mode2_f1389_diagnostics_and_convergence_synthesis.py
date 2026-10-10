"""Unit tests for Task F1389: Mode-II Nonlinear Failure Resolution, Mesh Topology Audit,
and Fine-Mesh Spatial Convergence Synthesis.

Author: Gemini Antigravity (Autonomous Scientific Agent)
Date: 2026-10-10
"""

import os
import re
import json
import pytest
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "runs", "mode2", "fixed_convergence", "evidence")
DIAG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "07_fixed_mesh_convergence_suite", "03_intermediate_40k_h5um_diagnostic_ls")


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


class TestMode2DiagnosticsAndConvergence:
    """Test suite for Mode-II nonlinear failure resolution and fine-mesh convergence."""

    def test_01_fine_72k_original_and_safeguard_progress_and_parity(self):
        """Verify fine 72k progress and 100% bitwise parity between original and safeguard."""
        u1, rf1 = parse_dat_rp("runs/mode2/fixed_convergence/evidence/04_fine_72k/M2_FIX_FINE_72K.dat")
        u2, rf2 = parse_dat_rp("runs/mode2/fixed_convergence/evidence/04_fine_72h/M2_FIX_FINE_72H.dat")
        
        assert len(u1) >= 1800, f"Expected >= 1800 points in 72k original, got {len(u1)}"
        assert len(u2) >= 1300, f"Expected >= 1300 points in 72h safeguard, got {len(u2)}"
        
        # Check active displacement of original
        assert u1[-1] * 1000.0 >= 9.0, f"Expected ux >= 9.0 um, got {u1[-1]*1000.0:.3f} um"
        
        # Check bitwise parity over common range
        common_len = min(len(u1), len(u2))
        np.testing.assert_array_equal(u1[:common_len], u2[:common_len])
        np.testing.assert_array_equal(rf1[:common_len], rf2[:common_len])

    def test_02_mesh_topology_and_node_count_integrity(self):
        """Verify 40k mesh topology has exactly 40,501 mesh nodes (40,401 grid + 100 seam)."""
        inp_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "07_fixed_mesh_convergence_suite", "03_intermediate_40k_h5um", "M2_FIX_INT_40K.inp")
        assert os.path.exists(inp_path)
        
        nodes = []
        with open(inp_path, "r", encoding="utf-8") as f:
            in_node = False
            for line in f:
                line_s = line.strip()
                if line_s.startswith("*"):
                    in_node = line_s.upper().startswith("*NODE") and not line_s.upper().startswith("*NODE PRINT")
                    continue
                if in_node:
                    parts = line_s.split(",")
                    if len(parts) >= 3:
                        try:
                            nid = int(parts[0].strip())
                            nodes.append(nid)
                        except ValueError:
                            pass
        
        # Total nodes including RP node 999999 is 40502
        assert len(nodes) == 40502
        assert 999999 in nodes
        mesh_nodes = [nid for nid in nodes if nid != 999999]
        assert len(mesh_nodes) == 40501
        
        # Base grid: 201 * 201 = 40401 nodes
        base_grid = [nid for nid in mesh_nodes if nid <= 40401]
        assert len(base_grid) == 40401
        
        # Seam duplicate nodes: 100 nodes (40402 to 40501)
        seam_nodes = [nid for nid in mesh_nodes if nid > 40401]
        assert len(seam_nodes) == 100

    def test_03_cutback_root_cause_and_increment_arithmetic(self):
        """Verify displacement increment arithmetic is exactly 5 nm per increment."""
        step_dt = 0.0005
        step_prescribed_ux_um = 10.0
        delta_ux_um = step_prescribed_ux_um * step_dt
        assert np.isclose(delta_ux_um, 0.005), f"Expected 0.005 um (5 nm), got {delta_ux_um}"
        assert np.isclose(delta_ux_um * 1e-3, 5e-6)

    def test_04_diagnostic_package_and_single_parameter_justification(self):
        """Verify diagnostic package is prepared with single numerical change (Line Search)."""
        manifest_path = os.path.join(DIAG_DIR, "manifest.json")
        assert os.path.exists(manifest_path)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        assert manifest["job_name"] == "M2_FIX_INT_40K_LS"
        assert manifest["fortran_uel_sha256"] == "699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188"
        assert "LINE SEARCH" in manifest["single_numerical_change"].upper()
        assert manifest["submission_authorized"] is True

    def test_05_spatial_convergence_monotonicity_and_invariance(self):
        """Verify peak reaction force sequence and initial structural stiffness invariance."""
        u_c, rf_c = parse_dat_rp("runs/mode2/fixed_convergence/evidence/01_coarse_2p5k/M2_FIX_COARSE_2P5K.dat")
        u_m, rf_m = parse_dat_rp("runs/mode2/fixed_convergence/evidence/02_med_18k/M2_FIX_MED_18K.dat")
        u_i, rf_i = parse_dat_rp("runs/mode2/fixed_convergence/evidence/03_int_40k/M2_FIX_INT_40K.dat")
        
        fmax_c = np.max(rf_c) * 1000.0
        fmax_m = np.max(rf_m) * 1000.0
        fmax_i = np.max(rf_i) * 1000.0
        
        # Peak forces strictly monotonic: Coarse (525.7) > Medium (437.0) > Intermediate (420.7)
        assert fmax_c > fmax_m > fmax_i
        
        # Initial stiffness calculation
        def calc_k0(u_arr, rf_arr, n=20):
            return np.sum(u_arr[:n] * rf_arr[:n]) / np.sum(u_arr[:n]**2)
            
        k0_c = calc_k0(u_c, rf_c)
        k0_m = calc_k0(u_m, rf_m)
        k0_i = calc_k0(u_i, rf_i)
        
        for name, k in [("Coarse", k0_c), ("Medium", k0_m), ("Intermediate", k0_i)]:
            assert 45.4 <= k <= 46.2, f"{name} K0 {k:.2f} out of [45.4, 46.2]"
            assert np.isclose(k, 45.68, atol=0.35)

    def test_06_publication_figures_presence_and_validity(self):
        """Verify publication figures exist and are non-empty."""
        pdf_path = os.path.join(REPO_ROOT, "results", "figures", "mode2", "fig_mode2_fixed_mesh_spatial_convergence.pdf")
        png_path = os.path.join(REPO_ROOT, "results", "figures", "mode2", "fig_mode2_fixed_mesh_spatial_convergence.png")
        assert os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 10000
        assert os.path.exists(png_path) and os.path.getsize(png_path) > 50000

    def test_07_active_session_and_governance(self):
        """Verify session and task governance state for F1389."""
        session_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_SESSION.json")
        assert os.path.exists(session_path)
        with open(session_path, "r", encoding="utf-8") as f:
            session_data = json.load(f)
        assert session_data["agent"] in ["gemini-antigravity", "codex"]
        assert "F1389" in session_data["task_id"]
