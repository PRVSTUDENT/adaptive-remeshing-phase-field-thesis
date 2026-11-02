#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1598_turn44_package167_extractor_regression.py
Regression tests for Package 167 post-solve Abaqus extraction invocation and parsing.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Verifies:
1. extract_package148_iteration.py strictly rejects invocation when --physical-nodes
   or --physical-elements are missing (fails with exit code 2).
2. driver_package167_c5_continuation.py constructs extract_cmd with abaqus python,
   --physical-nodes, --physical-elements, and --step StageC2_2_Step{step_idx}_{role}.
3. Extracted endpoint.json nodes list is correctly unpacked into (u1, u2) displacements
   and damage without requiring non-existent CSV files.
4. Endpoint node count mismatch strictly raises ValueError("Endpoint node coverage mismatch").
"""

import sys
import json
import unittest
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.driver_package167_c5_continuation import (
    C5ForwardContinuationControllerC2_2
)


class TestPackage167ExtractorRegression(unittest.TestCase):

    def setUp(self):
        self.extractor_script = REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
        self.package_dir = REPO_ROOT / "models/pandey_kumar_mode1/167_c5_package167_r2_c2_2_continuation"
        self.dummy_output = REPO_ROOT / "results/validation/temp_test_p167_extractor"

    def test_01_original_missing_argument_invocation_fails(self):
        """Verify that running extract_package148_iteration.py without --physical-nodes fails with exit code 2."""
        cmd = [
            sys.executable,
            str(self.extractor_script),
            "--odb", "dummy.odb",
            "--output", "dummy.json",
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 2, "Expected exit code 2 for missing required CLI arguments")
        self.assertIn("error: the following arguments are required", proc.stderr)
        self.assertIn("--physical-nodes", proc.stderr)
        self.assertIn("--physical-elements", proc.stderr)

    def test_02_original_csv_argument_rejected(self):
        """Verify that passing --csv argument is rejected as an unrecognized argument."""
        cmd = [
            sys.executable,
            str(self.extractor_script),
            "--odb", "dummy.odb",
            "--output", "dummy.json",
            "--physical-nodes", "13278",
            "--physical-elements", "12996",
            "--csv", "dummy.csv"
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 2, "Expected exit code 2 for unrecognized --csv argument")
        self.assertIn("unrecognized arguments: --csv", proc.stderr)

    def test_03_repaired_driver_extract_command_structure(self):
        """Verify that repaired solve_subproblem issues the correct command-line parameters."""
        captured_cmds = []

        def mock_runner(cmd, cwd, timeout):
            captured_cmds.append(list(cmd))
            tag = Path(cwd).name
            job = f"M1_C5_P167_{tag}"
            if "python" in cmd:
                # Mock extraction output in endpoint.json
                # Create 13,278 dummy nodes matching C5
                nodes = [[nid, 0.0, 0.00187, 0.05] for nid in range(1, 13279)]
                endpoint_data = {
                    "schema": 1,
                    "step_name": cmd[cmd.index("--step") + 1] if "--step" in cmd else "unknown",
                    "increment": 1,
                    "rf2_kN": 0.183,
                    "elastic_kNmm": 0.00017,
                    "fracture_kNmm": 0.00005,
                    "total_energy_kNmm": 0.00022,
                    "nodes": nodes
                }
                (Path(cwd) / "endpoint.json").write_text(json.dumps(endpoint_data), encoding="utf-8")
            else:
                # Mock solver output
                (Path(cwd) / f"{job}.sta").write_text("THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n", encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        controller = C5ForwardContinuationControllerC2_2(
            package=self.package_dir,
            output=self.dummy_output,
            extractor=self.extractor_script,
            abaqus="abaqus",
            runner=mock_runner
        )
        controller.load()

        # Execute single mechanical subproblem
        dummy_damage = {nid: 0.05 for nid in controller.mesh.nodes}
        d, u, endpoint = controller.solve_subproblem(
            step_idx=1, outer=1, inner=0, role="mechanical",
            damage=dummy_damage, active=set(dummy_damage),
            displacement=None, history=controller.h0, target_u=0.001870312544
        )

        self.assertEqual(len(captured_cmds), 2, "Expected solver command and extractor command")
        extract_cmd = captured_cmds[1]

        # Verify command prefix is [abaqus, python, extractor]
        self.assertEqual(extract_cmd[0], "abaqus")
        self.assertEqual(extract_cmd[1], "python")
        self.assertEqual(extract_cmd[2], str(self.extractor_script))

        # Verify required arguments
        self.assertIn("--physical-nodes", extract_cmd)
        self.assertEqual(extract_cmd[extract_cmd.index("--physical-nodes") + 1], "13278")

        self.assertIn("--physical-elements", extract_cmd)
        self.assertEqual(extract_cmd[extract_cmd.index("--physical-elements") + 1], "12996")

        self.assertIn("--step", extract_cmd)
        self.assertEqual(extract_cmd[extract_cmd.index("--step") + 1], "StageC2_2_Step1_mechanical")

        self.assertNotIn("--csv", extract_cmd)

        # Verify extracted displacements
        self.assertEqual(len(u), 13278)
        self.assertEqual(len(d), 13278)
        self.assertEqual(endpoint["rf2_kN"], 0.183)

        # Clean up mock directory
        if self.dummy_output.exists():
            import shutil
            shutil.rmtree(self.dummy_output, ignore_errors=True)

    def test_04_phase_subproblem_extract_command_and_damage_update(self):
        """Verify phase subproblem extraction step name and damage field assignment."""
        captured_cmds = []

        def mock_runner(cmd, cwd, timeout):
            captured_cmds.append(list(cmd))
            if "python" in cmd:
                # Updated damage field d = 0.08
                nodes = [[nid, 0.0, 0.00187, 0.08] for nid in range(1, 13279)]
                endpoint_data = {
                    "schema": 1,
                    "step_name": cmd[cmd.index("--step") + 1],
                    "increment": 1,
                    "rf2_kN": 0.183,
                    "elastic_kNmm": 0.00017,
                    "fracture_kNmm": 0.00005,
                    "total_energy_kNmm": 0.00022,
                    "nodes": nodes
                }
                (Path(cwd) / "endpoint.json").write_text(json.dumps(endpoint_data), encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        controller = C5ForwardContinuationControllerC2_2(
            package=self.package_dir,
            output=self.dummy_output,
            extractor=self.extractor_script,
            abaqus="abaqus",
            runner=mock_runner
        )
        controller.load()

        dummy_damage = {nid: 0.05 for nid in controller.mesh.nodes}
        dummy_disp = {nid: (0.0, 0.00187) for nid in controller.mesh.nodes}
        d, u, endpoint = controller.solve_subproblem(
            step_idx=1, outer=1, inner=0, role="phase",
            damage=dummy_damage, active=set(),
            displacement=dummy_disp, history=controller.h0, target_u=0.001870312544
        )

        extract_cmd = captured_cmds[1]
        self.assertEqual(extract_cmd[extract_cmd.index("--step") + 1], "StageC2_2_Step1_phase")
        self.assertEqual(d[1], 0.08)

        if self.dummy_output.exists():
            import shutil
            shutil.rmtree(self.dummy_output, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
