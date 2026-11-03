#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r4_c6_coupled_driver_gates.py
=============================================
Regression test suite verifying Package 171-R4 driver-level consistency and KKT gates:
1. Excessive final displacement correction (> 1e-9 mm) independently prohibits checkpoint serialization.
2. Excessive final history correction (> 1e-4 MPa) independently prohibits checkpoint serialization.
3. Failed final KKT stationarity (> 1e-6) independently prohibits checkpoint serialization.
4. Compliant passing state jointly satisfies all physical and consistency gates, committing converged_checkpoint_01.json.

Exercises the actual driver's acceptance and checkpoint-writing logic using controlled mechanical-solver outputs.

Task: F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION -> R4 Candidate Qualification
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
from scripts.state_transfer.driver_package171_r4_c6_coupled_pdas import (
    Package171R4C6PDASDriver,
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


class TestPackage171R4DriverGates(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.tmpdir.name)
        self.pkg_path = self.out_path / "mock_pkg"
        self.pkg_path.mkdir(parents=True, exist_ok=True)

        # Instantiate driver with mock paths
        self.driver = Package171R4C6PDASDriver(
            package=self.pkg_path,
            output=self.out_path,
            extractor=self.pkg_path / "dummy_ext.py",
            damping_omega_d=0.5
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
        and records physical_acceptance=FAIL in summary.
        """
        solver, damage = self._setup_stationary_state()

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        # Excess displacement correction: 5e-9 mm > 1e-9 mm
        consistent_u = {
            1: (0.0, 0.00187),
            2: (0.0, 0.00187),
            3: (0.0, 0.00187 + 5e-9),
            4: (0.0, 0.00187)
        }

        # Driving history from consistent_u
        zero_baseline = {(1, g): 0.0 for g in range(1, 5)}
        psi_final = driving_history(self.driver.mesh, consistent_u, zero_baseline)
        history_staggered = {k: max(self.driver.h0[k], psi_final[k]) for k in self.driver.h0}

        endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }

        chkpt_path = self.out_path / "converged_checkpoint_01.json"
        # Pre-seed to test deletion
        chkpt_path.write_text("STALE_DATA", encoding="utf-8")

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_staggered,
            damage_relaxed=damage,
            consistent_u=consistent_u,
            consistent_endpoint=endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertFalse(physical_pass, "Must reject physical acceptance on excessive displacement correction")
        self.assertFalse(summary["coupled_field_consistency_u_pass"])
        self.assertEqual(summary["physical_acceptance"], "FAIL")
        self.assertGreater(summary["coupled_field_consistency_delta_u_mm"], 1e-9)
        self.assertFalse(chkpt_path.exists(), "converged_checkpoint_01.json must be suppressed on failure")

    def test_excessive_final_history_correction_blocks_checkpoint(self):
        """
        Verify that ||H_final - H_staggered||_inf > 1e-4 MPa prohibits checkpoint serialization.
        """
        solver, damage = self._setup_stationary_state()

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        # Displacement within 1e-9 mm
        consistent_u = {n: (0.0, 0.00187 + 5e-10) for n in range(1, 5)}

        zero_baseline = {(1, g): 0.0 for g in range(1, 5)}
        psi_final = driving_history(self.driver.mesh, consistent_u, zero_baseline)
        history_final = {k: max(self.driver.h0[k], psi_final[k]) for k in self.driver.h0}

        # Staggered history is significantly different: delta_h = 5e-3 MPa > 1e-4 MPa
        history_staggered = {k: history_final[k] + 5e-3 for k in history_final}

        endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }

        chkpt_path = self.out_path / "converged_checkpoint_01.json"

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_staggered,
            damage_relaxed=damage,
            consistent_u=consistent_u,
            consistent_endpoint=endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertFalse(physical_pass, "Must reject physical acceptance on excessive history correction")
        self.assertFalse(summary["coupled_field_consistency_h_pass"])
        self.assertEqual(summary["physical_acceptance"], "FAIL")
        self.assertGreater(summary["coupled_field_consistency_delta_h_MPa"], 1e-4)
        self.assertFalse(chkpt_path.exists(), "converged_checkpoint_01.json must be suppressed on failure")

    def test_failed_final_kkt_blocks_checkpoint(self):
        """
        Verify that failed final KKT stationarity (> 1e-6) prohibits checkpoint serialization.
        """
        solver, damage = self._setup_stationary_state()

        # Perturb damage slightly within bounds [d0, 1.0] so KKT free residual fails
        damage_perturbed = {}
        for n in damage:
            val = damage[n] - 0.005 if damage[n] > self.driver.d0[n] + 0.01 else damage[n] + 0.005
            damage_perturbed[n] = min(0.99, max(self.driver.d0[n], val))

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        consistent_u = {n: (0.0, 0.00187) for n in range(1, 5)}

        zero_baseline = {(1, g): 0.0 for g in range(1, 5)}
        psi_final = driving_history(self.driver.mesh, consistent_u, zero_baseline)
        history_staggered = {k: max(self.driver.h0[k], psi_final[k]) for k in self.driver.h0}

        endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }

        chkpt_path = self.out_path / "converged_checkpoint_01.json"

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_staggered,
            damage_relaxed=damage_perturbed,
            consistent_u=consistent_u,
            consistent_endpoint=endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertFalse(physical_pass, "Must reject physical acceptance on failed final KKT")
        self.assertFalse(summary["kkt_final_pass"])
        self.assertEqual(summary["physical_acceptance"], "FAIL")
        self.assertGreater(summary["kkt_free_error"], 1e-6)
        self.assertFalse(chkpt_path.exists(), "converged_checkpoint_01.json must be suppressed on failure")

    def test_passing_case_commits_valid_checkpoint(self):
        """
        Verify that when all consistency (delta_u <= 1e-9 mm, delta_h <= 1e-4 MPa), KKT (<= 1e-6),
        force/energy (<= 2%), and physical monotonicity/healing criteria are met, the driver
        commits converged_checkpoint_01.json atomically with physical_acceptance=PASS.
        """
        solver, damage = self._setup_stationary_state()

        u_staggered = {n: (0.0, 0.00187) for n in range(1, 5)}
        # Very tiny displacement change: 1e-10 mm <= 1e-9 mm
        consistent_u = {n: (0.0, 0.00187 + 1e-10) for n in range(1, 5)}

        zero_baseline = {(1, g): 0.0 for g in range(1, 5)}
        psi_final = driving_history(self.driver.mesh, consistent_u, zero_baseline)
        history_final = {k: max(self.driver.h0[k], psi_final[k]) for k in self.driver.h0}
        # Very tiny history change: 1e-6 MPa <= 1e-4 MPa
        history_staggered = {k: history_final[k] + 1e-6 for k in history_final}

        endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN * 1.005,  # 0.5% drift <= 2%
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM * 1.005,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM * 1.005
        }

        chkpt_path = self.out_path / "converged_checkpoint_01.json"

        summary, physical_pass = self.driver.finalize_coupled_acceptance(
            u_staggered=u_staggered,
            history_staggered=history_staggered,
            damage_relaxed=damage,
            consistent_u=consistent_u,
            consistent_endpoint=endpoint,
            solver=solver,
            step_idx=1,
            outer=10,
            target_uy=self.driver.target_uy
        )

        self.assertTrue(physical_pass, "Must accept compliant physical and consistency state")
        self.assertTrue(summary["coupled_field_consistency_u_pass"])
        self.assertTrue(summary["coupled_field_consistency_h_pass"])
        self.assertTrue(summary["kkt_final_pass"])
        self.assertEqual(summary["physical_acceptance"], "PASS")
        self.assertTrue(chkpt_path.is_file(), "converged_checkpoint_01.json must exist")

        chkpt_data = json.loads(chkpt_path.read_text(encoding="utf-8"))
        self.assertEqual(chkpt_data["schema"], 1)
        self.assertEqual(chkpt_data["physical_acceptance"], "PASS")
        self.assertEqual(len(chkpt_data["displacement"]), 4)
        self.assertEqual(len(chkpt_data["damage"]), 4)
        self.assertEqual(len(chkpt_data["history"]), 4)


if __name__ == "__main__":
    unittest.main()
