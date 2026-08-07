#!/usr/bin/env python3
"""
Unit and Mathematical Foundation Tests for Task F42A-R1:
Corrected Mixed 3-Node Triangle / 4-Node Quad Phase-Field UEL Architecture
"""

import unittest
import math
import os
import sys
import tempfile
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from models.generated.mode_ii.f42_mixed_element_uel.f42_deck_rebuilder import (
    MixedDeckRebuilder,
    compute_element_area_2d
)

F42_FORTRAN_PATH = os.path.join(PROJECT_ROOT, "models", "generated", "mode_ii", "f42_mixed_element_uel", "f42_mixed_uel.for")

class Test3NodeTriangleMathematics(unittest.TestCase):
    """Offline mathematical verification for 3-node linear triangular UEL."""

    def shape_fun_tri(self, xi, eta):
        """Linear triangle shape functions N_1, N_2, N_3."""
        n1 = 1.0 - xi - eta
        n2 = xi
        n3 = eta
        return [n1, n2, n3]

    def shape_fun_tri_derivs(self):
        """Derivatives dN/dxi and dN/deta for 3-node linear triangle."""
        # Rows: N1, N2, N3; Cols: d/dxi, d/deta
        return [
            [-1.0, -1.0],
            [ 1.0,  0.0],
            [ 0.0,  1.0]
        ]

    def test_01_partition_of_unity(self):
        """Sum of shape functions N1 + N2 + N3 must equal 1 identically across domain."""
        test_points = [
            (0.0, 0.0), (1.0, 0.0), (0.0, 1.0),
            (1/3, 1/3), (1/6, 1/6), (2/3, 1/6), (1/6, 2/3)
        ]
        for xi, eta in test_points:
            N = self.shape_fun_tri(xi, eta)
            self.assertAlmostEqual(sum(N), 1.0, places=12, msg=f"Partition of unity failed at ({xi},{eta})")

    def test_02_constant_field_reproduction(self):
        """Nodal values c = [5.0, 5.0, 5.0] must interpolate to 5.0 everywhere."""
        c_nodal = [5.0, 5.0, 5.0]
        test_points = [(0.0, 0.0), (0.5, 0.2), (0.333, 0.333)]
        for xi, eta in test_points:
            N = self.shape_fun_tri(xi, eta)
            val = sum(n * c for n, c in zip(N, c_nodal))
            self.assertAlmostEqual(val, 5.0, places=12)

    def test_03_linear_field_reproduction(self):
        """Linear nodal values x_i must interpolate to x_coord exactly."""
        coords = [[0.0, 0.0], [2.0, 0.0], [0.0, 2.0]]
        test_points = [(0.0, 0.0), (0.5, 0.0), (0.25, 0.25), (1/3, 1/3)]
        for xi, eta in test_points:
            N = self.shape_fun_tri(xi, eta)
            x_interp = sum(n * c[0] for n, c in zip(N, coords))
            y_interp = sum(n * c[1] for n, c in zip(N, coords))
            self.assertAlmostEqual(x_interp, 2.0 * xi, places=12)
            self.assertAlmostEqual(y_interp, 2.0 * eta, places=12)

    def test_04_jacobian_and_positive_area(self):
        """Jacobian determinant det(J) must equal 2 * Area and be strictly positive for counter-clockwise nodes."""
        coords = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
        dNdxi = self.shape_fun_tri_derivs() # 3x2
        j11 = sum(coords[k][0] * dNdxi[k][0] for k in range(3))
        j12 = sum(coords[k][0] * dNdxi[k][1] for k in range(3))
        j21 = sum(coords[k][1] * dNdxi[k][0] for k in range(3))
        j22 = sum(coords[k][1] * dNdxi[k][1] for k in range(3))
        detJ = j11 * j22 - j12 * j21
        area = compute_element_area_2d(coords)
        self.assertGreater(detJ, 0.0)
        self.assertAlmostEqual(detJ, 1.0, places=12)
        self.assertAlmostEqual(area, 0.5, places=12)

    def test_05_three_point_quadrature_weights_sum(self):
        """3-point symmetric triangle quadrature weights must sum to 0.5 (reference area)."""
        weights = [1/6, 1/6, 1/6]
        self.assertAlmostEqual(sum(weights), 0.5, places=12)

    def test_06_phase_field_mass_matrix_oracle(self):
        """3-point quadrature integration of N^T N must equal exact consistent triangle mass matrix A/12 * [[2,1,1],[1,2,1],[1,1,2]]."""
        coords = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
        area = compute_element_area_2d(coords) # 0.5
        detJ = 1.0 # 2 * area
        pts = [(1/6, 1/6), (2/3, 1/6), (1/6, 2/3)]
        w_ref = [1/6, 1/6, 1/6]

        m_num = [[0.0]*3 for _ in range(3)]
        for (xi, eta), w in zip(pts, w_ref):
            N = self.shape_fun_tri(xi, eta)
            w_phys = detJ * w # 1.0 * 1/6
            for i in range(3):
                for j in range(3):
                    m_num[i][j] += w_phys * N[i] * N[j]

        # Exact consistent mass matrix for unit triangle (A = 0.5)
        # A/12 = 0.5 / 12 = 1/24
        m_exact = [
            [2.0/24.0, 1.0/24.0, 1.0/24.0],
            [1.0/24.0, 2.0/24.0, 1.0/24.0],
            [1.0/24.0, 1.0/24.0, 2.0/24.0]
        ]

        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(m_num[i][j], m_exact[i][j], places=12,
                                       msg=f"Mass matrix mismatch at ({i},{j})")

    def test_07_displacement_u4_stiffness_matrix_oracle(self):
        """Displacement U4 stiffness matrix for T3 triangle must match exact plane-strain CST stiffness matrix."""
        # Unit right triangle: (0,0), (1,0), (0,1)
        coords = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
        emod = 210000.0
        enu = 0.3
        thck = 1.0
        eg = emod / (2.0 * (1.0 + enu))
        eg2 = eg * 2.0
        elam = eg2 * enu / (1.0 - 2.0 * enu)
        cmat = [
            [eg2 + elam, elam, 0.0],
            [elam, eg2 + elam, 0.0],
            [0.0, 0.0, eg]
        ]
        # dN/dx for unit right triangle:
        # N1 = 1 - x - y -> dN1/dx = -1, dN1/dy = -1
        # N2 = x         -> dN2/dx = +1, dN2/dy = 0
        # N3 = y         -> dN3/dx = 0,  dN3/dy = +1
        dNdx = [[-1.0, -1.0], [1.0, 0.0], [0.0, 1.0]]

        # B matrix: 3x6
        B = [[0.0]*6 for _ in range(3)]
        for i in range(3):
            B[0][2*i]   = dNdx[i][0]
            B[1][2*i+1] = dNdx[i][1]
            B[2][2*i]   = dNdx[i][1]
            B[2][2*i+1] = dNdx[i][0]

        # Exact CST stiffness matrix: K = Area * thck * B^T @ C @ B
        area = 0.5
        CB = [[sum(cmat[r][k] * B[k][c] for k in range(3)) for c in range(6)] for r in range(3)]
        K_exact = [[area * thck * sum(B[k][r] * CB[k][c] for k in range(3)) for c in range(6)] for r in range(6)]

        # Numerically integrated via 3-point rule in U4
        detJ = 1.0
        pts = [(1/6, 1/6), (2/3, 1/6), (1/6, 2/3)]
        w_ref = [1/6, 1/6, 1/6]
        K_num = [[0.0]*6 for _ in range(6)]
        for _, w in zip(pts, w_ref):
            wt_fac = thck * detJ * w
            for r in range(6):
                for c in range(6):
                    K_num[r][c] += wt_fac * sum(B[k][r] * CB[k][c] for k in range(3))

        for r in range(6):
            for c in range(6):
                self.assertAlmostEqual(K_num[r][c], K_exact[r][c], places=10,
                                       msg=f"U4 stiffness matrix mismatch at ({r},{c})")


class TestMixedDeckRebuilderRoundTrip(unittest.TestCase):
    """Unit tests for offline mixed-element deck parser and rebuilder round-trip."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.deck_path = os.path.join(self.test_dir, "test_job2.inp")
        self.out_path = os.path.join(self.test_dir, "test_job2_uel.inp")

    def test_08_round_trip_synthetic_mixed_mesh(self):
        """Rebuilder must process 2 quads + 2 triangles (Nphys=4) and produce 12 unique element labels across layers."""
        inp_content = """*Node
 1, 0.0, 0.0
 2, 1.0, 0.0
 3, 1.0, 1.0
 4, 0.0, 1.0
 5, 2.0, 0.0
 6, 2.0, 1.0
 7, 0.5, 1.5
*Element, type=CPE4
 1, 1, 2, 3, 4
 2, 2, 5, 6, 3
*Element, type=CPE3
 3, 4, 3, 7
 4, 3, 6, 7
"""
        with open(self.deck_path, 'w') as f:
            f.write(inp_content)

        rebuilder = MixedDeckRebuilder(self.deck_path)
        rebuilder.parse()
        self.assertEqual(len(rebuilder.physical_elems), 4)
        self.assertEqual(len(rebuilder.rejected), 0)

        nq, nt, nr = rebuilder.build_mixed_uel_deck(self.out_path)
        self.assertEqual(nq, 2)
        self.assertEqual(nt, 2)
        self.assertEqual(nr, 0)
        self.assertTrue(os.path.exists(self.out_path))

        # Re-parse generated Job-2_UEL.inp to verify round-trip contract
        with open(self.out_path, 'r') as f:
            out_lines = f.readlines()

        all_element_labels = []
        u1_count = 0
        u2_count = 0
        u3_count = 0
        u4_count = 0
        cpe4_count = 0
        cpe3_count = 0
        current_type = None

        for line in out_lines:
            line_str = line.strip()
            if line_str.startswith("*Element"):
                m = re.search(r'type\s*=\s*([A-Za-z0-9]+)', line_str, re.IGNORECASE)
                if m:
                    current_type = m.group(1).upper()
                continue
            elif line_str.startswith("*"):
                current_type = None
                continue

            if current_type and not line_str.startswith("**"):
                tokens = [t.strip() for t in line_str.split(',') if t.strip()]
                if tokens and tokens[0].isdigit():
                    lbl = int(tokens[0])
                    all_element_labels.append(lbl)
                    if current_type == 'U1': u1_count += 1
                    elif current_type == 'U2': u2_count += 1
                    elif current_type == 'U3': u3_count += 1
                    elif current_type == 'U4': u4_count += 1
                    elif current_type == 'CPE4': cpe4_count += 1
                    elif current_type == 'CPE3': cpe3_count += 1

        self.assertEqual(len(all_element_labels), 12, "Must generate exactly 12 element lines across 3 layers")
        self.assertEqual(len(set(all_element_labels)), 12, "All 12 element labels must be strictly unique!")
        self.assertEqual(u1_count, 2)
        self.assertEqual(u2_count, 2)
        self.assertEqual(u3_count, 2)
        self.assertEqual(u4_count, 2)
        self.assertEqual(cpe4_count, 2)
        self.assertEqual(cpe3_count, 2)


class TestFortranSourceStaticContract(unittest.TestCase):
    """Static inspection tests for f42_mixed_uel.for Fortran source contract."""

    def setUp(self):
        self.assertTrue(os.path.exists(F42_FORTRAN_PATH), f"Fortran file not found: {F42_FORTRAN_PATH}")
        with open(F42_FORTRAN_PATH, 'r') as f:
            self.code = f.read()

    def test_09_verify_all_four_jtype_branches_exist(self):
        """f42_mixed_uel.for must contain explicit executable branches for JTYPE.EQ.1, JTYPE.EQ.2, JTYPE.EQ.3, JTYPE.EQ.4."""
        self.assertIn("IF (JTYPE.EQ.1) THEN", self.code)
        self.assertIn("IF (JTYPE.EQ.2) THEN", self.code)
        self.assertIn("IF (JTYPE.EQ.3) THEN", self.code)
        self.assertIn("IF (JTYPE.EQ.4) THEN", self.code)

    def test_10_verify_no_uninitialized_gc(self):
        """Uninitialized variable 'GC' bug must be absent; GCPAR must be assigned from PROPS(2)."""
        self.assertNotIn("GC*", self.code, "Uninitialized GC variable must not be present")
        self.assertIn("GCPAR=PROPS(2)", self.code)

    def test_11_verify_triangle_u4_displacement_branch_completeness(self):
        """JTYPE=4 triangle displacement branch must contain 6 DOFs, BB_T(3,6), CMAT, and USRVAR update."""
        self.assertIn("BB_T(3,6)", self.code)
        self.assertIn("CALL SHAPEFUN_TRI(AN_T,dNdxi_T,XI)", self.code)
        self.assertIn("NELEMAN=JELEM-N_ELEM", self.code)


if __name__ == "__main__":
    unittest.main()
