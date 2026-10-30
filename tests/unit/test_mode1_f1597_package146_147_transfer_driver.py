# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package146_147_transfer_driver.py
Unit and validation test suite for Package 146 -> Package 147 nonmatching state transfer and PDAS driver.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Tests:
  1. Slit-flank topology separation: zero cross-slit interpolation along y=0.05, x<=0.04.
  2. Exact nodal, element, and Gauss-point counts and indexing.
  3. Finite, complete initial transferred fields (no NaN, no Inf, d in [0, 1]).
  4. Non-negativity and no-healing guarantees (H >= 0, d >= d0).
  5. Correctness of *INITIAL CONDITIONS, TYPE=SOLUTION cards (7,056 elements, SVARS 9..12).
  6. Correctness of active-set boundary cards (DOF 3 Dirichlet clamping).
  7. Committed donor state preservation mechanism across subproblem iterations.
  8. PDAS active-set partitioning, complementarity evaluation, and convergence.
  9. Stage C1-1 multi-gate physical acceptance evaluation.
  10. Fail-closed behavior on corrupted hashes or missing files.
  11. AbaqusPDASIterationController subproblem preparation and active-set decoupling.
  12. AbaqusPDASIterationController PBS wrapper generation with dual-channel notification traps.
  13. AbaqusPDASIterationController output parsing for STA, CSV, and DAT files.
  14. AbaqusPDASIterationController active set update and healing detection from solver outputs.
  15. Canonical KKT sign convention verification on discrete phase equations.
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_package146_147_transfer_deck import (
    Package146To147DeckGenerator,
    parse_donor_dat_file,
    parse_donor_history_from_evaluation,
    sha256_file,
    TARGET_DISP_STEP1_MM,
    FROZEN_UEL_SHA256,
    SEAM_Y,
    SEAM_X_MAX,
    DONOR_INP_DEFAULT,
    RECEIVER_INP_DEFAULT,
    DONOR_DAT_DEFAULT,
    EVALUATION_JSON_DEFAULT,
    FROZEN_UEL_DEFAULT
)
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    PDASReEquilibrationSolver,
    AbaqusPDASIterationController,
    CoupledAbaqusRuntime,
    StageC1GateEvaluator,
    GATE_FORCE_TOL,
    GATE_ENERGY_TOL,
    HEALING_TOL
)
from scripts.state_transfer.c3_int_to_c4_spatial_mapping import Mesh2D


class TestPackage146To147TransferDriver(unittest.TestCase):
    """Validation test suite for Package 146 -> Package 147 state transfer and PDAS continuation driver."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="test_pkg148_")
        cls.generator = Package146To147DeckGenerator(
            output_dir=cls.temp_dir,
            donor_inp=DONOR_INP_DEFAULT,
            receiver_inp=RECEIVER_INP_DEFAULT,
            donor_dat=DONOR_DAT_DEFAULT,
            eval_json=EVALUATION_JSON_DEFAULT,
            frozen_uel=FROZEN_UEL_DEFAULT
        )
        cls.generator.verify_prerequisites()
        cls.generator.load_donor_data()
        cls.generator.initialize_meshes_and_mapper()
        cls.projection = cls.generator.execute_state_projection()
        cls.artifacts = cls.generator.generate_all_artifacts(cls.projection)

    def test_01_exact_mesh_counts_and_indexing(self):
        """Verifies exact nodal, element, and Gauss-point counts for donor and receiver."""
        m_donor = self.generator.donor_mesh
        m_rec = self.generator.receiver_mesh

        # Donor counts
        self.assertEqual(len(m_donor.nodes), 5290)
        self.assertEqual(len(m_donor.elements), 5112)
        self.assertEqual(len(m_donor.gauss_points), 20448)

        # Receiver counts
        self.assertEqual(len(m_rec.nodes), 7265)
        self.assertEqual(len(m_rec.elements), 7056)
        self.assertEqual(len(m_rec.gauss_points), 28224)

    def test_02_slit_flank_separation(self):
        """Verifies strict crack-flank isolation: zero cross-slit interpolation along y=0.05, x<=0.04."""
        node_map = self.projection["node_map"]
        m_donor = self.generator.donor_mesh
        m_rec = self.generator.receiver_mesh

        # For every receiver node on the seam, verify its host element is on the same flank
        cross_slit_violations = 0
        for nid, (x, y) in m_rec.nodes.items():
            if abs(y - SEAM_Y) < 1e-6 and x <= SEAM_X_MAX + 1e-6:
                rec_flank = m_rec.node_flank.get(nid)
                host_eid = node_map[nid]["host_eid"]
                donor_flank = m_donor.element_flank.get(host_eid)

                if rec_flank in ("UPPER", "LOWER"):
                    if rec_flank != donor_flank:
                        cross_slit_violations += 1

        self.assertEqual(cross_slit_violations, 0,
                         "Detected cross-slit interpolation violations along seam!")

    def test_03_finite_and_bounded_initial_fields(self):
        """Verifies that all projected fields are finite, non-null, and physically bounded."""
        target_disp = self.projection["target_disp"]
        target_phase = self.projection["target_phase"]
        target_gp_h = self.projection["target_gp_h"]

        self.assertEqual(len(target_disp), 7265)
        self.assertEqual(len(target_phase), 7265)
        self.assertEqual(len(target_gp_h), 28224)

        for nid, (u1, u2) in target_disp.items():
            self.assertTrue(math.isfinite(u1))
            self.assertTrue(math.isfinite(u2))

        for nid, d_val in target_phase.items():
            self.assertTrue(math.isfinite(d_val))
            self.assertGreaterEqual(d_val, 0.0)
            self.assertLessEqual(d_val, 1.0)

        for gp_key, h_val in target_gp_h.items():
            self.assertTrue(math.isfinite(h_val))
            self.assertGreaterEqual(h_val, 0.0)

    def test_04_initial_conditions_solution_cards(self):
        """Verifies that *INITIAL CONDITIONS, TYPE=SOLUTION cards write exactly 18 SVARS per element."""
        sol_inc = self.artifacts["sol_inc"]
        self.assertTrue(sol_inc.exists())

        with open(str(sol_inc), "r") as f:
            lines = [l.strip() for l in f if l.strip()]

        # Filter out comments and header
        data_lines = [l for l in lines if not l.startswith("*")]
        # Exactly 7,056 elements * 3 lines per element = 21,168 data lines
        self.assertEqual(len(data_lines), 7056 * 3)

        # Inspect first element cards
        l1 = [float(x) for x in data_lines[0].split(",")]
        self.assertEqual(int(l1[0]), 1)  # Element 1
        self.assertEqual(len(l1), 9)     # eid + 8 zeros

        l2 = [float(x) for x in data_lines[1].split(",")]
        self.assertEqual(len(l2), 8)     # h1, h2, h3, h4 + 4 zeros
        for h in l2[:4]:
            self.assertGreaterEqual(h, 0.0)

        l3 = [float(x) for x in data_lines[2].split(",")]
        self.assertEqual(len(l3), 2)     # 2 zeros
        self.assertEqual(l3, [0.0, 0.0])

    def test_05_active_set_boundary_cards(self):
        """Verifies active set Dirichlet boundary cards syntax and completeness."""
        active_inc = self.artifacts["active_inc"]
        self.assertTrue(active_inc.exists())

        with open(str(active_inc), "r") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("*")]

        self.assertEqual(len(lines), 7265)
        # Verify syntax: node_id, 3, 3, d_value
        first_parts = [p.strip() for p in lines[0].split(",")]
        self.assertEqual(len(first_parts), 4)
        self.assertEqual(int(first_parts[0]), 1)
        self.assertEqual(first_parts[1], "3")
        self.assertEqual(first_parts[2], "3")
        d_val = float(first_parts[3])
        self.assertGreaterEqual(d_val, 0.0)
        self.assertLessEqual(d_val, 1.0)

    def test_06_master_input_deck_integrity(self):
        """Verifies that M1_C4_PACKAGE148_STATE_TRANSFER.inp includes required blocks and references frozen UEL."""
        master_inp = self.artifacts["master_inp"]
        self.assertTrue(master_inp.exists())

        with open(str(master_inp), "r") as f:
            content = f.read()

        self.assertIn("*USER ELEMENT, TYPE=U1", content)
        self.assertIn("*USER ELEMENT, TYPE=U2", content)
        self.assertIn("*Include, input=initial_conditions_solution.inc", content)
        self.assertIn("*Include, input=active_set_boundary_cards.inc", content)
        self.assertIn("*Step, name=C1-1-ReEquil", content)

        # Verify frozen UEL copy hash
        copied_uel = Path(self.temp_dir) / "f42_mixed_uel.for"
        self.assertTrue(copied_uel.exists())
        self.assertEqual(sha256_file(copied_uel), FROZEN_UEL_SHA256)
        runtime = CoupledAbaqusRuntime(self.temp_dir, Path(self.temp_dir)/'runtime',
                                       REPO_ROOT/'scripts/validation/extract_package148_iteration.py',
                                       .1873079389333725, .00021270454)
        runtime.load()
        self.assertEqual(len(runtime.h0), 28224)
        for eid in (1, 100, 7056):
            for gp, col in [(1, 1), (2, 2), (3, 4), (4, 3)]:
                self.assertAlmostEqual(runtime.h0[eid, gp], self.projection['target_gp_h'][eid, col], places=12)

    def test_07_committed_state_preservation_mechanism(self):
        """Verifies that the PDAS driver strictly preserves baseline H0 across iterations."""
        receiver_mesh = self.generator.receiver_mesh
        d0_nodal = self.projection["target_phase"]
        h0_gp = self.projection["target_gp_h"]

        solver = PDASReEquilibrationSolver(receiver_mesh, d0_nodal, h0_gp)

        # Test 1: Mechanical strain energy smaller than H0
        small_mech_energy = {k: 0.5 * v for k, v in list(h0_gp.items())[:100]}
        solver.enforce_state_preservation(small_mech_energy)
        for k in small_mech_energy:
            # Baseline H0 must NOT be decreased
            self.assertEqual(solver.h_gp[k], h0_gp[k])

        # Test 2: Mechanical strain energy larger than H0
        large_mech_energy = {k: 2.0 * v + 0.1 for k, v in list(h0_gp.items())[:100]}
        solver.enforce_state_preservation(large_mech_energy)
        for k in large_mech_energy:
            # Must take maximum
            self.assertAlmostEqual(solver.h_gp[k], large_mech_energy[k])

    def test_08_pdas_active_set_partitioning_and_no_healing(self):
        """Verifies PDAS active-set partitioning and strict irreversibility on receiver mesh."""
        receiver_mesh = self.generator.receiver_mesh
        d0_nodal = self.projection["target_phase"]
        h0_gp = self.projection["target_gp_h"]

        # Run 2 PDAS iterations
        solver = PDASReEquilibrationSolver(receiver_mesh, d0_nodal, h0_gp, max_iter=2)
        res = solver.run_re_equilibration(max_iter=2)

        # Check admissibility: no damage healing
        self.assertTrue(res["is_admissible"])
        self.assertGreaterEqual(res["min_damage_change"], -HEALING_TOL)
        self.assertEqual(res["total_nodes"], 7265)
        self.assertGreaterEqual(res["active_nodes_count"], 0)
        self.assertLessEqual(res["active_nodes_count"], 7265)

    def test_09_stage_c1_gate_evaluator(self):
        """Verifies multi-gate acceptance evaluation logic."""
        donor_rf2 = 0.1873079389333725
        donor_energy = 0.00021270454
        evaluator = StageC1GateEvaluator(donor_rf2=donor_rf2, donor_energy=donor_energy)

        # Case 1: Pass all gates (e.g. 0.1% force difference, 0.2% energy difference, no healing)
        res_pass = evaluator.evaluate_gates(
            receiver_rf2=donor_rf2 * 1.001,
            receiver_energy=donor_energy * 1.002,
            min_delta_d=0.0,
            damage_max=0.5
        )
        self.assertTrue(res_pass["pass_all"])
        self.assertTrue(res_pass["pass_rf2"])
        self.assertTrue(res_pass["pass_energy"])
        self.assertTrue(res_pass["no_healing"])

        # Case 2: Fail force gate (> 5% difference)
        res_fail_force = evaluator.evaluate_gates(
            receiver_rf2=donor_rf2 * 1.06,
            receiver_energy=donor_energy * 1.002,
            min_delta_d=0.0,
            damage_max=0.5
        )
        self.assertFalse(res_fail_force["pass_all"])
        self.assertFalse(res_fail_force["pass_rf2"])

        # Case 3: Fail healing gate (damage decreased by > 1e-6)
        res_fail_healing = evaluator.evaluate_gates(
            receiver_rf2=donor_rf2 * 1.001,
            receiver_energy=donor_energy * 1.002,
            min_delta_d=-1e-4,
            damage_max=0.5
        )
        self.assertFalse(res_fail_healing["pass_all"])
        self.assertFalse(res_fail_healing["no_healing"])

    def test_10_fail_closed_on_corrupted_prerequisites(self):
        """Verifies fail-closed behavior on missing or hash-tampered files."""
        # Non-existent DAT
        with self.assertRaises(RuntimeError):
            gen_bad = Package146To147DeckGenerator(
                output_dir=self.temp_dir,
                donor_dat=Path(self.temp_dir) / "non_existent.dat"
            )
            gen_bad.verify_prerequisites()

        # Tampered UEL file
        tampered_uel = Path(self.temp_dir) / "tampered_uel.for"
        with open(str(tampered_uel), "w") as f:
            f.write("TAMPERED")
        with self.assertRaises(ValueError):
            gen_bad_uel = Package146To147DeckGenerator(
                output_dir=self.temp_dir,
                frozen_uel=tampered_uel
            )
            gen_bad_uel.verify_prerequisites()

    def test_11_abaqus_controller_subproblem_preparation(self):
        """Verifies AbaqusPDASIterationController prepares decoupled active-set boundary cards."""
        ctrl = AbaqusPDASIterationController(work_dir=self.temp_dir)
        ctrl.verify_work_dir_integrity()

        # Create synthetic active mask with 5,000 active nodes and 2,265 free nodes
        d0_nodal = self.projection["target_phase"]
        all_nids = sorted(d0_nodal.keys())
        active_mask = {nid: (i < 5000) for i, nid in enumerate(all_nids)}

        prep = ctrl.prepare_subproblem_iteration(iter_idx=1, active_mask=active_mask, d0_nodal=d0_nodal)
        self.assertEqual(prep["clamped_nodes_count"], 5000)
        self.assertEqual(prep["free_nodes_count"], 2265)
        self.assertEqual(prep["total_nodes"], 7265)

        # Inspect generated boundary cards file
        with open(str(prep["active_inc_path"]), "r") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("*")]
        self.assertEqual(len(lines), 5000)

        # Confirm first active node is clamped, and 5001st node is NOT clamped
        first_nid = all_nids[0]
        self.assertIn("%d, 3, 3" % first_nid, lines[0])

    def test_12_abaqus_controller_pbs_wrapper_generation(self):
        """Verifies AbaqusPDASIterationController generates valid PBS wrappers with dual notification traps."""
        ctrl = AbaqusPDASIterationController(work_dir=self.temp_dir)
        pbs_path = ctrl.build_pbs_wrapper(iter_idx=1, job_name="M1_C4_P148_TEST", cpus=1, memory_gb=16, walltime="00:15:00",
                                         donor_rf2=0.1873079389333725, donor_energy=0.00021270454)
        self.assertTrue(pbs_path.exists())

        with open(str(pbs_path), "r") as f:
            pbs_text = f.read()

        self.assertIn("#PBS -N M1_C4_P148_TEST", pbs_text)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", pbs_text)
        self.assertIn("#PBS -m abe", pbs_text)
        self.assertIn("job_notifications.sh", pbs_text)
        self.assertIn("notification_install_terminal_trap", pbs_text)
        self.assertIn('driver_package146_147_pdas_continuation.py', pbs_text)
        self.assertIn('notification_load_config', pbs_text)
        self.assertNotIn('|| true', pbs_text)

    def test_13_abaqus_controller_output_parsing(self):
        """Verifies AbaqusPDASIterationController parses real solver output fixtures."""
        ctrl = AbaqusPDASIterationController(work_dir=self.temp_dir)
        # Parse authentic Package 142 outputs as fixture
        p142_dir = REPO_ROOT / "models/pandey_kumar_mode1/142_c4_c3_int_state_transfer"
        res = ctrl.parse_subproblem_results(run_dir=p142_dir, job_name="M1_C4_PACKAGE142_STATE_TRANSFER")

        self.assertEqual(res["exit_status"], 0)
        self.assertEqual(res["increments"], 1)
        self.assertAlmostEqual(res["e_total_kNmm"], 0.00021383294, places=8)
        self.assertAlmostEqual(res["e_elas_kNmm"], 0.00017473955, places=8)
        self.assertAlmostEqual(res["e_frac_kNmm"], 0.000039093387, places=8)

    def test_14_abaqus_controller_active_set_updating(self):
        """Verifies active-set update logic and damage healing detection."""
        ctrl = AbaqusPDASIterationController(work_dir=self.temp_dir)
        d0_nodal = {1: 0.2, 2: 0.3, 3: 0.4}
        prev_active = {1, 2, 3}

        # Case A: node 2 grows damage to 0.35 -> should flip to inactive (free)
        # nodes 1 and 3 stay at d0 -> remain active (clamped)
        damage_case_a = {1: 0.2, 2: 0.35, 3: 0.4}
        update_a = ctrl.update_active_set_from_abaqus(damage_case_a, d0_nodal, prev_active,
                                                     residuals={1: 1., 2: 0., 3: 1.})
        self.assertIn(1, update_a["new_active_set"])
        self.assertIn(3, update_a["new_active_set"])
        self.assertIn(2, update_a["new_inactive_set"])
        self.assertEqual(update_a["active_flips"], 1)
        self.assertTrue(update_a["no_healing"])

        # Case B: node 1 attempts to heal (damage drops to 0.15) -> detected as healing violation
        damage_case_b = {1: 0.15, 2: 0.35, 3: 0.4}
        update_b = ctrl.update_active_set_from_abaqus(damage_case_b, d0_nodal, prev_active,
                                                     residuals={1: 1., 2: 0., 3: 1.})
        self.assertFalse(update_b["no_healing"])
        self.assertAlmostEqual(update_b["healing_violation"], -0.05)

    def test_15_canonical_kkt_sign_convention(self):
        """Verifies canonical KKT sign convention: lambda_i = r_i >= 0 on active set."""
        receiver_mesh = self.generator.receiver_mesh
        d0_nodal = self.projection["target_phase"]
        h0_gp = self.projection["target_gp_h"]

        solver = PDASReEquilibrationSolver(receiver_mesh, d0_nodal, h0_gp)
        diag, off_diag, rhs = solver.assemble_system()
        residuals, multipliers = solver.compute_kkt_residuals(diag, off_diag, rhs)

        # On active set, multiplier must be identical to the residual r_i
        for nid in solver.active_set:
            self.assertEqual(multipliers[nid], residuals[nid])

        # On inactive set, multiplier must be exactly zero
        for nid in solver.inactive_set:
            self.assertEqual(multipliers[nid], 0.0)


if __name__ == "__main__":
    unittest.main()
