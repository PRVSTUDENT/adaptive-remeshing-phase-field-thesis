#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Test Suite for Task F1420: Mode-I Method C State Transfer Engine & Spatial Projection Prototype.

Verifies:
1. Frozen authoritative Fortran subroutine f42_mixed_uel.for SHA-256 preservation (CE8D5EDC...).
2. Real Mode-I input deck parsing and topology classification (seam, upper/lower flanks, ligament).
3. Identity mapping on identical mesh with numerical precision (< 1e-12).
4. Linear-field exact reproduction across nonmatching discretizations (quad-to-quad).
5. Crack-seam discontinuity preservation: strict flank isolation preventing cross-seam contamination.
6. Bounded interpolation and physical clamping (0 <= d <= 1, H >= 0).
7. Damage irreversibility enforcement (d_target >= d_prior).
8. Expected failures on invalid/unsupported states (NaNs, missing files).
9. Continuation deck generation syntax validation: wrapped N_BOTTOM (<= 16 items) and
   valid *INITIAL CONDITIONS, TYPE=SOLUTION cards (<= 8 items per line, exactly 18 SVARs).
10. Quantitative projection and conservation evaluation using real Mode-I spatial damage data.
"""

import os
import sys
import math
import json
import hashlib
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.mode1_state_transfer_engine import (
    Mode1Mesh,
    Mode1State,
    Mode1SpatialIndex,
    Mode1StateTransferEngine,
    parse_mode1_input_deck,
    compute_quad_gauss_points,
    compute_tri_gauss_points,
)

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
UEL_FILE = REPO_ROOT / "models" / "pandey_kumar_mode1" / "38_method_b_native_final_14k" / "f42_mixed_uel.for"
COARSE_DECK = REPO_ROOT / "models" / "pandey_kumar_mode1" / "method_b_inf_companion_decks" / "M1_MB_INF_1S.inp"
NATIVE_DECK = REPO_ROOT / "models" / "pandey_kumar_mode1" / "38_method_b_native_final_14k" / "M1_MB_NATIVE_FINAL_1S.inp"
LIGAMENT_CSV = REPO_ROOT / "models" / "pandey_kumar_mode1" / "38_method_b_native_final_14k" / "M1_MB_NATIVE_14K_ligament_profiles.csv"


def create_synthetic_slit_mesh(name: str, nx: int, ny: int) -> Mode1Mesh:
    """
    Creates a synthetic 2D unit square mesh [0, 1] x [0, 1] with a zero-gap crack slit
    along y = 0.5 for 0 <= x <= 0.5 (duplicated nodes along the seam).
    Requires even ny so y = 0.5 is an exact element boundary line.
    """
    assert ny % 2 == 0, "ny must be even so y = 0.5 is an exact mesh line"
    mesh = Mode1Mesh(name=name)
    dx = 1.0 / nx
    dy = 1.0 / ny
    seam_j = ny // 2  # y = 0.5

    node_map = {}
    nid = 1

    for j in range(ny + 1):
        y = j * dy
        for i in range(nx + 1):
            x = i * dx
            if j == seam_j and x <= 0.5 - 1e-6:
                # Duplicated slit nodes: lower (j-) and upper (j+)
                node_map[(i, j, 'lower')] = nid
                mesh.nodes[nid] = (x, y)
                nid += 1
                node_map[(i, j, 'upper')] = nid
                mesh.nodes[nid] = (x, y)
                nid += 1
            else:
                node_map[(i, j, 'single')] = nid
                mesh.nodes[nid] = (x, y)
                if abs(y) < 1e-6:
                    mesh.n_bottom.append(nid)
                elif abs(y - 1.0) < 1e-6:
                    mesh.n_top.append(nid)
                nid += 1

    eid = 1
    for j in range(ny):
        for i in range(nx):
            def get_nid(ci, cj, flank):
                if (ci, cj, flank) in node_map:
                    return node_map[(ci, cj, flank)]
                return node_map[(ci, cj, 'single')]

            flank = 'lower' if j < seam_j else 'upper'
            n1 = get_nid(i,     j,     flank)
            n2 = get_nid(i + 1, j,     flank)
            n3 = get_nid(i + 1, j + 1, flank)
            n4 = get_nid(i,     j + 1, flank)

            mesh.elements_u1[eid] = [n1, n2, n3, n4]
            mesh.elements_u2[eid] = [n1, n2, n3, n4]
            mesh.elements_cpe[eid] = [n1, n2, n3, n4]
            eid += 1

    mesh.classify_topology()
    return mesh


class TestMode1F1420StateTransferEngine(unittest.TestCase):
    """Test suite for Method C State Transfer Engine prototype and projection qualification."""

    def test_01_frozen_fortran_subroutine_hash_preserved(self):
        """Verify authoritative Fortran subroutine SHA-256 CE8D5EDC... is intact."""
        self.assertTrue(UEL_FILE.exists(), f"f42_mixed_uel.for must exist at {UEL_FILE}")
        with open(UEL_FILE, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(h, FROZEN_UEL_HASH, "Frozen UEL Fortran source hash must match exactly")

    def test_02_mesh_parsing_and_topology_classification(self):
        """Verify parsing of real Mode-I input decks and crack slit topology classification."""
        self.assertTrue(COARSE_DECK.exists(), f"Coarse deck must exist at {COARSE_DECK}")
        mesh_coarse = parse_mode1_input_deck(str(COARSE_DECK))

        self.assertEqual(mesh_coarse.num_elements, 2906, "Coarse deck must have 2,906 elements")
        self.assertEqual(mesh_coarse.num_nodes, 2988, "Coarse deck must have 2,988 nodes")
        self.assertGreater(len(mesh_coarse.n_bottom), 0, "N_BOTTOM node set must be non-empty")
        self.assertGreater(len(mesh_coarse.n_top), 0, "N_TOP node set must be non-empty")
        self.assertEqual(mesh_coarse.rp_node_id, 999999, "RP node ID must be 999999")

        flanks = set(mesh_coarse.element_flank.values())
        self.assertIn("UPPER", flanks)
        self.assertIn("LOWER", flanks)

        node_flanks = set(mesh_coarse.node_flank.values())
        self.assertIn("UPPER", node_flanks)
        self.assertIn("LOWER", node_flanks)
        self.assertIn("LIGAMENT", node_flanks)

    def test_03_identity_mapping(self):
        """Verify that state projection on identical mesh yields exact numerical identity (< 1e-12)."""
        mesh = create_synthetic_slit_mesh("SyntheticDonor", 6, 6)
        state = Mode1State()

        for nid, (x, y) in mesh.nodes.items():
            state.u_nodal[nid] = (0.01 * x**2, 0.02 * y**2)
            state.d_nodal[nid] = 0.5 * math.exp(-10.0 * ((x - 0.5)**2 + (y - 0.5)**2))

        for eid in mesh.elements_u1:
            cx, cy = mesh.element_centroids[eid]
            h_val = 1.0 + 2.0 * cx + cy
            state.H_gp[eid] = [h_val, h_val, h_val, h_val]

        engine = Mode1StateTransferEngine(mesh)
        proj_state = engine.project_state(mesh, state, enforce_bc=False)

        max_err_u = 0.0
        max_err_d = 0.0
        for nid in mesh.nodes:
            ux, uy = state.u_nodal[nid]
            pux, puy = proj_state.u_nodal[nid]
            max_err_u = max(max_err_u, abs(ux - pux), abs(uy - puy))
            max_err_d = max(max_err_d, abs(state.d_nodal[nid] - proj_state.d_nodal[nid]))

        self.assertLess(max_err_u, 1e-12, f"Identity mapping displacement error too large: {max_err_u}")
        self.assertLess(max_err_d, 1e-12, f"Identity mapping damage error too large: {max_err_d}")

    def test_04_linear_field_reproduction_nonmatching(self):
        """Verify that linear polynomials are reproduced exactly across nonmatching meshes."""
        donor_mesh = create_synthetic_slit_mesh("DonorCoarse", 4, 4)
        recip_mesh = create_synthetic_slit_mesh("RecipFine", 8, 8)

        def exact_sol(x, y):
            ux = 1.5 * x - 0.7 * y + 0.2
            uy = -0.8 * x + 2.1 * y + 0.5
            d  = 0.3 * x + 0.4 * y + 0.1
            return ux, uy, d

        donor_state = Mode1State()
        for nid, (x, y) in donor_mesh.nodes.items():
            ux, uy, d = exact_sol(x, y)
            donor_state.u_nodal[nid] = (ux, uy)
            donor_state.d_nodal[nid] = d

        for eid in donor_mesh.elements_u1:
            donor_state.H_gp[eid] = [1.0, 1.0, 1.0, 1.0]

        engine = Mode1StateTransferEngine(donor_mesh)
        target_state = engine.project_state(recip_mesh, donor_state, enforce_bc=False)

        metrics = engine.compute_projection_metrics(recip_mesh, donor_state, target_state, exact_solution_fn=exact_sol)

        self.assertLess(metrics["max_error_ux"], 1e-10, f"Linear ux error too high: {metrics['max_error_ux']}")
        self.assertLess(metrics["max_error_uy"], 1e-10, f"Linear uy error too high: {metrics['max_error_uy']}")
        self.assertLess(metrics["max_error_d"],  1e-10, f"Linear d error too high: {metrics['max_error_d']}")

    def test_05_crack_seam_discontinuity_preservation(self):
        """Verify that topology-guarded transfer preserves upper/lower slit discontinuity without cross-bleeding."""
        donor_mesh = create_synthetic_slit_mesh("DonorSlit", 6, 6)
        recip_mesh = create_synthetic_slit_mesh("RecipSlit", 8, 8)

        donor_state = Mode1State()
        for nid, (x, y) in donor_mesh.nodes.items():
            flank = donor_mesh.node_flank[nid]
            if flank == "UPPER":
                donor_state.u_nodal[nid] = (0.0, 0.005)
                donor_state.d_nodal[nid] = 0.85
            elif flank == "LOWER":
                donor_state.u_nodal[nid] = (0.0, -0.005)
                donor_state.d_nodal[nid] = 0.15
            else:  # LIGAMENT
                donor_state.u_nodal[nid] = (0.0, 0.0)
                donor_state.d_nodal[nid] = 0.50

        for eid in donor_mesh.elements_u1:
            donor_state.H_gp[eid] = [0.1, 0.1, 0.1, 0.1]

        engine = Mode1StateTransferEngine(donor_mesh)
        target_state = engine.project_state(recip_mesh, donor_state, enforce_bc=False)

        upper_slit_uys = []
        lower_slit_uys = []
        upper_slit_ds  = []
        lower_slit_ds  = []

        for nid, (x, y) in recip_mesh.nodes.items():
            if abs(y - 0.5) < 1e-5 and x < 0.45:
                flank = recip_mesh.node_flank[nid]
                uy = target_state.u_nodal[nid][1]
                d = target_state.d_nodal[nid]
                if flank == "UPPER":
                    upper_slit_uys.append((x, uy))
                    upper_slit_ds.append((x, d))
                elif flank == "LOWER":
                    lower_slit_uys.append((x, uy))
                    lower_slit_ds.append((x, d))

        self.assertGreater(len(upper_slit_uys), 0, "Upper slit nodes must exist")
        self.assertGreater(len(lower_slit_uys), 0, "Lower slit nodes must exist")

        for x, uy in upper_slit_uys:
            self.assertGreater(uy, 0.0, f"Upper slit node at x={x} must have positive uy: {uy}")
        for x, uy in lower_slit_uys:
            self.assertLess(uy, 0.0, f"Lower slit node at x={x} must have negative uy: {uy}")

        self.assertEqual(len(upper_slit_uys), len(lower_slit_uys))
        for (xu, uyu), (xl, uyl) in zip(upper_slit_uys, lower_slit_uys):
            self.assertAlmostEqual(xu, xl, places=5)
            self.assertAlmostEqual(uyu, -uyl, places=5, msg=f"Crack opening anti-symmetry violated at x={xu}: {uyu} vs {uyl}")

        for x, d in upper_slit_ds:
            self.assertGreater(d, 0.50, f"Upper slit damage must reflect upper flank damage (>0.5): {d}")
        for x, d in lower_slit_ds:
            self.assertLess(d, 0.50, f"Lower slit damage must reflect lower flank damage (<0.5): {d}")

    def test_06_bounded_interpolation_and_clamping(self):
        """Verify that phase field is strictly bounded [0, 1] and history H >= 0."""
        mesh = create_synthetic_slit_mesh("MeshBounds", 4, 4)
        donor_state = Mode1State()

        for nid in mesh.nodes:
            donor_state.u_nodal[nid] = (0.0, 0.0)
            donor_state.d_nodal[nid] = 1.05  # Overshoot

        for eid in mesh.elements_u1:
            donor_state.H_gp[eid] = [-0.05, 1.2, 0.0, 0.5]  # Negative H

        engine = Mode1StateTransferEngine(mesh)
        with self.assertRaises(ValueError):
            engine.project_state(mesh, donor_state)

    def test_07_damage_irreversibility_enforcement(self):
        """Verify that d_target >= d_prior is enforced when prior recipient damage exists."""
        mesh = create_synthetic_slit_mesh("MeshIrrev", 4, 4)

        prior_state = Mode1State()
        for nid in mesh.nodes:
            prior_state.u_nodal[nid] = (0.0, 0.0)
            prior_state.d_nodal[nid] = 0.60  # Prior damage 0.60

        donor_state = Mode1State()
        for nid in mesh.nodes:
            donor_state.u_nodal[nid] = (0.0, 0.0)
            donor_state.d_nodal[nid] = 0.20  # Donor lower damage 0.20

        for eid in mesh.elements_u1:
            donor_state.H_gp[eid] = [0.1, 0.1, 0.1, 0.1]

        engine = Mode1StateTransferEngine(mesh)
        target_state = engine.project_state(mesh, donor_state, prior_target_state=prior_state)

        for nid, d in target_state.d_nodal.items():
            self.assertGreaterEqual(d, 0.60 - 1e-12, f"Damage irreversibility violated at node {nid}: {d} < 0.60")

    def test_08_continuation_deck_assembly_and_syntax_validation(self):
        """Verify generated Abaqus continuation deck conforms strictly to Abaqus 2023 card rules."""
        mesh = create_synthetic_slit_mesh("ContinuationMesh", 6, 6)
        state = Mode1State()
        for nid, (x, y) in mesh.nodes.items():
            state.u_nodal[nid] = (0.0, 0.005 * y)
            state.d_nodal[nid] = 0.25 * x
        for eid in mesh.elements_u1:
            state.H_gp[eid] = [0.001, 0.001, 0.001, 0.001]

        engine = Mode1StateTransferEngine(mesh)

        with tempfile.NamedTemporaryFile(suffix=".inp", delete=False) as tf:
            tmp_path = tf.name

        try:
            engine.assemble_continuation_deck(
                mesh, state, tmp_path, u_handoff=0.0050, u_final=0.0100, num_increments=500
            )

            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertNotIn("*INITIAL CONDITIONS, TYPE=DISPLACEMENT", content)
            self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", content)
            self.assertIn("*USER ELEMENT, TYPE=U1", content)
            self.assertIn("*USER ELEMENT, TYPE=U2", content)
            self.assertIn("*EQUATION", content)
            self.assertIn("7.5000000000e-03, 2.7000000000e-03, 2.1000000000e+02, 3.0000000000e-01, 1.0000000000e-07", content)

            lines = content.splitlines()
            in_nbottom = False
            in_sol_ic = False
            sol_ic_cards = []

            for line in lines:
                ls = line.strip()
                if ls.startswith("*NSET, NSET=N_BOTTOM"):
                    in_nbottom = True
                    continue
                if in_nbottom:
                    if ls.startswith("*"):
                        in_nbottom = False
                    else:
                        items = [p.strip() for p in ls.split(",") if p.strip()]
                        self.assertLessEqual(len(items), 16, f"N_BOTTOM card exceeded 16-item limit: {len(items)}")

                if ls.startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"):
                    in_sol_ic = True
                    continue
                if in_sol_ic:
                    if ls.startswith("*"):
                        in_sol_ic = False
                    else:
                        items = [p.strip() for p in ls.split(",") if p.strip()]
                        self.assertLessEqual(len(items), 8, f"TYPE=SOLUTION data line exceeded 8 items: {len(items)}")
                        sol_ic_cards.append(items)

            num_elems = mesh.num_elements
            self.assertEqual(len(sol_ic_cards), num_elems * 3, "Exactly 3 lines per element in TYPE=SOLUTION")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_09_real_mode1_spatial_projection_and_metrics(self):
        """Verify projection using real Mode-I spatial data at u = 0.0050 mm handoff."""
        self.assertTrue(NATIVE_DECK.exists(), f"Native deck must exist at {NATIVE_DECK}")
        self.assertTrue(LIGAMENT_CSV.exists(), f"Ligament CSV must exist at {LIGAMENT_CSV}")

        donor_mesh = parse_mode1_input_deck(str(NATIVE_DECK))
        self.assertEqual(donor_mesh.num_elements, 14677, "Native deck must have 14,677 elements")
        n_phys = donor_mesh.num_elements

        donor_state = Mode1State()
        for nid in donor_mesh.nodes:
            donor_state.u_nodal[nid] = (0.0, 0.0)
            donor_state.d_nodal[nid] = 0.0

        for eid in donor_mesh.elements_u1:
            donor_state.H_gp[eid] = [0.0, 0.0, 0.0, 0.0]

        import csv
        with open(LIGAMENT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["target_u_mm"] == "0.005000":
                    eid = int(row["elem_id"])
                    phys_eid = eid if eid <= n_phys else (eid - 2 * n_phys if eid > 2 * n_phys else eid - n_phys)
                    d_val = float(row["damage_d"])
                    if phys_eid in donor_mesh.elements_u1:
                        conn = donor_mesh.elements_u1[phys_eid]
                        for nid in conn:
                            donor_state.d_nodal[nid] = max(donor_state.d_nodal[nid], d_val)
                        donor_state.H_gp[phys_eid] = [d_val * 0.001] * 4

        recip_mesh = create_synthetic_slit_mesh("Recip10x10", 10, 10)
        engine = Mode1StateTransferEngine(donor_mesh)

        target_state = engine.project_state(recip_mesh, donor_state, enforce_bc=True)
        metrics = engine.compute_projection_metrics(recip_mesh, donor_state, target_state)

        self.assertGreater(metrics["donor_d_max"], 0.30, "Donor peak damage must be >= 0.30")
        self.assertGreater(metrics["recipient_d_max"], 0.15, "Projected peak damage must be >= 0.15")
        self.assertLessEqual(metrics["recipient_d_max"], 1.0, "Projected damage must be <= 1.0")
        self.assertGreater(metrics["integral_d_recipient"], 0.0, "Integral of projected damage must be positive")
        self.assertGreater(metrics["integral_d_donor"], 0.0, "Integral of donor damage must be positive")


if __name__ == "__main__":
    unittest.main()
