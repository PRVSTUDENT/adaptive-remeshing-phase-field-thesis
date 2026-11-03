#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r7_c6_coupled_driver_gates.py
=============================================
Regression test suite verifying Package 171-R7 driver-level consistency, KKT, and physical gates:
1. Excessive final displacement correction (> 1e-9 mm) independently prohibits checkpoint serialization.
2. Excessive final history correction (> 1e-4 MPa) independently prohibits checkpoint serialization.
3. Failed final KKT stationarity (> 1e-6) independently prohibits checkpoint serialization.
4. Excessive reaction force drift (> 2.0%) independently prohibits checkpoint serialization.
5. Excessive energy drift (> 2.0%) independently prohibits checkpoint serialization.
6. Damage healing violation (> 1e-6 below d0) independently prohibits checkpoint serialization.
7. Compliant passing state jointly satisfies all physical and consistency gates, committing converged_checkpoint_01.json.
8. Coupled convergence and final consistency remain mandatory independently of KKT stationarity.

Task: F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION
Protocol Version: 2
"""

import sys
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    PDASReEquilibrationSolver, HEALING_TOL, driving_history
)
from scripts.state_transfer.driver_package171_r7_c6_coupled_pdas import (
    Package171R7C6PDASDriver,
    DONOR_REFERENCE_FORCE_KN,
    DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
    DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
    DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
)


class MockQuadMesh(object):
    """1-element quad mesh for driver testing."""
    def __init__(self):
        self.elements = {1: [1, 2, 3, 4]}
        self.nodes = {
            1: (0.0, 0.0),
            2: (1.0, 0.0),
            3: (1.0, 1.0),
            4: (0.0, 1.0)
        }
        self.node_flank = {}


class TestPackage171R7DriverGates(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.tmpdir.name)
        self.pkg_path = self.out_path / "mock_pkg"
        self.pkg_path.mkdir(parents=True, exist_ok=True)

        self.driver = Package171R7C6PDASDriver(
            package=self.pkg_path,
            output=self.out_path,
            extractor=self.pkg_path / "dummy_ext.py",
            omega_d_stage1=0.5,
            omega_d_stage2=0.85
        )
        self.driver.mesh = MockQuadMesh()
        self.driver.d0 = {1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1}
        self.driver.h0 = {(1, g): 10.0 for g in range(1, 5)}
        self.driver.u0 = {n: (0.0, 0.0) for n in range(1, 5)}
        self.driver.target_uy = 0.0018703125442191958

    def tearDown(self):
        self.tmpdir.cleanup()

    def _setup_stationary_state(self):
        solver = PDASReEquilibrationSolver(self.driver.mesh, self.driver.d0, self.driver.h0)
        diag, off, rhs = solver.assemble_system()
        K = np.zeros((4, 4))
        for i in range(1, 5):
            K[i - 1, i - 1] = diag[i]
        for (i, j), val in off.items():
            K[i - 1, j - 1] += val
        b = np.array([rhs[i] for i in range(1, 5)])
        d_stationary = np.linalg.solve(K, b)
        damage = {i + 1: float(max(self.driver.d0[i + 1] + 0.01, d_stationary[i])) for i in range(4)}
        return solver, damage

    def test_excessive_final_displacement_correction_blocks_checkpoint(self):
        """
        Verify that ||u_final - u_staggered||_inf > 1e-9 mm prohibits checkpoint serialization
        and records physical_acceptance=FAIL in summary, even when KKT stationarity passes.
        """
        solver, damage = self._setup_stationary_state()

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        # Excess displacement correction: 5e-9 mm > 1e-9 mm
        consistent_u = {
            1: (0.0, 0.00187 + 5e-9),
            2: (0.0, 0.00187),
            3: (0.0, 0.00187),
            4: (0.0, 0.00187)
        }
        consistent_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }
        history_staggered = dict(self.driver.h0)

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_staggered,
            damage_relaxed=damage,
            consistent_u=consistent_u,
            consistent_endpoint=consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertFalse(physical_pass, "Physical acceptance must fail on delta_u consistency violation")
        self.assertFalse(summary["coupled_field_consistency_u_pass"])
        self.assertGreater(summary["coupled_field_consistency_delta_u_mm"], 1e-9)
        self.assertEqual(summary["physical_acceptance"], "FAIL")

        chkpt_path = self.out_path / "converged_checkpoint_01.json"
        self.assertFalse(chkpt_path.is_file(), "Checkpoint must NOT be serialized on consistency failure")

        summary_on_disk = json.loads((self.out_path / "re_equilibration_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary_on_disk["physical_acceptance"], "FAIL")

    def test_excessive_final_history_correction_blocks_checkpoint(self):
        """
        Verify that ||H_final - H_staggered||_inf > 1e-4 MPa prohibits checkpoint serialization
        and records physical_acceptance=FAIL in summary.
        """
        solver, damage = self._setup_stationary_state()

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        consistent_u = dict(u_staggered)
        consistent_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }

        # Staggered history differs by 5e-4 MPa > 1e-4 MPa
        history_staggered = {k: self.driver.h0[k] + 5.0e-4 for k in self.driver.h0}

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_staggered,
            damage_relaxed=damage,
            consistent_u=consistent_u,
            consistent_endpoint=consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertFalse(physical_pass, "Physical acceptance must fail on delta_H consistency violation")
        self.assertFalse(summary["coupled_field_consistency_h_pass"])
        self.assertGreater(summary["coupled_field_consistency_delta_h_MPa"], 1e-4)
        self.assertEqual(summary["physical_acceptance"], "FAIL")

        chkpt_path = self.out_path / "converged_checkpoint_01.json"
        self.assertFalse(chkpt_path.is_file(), "Checkpoint must NOT be serialized on history consistency failure")

    def test_failed_final_kkt_stationarity_blocks_checkpoint(self):
        """
        Verify that failed final KKT stationarity (e.g. non-stationary damage state)
        prohibits checkpoint serialization.
        """
        solver = PDASReEquilibrationSolver(self.driver.mesh, self.driver.d0, self.driver.h0)

        damage_nonstationary = {1: 0.95, 2: 0.05, 3: 0.85, 4: 0.15}

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        consistent_u = dict(u_staggered)
        consistent_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }
        history_staggered = dict(self.driver.h0)

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_staggered,
            damage_relaxed=damage_nonstationary,
            consistent_u=consistent_u,
            consistent_endpoint=consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertFalse(physical_pass, "Physical acceptance must fail on KKT violation")
        self.assertFalse(summary["kkt_final_pass"])
        self.assertEqual(summary["physical_acceptance"], "FAIL")

        chkpt_path = self.out_path / "converged_checkpoint_01.json"
        self.assertFalse(chkpt_path.is_file(), "Checkpoint must NOT be serialized on KKT failure")

    def test_excessive_force_drift_blocks_checkpoint(self):
        """
        Verify that reaction force discrepancy > 2.0% prohibits checkpoint serialization.
        """
        solver, damage = self._setup_stationary_state()

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        consistent_u = dict(u_staggered)
        # Drift force by +5.0% (> 2.0%)
        consistent_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN * 1.05,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }
        zero_baseline = {(1, g): 0.0 for g in range(1, 5)}
        psi_final = driving_history(self.driver.mesh, consistent_u, zero_baseline)
        history_consistent = {k: max(self.driver.h0[k], psi_final[k]) for k in self.driver.h0}

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_consistent,
            damage_relaxed=damage,
            consistent_u=consistent_u,
            consistent_endpoint=consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertFalse(physical_pass, "Physical acceptance must fail on force discrepancy violation")
        self.assertFalse(summary["force_gate_pass"])
        self.assertGreater(summary["force_discrepancy_pct"], 2.0)
        chkpt_path = self.out_path / "converged_checkpoint_01.json"
        self.assertFalse(chkpt_path.is_file())

    def test_excessive_energy_drift_blocks_checkpoint(self):
        """
        Verify that total energy discrepancy > 2.0% prohibits checkpoint serialization.
        """
        solver, damage = self._setup_stationary_state()

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        consistent_u = dict(u_staggered)
        # Drift energy by +5.0% (> 2.0%)
        consistent_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_TOTAL_ENERGY_KNMM * 1.05,
            "fracture_kNmm": 0.0
        }
        zero_baseline = {(1, g): 0.0 for g in range(1, 5)}
        psi_final = driving_history(self.driver.mesh, consistent_u, zero_baseline)
        history_consistent = {k: max(self.driver.h0[k], psi_final[k]) for k in self.driver.h0}

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_consistent,
            damage_relaxed=damage,
            consistent_u=consistent_u,
            consistent_endpoint=consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertFalse(physical_pass, "Physical acceptance must fail on energy discrepancy violation")
        self.assertFalse(summary["energy_gate_pass"])
        self.assertGreater(summary["energy_discrepancy_pct"], 2.0)
        chkpt_path = self.out_path / "converged_checkpoint_01.json"
        self.assertFalse(chkpt_path.is_file())

    def test_healing_violation_blocks_checkpoint(self):
        """
        Verify that damage healing below d0 prohibits checkpoint serialization.
        """
        solver, damage = self._setup_stationary_state()
        # Create healing: damage at node 1 drops below d0
        damage_healed = dict(damage)
        damage_healed[1] = self.driver.d0[1] - 0.05

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        consistent_u = dict(u_staggered)
        consistent_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }
        zero_baseline = {(1, g): 0.0 for g in range(1, 5)}
        psi_final = driving_history(self.driver.mesh, consistent_u, zero_baseline)
        history_consistent = {k: max(self.driver.h0[k], psi_final[k]) for k in self.driver.h0}

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_consistent,
            damage_relaxed=damage_healed,
            consistent_u=consistent_u,
            consistent_endpoint=consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertFalse(physical_pass, "Physical acceptance must fail on healing violation")
        self.assertFalse(summary["healing_pass"])
        self.assertGreater(summary["healing_violations_count"], 0)
        chkpt_path = self.out_path / "converged_checkpoint_01.json"
        self.assertFalse(chkpt_path.is_file())

    def test_compliant_passing_state_commits_checkpoint(self):
        """
        Verify that a state satisfying all physical and consistency gates:
        - delta_u <= 1e-9 mm
        - delta_h <= 1e-4 MPa
        - KKT errors <= 1e-6
        - force within 2%
        - energy within 2%
        - healing violations == 0
        jointly passes physical acceptance and commits converged_checkpoint_01.json.
        """
        solver, damage = self._setup_stationary_state()

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        consistent_u = dict(u_staggered)

        zero_baseline = {(1, g): 0.0 for g in range(1, 5)}
        psi_final = driving_history(self.driver.mesh, consistent_u, zero_baseline)
        history_consistent = {k: max(self.driver.h0[k], psi_final[k]) for k in self.driver.h0}

        consistent_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_consistent,
            damage_relaxed=damage,
            consistent_u=consistent_u,
            consistent_endpoint=consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertTrue(physical_pass, "All gates should pass in compliant scenario")
        self.assertEqual(summary["physical_acceptance"], "PASS")
        self.assertTrue(summary["coupled_field_consistency_u_pass"])
        self.assertTrue(summary["coupled_field_consistency_h_pass"])
        self.assertTrue(summary["kkt_final_pass"])
        self.assertTrue(summary["force_gate_pass"])
        self.assertTrue(summary["energy_gate_pass"])
        self.assertTrue(summary["healing_pass"])

        chkpt_path = self.out_path / "converged_checkpoint_01.json"
        self.assertTrue(chkpt_path.is_file(), "Checkpoint must be atomically serialized on pass")

        chkpt = json.loads(chkpt_path.read_text(encoding="utf-8"))
        self.assertEqual(chkpt["schema"], 1)
        self.assertEqual(chkpt["contract"], "Package 171-R7 C6 Coupled PDAS Re-Equilibration")
        self.assertEqual(chkpt["physical_acceptance"], "PASS")
        self.assertEqual(len(chkpt["displacement"]), 4)
        self.assertEqual(len(chkpt["damage"]), 4)
        self.assertEqual(len(chkpt["history"]), 4)


if __name__ == "__main__":
    unittest.main()
