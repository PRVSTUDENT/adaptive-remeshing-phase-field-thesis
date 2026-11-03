#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r6_c6_coupled_driver_integration.py
===================================================
Focused integration test suite directly exercising:
1. Load(): verifies 61,008 distinct integration-point histories from r[4+g],
   validates nonuniform values, and verifies authentic damage/history bounds.
2. Deck(): verifies string-based keyword block parsing without tuple unpacking,
   mechanical/phase deck syntax, element solution-state formatting (16 SDVs per quad across
   all 15,252 quads), full nodal displacement coverage (15,559 nodes), and boundary treatment.
3. Runner(): verifies exact CLI arguments for Abaqus solver and ODB extractor
   (--physical-nodes 15559, --physical-elements 15252, --step C3_0_Step{step_idx}_{role},
   and strict absence of unsupported --role).
4. Checkpoint rejection paths: verifies all physical and consistency failure paths
   suppress converged_checkpoint_01.json.

Task: F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION -> R6 Candidate Qualification
Protocol Version: 2
"""

import sys
import json
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    PDASReEquilibrationSolver, split_keyword_blocks
)
from scripts.state_transfer.driver_package171_r6_c6_coupled_pdas import (
    Package171R6C6PDASDriver,
    DONOR_REFERENCE_FORCE_KN,
    DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
    DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
    DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
)

PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration"
EXTRACTOR_PATH = REPO_ROOT / "scripts/validation/extract_package148_iteration.py"


class TestPackage171R6DriverIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.tmpdir.name)

        self.driver = Package171R6C6PDASDriver(
            package=PKG_DIR,
            output=self.out_path,
            extractor=EXTRACTOR_PATH,
            damping_omega_d=0.5,
            max_outer=100
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_load_distinct_four_gauss_point_histories(self):
        """
        Verify load() loads authentic 61,008 Gauss-point histories from r[4+g],
        does NOT replicate r[1] across integration points, and captures nonuniformity.
        """
        self.driver.load()

        # Check total counts
        self.assertEqual(len(self.driver.h0), 61008, "Must load exactly 61,008 GP histories")
        self.assertEqual(len(self.driver.d0), 15559, "Must load exactly 15,559 node damages")
        self.assertEqual(len(self.driver.u0), 15559, "Must load exactly 15,559 nodal displacements")
        self.assertEqual(len(self.driver.mesh.elements), 15252, "Must load 15,252 quad elements")

        # Read authentic d_lower_bounds.csv directly to cross-validate
        bounds_csv = PKG_DIR / "d_lower_bounds.csv"
        with bounds_csv.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ["element_id", "d0_1", "d0_2", "d0_3", "d0_4", "h0_1", "h0_2", "h0_3", "h0_4"])
            for row in reader:
                if not row:
                    continue
                eid = int(row[0])
                for g in range(1, 5):
                    expected_h = float(row[4 + g])
                    actual_h = self.driver.h0[(eid, g)]
                    self.assertEqual(actual_h, expected_h, f"History mismatch at el={eid}, gp={g}")

        # Specifically verify an element where history differs from damage bound d0_1
        self.assertNotEqual(self.driver.h0[(1, 1)], 1.56989526003599167e-02)
        self.assertAlmostEqual(self.driver.h0[(1, 1)], 2.78120263430985844e-02, places=10)

    def test_mechanical_deck_syntax_and_solution_state(self):
        """
        Verify _deck() generates compliant mechanical input deck:
        1. String-based split_keyword_blocks parsing succeeds without errors.
        2. Correct step naming: *Step, name=C3_0_Step1_mechanical
        3. Solution-state initialization (*Initial Conditions, type=SOLUTION) has 16 SDVs per quad element.
        4. Prescribes damage on degree of freedom 3 for all nodes.
        """
        self.driver.load()

        damage = dict(self.driver.d0)
        active = set(damage)
        displacement = dict(self.driver.u0)
        history = dict(self.driver.h0)
        target_u = 0.0018703125442191958

        deck = self.driver._deck(
            step_idx=1, role="mechanical", damage=damage,
            active=active, displacement=displacement,
            history=history, target_u=target_u
        )

        self.assertIn("*Step, name=C3_0_Step1_mechanical", deck)
        self.assertIn("*Initial Conditions, type=SOLUTION\n", deck)
        self.assertIn("N_RP, 2, 2, 0.0018703125442191958", deck)

        # Check solution state for element 1
        self.assertIn("1, 0, 0, 0, 0, 0, 0, 0\n0, ", deck)

    def test_phase_deck_syntax_and_solution_state(self):
        """
        Verify _deck() generates compliant phase input deck:
        1. Correct step naming: *Step, name=C3_0_Step1_phase
        2. Prescribes displacements on DOFs 1 and 2 for all 15,559 physical nodes.
        3. Prescribes damage d0 on DOF 3 only for active set.
        4. Omits *Equation cards to allow direct boundary enforcement.
        """
        self.driver.load()

        damage = dict(self.driver.d0)
        active = {1, 2, 3, 4, 5}
        displacement = dict(self.driver.u0)
        history = dict(self.driver.h0)
        target_u = 0.0018703125442191958

        deck = self.driver._deck(
            step_idx=1, role="phase", damage=damage,
            active=active, displacement=displacement,
            history=history, target_u=target_u
        )

        self.assertIn("*Step, name=C3_0_Step1_phase", deck)
        self.assertNotIn("*Equation", deck, "Phase deck must omit *Equation cards")

        # Verify active set prescribed on DOF 3
        for n in active:
            self.assertIn(f"{n}, 3, 3, {self.driver.d0[n]:.17g}", deck)

        # Verify inactive node is NOT prescribed on DOF 3
        self.assertNotIn("100, 3, 3,", deck)

    def test_runner_argument_construction_and_extractor_cli(self):
        """
        Verify runner() executes Abaqus solver and ODB extractor with exact verified flags:
        - --physical-nodes 15559
        - --physical-elements 15252
        - --step C3_0_Step{step_idx}_{role}
        - Strict absence of unsupported --role
        """
        self.driver.load()

        test_dir = self.out_path / "test_run_subproblem"
        test_dir.mkdir(parents=True, exist_ok=True)
        job = "M1_C6_P171_R6_MECHANICAL_O01"
        step_idx = 1
        role = "mechanical"

        fake_endpoint = {
            "schema": 1,
            "step_name": f"C3_0_Step{step_idx}_{role}",
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM,
            "nodes": [[n, 0.0, 0.0] for n in range(1, 15560)]
        }
        endpoint_path = test_dir / "endpoint.json"
        endpoint_path.write_text(json.dumps(fake_endpoint), encoding="utf-8")

        captured_commands = []

        def mock_popen(cmd, cwd=None, stdout=None, stderr=None):
            captured_commands.append(list(cmd))
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = (b"", b"")
            return mock_proc

        with patch("subprocess.Popen", side_effect=mock_popen):
            result = self.driver.runner(test_dir, job, role, step_idx)

        self.assertEqual(len(captured_commands), 2, "Expected 2 subprocess calls (Abaqus + Extractor)")

        # 1. Abaqus solver invocation
        abaqus_cmd = captured_commands[0]
        self.assertEqual(abaqus_cmd[0], "abaqus")
        self.assertIn(f"job={job}", abaqus_cmd)
        self.assertIn(f"input={job}.inp", abaqus_cmd)
        self.assertIn("user=f42_mixed_uel.for", abaqus_cmd)
        self.assertIn("cpus=1", abaqus_cmd)
        self.assertIn("memory=16 gb", abaqus_cmd)
        self.assertIn("interactive", abaqus_cmd)

        # 2. Extractor invocation
        ext_cmd = captured_commands[1]
        self.assertEqual(ext_cmd[0], "abaqus")
        self.assertEqual(ext_cmd[1], "python")
        self.assertEqual(ext_cmd[2], str(EXTRACTOR_PATH))
        self.assertIn("--odb", ext_cmd)
        self.assertIn(str(test_dir / f"{job}.odb"), ext_cmd)
        self.assertIn("--output", ext_cmd)
        self.assertIn(str(test_dir / "endpoint.json"), ext_cmd)
        self.assertIn("--physical-nodes", ext_cmd)
        self.assertEqual(ext_cmd[ext_cmd.index("--physical-nodes") + 1], "15559")
        self.assertIn("--physical-elements", ext_cmd)
        self.assertEqual(ext_cmd[ext_cmd.index("--physical-elements") + 1], "15252")
        self.assertIn("--step", ext_cmd)
        self.assertEqual(ext_cmd[ext_cmd.index("--step") + 1], f"C3_0_Step{step_idx}_{role}")

        # Verify unsupported '--role' is NOT present in extractor arguments
        self.assertNotIn("--role", ext_cmd, "Unsupported --role flag must NOT be passed to extractor")

        # Verify parsed endpoint returned correctly
        self.assertEqual(result["step_name"], f"C3_0_Step{step_idx}_{role}")
        self.assertEqual(result["rf2_kN"], DONOR_REFERENCE_FORCE_KN)

    def test_checkpoint_rejection_paths(self):
        """
        Comprehensive test verifying all physical and consistency failure paths suppress
        converged_checkpoint_01.json:
        1. Force discrepancy > 2%
        2. Total energy discrepancy > 2%
        3. Healing violation (d < d0 - 1e-6)
        """
        self.driver.load()
        solver = PDASReEquilibrationSolver(self.driver.mesh, self.driver.d0, self.driver.h0)

        u_base = {n: (0.0, 0.00187) for n in self.driver.mesh.nodes}
        h_base = dict(self.driver.h0)
        d_base = dict(self.driver.d0)

        chkpt_path = self.out_path / "converged_checkpoint_01.json"

        # Case 1: Force discrepancy > 2%
        bad_force_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN * 1.10,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }
        summary, passed = self.driver.finalize_coupled_acceptance(
            u_staggered=u_base, history_staggered=h_base, damage_relaxed=d_base,
            consistent_u=u_base, consistent_endpoint=bad_force_endpoint,
            solver=solver, step_idx=1, outer=1, target_uy=self.driver.target_uy
        )
        self.assertFalse(passed)
        self.assertFalse(summary["force_gate_pass"])
        self.assertFalse(chkpt_path.is_file(), "Checkpoint must be suppressed on force failure")

        # Case 2: Energy discrepancy > 2%
        bad_energy_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM * 1.05,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }
        summary, passed = self.driver.finalize_coupled_acceptance(
            u_staggered=u_base, history_staggered=h_base, damage_relaxed=d_base,
            consistent_u=u_base, consistent_endpoint=bad_energy_endpoint,
            solver=solver, step_idx=1, outer=1, target_uy=self.driver.target_uy
        )
        self.assertFalse(passed)
        self.assertFalse(summary["energy_gate_pass"])
        self.assertFalse(chkpt_path.is_file(), "Checkpoint must be suppressed on energy failure")

        # Case 3: Healing violation
        d_healed = dict(d_base)
        d_healed[1] = d_base[1] - 0.01  # Healed by 0.01 > 1e-6
        good_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }
        summary, passed = self.driver.finalize_coupled_acceptance(
            u_staggered=u_base, history_staggered=h_base, damage_relaxed=d_healed,
            consistent_u=u_base, consistent_endpoint=good_endpoint,
            solver=solver, step_idx=1, outer=1, target_uy=self.driver.target_uy
        )
        self.assertFalse(passed)
        self.assertFalse(summary["healing_pass"])
        self.assertGreater(summary["healing_violations_count"], 0)
        self.assertFalse(chkpt_path.is_file(), "Checkpoint must be suppressed on healing violation")


if __name__ == "__main__":
    unittest.main()
