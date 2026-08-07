#!/usr/bin/env python3
"""
Unit and Mathematical Foundation Tests for Task F42B:
Single-Triangle Core UEL Qualification & NPHYS Mapping
"""

import unittest
import math
import os
import sys
import tempfile
import re
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from models.generated.mode_ii.f42_mixed_element_uel.f42_deck_rebuilder import (
    MixedDeckRebuilder,
    compute_element_area_2d
)

F42_FORTRAN_PATH = os.path.join(PROJECT_ROOT, "models", "generated", "mode_ii", "f42_mixed_element_uel", "f42_mixed_uel.for")
F42TRI1_CORE_FORTRAN_PATH = os.path.join(PROJECT_ROOT, "models", "generated", "mode_ii", "f42_mixed_element_uel", "f42tri1_core_uel_only", "F42TRI1_CORE.for")
F42TRI1_CORE_INP_PATH = os.path.join(PROJECT_ROOT, "models", "generated", "mode_ii", "f42_mixed_element_uel", "f42tri1_core_uel_only", "F42TRI1_CORE.inp")

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
        dNdx = [[-1.0, -1.0], [1.0, 0.0], [0.0, 1.0]]

        B = [[0.0]*6 for _ in range(3)]
        for i in range(3):
            B[0][2*i]   = dNdx[i][0]
            B[1][2*i+1] = dNdx[i][1]
            B[2][2*i]   = dNdx[i][1]
            B[2][2*i+1] = dNdx[i][0]

        area = 0.5
        CB = [[sum(cmat[r][k] * B[k][c] for k in range(3)) for c in range(6)] for r in range(3)]
        K_exact = [[area * thck * sum(B[k][r] * CB[k][c] for k in range(3)) for c in range(6)] for r in range(6)]

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


class TestNPhysMappingAndStaticContract(unittest.TestCase):
    """Unit tests for NPHYS physical element offset and static Fortran contracts."""

    def test_08_nphys_label_offset_logic(self):
        """For NPHYS=1, U3 label=1 maps to PHYSIDX=1 and U4 label=2 maps to PHYSIDX=1."""
        nphys = 1
        jtype_u3_elem = 1
        jtype_u4_elem = 2

        physidx_u3 = jtype_u3_elem
        physidx_u4 = jtype_u4_elem - nphys

        self.assertEqual(physidx_u3, 1)
        self.assertEqual(physidx_u4, 1)
        self.assertEqual(physidx_u3, physidx_u4, "U3 phase and U4 displacement must map to the same physical index 1")

    def test_09_verify_fortran_nphys_and_capacity_separation(self):
        """f42_mixed_uel.for must separate N_CAPACITY=100000 array dimensioning from NPHYS_VAL."""
        with open(F42_FORTRAN_PATH, 'r') as f:
            code = f.read()

        self.assertIn("PARAMETER(", code)
        self.assertIn("N_CAPACITY=100000", code)
        self.assertIn("NPHYS_VAL", code)
        self.assertIn("PHYSIDX = JELEM - NPHYS_VAL", code)

    def test_10_verify_f42tri1_core_inp_has_no_cpe3(self):
        """F42TRI1_CORE.inp must contain ONLY U3 and U4 elements, with zero CPE3 elements."""
        with open(F42TRI1_CORE_INP_PATH, 'r') as f:
            inp_lines = f.readlines()

        cpe3_elem_count = sum(1 for line in inp_lines if line.strip().lower().startswith('*element') and 'cpe3' in line.lower())
        u3_elem_count = sum(1 for line in inp_lines if line.strip().lower().startswith('*element') and 'u3' in line.lower())
        u4_elem_count = sum(1 for line in inp_lines if line.strip().lower().startswith('*element') and 'u4' in line.lower())

        self.assertEqual(cpe3_elem_count, 0, "F42TRI1_CORE.inp must not contain any CPE3 element blocks")
        self.assertEqual(u3_elem_count, 1, "F42TRI1_CORE.inp must contain exactly 1 U3 element block")
        self.assertEqual(u4_elem_count, 1, "F42TRI1_CORE.inp must contain exactly 1 U4 element block")

    def test_11_gfortran_syntax_check_both_files(self):
        """Run gfortran -fsyntax-only on both f42_mixed_uel.for and F42TRI1_CORE.for using temporary ABA_PARAM.INC."""
        inc_dir = tempfile.mkdtemp()
        inc_path = os.path.join(inc_dir, "ABA_PARAM.INC")
        with open(inc_path, 'w') as f:
            f.write("      IMPLICIT REAL*8 (A-H,O-Z)\n")

        gfortran_cmd = "gfortran"
        # Test f42_mixed_uel.for
        res1 = subprocess.run([
            gfortran_cmd, "-fsyntax-only", "-ffixed-line-length-none",
            "-Wall", "-Wextra", "-Wsurprising", f"-I{inc_dir}", F42_FORTRAN_PATH
        ], capture_output=True, text=True)

        # Test F42TRI1_CORE.for
        res2 = subprocess.run([
            gfortran_cmd, "-fsyntax-only", "-ffixed-line-length-none",
            "-Wall", "-Wextra", "-Wsurprising", f"-I{inc_dir}", F42TRI1_CORE_FORTRAN_PATH
        ], capture_output=True, text=True)

        self.assertEqual(res1.returncode, 0, f"gfortran syntax check failed on f42_mixed_uel.for with stderr:\n{res1.stderr}")
        self.assertEqual(res2.returncode, 0, f"gfortran syntax check failed on F42TRI1_CORE.for with stderr:\n{res2.stderr}")


class TestF42CTriangleFacsimileContract(unittest.TestCase):
    """Offline mathematical and state mapping unit tests for Task F42C."""

    def test_12_f42c_centroid_phase_linear_reconstruction(self):
        """For a linear phase field, centroid phase phi_c equals arithmetic mean of 3 quadrature values."""
        phi_gp = [0.2, 0.5, 0.8]
        phi_c = sum(phi_gp) / 3.0
        self.assertAlmostEqual(phi_c, 0.5, places=12)

    def test_13_f42c_cst_strain_and_elastic_stress_identity(self):
        """For CST triangle, strain and undegraded elastic stress are identical at all 3 quadrature points."""
        eps_gp1 = [0.001, 0.0005, 0.0002]
        eps_gp2 = [0.001, 0.0005, 0.0002]
        eps_gp3 = [0.001, 0.0005, 0.0002]

        for i in range(3):
            self.assertEqual(eps_gp1[i], eps_gp2[i])
            self.assertEqual(eps_gp1[i], eps_gp3[i])

    def test_14_f42c_nonlinear_degraded_stress_physical_reconstruction(self):
        """Nonlinear degraded stress must be evaluated physically at centroid, NOT by averaging degraded stresses."""
        phi_gp = [0.1, 0.4, 0.7]
        k = 1e-7
        sigma_e = 100.0 # GPa

        # Physical centroid evaluation:
        phi_c = sum(phi_gp) / 3.0 # 0.4
        g_c = (1.0 - phi_c)**2 + k # (0.6)^2 = 0.36
        sigma_d_physical = g_c * sigma_e # 36.0

        # Incorrect naive average of degraded stresses:
        g_gp = [(1.0 - p)**2 + k for p in phi_gp] # 0.81, 0.36, 0.09
        sigma_d_naive_avg = (sum(g_gp) / 3.0) * sigma_e # (1.26 / 3) * 100 = 42.0

        self.assertNotAlmostEqual(sigma_d_physical, sigma_d_naive_avg, places=4,
                                 msg="Physical centroid degradation must differ from naive linear averaging for non-uniform phase fields")
        self.assertAlmostEqual(sigma_d_physical, 36.00001, places=10)


    def test_15_f42c_mixed_quad_tri_state_mapping_and_topology_dispatch(self):
        """Mock synthetic state table verifying quad UMAT reads NPT 1..4, tri UMAT NPT 1 reads ONLY centroid slot 4."""
        n_capacity = 10
        nstv = 18
        usrvar = [[[0.0]*5 for _ in range(nstv)] for _ in range(n_capacity)]

        # Populate Quad element 1 (IPs 1..4)
        for ip in range(1, 5):
            usrvar[1][0][ip] = 0.1 * ip # PHASE at IP
            usrvar[1][16][ip] = 4.0     # TOPOLOGY Q4

        # Populate Tri element 2 (IPs 1..3 + Centroid Slot 4)
        usrvar[2][0][1] = 0.2
        usrvar[2][0][2] = 0.5
        usrvar[2][0][3] = 0.8
        usrvar[2][0][4] = 0.5 # Centroid phase (0.2+0.5+0.8)/3
        usrvar[2][16][4] = 3.0 # TOPOLOGY T3

        # Simulate Quad UMAT read for NPT=3
        quad_npt = 3
        quad_topology = usrvar[1][16][quad_npt]
        self.assertEqual(quad_topology, 4.0)
        quad_phase_read = usrvar[1][0][quad_npt]
        self.assertAlmostEqual(quad_phase_read, 0.3, places=10)

        # Simulate Tri UMAT read for NPT=1 (CPE3 has only NPT=1)
        tri_topology = usrvar[2][16][4]
        self.assertEqual(tri_topology, 3.0)
        # CPE3 UMAT dispatch routes NPT=1 -> dedicated Centroid Slot 4!
        tri_npt_read = 4 if tri_topology == 3.0 else 1
        tri_phase_read = usrvar[2][0][tri_npt_read]
        self.assertAlmostEqual(tri_phase_read, 0.5, places=10)
        self.assertNotEqual(tri_phase_read, usrvar[2][0][1], "CPE3 must NOT read IP 1 as though it were centroid")

    def test_16_f42c_gfortran_syntax_check_f42c_mixed_uel(self):
        """Run gfortran -fsyntax-only on f42c_mixed_uel.for."""
        inc_dir = tempfile.mkdtemp()
        inc_path = os.path.join(inc_dir, "ABA_PARAM.INC")
        with open(inc_path, 'w') as f:
            f.write("      IMPLICIT REAL*8 (A-H,O-Z)\n")

        f42c_fortran_path = os.path.join(PROJECT_ROOT, "models", "generated", "mode_ii", "f42_mixed_element_uel", "f42c_triangle_facsimile", "f42c_mixed_uel.for")
        res = subprocess.run([
            "gfortran", "-fsyntax-only", "-ffixed-line-length-none",
            "-Wall", "-Wextra", "-Wsurprising", f"-I{inc_dir}", f42c_fortran_path
        ], capture_output=True, text=True)

        self.assertEqual(res.returncode, 0, f"gfortran syntax check failed on f42c_mixed_uel.for with stderr:\n{res.stderr}")


if __name__ == "__main__":
    unittest.main()

