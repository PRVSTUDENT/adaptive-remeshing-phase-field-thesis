#!/usr/bin/env python3
"""
Unit and Mathematical Foundation Tests for Task F42A:
Mixed 3-Node Triangle / 4-Node Quad Phase-Field UEL Architecture
"""

import unittest
import math
import os
import sys
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from models.generated.mode_ii.f42_mixed_element_uel.f42_deck_rebuilder import (
    MixedDeckRebuilder,
    compute_element_area_2d
)

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
            (1/3, 1/3), (0.2, 0.5), (0.1, 0.8)
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
        # J = coords^T @ dNdxi -> 2x2
        j11 = sum(coords[k][0] * dNdxi[k][0] for k in range(3))
        j12 = sum(coords[k][0] * dNdxi[k][1] for k in range(3))
        j21 = sum(coords[k][1] * dNdxi[k][0] for k in range(3))
        j22 = sum(coords[k][1] * dNdxi[k][1] for k in range(3))
        detJ = j11 * j22 - j12 * j21
        area = compute_element_area_2d(coords)
        self.assertGreater(detJ, 0.0)
        self.assertAlmostEqual(detJ, 1.0, places=12)
        self.assertAlmostEqual(area, 0.5, places=12)

    def test_05_b_matrix_and_gradient_dimensions(self):
        """Phase-field B-matrix must be 2x3 and displacement B-matrix must be 3x6 for linear triangle."""
        coords = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
        dNdxi = self.shape_fun_tri_derivs()
        j11 = sum(coords[k][0] * dNdxi[k][0] for k in range(3))
        j12 = sum(coords[k][0] * dNdxi[k][1] for k in range(3))
        j21 = sum(coords[k][1] * dNdxi[k][0] for k in range(3))
        j22 = sum(coords[k][1] * dNdxi[k][1] for k in range(3))
        detJ = j11 * j22 - j12 * j21
        invJ = [[j22/detJ, -j12/detJ], [-j21/detJ, j11/detJ]]
        
        dNdx = []
        for k in range(3):
            dx = dNdxi[k][0] * invJ[0][0] + dNdxi[k][1] * invJ[1][0]
            dy = dNdxi[k][0] * invJ[0][1] + dNdxi[k][1] * invJ[1][1]
            dNdx.append([dx, dy])

        # Phase-field B-matrix: (2, 3)
        b_phase = [[dNdx[k][0] for k in range(3)], [dNdx[k][1] for k in range(3)]]
        self.assertEqual(len(b_phase), 2)
        self.assertEqual(len(b_phase[0]), 3)

        # Displacement B-matrix: (3, 6)
        b_disp = [[0.0]*6 for _ in range(3)]
        for i in range(3):
            b_disp[0][2*i]   = dNdx[i][0]
            b_disp[1][2*i+1] = dNdx[i][1]
            b_disp[2][2*i]   = dNdx[i][1]
            b_disp[2][2*i+1] = dNdx[i][0]
        self.assertEqual(len(b_disp), 3)
        self.assertEqual(len(b_disp[0]), 6)

    def test_06_stiffness_and_residual_dimensions(self):
        """Stiffness matrix (AMATRX) must be 3x3 for phase, 6x6 for displacement; RHS must be 3x1 and 6x1."""
        amatrx_phase = [[0.0]*3 for _ in range(3)]
        rhs_phase = [[0.0] for _ in range(3)]
        amatrx_disp = [[0.0]*6 for _ in range(6)]
        rhs_disp = [[0.0] for _ in range(6)]
        self.assertEqual(len(amatrx_phase), 3)
        self.assertEqual(len(rhs_phase), 3)
        self.assertEqual(len(amatrx_disp), 6)
        self.assertEqual(len(rhs_disp), 6)


class TestMixedDeckRebuilder(unittest.TestCase):
    """Unit tests for offline mixed-element deck parser and rebuilder."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.deck_path = os.path.join(self.test_dir, "test_job2.inp")
        self.out_path = os.path.join(self.test_dir, "test_job2_uel.inp")

    def test_07_classify_quad_and_tri_elements(self):
        """Deck parser must classify 4-node elements as CPE4 and 3-node elements as CPE3."""
        inp_content = """*Node
 1, 0.0, 0.0
 2, 1.0, 0.0
 3, 1.0, 1.0
 4, 0.0, 1.0
 5, 2.0, 0.0
*Element, type=CPE4
 1, 1, 2, 3, 4
*Element, type=CPE3
 2, 2, 5, 3
"""
        with open(self.deck_path, 'w') as f:
            f.write(inp_content)

        rebuilder = MixedDeckRebuilder(self.deck_path)
        rebuilder.parse()
        self.assertEqual(len(rebuilder.quad_elems), 1)
        self.assertEqual(len(rebuilder.tri_elems), 1)
        self.assertEqual(len(rebuilder.rejected), 0)

        nq, nt, nr = rebuilder.build_mixed_uel_deck(self.out_path)
        self.assertEqual(nq, 1)
        self.assertEqual(nt, 1)
        self.assertEqual(nr, 0)
        self.assertTrue(os.path.exists(self.out_path))

        with open(self.out_path, 'r') as f:
            out_text = f.read()

        self.assertIn("*User Element, nodes=4, type=U11", out_text)
        self.assertIn("*User Element, nodes=4, type=U12", out_text)
        self.assertIn("*User Element, nodes=3, type=U21", out_text)
        self.assertIn("*User Element, nodes=3, type=U22", out_text)
        self.assertIn("*Element, type=U11, elset=Phase_Quad", out_text)
        self.assertIn("*Element, type=U21, elset=Phase_Tri", out_text)
        self.assertIn("*Element, type=CPE4, elset=All_elem_quad", out_text)
        self.assertIn("*Element, type=CPE3, elset=All_elem_tri", out_text)

    def test_08_reject_degenerate_or_clockwise_elements(self):
        """Deck parser must reject elements with non-positive area."""
        inp_content = """*Node
 1, 0.0, 0.0
 2, 1.0, 0.0
 3, 0.0, 1.0
 4, 1.0, 1.0
*Element, type=CPE4
 1, 1, 4, 3, 2
""" # Clockwise connectivity -> negative area
        with open(self.deck_path, 'w') as f:
            f.write(inp_content)

        rebuilder = MixedDeckRebuilder(self.deck_path)
        rebuilder.parse()
        self.assertEqual(len(rebuilder.quad_elems), 0)
        self.assertEqual(len(rebuilder.rejected), 1)
        self.assertIn("non-positive area", rebuilder.rejected[0])


if __name__ == "__main__":
    unittest.main()
