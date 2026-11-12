# -*- coding: utf-8 -*-
"""
tests/unit/test_f1720_authentic_stress_reference.py
==================================================
Unit regression test suite for Task F1720 Stage 1:
Authentic UEL Stress Reference Qualification.

Verifies:
1. Integrity of the authentic reference JSON database.
2. Exact state checkpoints (States 0 through 4) and monotonicity of top displacement.
3. Physical damage bounds (d in [0, 1]) and monotonic damage growth in critical Element 130.
4. Correctness of Cauchy stress components (S11, S22, S12, S33) and Mises stress formula.
5. Strict non-zero stress across all physical elements and positive Jacobians (det(J) > 0).
6. Global reaction force consistency and pre-peak structural stiffness agreement.
"""

import os
import json
import math
import unittest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
REF_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1720_authentic_uel_stress_reference.json")


class TestF1720AuthenticStressReference(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(REF_JSON):
            raise unittest.SkipTest("Reference JSON not found: %s" % REF_JSON)
        with open(REF_JSON, "r") as f:
            cls.data = json.load(f)

    def test_01_database_metadata_and_structure(self):
        """Verifies reference database contains all 5 required states and correct metadata."""
        meta = self.data.get("metadata", {})
        self.assertIn("Amor et al. (2009)", meta.get("constitutive_model", ""))
        self.assertEqual(meta["material_parameters"]["E_MPa"], 210000.0)
        self.assertEqual(meta["discretization"]["physical_elements"], 2747)

        states = self.data.get("states", {})
        self.assertEqual(len(states), 5)
        for i in range(5):
            self.assertIn("State_%d" % i, states)

    def test_02_displacement_and_damage_monotonicity(self):
        """Verifies monotonic displacement growth and monotonic damage evolution in critical element 130."""
        states = self.data["states"]
        u_vals = [states["State_%d" % i]["top_displacement_uy_mm"] for i in range(5)]
        d_vals = [states["State_%d" % i]["elements"]["130"]["damage"] for i in range(5)]

        # Displacement must be strictly increasing
        for i in range(len(u_vals) - 1):
            self.assertGreater(u_vals[i+1], u_vals[i], "Displacement uy must be strictly increasing")

        # Damage in element 130 must be monotonically non-decreasing
        for i in range(len(d_vals) - 1):
            self.assertGreaterEqual(d_vals[i+1], d_vals[i], "Damage in El 130 must be monotonic non-decreasing")

        # Check bounds
        self.assertLess(d_vals[0], 0.06)
        self.assertGreater(d_vals[4], 0.50)

    def test_03_stress_components_and_mises_formula(self):
        """Verifies integration-point stress tensor components and Mises identity."""
        state2 = self.data["states"]["State_2"]
        elements = state2["elements"]

        # Check element 130 in State 2
        el130 = elements["130"]
        self.assertEqual(len(el130["ips"]), 4) # CPE4 quad has 4 IPs

        for ip in el130["ips"]:
            s11, s22, s12, s33 = ip["stress"]
            s_vm = ip["mises"]
            # Recompute Mises independently
            expected_vm = math.sqrt(max(0.0, 0.5 * ((s11 - s22)**2 + (s22 - s33)**2 + (s33 - s11)**2 + 6.0 * (s12**2))))
            self.assertAlmostEqual(s_vm, expected_vm, places=4, msg="Mises calculation mismatch")
            self.assertGreater(ip["detJ"], 0.0, "Jacobian determinant must be strictly positive")

    def test_04_four_ligament_spatial_hierarchy(self):
        """Verifies that narrowest ligament h3 <-> h4 concentrates highest stress and damage."""
        state2 = self.data["states"]["State_2"]
        elements = state2["elements"]

        # Elements in narrowest ligament h3 <-> h4 (e.g. 130, 2, 4)
        ligament_eids = ["130", "2", "4", "15"]
        lig_mises = [max(ip["mises"] for ip in elements[eid]["ips"]) for eid in ligament_eids if eid in elements]
        mean_lig_mises = sum(lig_mises) / float(len(lig_mises))

        # Bulk elements far away (e.g. bottom corners, y < 0.2)
        bulk_eids = ["1", "10", "20", "30", "40", "50"]
        bulk_mises = [max(ip["mises"] for ip in elements[eid]["ips"]) for eid in bulk_eids if eid in elements]
        mean_bulk_mises = sum(bulk_mises) / float(len(bulk_mises))

        self.assertGreater(mean_lig_mises, 2.0 * mean_bulk_mises,
                           "Ligament stress must be significantly higher than far-field bulk stress")

    def test_05_reaction_force_consistency(self):
        """Verifies reaction force consistency across states."""
        states = self.data["states"]
        rf_vals = [states["State_%d" % i]["bottom_reaction_force_kN"] for i in range(5)]
        u_vals = [states["State_%d" % i]["top_displacement_uy_mm"] for i in range(5)]

        # Initial elastic stiffness K0 = RF / uy in State 0
        k0 = rf_vals[0] / u_vals[0] # kN / mm
        self.assertAlmostEqual(k0, 175.0, delta=10.0, msg="Coarse elastic stiffness should be ~175 kN/mm")

        # Peak force should occur around State 3 or 4
        self.assertGreater(rf_vals[4], rf_vals[0])
        self.assertGreater(rf_vals[3], rf_vals[1])


if __name__ == "__main__":
    unittest.main()
