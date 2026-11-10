# -*- coding: utf-8 -*-
"""
tests/unit/test_f1714_compiled_amor_uel_verification.py
=======================================================
Verification of the target-cluster compiled Amor-split UEL (f42_amor_split_uel.for)
running under Abaqus/Standard 2023 on mlogin01.cluster.

This test suite reads and dynamically parses the authentic Abaqus solver output files
stored in results/validation/:
- PK_F1714_1ELEM_AMOR_TEST.dat (Intact elastic 1-element solve)
- PK_F1714_1ELEM_AMOR_DAMAGED_TEST.dat (Damaged-state d = 0.5 solve)
- f1714_1elem_uel_energy_balance.csv (Transactional energy balance telemetry)

Verifications:
1. File hash authentication (SHA-256 of authentic solver outputs).
2. Uniaxial tension parity (reaction force RF2 vs analytical plane strain).
3. Pure shear parity (reaction force RF1 vs analytical elasticity).
4. Biaxial compression bulk stiffness parity (RF vs undegraded bulk modulus K = 175 GPa).
5. Domain energy balance telemetry (E_elastic, E_fracture, E_total in uel_energy_balance.csv).
6. Production deck schedule and cutback safeguards verification.
7. Damaged-state uniaxial tension parity (exact 75% degradation, g(0.5) = 0.25).
8. Damaged-state pure shear parity (exact 75% degradation, g(0.5) = 0.25).
9. Damaged-state equibiaxial compression (K = 175 GPa 100% PRESERVED, deviatoric degraded).
10. Damaged-state fracture energy reconciliation: authentic CSV string '0.42187500E-01'
    evaluates to 0.0421875 kN*mm, matching analytical Gc/(2*l0)*d^2*A to 8 decimal places.
"""

import csv
import hashlib
import math
import os
import re
import unittest


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def parse_dat_node_tables(filepath):
    """Parses node print tables from an Abaqus .dat file."""
    with open(filepath, "r") as f:
        text = f.read()
    pattern = r"THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET (\w+).*?NODE FOOT-.*?\n\s*\n(.*?)\n\s*MAXIMUM"
    matches = re.findall(pattern, text, re.DOTALL)
    tables = []
    for nset, body in matches:
        rows = {}
        for line in body.strip().splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                node = int(parts[0])
                u_val = float(parts[1])
                rf_val = float(parts[2])
                rows[node] = (u_val, rf_val)
        tables.append({"nset": nset, "nodes": rows})
    return tables


def parse_energy_csv(filepath):
    """Parses transactional UEL domain energy balance CSV."""
    rows = []
    with open(filepath, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) >= 7:
                rows.append({
                    "step": int(row[0]),
                    "inc": int(row[1]),
                    "tot_time": float(row[2]),
                    "step_time": float(row[3]),
                    "e_elas": float(row[4]),
                    "e_frac": float(row[5]),
                    "e_tot": float(row[6]),
                    "raw_e_frac_str": row[5].strip()
                })
    return rows


class TestCompiledAmorUelVerification(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Locate authentic solver receipts in results/validation/
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        val_dir = os.path.join(repo_root, "results", "validation")

        cls.intact_dat_path = os.path.join(val_dir, "PK_F1714_1ELEM_AMOR_TEST.dat")
        cls.damaged_dat_path = os.path.join(val_dir, "PK_F1714_1ELEM_AMOR_DAMAGED_TEST.dat")
        cls.energy_csv_path = os.path.join(val_dir, "f1714_1elem_uel_energy_balance.csv")

        # Benchmark material constants (Pandey & Kumar 2025 Section 4.5)
        cls.E = 210.0          # kN/mm^2 (210 GPa)
        cls.nu = 0.30
        cls.K_bulk = cls.E / (3.0 * (1.0 - 2.0 * cls.nu))  # 175.0 kN/mm^2
        cls.mu = cls.E / (2.0 * (1.0 + cls.nu))             # 80.76923 kN/mm^2
        cls.lam = (cls.E * cls.nu) / ((1.0 + cls.nu) * (1.0 - 2.0 * cls.nu)) # 121.15385 kN/mm^2

        # Expected SHA-256 hashes of authentic target-cluster outputs
        cls.expected_intact_dat_sha = "7b936e08db0a33ecce4f93a55ec9baac902f25d9905c16b6ef5a77774af16054"
        cls.expected_damaged_dat_sha = "d54c8aa37d6794f0c24dcb556bdd7237c24c335336f318900164d7b884e41621"
        cls.expected_energy_csv_sha = "15da52b27dcbd86ff831b153e7cb2d5d8fcb2079ceab521c477392c2887a1d72"

        # Dynamically parse authentic outputs during test setup
        cls.intact_tables = parse_dat_node_tables(cls.intact_dat_path)
        cls.damaged_tables = parse_dat_node_tables(cls.damaged_dat_path)
        cls.energy_rows = parse_energy_csv(cls.energy_csv_path)

    def test_00_solver_receipts_hash_authentication(self):
        """Authentic Abaqus solver output files must match verified SHA-256 checksums."""
        self.assertTrue(os.path.isfile(self.intact_dat_path), "Intact .dat file missing")
        self.assertTrue(os.path.isfile(self.damaged_dat_path), "Damaged .dat file missing")
        self.assertTrue(os.path.isfile(self.energy_csv_path), "Energy CSV file missing")

        intact_sha = sha256_file(self.intact_dat_path)
        damaged_sha = sha256_file(self.damaged_dat_path)
        energy_sha = sha256_file(self.energy_csv_path)

        self.assertEqual(intact_sha, self.expected_intact_dat_sha, "Intact .dat SHA-256 mismatch")
        self.assertEqual(damaged_sha, self.expected_damaged_dat_sha, "Damaged .dat SHA-256 mismatch")
        self.assertEqual(energy_sha, self.expected_energy_csv_sha, "Energy CSV SHA-256 mismatch")

    def test_01_tension_step_parity(self):
        """Tensile reaction force parsed from authentic .dat must match analytical elasticity."""
        # Table 0: Step 1 N_TOP (Node 3 and 4)
        u2, rf2 = self.intact_tables[0]["nodes"][3]
        eps_yy = u2
        analytical_sigma_yy = (self.E / (1.0 - self.nu**2)) * eps_yy
        analytical_rf2 = analytical_sigma_yy * 1.0  # unit depth & width (0.23076923 kN)

        rel_diff = abs(rf2 - analytical_rf2) / analytical_rf2
        self.assertLess(rel_diff, 1.0e-6,
                        "Tension parity error %.4e exceeds 1e-6 (RF2=%.8f)" % (rel_diff, rf2))

    def test_02_shear_step_parity(self):
        """Shear reaction force parsed from authentic .dat must match analytical shear modulus mu."""
        # Table 2: Step 2 N_TOP (Node 3 and 4)
        u1_3, rf1_3 = self.intact_tables[2]["nodes"][3]
        u1_4, rf1_4 = self.intact_tables[2]["nodes"][4]
        total_shear_rf = rf1_3 + rf1_4
        gamma_xy = u1_3
        analytical_shear_rf = self.mu * gamma_xy * 1.0  # 0.0807692 kN

        rel_diff = abs(total_shear_rf - analytical_shear_rf) / analytical_shear_rf
        self.assertLess(rel_diff, 0.002,
                        "Shear parity error %.4e exceeds 0.2%%" % rel_diff)

    def test_03_compression_step_bulk_preservation(self):
        """Under equibiaxial compression, bulk modulus K = 175 GPa must be undegraded."""
        # Table 3: Step 3 N_TOP (Node 3)
        u2, rf2 = self.intact_tables[3]["nodes"][3]
        exx = u2
        eyy = u2
        d11 = self.K_bulk + (4.0/3.0)*self.mu
        d12 = self.K_bulk - (2.0/3.0)*self.mu
        analytical_sigma_yy = d11*eyy + d12*exx  # -0.8076923 kN/mm^2

        rel_diff = abs(rf2 - analytical_sigma_yy) / abs(analytical_sigma_yy)
        self.assertLess(rel_diff, 0.001,
                        "Compression parity error %.4e exceeds 0.1%%" % rel_diff)

    def test_04_energy_balance_analytical_consistency(self):
        """Internal elastic energies parsed from authentic CSV must match analytical work."""
        # Row 0: Intact Step 1 Inc 1
        e_elas_1 = self.energy_rows[0]["e_elas"]
        eps_yy = 0.001
        analytical_e1 = 0.5 * (self.E / (1.0 - self.nu**2) * eps_yy) * eps_yy
        rel_diff_e1 = abs(e_elas_1 - analytical_e1) / analytical_e1
        self.assertLess(rel_diff_e1, 1.0e-5)

        # Row 2: Intact Step 3 Inc 1
        e_elas_3 = self.energy_rows[2]["e_elas"]
        exx, eyy = -0.002, -0.002
        d11 = self.K_bulk + (4.0/3.0)*self.mu
        d12 = self.K_bulk - (2.0/3.0)*self.mu
        sig = d11*eyy + d12*exx
        analytical_e3 = 0.5 * (sig*exx + sig*eyy)
        rel_diff_e3 = abs(e_elas_3 - analytical_e3) / analytical_e3
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

    def test_06_damaged_tension_parity(self):
        """Under d = 0.5, tensile stiffness parsed from damaged .dat must drop by 75% (g(0.5) = 0.25)."""
        # Damaged Table 0: Step 1 N_TOP
        u2, rf2_damaged = self.damaged_tables[0]["nodes"][3]
        analytical_rf2_intact = (self.E / (1.0 - self.nu**2)) * u2 * 1.0
        expected_rf2_damaged = 0.25 * analytical_rf2_intact  # 0.057692308 kN

        rel_diff = abs(rf2_damaged - expected_rf2_damaged) / expected_rf2_damaged
        self.assertLess(rel_diff, 1.0e-6,
                        "Damaged tension parity error %.4e exceeds 1e-6" % rel_diff)

        # Direct ratio vs intact solve
        _, rf2_intact = self.intact_tables[0]["nodes"][3]
        ratio = rf2_damaged / rf2_intact
        self.assertAlmostEqual(ratio, 0.25, places=5,
                               msg="Stiffness degradation ratio %.6f deviates from g(d)=0.25" % ratio)

    def test_07_damaged_shear_parity(self):
        """Under d = 0.5, shear stiffness parsed from damaged .dat must drop by 75%."""
        u1_3, rf1_3 = self.damaged_tables[2]["nodes"][3]
        u1_4, rf1_4 = self.damaged_tables[2]["nodes"][4]
        total_damaged_shear_rf = rf1_3 + rf1_4
        expected_shear_rf = 0.25 * (self.mu * u1_3 * 1.0)  # 0.0201923 kN

        rel_diff = abs(total_damaged_shear_rf - expected_shear_rf) / expected_shear_rf
        self.assertLess(rel_diff, 0.002,
                        "Damaged shear parity error %.4e exceeds 0.2%%" % rel_diff)

    def test_08_damaged_compression_bulk_preservation(self):
        """Under equibiaxial compression with d = 0.5, volumetric bulk modulus K = 175 GPa is 100% PRESERVED."""
        # Damaged Table 3: Step 3 N_TOP
        u2, rf2_damaged = self.damaged_tables[3]["nodes"][3]
        exx, eyy = u2, u2
        tr_eps = exx + eyy  # -0.004
        eps_dev_yy = eyy - (1.0/3.0)*tr_eps  # -0.000666667
        sig_vol = self.K_bulk * tr_eps  # -0.700 kN/mm^2 (UNDGRADED)
        sig_dev_yy = 0.25 * (2.0 * self.mu * eps_dev_yy)  # -0.0269231 kN/mm^2
        expected_sigma_yy = sig_vol + sig_dev_yy  # -0.7269231 kN/mm^2

        rel_diff = abs(rf2_damaged - expected_sigma_yy) / abs(expected_sigma_yy)
        self.assertLess(rel_diff, 1.0e-5,
                        "Damaged compression bulk preservation error %.4e exceeds 1e-5" % rel_diff)

    def test_09_damaged_fracture_energy_reconciliation(self):
        """Damaged fracture energy from authentic CSV matches analytical Gc/(2*l0)*d^2*A = 0.0421875 kN*mm."""
        # Row 3 is Step 1 Inc 1 of the damaged solve (prescribed uniform d = 0.5)
        row = self.energy_rows[3]
        parsed_ef = row["e_frac"]
        raw_ef_str = row["raw_e_frac_str"]

        # 1. Verify exact raw string produced by Fortran solver (E18.8 format)
        self.assertEqual(raw_ef_str, "0.42187500E-01",
                         "Raw Fortran string in CSV differs from expected '0.42187500E-01'")

        # 2. Mathematical proof: 0.42187500E-01 = 0.42187500 * 10^(-1) = 0.042187500
        evaluated_from_string = float(raw_ef_str)
        self.assertEqual(evaluated_from_string, 0.0421875)

        # 3. Analytical expectation: Gc = 0.0027 kN/mm, l0 = 0.008 mm, d = 0.5, A = 1.0 mm^2
        Gc = 0.0027
        l0 = 0.0080
        expected_Ef = (Gc / (2.0 * l0)) * (0.5**2) * 1.0  # 0.0421875 kN*mm

        # 4. Parity check between parsed solver value and analytical value
        rel_diff = abs(parsed_ef - expected_Ef) / expected_Ef
        self.assertLess(rel_diff, 1.0e-7,
                        "Fracture energy parity error %.4e exceeds 1e-7" % rel_diff)

    def test_10_production_deck_cutback_safeguards(self):
        """Production deck must permit genuine automatic increment reduction down to dt = 1e-9."""
        prod_deck = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark",
            "PK_F1714_JOB2_ADAPTED_PROD.inp"
        )
        with open(prod_deck, "r") as f:
            lines = [line.strip() for line in f]

        # Verify DIRECT keyword is NOT used in *STATIC lines
        static_lines = [l for l in lines if l.startswith("*STATIC")]
        for sl in static_lines:
            self.assertNotIn("DIRECT", sl, "DIRECT keyword found in *STATIC, preventing cutbacks")

        # Verify Step 1 permits cutbacks: minimum dt (1.0e-9) << initial dt (5.0e-4)
        self.assertIn("5.0E-4, 1.0, 1.0E-9, 5.0E-4", lines,
                      "Step 1 *STATIC line missing required dt_min=1e-9")

        # Verify Step 2 permits cutbacks: minimum dt (1.0e-9) << initial dt (2.0e-4)
        self.assertIn("2.0E-4, 1.0, 1.0E-9, 2.0E-4", lines,
                      "Step 2 *STATIC line missing required dt_min=1e-9")

        # Verify time incrementation controls are configured
        self.assertIn("*CONTROLS, PARAMETERS=TIME INCREMENTATION", lines)
        self.assertIn("4, 10, 9, 20, 10, 4, 0, 10", lines)


if __name__ == "__main__":
    unittest.main()
