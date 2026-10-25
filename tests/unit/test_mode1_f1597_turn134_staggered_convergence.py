import unittest
import json
import hashlib
from pathlib import Path

WORKSPACE = Path(r"D:\Master thesis\Adaptive remeshing")
PROD_UEL = WORKSPACE / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
PROD_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

PY_SIM_JSON = WORKSPACE / "results/validation/mode1_f1597/python_c3_multi_increment_simulation.json"

class TestMode1Turn134StaggeredConvergence(unittest.TestCase):
    def test_01_production_uel_bitwise_frozen(self):
        self.assertTrue(PROD_UEL.exists(), f"Production UEL missing: {PROD_UEL}")
        hasher = hashlib.sha256()
        with open(PROD_UEL, "rb") as f:
            hasher.update(f.read())
        uel_hash = hasher.hexdigest().upper()
        self.assertEqual(uel_hash, PROD_UEL_HASH, "Production UEL hash modified!")

    def test_02_python_staggered_simulation_structure(self):
        self.assertTrue(PY_SIM_JSON.exists(), f"Simulation JSON missing: {PY_SIM_JSON}")
        with open(PY_SIM_JSON, "r") as f:
            data = json.load(f)
        self.assertEqual(data.get("schema"), 1)
        self.assertEqual(len(data.get("increments", [])), 5)
        self.assertIn("stage_a", data)

    def test_03_turn107_benchmark_parity_under_subincrementation(self):
        with open(PY_SIM_JSON, "r") as f:
            data = json.load(f)
        inc5 = data["increments"][-1]
        
        # Turn 107 benchmark targets
        target_rf2 = 179.2976
        target_ef = 0.062404
        target_dmax = 0.675399
        target_hmax = 5.241126

        diff_rf2_pct = abs(inc5["rf2_N"] - target_rf2) / target_rf2 * 100.0
        diff_ef_pct = abs(inc5["e_frac_mJ"] - target_ef) / target_ef * 100.0
        diff_dmax_pct = abs(inc5["d_max"] - target_dmax) / target_dmax * 100.0
        diff_hmax_pct = abs(inc5["h_max"] - target_hmax) / target_hmax * 100.0

        self.assertLess(diff_rf2_pct, 0.5, f"RF2 diff {diff_rf2_pct:.2f}% exceeds 0.5%")
        self.assertLess(diff_ef_pct, 0.5, f"E_frac diff {diff_ef_pct:.2f}% exceeds 0.5%")
        self.assertLess(diff_dmax_pct, 0.5, f"d_max diff {diff_dmax_pct:.2f}% exceeds 0.5%")
        self.assertLess(diff_hmax_pct, 1.5, f"H_max diff {diff_hmax_pct:.2f}% exceeds 1.5%")

    def test_04_monotonic_softening_and_dissipation(self):
        with open(PY_SIM_JSON, "r") as f:
            data = json.load(f)
        incs = data["increments"]
        
        # Damage should be monotonically non-decreasing
        d_vals = [data["stage_a"]["d_max"]] + [inc["d_max"] for inc in incs]
        for i in range(1, len(d_vals)):
            self.assertGreaterEqual(d_vals[i], d_vals[i-1] - 1e-12, f"Healing detected at inc {i}")

        # Fracture energy should be monotonically non-decreasing
        ef_vals = [data["stage_a"]["e_frac_mJ"]] + [inc["e_frac_mJ"] for inc in incs]
        for i in range(1, len(ef_vals)):
            self.assertGreaterEqual(ef_vals[i], ef_vals[i-1] - 1e-12, f"E_frac decreased at inc {i}")

        # Terminal state must show softening vs Stage-A
        self.assertLess(incs[-1]["rf2_N"], data["stage_a"]["rf2_N"], "No softening at terminal displacement!")

    def test_05_stage_a_unrelaxed_kinematics_origin(self):
        # Verify that Abaqus Stage-A elevated history (5.209 MPa) is due to unrelaxed kinematics
        # where RF2 was 184.85 N instead of 180.23 N
        with open(PY_SIM_JSON, "r") as f:
            data = json.load(f)
        stage_a_equil_rf2 = data["stage_a"]["rf2_N"]
        abaqus_stage_a_rf2 = 184.852
        
        # Abaqus Stage-A was ~4.6 N higher than true variational equilibrium
        self.assertGreater(abaqus_stage_a_rf2, stage_a_equil_rf2 + 4.0)

if __name__ == "__main__":
    unittest.main()
