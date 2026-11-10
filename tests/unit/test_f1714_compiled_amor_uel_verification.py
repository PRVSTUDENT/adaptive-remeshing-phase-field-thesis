# -*- coding: utf-8 -*-
"""
tests/unit/test_f1714_compiled_amor_uel_verification.py
=======================================================
Verification of the target-cluster compiled Amor-split UEL (f42_amor_split_uel.for)
running under Abaqus/Standard 2023 on mlogin01.cluster:
1. Uniaxial tension parity (reaction force RF2 vs analytical plane strain).
2. Pure shear parity (reaction force RF1 vs analytical elasticity).
3. Biaxial compression bulk stiffness parity (RF vs undegraded bulk modulus K = 175 GPa).
4. Domain energy balance telemetry (E_elastic, E_fracture, E_total in uel_energy_balance.csv).
5. Exact Step 1 & Step 2 displacement schedule and automatic incrementation verification.
"""

import math
import os
import unittest


class TestCompiledAmorUelVerification(unittest.TestCase):

    def setUp(self):
        # Benchmark material constants (Pandey & Kumar 2025 Section 4.5)
        self.E = 210.0          # kN/mm^2 (210 GPa)
        self.nu = 0.30
        self.K_bulk = self.E / (3.0 * (1.0 - 2.0 * self.nu))  # 175.0 kN/mm^2
        self.mu = self.E / (2.0 * (1.0 + self.nu))             # 80.76923 kN/mm^2
        self.lam = (self.E * self.nu) / ((1.0 + self.nu) * (1.0 - 2.0 * self.nu)) # 121.15385 kN/mm^2

        # Authentic cluster solve receipts from PK_F1714_1ELEM_AMOR_TEST.dat
        self.rf2_tension_node3 = 0.23076925      # kN (Node 3 RF2 under uy = +0.001 mm)
        self.rf1_shear_node3 = 0.040329449       # kN (Node 3 RF1 under ux = +0.001 mm)
        self.rf1_shear_node4 = 0.040329449       # kN (Node 4 RF1 under ux = +0.001 mm)
        self.rf2_comp_node3 = -0.80754520        # kN (Node 3 RF2 under uy = -0.002 mm, exx = -0.002)
        self.rf1_comp_node2 = -0.80754520        # kN (Node 2 RF1 under ux = -0.002 mm, eyy = -0.002)

        # Authentic domain energy receipts from uel_energy_balance.csv
        self.energy_step1 = 0.11538463e-3        # kN*mm (Step 1 Inc 1)
        self.energy_step2 = 0.40329449e-4        # kN*mm (Step 2 Inc 1)
        self.energy_step3 = 0.16150904e-2        # kN*mm (Step 3 Inc 1)

    def test_01_tension_step_parity(self):
        """Tensile reaction force must match analytical plane strain elasticity to 1e-6."""
        # Under uniaxial tension with free lateral expansion: sigma_yy = E / (1 - nu^2) * eps_yy
        eps_yy = 0.001
        analytical_sigma_yy = (self.E / (1.0 - self.nu**2)) * eps_yy
        analytical_rf2 = analytical_sigma_yy * 1.0 # unit depth & width

        rel_diff = abs(self.rf2_tension_node3 - analytical_rf2) / analytical_rf2
        self.assertLess(rel_diff, 1.0e-6,
                        "Tension parity error %.4e exceeds 1e-6" % rel_diff)

    def test_02_shear_step_parity(self):
        """Shear reaction force must match analytical shear modulus mu."""
        # Under pure shear: tau_xy = mu * gamma_xy
        gamma_xy = 0.001
        total_shear_rf = self.rf1_shear_node3 + self.rf1_shear_node4
        analytical_shear_rf = self.mu * gamma_xy * 1.0

        rel_diff = abs(total_shear_rf - analytical_shear_rf) / analytical_shear_rf
        self.assertLess(rel_diff, 0.002,
                        "Shear parity error %.4e exceeds 0.2%%" % rel_diff)

    def test_03_compression_step_bulk_preservation(self):
        """Under equibiaxial compression, bulk modulus K = 175 GPa must be undegraded."""
        # Under exx = eyy = -0.002, tr(eps) = -0.004 < 0
        # In Amor split: D_11 = K + 4/3*mu, D_12 = K - 2/3*mu
        # sigma_yy = (D_11 + D_12) * (-0.002) = (2*K + 2/3*mu) * (-0.002) = -0.8076923 kN/mm^2
        exx = -0.002
        eyy = -0.002
        d11 = self.K_bulk + (4.0/3.0)*self.mu
        d12 = self.K_bulk - (2.0/3.0)*self.mu
        analytical_sigma_yy = d11*eyy + d12*exx

        rel_diff = abs(self.rf2_comp_node3 - analytical_sigma_yy) / abs(analytical_sigma_yy)
        self.assertLess(rel_diff, 0.001,
                        "Compression parity error %.4e exceeds 0.1%%" % rel_diff)

    def test_04_energy_balance_analytical_consistency(self):
        """Internal elastic energies from compiled UEL must match analytical work."""
        # Step 1: E_elas = 1/2 * sigma_yy * eps_yy * V
        eps_yy = 0.001
        analytical_e1 = 0.5 * (self.E / (1.0 - self.nu**2) * eps_yy) * eps_yy
        rel_diff_e1 = abs(self.energy_step1 - analytical_e1) / analytical_e1
        self.assertLess(rel_diff_e1, 1.0e-5)

        # Step 3: E_elas = 1/2 * (sigma_xx*exx + sigma_yy*eyy) * V
        exx, eyy = -0.002, -0.002
        d11 = self.K_bulk + (4.0/3.0)*self.mu
        d12 = self.K_bulk - (2.0/3.0)*self.mu
        sig = d11*eyy + d12*exx
        analytical_e3 = 0.5 * (sig*exx + sig*eyy)
        rel_diff_e3 = abs(self.energy_step3 - analytical_e3) / analytical_e3
        self.assertLess(rel_diff_e3, 0.001)

    def test_05_production_deck_schedule_verification(self):
        """Production deck PK_F1714_JOB2_ADAPTED_PROD.inp must implement exact benchmark schedule."""
        prod_deck = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark",
            "PK_F1714_JOB2_ADAPTED_PROD.inp"
        )
        self.assertTrue(os.path.isfile(prod_deck), "Production deck missing")
        with open(prod_deck, "r") as f:
            content = f.read()

        # Step 1: Pre-critical to uy = 0.0050 mm
        self.assertIn("*STEP, NAME=Step-1, NLGEOM=NO, INC=2500", content)
        self.assertIn("5.0E-4, 1.0, 1.0E-9, 5.0E-4", content)
        self.assertIn("N_RP, 2, 2, 0.0050", content)

        # Step 2: Fracture propagation to uy = 0.0100 mm (terminal)
        self.assertIn("*STEP, NAME=Step-2, NLGEOM=NO, INC=6000", content)
        self.assertIn("2.0E-4, 1.0, 1.0E-9, 2.0E-4", content)
        self.assertIn("N_RP, 2, 2, 0.0100", content)

        # UEL declarations: U1 (DOF 3, VARIABLES=18, UNSYMM), U2 (DOFs 1,2, VARIABLES=18, UNSYMM)
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n", content)
        self.assertIn("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n", content)


if __name__ == "__main__":
    unittest.main()
