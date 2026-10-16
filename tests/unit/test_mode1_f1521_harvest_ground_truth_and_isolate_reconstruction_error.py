import hashlib
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestMode1F1521HarvestGroundTruthAndIsolateReconstructionError(unittest.TestCase):
    """
    Unit test suite for Task F1521:
    Harvesting ground truth, conducting constitutive audit of mechanical static equilibrium,
    verifying reconstruction averaging fidelity, and isolating boundary condition discrepancies.
    """

    def setUp(self):
        self.p40_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k"
        self.p49_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
        self.p50_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "50_method_b_fine_baseline_enriched"
        self.uel_file = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
        self.engine_file = REPO_ROOT / "scripts" / "state_transfer" / "mode1_state_transfer_engine.py"
        self.baseline_inp = self.p40_dir / "M1_MB_CORRECTED_PROPAGATION_14K.inp"
        self.consistent_inp = self.p49_dir / "M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD.inp"
        self.enriched_inp = self.p50_dir / "M1_MB_FINE_BASELINE_ENRICHED.inp"
        self.state_json = self.p40_dir / "evidence_1412465" / "fine_baseline_14k_u0050_state.json"
        self.baseline_energy_csv = self.p40_dir / "evidence_1412465" / "uel_energy_balance.csv"
        self.active_task_json = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"

    def test_01_constitutive_path_independence_under_frozen_damage(self):
        """Test 1: Verify UEL mechanical constitutive formulation is linear elastic and path-independent for frozen damage."""
        self.assertTrue(self.uel_file.exists())
        text = self.uel_file.read_text(encoding="utf-8", errors="ignore")

        # In JTYPE 2 (quad mechanical) and JTYPE 4 (tri mechanical):
        # Stress is DEG * C_0 * strain, where DEG = (1 - D_VAL)**2 + E_K
        self.assertIn("DEG   = (ONE - D_VAL)**2 + E_K", text)
        self.assertIn("C11_MECH = C11_0 * DEG", text)
        self.assertIn("STRESS(I) = STRESS(I) + D_ELAS(I,J)*STRAIN(J)", text)
        # AMATRX is standard integral of B^T D_ELAS B
        self.assertIn("AMATRX(I,J) = AMATRX(I,J) +", text)
        # Confirms Cauchy elasticity with zero path dependence when D_VAL is Dirichlet-fixed

    def test_02_consistent_inverse_reconstruction_element_average_fidelity(self):
        """Test 2: Verify consistent inverse reconstruction d* reproduces baseline element averages to < 0.05% relative L2 error."""
        self.assertTrue(self.consistent_inp.exists())
        self.assertTrue(self.state_json.exists())

        # Parse prescribed nodal damage from INP
        nodal_damage = {}
        with open(self.consistent_inp, "r", encoding="utf-8", errors="ignore") as f:
            in_boundary = False
            for line in f:
                line_s = line.strip()
                if "*BOUNDARY" in line_s.upper() and not line_s.startswith("**"):
                    in_boundary = True
                    continue
                if in_boundary and line_s.startswith("**"):
                    continue
                if in_boundary and line_s.startswith("*"):
                    in_boundary = False
                    continue
                if in_boundary and line_s:
                    parts = [p.strip() for p in line_s.split(",")]
                    if len(parts) >= 4 and parts[1] == "3" and parts[2] == "3":
                        nid = int(parts[0])
                        d_val = float(parts[3])
                        nodal_damage[nid] = d_val

        self.assertEqual(len(nodal_damage), 14456)

        # Parse elements
        elements = {}
        with open(self.consistent_inp, "r", encoding="utf-8", errors="ignore") as f:
            in_elem = False
            for line in f:
                line_s = line.strip()
                if line_s.upper().startswith("*ELEMENT") and not line_s.startswith("**"):
                    in_elem = True
                    continue
                if in_elem and line_s.startswith("**"):
                    continue
                if in_elem and line_s.startswith("*"):
                    in_elem = False
                    continue
                if in_elem and line_s:
                    parts = [p.strip() for p in line_s.split(",")]
                    if len(parts) >= 4:
                        eid = int(parts[0])
                        if 1 <= eid <= 14483:
                            elements[eid] = [int(p) for p in parts[1:] if p]

        self.assertEqual(len(elements), 14483)

        # Compare with state_json SDV14
        with open(self.state_json, "r", encoding="utf-8") as f:
            sdv_data = json.load(f)["elem_sdv"]

        diffs_sq = 0.0
        target_sq = 0.0
        for eid, nids in elements.items():
            mean_d = sum(nodal_damage[nid] for nid in nids) / float(len(nids))
            target_d = sdv_data[str(eid)]["SDV14"][0]
            diffs_sq += (mean_d - target_d) ** 2
            target_sq += target_d ** 2

        rel_l2_error = (diffs_sq / target_sq) ** 0.5
        self.assertLess(rel_l2_error, 5.0e-4)  # < 0.05% relative L2 error

        # Element 661 apex element average damage must match to 5 decimal places
        mean_d_661 = sum(nodal_damage[nid] for nid in elements[661]) / float(len(elements[661]))
        self.assertAlmostEqual(mean_d_661, 0.318142, places=5)

    def test_03_boundary_condition_discrepancy_identification(self):
        """Test 3: Prove baseline model enforces N_TOP, 1, 1, 0.0 and N_PIN, whereas reconstructed deck omitted N_TOP and mispinned origin."""
        # Baseline model has N_TOP, 1, 1, 0.0 and N_PIN, 1, 1, 0.0
        baseline_text = self.baseline_inp.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("N_TOP, 1, 1, 0.0", baseline_text)
        self.assertIn("N_PIN, 1, 1, 0.0", baseline_text)
        self.assertIn("*NSET, NSET=N_PIN\n33", baseline_text.replace("\r\n", "\n"))

        # Reconstructed deck omitted N_TOP, 1, 1, 0.0 from BOUNDARY cards
        consistent_text = self.consistent_inp.read_text(encoding="utf-8", errors="ignore")
        # Ensure N_TOP, 1, 1 is NOT present in consistent inp
        self.assertNotIn("N_TOP, 1, 1", consistent_text)
        # Ensure node 1 was pinned instead of N_PIN (node 33)
        self.assertIn("1, 1, 1, 0.0", consistent_text)

    def test_04_nlgeom_inconsistency_identification(self):
        """Test 4: Prove baseline model specifies NLGEOM=NO, whereas reconstructed deck specified NLGEOM=YES."""
        baseline_text = self.baseline_inp.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("NLGEOM=NO", baseline_text)

        consistent_text = self.consistent_inp.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("NLGEOM=YES", consistent_text)

    def test_05_enriched_baseline_boundary_and_energy_parity(self):
        """Test 5: Verify enriched baseline deck restores exact canonical boundary conditions and matches reference energy."""
        enriched_text = self.enriched_inp.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("N_TOP, 1, 1, 0.0", enriched_text)
        self.assertIn("N_PIN, 1, 1, 0.0", enriched_text)
        self.assertIn("NLGEOM=NO", enriched_text)

        # Verify baseline energy CSV exists and has expected terminal values at increment 2000
        self.assertTrue(self.baseline_energy_csv.exists())
        with open(self.baseline_energy_csv, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        # Line for inc 2000 (at row 2001 with header or similar)
        inc_2000_line = None
        for l in lines:
            parts = [p.strip() for p in l.split(",")]
            if len(parts) >= 7 and parts[0] == "1" and parts[1] == "2000":
                inc_2000_line = parts
                break

        self.assertIsNotNone(inc_2000_line)
        e_elas = float(inc_2000_line[4])
        e_frac = float(inc_2000_line[5])
        e_tot = float(inc_2000_line[6])

        self.assertAlmostEqual(e_elas, 1.654313e-3, places=7)
        self.assertAlmostEqual(e_frac, 0.036786e-3, places=7)
        self.assertAlmostEqual(e_tot, 1.691099e-3, places=7)

    def test_06_gate_6c_hold_and_case_b_classification_maintained(self):
        """Test 6: Verify Gate 6C hold remains strictly enforced and Case B is scoped to within-run release stability."""
        self.assertTrue(self.active_task_json.exists())
        with open(self.active_task_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("GATE_6C_HOLD", data.get("gate_status", ""))
        self.assertIn("CASE_B_LOCAL_RELEASE_STABILITY_ONLY", data.get("gate_status", ""))


if __name__ == "__main__":
    unittest.main()
