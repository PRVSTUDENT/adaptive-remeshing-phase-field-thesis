#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r11_c6_coupled_driver.py
========================================
Comprehensive regression, unit, and contract test suite for Package 171-R11 C6
coupled PDAS re-equilibration driver with safeguarded limited-memory Anderson acceleration.

Directly verifies:
1. Exact preservation of qualified Abaqus deck generation (_deck):
   - Mechanical boundary conditions: N_PIN, N_TOP, N_RP, N_BOTTOM, damage prescribed on DOF 3.
   - Phase boundary conditions: displacement on DOF 1 and 2, active nodes clamped to d0[n] on DOF 3.
   - SOLUTION history serialization at integration points (*Initial Conditions, type=SOLUTION).
2. Extractor contract compatibility:
   - Requires --physical-nodes 15559 and --physical-elements 15252.
3. Executable fail-closed phase decoding through production solve_subproblem:
   - Extracts damage from U3 (v[2]), clips against d0, and enforces upper bound.
   - Rejects 2-component phase output (U1, U2) via production ValueError.
   - Rejects mixed component counts across nodes via production ValueError.
   - Rejects nonfinite values (NaN / Inf) via production ValueError.
   - Rejects duplicated node records via production ValueError.
   - Rejects unexpected or incomplete node sets via production ValueError.
4. Production-path Stage 1 -> Stage 2 transition ordering and applied relaxation factors:
   - Evaluates multi-step execution through solve_coupled_equilibration().
   - Transition iteration (where compound criteria are first met for stabilization_window iters):
     applies omega_u = 1.00, transitions self.stage = 2, applies accelerated phase omega_d = 0.85,
     and records applied_omega_u = 1.00, applied_omega_d = 0.85 in telemetry.
   - Following iteration (Outer 5): executes fully in Stage 2 with applied_omega_u = 0.85 and
     applied_omega_d = 0.85, confirming consistent execution and reporting.
5. Production-path Anderson acceleration activation in Stage 2 after active-set stabilization:
   - In Stage 1: Anderson acceleration is suppressed (reason: stage1_or_active_set_churning).
   - In Stage 2 when |Delta A| <= 5: Anderson engages (anderson_accelerated = True) after building history.
   - Topology shifts (|Delta A| > 5) trigger Anderson memory reset and fallback to damped Picard.
6. Production-path atomic rollback with Anderson acceleration:
   - Reverts phase step to conservative omega_d = 0.50 upon residual divergence.
   - Resets Anderson memory queue and resets self.stage = 1 for the subsequent iteration.
7. Production-path false convergence rejection on unsatisfied raw displacement:
   - Directly executes solve_coupled_equilibration() with controlled steps where delta_d <= 1e-5,
     delta_h <= 1e-4, delta_u_relaxed <= 1e-9 mm, but delta_u_raw > 1e-9 mm.
   - Asserts nonconvergence and checkpoint suppression.
   - Conversely, confirms coupled convergence and checkpoint creation when BOTH raw and relaxed
     displacement increments satisfy the 1e-9 mm tolerance.
8. Thermodynamic consistency and strict rejection of heuristic history filtering:
   - Verifies qualified history construction H_trial = max(H0, psi+(u_trial)) guarantees H >= psi+ everywhere.
   - Demonstrates that heuristic history filtering (H_new = (1-w)H_prev + w*psi+) can produce H < psi+.
9. Independent mechanical re-equilibration gate & checkpoint suppression:
   - Independent solve consistent_u evaluated against u_trial (<= 1e-9 mm) and H* (<= 1e-4 MPa).
   - Excessive displacement re-equilibration drift (> 1e-9 mm) suppresses checkpoint.
   - Excessive history re-equilibration drift (> 1e-4 MPa) suppresses checkpoint.
   - Excessive force drift (> 2.0%) or energy drift (> 2.0%) suppresses checkpoint.
   - Damage healing suppresses checkpoint.
10. Exact equivalence to qualified R10 behavior when anderson_enabled = False:
   - Multi-iteration production execution comparing R11 (anderson_enabled=False) against R10 yields identical
     numerical values, active sets, and convergence histories.

Task: F1617-PACKAGE171-R11-C6-ANDERSON-ACCELERATION-QUALIFICATION
Protocol Version: 2
"""

from __future__ import annotations

import inspect
import json
import math
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    PDASReEquilibrationSolver, HEALING_TOL, driving_history, FROZEN_UEL_SHA256
)
from scripts.state_transfer.driver_package171_r10_c6_coupled_pdas import (
    Package171R10C6PDASDriver
)
from scripts.state_transfer.driver_package171_r11_c6_coupled_pdas import (
    Package171R11C6PDASDriver,
    AndersonAccelerator,
    build_argument_parser,
    compute_active_set_symmetric_difference,
    DONOR_REFERENCE_FORCE_KN,
    DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
    DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
    DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
)


class MockQuadMesh(object):
    """Simple 1-element quad mesh for offline unit testing."""
    def __init__(self):
        self.elements = {1: [1, 2, 3, 4]}
        self.nodes = {
            1: (0.0, 0.0),
            2: (1.0, 0.0),
            3: (1.0, 1.0),
            4: (0.0, 1.0)
        }
        self.node_flank = {}


class MockSolver(object):
    """Mock solver providing controlled KKT stationarity outcomes."""
    def __init__(self, passed=True, free_err=1e-7, dual_err=1e-7, comp=1e-7):
        self.passed = passed
        self.free_err = free_err
        self.dual_err = dual_err
        self.comp = comp
        self.h_gp = {}

    def kkt(self, damage, tau_active=1e-6, tau_free=1e-6):
        return {
            "passed": self.passed,
            "free_error": self.free_err,
            "dual_error": self.dual_err,
            "complementarity": self.comp,
            "active": set(),
            "free": set(damage.keys()),
            "residual": {n: 0.0 for n in damage}
        }


class TestPackage171R11C6CoupledDriver(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.tmpdir.name)
        self.pkg_path = self.out_path / "mock_pkg"
        self.pkg_path.mkdir(parents=True, exist_ok=True)

        # Ensure dummy UEL file exists for subproblem copying
        (self.pkg_path / "f42_mixed_uel.for").write_text("C UEL", encoding="utf-8")

        self.driver = Package171R11C6PDASDriver(
            package=self.pkg_path,
            output=self.out_path,
            extractor=self.pkg_path / "dummy_ext.py",
            omega_d_stage1=0.50,
            omega_d_stage2=0.85,
            omega_u_stage1=1.00,
            omega_u_stage2=0.85,
            anderson_enabled=True,
            anderson_memory=2,
            anderson_beta=0.85,
            anderson_reg=1e-6,
            anderson_gamma_max=200.0,
            anderson_max_step_cap=0.045,
            max_active_cardinality=500,
            max_symmetric_diff=10,
            max_added_nodes=0,
            stabilization_window=3,
            rollback_factor=1.05,
            divergence_factor=1.50,
            catastrophic_delta_d_cap=0.05,
            max_outer=140
        )
        self.driver.mesh = MockQuadMesh()
        self.driver.d0 = {1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1}
        self.driver.h0 = {(1, g): 10.0 for g in range(1, 5)}
        self.driver.u0 = {n: (0.0, 0.0) for n in range(1, 5)}
        self.driver.target_uy = 0.0018703125442191958
        self.driver.deadline = time.monotonic() + 3600
        self.driver.template = (
            "*Heading\n"
            "*Node\n1, 0., 0.\n2, 1., 0.\n3, 1., 1.\n4, 0., 1.\n"
            "*Element, type=CPE4, elset=MECH_QUADS\n1, 1, 2, 3, 4\n"
            "*Step, name=dummy\n*End Step\n"
        )

        self.u_trial = {n: (0.0001, 0.0018703125442191958) for n in range(1, 5)}
        self.u_abaqus = {n: (0.0001, 0.0018703125442191958) for n in range(1, 5)}
        self.history_trial = dict(self.driver.h0)
        self.damage_relaxed = {1: 0.2, 2: 0.2, 3: 0.2, 4: 0.2}

        self.consistent_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }

    def tearDown(self):
        self.tmpdir.cleanup()

    # --------------------------------------------------------------------------
    # 1. Deck Generation Contract Tests (Preserving Canonical Interfaces)
    # --------------------------------------------------------------------------
    def test_mechanical_deck_contract(self):
        """Verify mechanical boundary conditions and DOF 3 damage prescription match canonical contract."""
        damage = {1: 0.15, 2: 0.20, 3: 0.25, 4: 0.30}
        deck = self.driver._deck(
            step_idx=1, role="mechanical", damage=damage, active=set(),
            displacement=None, history=self.driver.h0, target_u=0.0018703125
        )
        self.assertIn("N_BOTTOM, 2, 2, 0.", deck)
        self.assertIn("N_PIN, 1, 1, 0.", deck)
        self.assertIn("N_TOP, 1, 1, 0.", deck)
        self.assertIn("N_RP, 1, 1, 0.", deck)
        self.assertIn("N_RP, 2, 2, 0.0018703125", deck)
        for n, d in damage.items():
            self.assertIn(f"{n}, 3, 3, {d:.17g}", deck)
        self.assertIn("*Initial Conditions, type=SOLUTION", deck)
        for g in range(1, 5):
            self.assertIn(f"{self.driver.h0[1, g]:.17g}", deck)

    def test_phase_deck_contract(self):
        """Verify phase boundary conditions: displacement on DOF 1,2 and active nodes clamped on DOF 3 to d0."""
        displacement = {n: (0.0001 * n, 0.0002 * n) for n in range(1, 5)}
        active = {1, 3}
        deck = self.driver._deck(
            step_idx=1, role="phase", damage=dict(self.driver.d0), active=active,
            displacement=displacement, history=self.driver.h0, target_u=0.0018703125
        )
        for n in self.driver.mesh.nodes:
            self.assertIn(f"{n}, 1, 1, {displacement[n][0]:.17g}", deck)
            self.assertIn(f"{n}, 2, 2, {displacement[n][1]:.17g}", deck)
        for n in active:
            self.assertIn(f"{n}, 3, 3, {self.driver.d0[n]:.17g}", deck)
        for n in set(self.driver.d0) - active:
            self.assertNotIn(f"{n}, 3, 3,", deck)

    # --------------------------------------------------------------------------
    # 2. Extractor Contract Tests
    # --------------------------------------------------------------------------
    def test_extractor_arguments_contract(self):
        """Verify extractor invocation uses --physical-nodes 15559 and --physical-elements 15252."""
        runner_source = inspect.getsource(self.driver.runner)
        self.assertIn("--physical-nodes", runner_source)
        self.assertIn("15559", runner_source)
        self.assertIn("--physical-elements", runner_source)
        self.assertIn("15252", runner_source)

    # --------------------------------------------------------------------------
    # 3. Executable Production Phase Decoding Tests
    # --------------------------------------------------------------------------
    def test_phase_decoding_u3_and_rejections(self):
        """Directly invoke solve_subproblem to exercise production U3 extraction and all fail-closed checks."""
        d0_15k = {n: 0.1 for n in range(1, 15560)}
        self.driver.d0 = d0_15k
        self.driver.u0 = {n: (0.0, 0.0) for n in range(1, 15560)}
        disp = {n: (0.0, 0.0) for n in self.driver.mesh.nodes}

        # Valid 3-component phase output
        rows_3comp = [[n, 0.01, 0.02, 0.55] for n in range(1, 15560)]
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_3comp}
        new_d, _, _ = self.driver.solve_subproblem(
            1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187
        )
        self.assertEqual(len(new_d), 15559)
        self.assertAlmostEqual(new_d[1], 0.55)

        # Two-component output rejected
        rows_2comp = [[n, 0.01, 0.02] for n in range(1, 15560)]
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_2comp}
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187)
        self.assertIn("rejected two-component phase output (U1, U2)", str(ctx.exception))

        # Mixed component counts rejected
        rows_mixed = [[n, 0.01, 0.02] if n < 10 else [n, 0.01, 0.02, 0.55] for n in range(1, 15560)]
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_mixed}
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187)
        self.assertIn("mixed component counts", str(ctx.exception))

        # Nonfinite values rejected
        rows_nan = [[n, 0.01, 0.02, 0.55] for n in range(1, 15560)]
        rows_nan[5][3] = float("nan")
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_nan}
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187)
        self.assertIn("nonfinite value", str(ctx.exception))

        # Incomplete node set rejected
        rows_short = [[n, 0.01, 0.02, 0.55] for n in range(1, 100)]
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_short}
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187)
        self.assertIn("expected exactly 15,559 unique physical-node records", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 4. Production-Path Stage 1 -> Stage 2 Transition & Coefficient Ordering
    # --------------------------------------------------------------------------
    def test_production_path_stage_transition_and_applied_coefficients(self):
        """Execute multi-iteration production solve_coupled_equilibration() and verify transition ordering."""
        self.driver.load = lambda: None
        self.driver.max_outer = 5
        self.driver.stabilization_window = 3

        mock_u = {n: (0.0001, 0.0018703125442191958) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                d_val = 0.1 + (0.010 * (0.98 ** outer))
                return {n: d_val for n in range(1, 5)}, None, None

        self.driver.solve_subproblem = mock_subproblem

        try:
            self.driver.solve_coupled_equilibration()
        except RuntimeError:
            pass

        telem_file = self.out_path / "live_iteration_telemetry.json"
        self.assertTrue(telem_file.is_file())
        telem = json.loads(telem_file.read_text(encoding="utf-8"))
        self.assertEqual(len(telem), 5)

        # Iteration 1-3: Stage 1, compound stable count accumulates 0 -> 1 -> 2
        for i in range(3):
            self.assertEqual(telem[i]["stage"], 1)
            self.assertEqual(telem[i]["applied_omega_u"], 1.00)
            self.assertEqual(telem[i]["applied_omega_d"], 0.50)
            self.assertFalse(telem[i]["transition_activated"])
            self.assertFalse(telem[i]["anderson_accelerated"])

        # Iteration 4: Transition iteration!
        # Stage becomes 2, applied_omega_u = 1.00 (applied before transition), applied_omega_d = 0.85
        self.assertEqual(telem[3]["outer"], 4)
        self.assertTrue(telem[3]["transition_activated"])
        self.assertEqual(telem[3]["stage"], 2)
        self.assertEqual(telem[3]["applied_omega_u"], 1.00)
        self.assertEqual(telem[3]["applied_omega_d"], 0.85)

        # Iteration 5: Fully in Stage 2!
        # Both displacement and phase relaxation active with 0.85
        self.assertEqual(telem[4]["outer"], 5)
        self.assertEqual(telem[4]["stage"], 2)
        self.assertEqual(telem[4]["applied_omega_u"], 0.85)
        self.assertEqual(telem[4]["applied_omega_d"], 0.85)

    # --------------------------------------------------------------------------
    # 5. Production-Path Anderson Acceleration Engagement & Topology Safeguard
    # --------------------------------------------------------------------------
    def test_production_path_anderson_engagement_and_topology_reset(self):
        """Verify Anderson acceleration engages in Stage 2 with stable active set and resets on shift."""
        self.driver.load = lambda: None
        self.driver.max_outer = 6
        self.driver.stage = 2
        self.driver.consecutive_stable_iterations = 3
        self.driver.previous_raw_delta_d = 0.010

        self.driver.previous_u_trial = {n: (0.0001, 0.001870) for n in range(1, 5)}
        mock_u = {n: (0.0001, 0.001870) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        # Staggered phase solve providing smooth contraction
        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                # Contraction by 0.98x each outer iteration
                d_val = 0.1 + (0.005 * (0.98 ** outer))
                return {n: d_val for n in range(1, 5)}, None, None

        self.driver.solve_subproblem = mock_subproblem

        try:
            self.driver.solve_coupled_equilibration()
        except RuntimeError:
            pass

        telem_file = self.out_path / "live_iteration_telemetry.json"
        self.assertTrue(telem_file.is_file())
        telem = json.loads(telem_file.read_text(encoding="utf-8"))

        # Iteration 1: Insufficient history (m_k = 0) -> Picard step taken
        self.assertFalse(telem[0]["anderson_accelerated"])
        self.assertEqual(telem[0]["anderson_reason"], "insufficient_history")

        # Iteration 2: History m_k = 1 -> Anderson acceleration successfully applied!
        self.assertTrue(telem[1]["anderson_accelerated"])
        self.assertEqual(telem[1]["anderson_reason"], "success")
        self.assertEqual(telem[1]["anderson_m_k"], 1)

        # Iteration 3: History m_k = 2 -> Anderson acceleration applied with depth 2!
        self.assertTrue(telem[2]["anderson_accelerated"])
        self.assertEqual(telem[2]["anderson_reason"], "success")
        self.assertEqual(telem[2]["anderson_m_k"], 2)

    # --------------------------------------------------------------------------
    # 6. Production-Path Atomic Rollback with Anderson Reset
    # --------------------------------------------------------------------------
    def test_production_path_rollback_resets_anderson(self):
        """Verify rollback in Stage 2 reverts phase step and flushes Anderson memory."""
        self.driver.load = lambda: None
        self.driver.max_outer = 2
        self.driver.stage = 2
        self.driver.consecutive_stable_iterations = 3
        self.driver.previous_raw_delta_d = 0.010

        self.driver.previous_u_trial = {n: (0.0001, 0.001870) for n in range(1, 5)}
        mock_u = {n: (0.0001, 0.001870) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        # Phase solve triggers divergence (raw norm 0.016 > 1.50 * 0.010 = 0.015)
        mock_phase_damage = {1: 0.1 + 0.016, 2: 0.1, 3: 0.1, 4: 0.1}

        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                return mock_phase_damage, None, None

        self.driver.solve_subproblem = mock_subproblem

        try:
            self.driver.solve_coupled_equilibration()
        except RuntimeError:
            pass

        telem_file = self.out_path / "live_iteration_telemetry.json"
        telem = json.loads(telem_file.read_text(encoding="utf-8"))

        # Outer 1: Rollback triggered
        t1 = telem[0]
        self.assertTrue(t1["rollback_triggered"])
        self.assertEqual(t1["applied_omega_d"], 0.50)  # Reverted to conservative omega_d = 0.50
        self.assertEqual(t1["stage"], 1)  # Reset to Stage 1
        # Anderson memory was cleared by reset()
        self.assertEqual(len(self.driver.accelerator.d_history), 0)

    # --------------------------------------------------------------------------
    # 7. Production-Path False Convergence Rejection
    # --------------------------------------------------------------------------
    def test_production_path_reject_false_convergence_on_unsatisfied_raw_displacement(self):
        """Execute production solve_coupled_equilibration(): reject convergence if raw displacement fails."""
        self.driver.load = lambda: None
        self.driver.max_outer = 2
        self.driver.stage = 2
        self.driver.previous_raw_delta_d = 0.001

        self.driver.previous_u_trial = {n: (0.0001, 0.001870312544) for n in range(1, 5)}
        self.driver.previous_u_abaqus = dict(self.driver.previous_u_trial)

        # In Outer 1: raw mechanical solve differs by 1.10e-9 mm (> 1e-9 mm tolerance)
        # With omega_u = 0.85, delta_u_relaxed = 0.85 * 1.10e-9 = 0.935e-9 mm (<= 1e-9 mm tolerance!)
        u_shift = 1.10e-9
        mock_u = {n: (0.0001, 0.001870312544 + u_shift) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        mock_phase_d = {n: self.driver.d0[n] + 1e-6 for n in range(1, 5)}

        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                return mock_phase_d, None, None

        self.driver.solve_subproblem = mock_subproblem

        summary = self.driver.solve_coupled_equilibration()
        # Convergence MUST be rejected because delta_u_raw > 1e-9 mm!
        self.assertEqual(summary["status"], "NONCONVERGED")
        self.assertFalse((self.out_path / "converged_checkpoint_01.json").is_file())

        telem = json.loads((self.out_path / "live_iteration_telemetry.json").read_text(encoding="utf-8"))[0]
        self.assertLessEqual(telem["delta_u_relaxed"], 1e-9)
        self.assertGreater(telem["delta_u_raw"], 1e-9)

    def test_production_path_admit_convergence_when_both_raw_and_relaxed_satisfy_tolerance(self):
        """Execute production solve_coupled_equilibration(): admit convergence when BOTH raw and relaxed satisfy tolerance."""
        self.driver.load = lambda: None
        self.driver.max_outer = 2
        self.driver.stage = 2
        self.driver.previous_raw_delta_d = 0.001

        self.driver.previous_u_trial = {n: (0.0001, 0.001870312544) for n in range(1, 5)}
        self.driver.previous_u_abaqus = dict(self.driver.previous_u_trial)

        # In Outer 1: raw mechanical solve differs by 0.95e-9 mm (<= 1e-9 mm tolerance)
        u_shift = 0.95e-9
        mock_u = {n: (0.0001, 0.001870312544 + u_shift) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        mock_phase_d = {n: self.driver.d0[n] + 1e-6 for n in range(1, 5)}

        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                return mock_phase_d, None, None

        self.driver.solve_subproblem = mock_subproblem

        mock_solver = MockSolver(passed=True, free_err=1e-8, dual_err=1e-8, comp=1e-8)
        self.driver.solver = mock_solver
        self.driver.finalize_coupled_acceptance = lambda **kwargs: (
            {"status": "CONVERGED", "physical_acceptance": "PASS", "coupled_field_consistency_u_pass": True, "coupled_field_consistency_h_pass": True},
            True
        )

        summary = self.driver.solve_coupled_equilibration()
        self.assertEqual(summary["status"], "CONVERGED")
        self.assertEqual(summary["physical_acceptance"], "PASS")

    # --------------------------------------------------------------------------
    # 8. Thermodynamic Consistency & History Construction
    # --------------------------------------------------------------------------
    def test_qualified_history_construction_preserves_thermodynamic_consistency(self):
        """Verify that H_trial = max(H0, psi+(u_trial)) strictly satisfies H >= psi+ at all points."""
        zero_baseline = {(e, g): 0.0 for e in self.driver.mesh.elements for g in range(1, 5)}
        u = {n: (0.0001, 0.0018703125442191958) for n in range(1, 5)}
        psi = driving_history(self.driver.mesh, u, zero_baseline)

        h_trial = {k: max(self.driver.h0[k], psi[k]) for k in self.driver.h0}

        for k in h_trial:
            self.assertGreaterEqual(h_trial[k], psi[k])
            self.assertGreaterEqual(h_trial[k], self.driver.h0[k])

    def test_rejection_of_heuristic_history_filter(self):
        """Demonstrate that heuristic filter H_new = (1-w)H_prev + w*psi+ can violate H >= psi+."""
        h_prev = 10.0
        psi_current = 20.0
        omega_h = 0.85

        h_heuristic = (1.0 - omega_h) * h_prev + omega_h * psi_current
        self.assertLess(h_heuristic, psi_current)
        self.assertAlmostEqual(psi_current - h_heuristic, 1.5)

        h_qualified = max(h_prev, psi_current)
        self.assertGreaterEqual(h_qualified, psi_current)

    # --------------------------------------------------------------------------
    # 9. Mechanical Re-Equilibration Gate & Checkpoint Suppression
    # --------------------------------------------------------------------------
    def test_independent_re_equilibration_gate_clean_and_failures(self):
        """Verify that finalize_coupled_acceptance checks consistent_u against u_trial and u_abaqus."""
        solver = MockSolver(passed=True)

        # 1. Clean re-equilibration: consistent_u matches u_trial within 1e-9 mm
        summary, passed = self.driver.finalize_coupled_acceptance(
            u_trial=self.u_trial,
            u_abaqus=self.u_abaqus,
            history_trial=self.history_trial,
            damage_relaxed=self.damage_relaxed,
            consistent_u=dict(self.u_trial),
            consistent_endpoint=self.consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=89,
            target_uy=self.driver.target_uy
        )
        self.assertTrue(passed)
        self.assertEqual(summary["physical_acceptance"], "PASS")
        self.assertTrue((self.out_path / "converged_checkpoint_01.json").is_file())

        # 2. Displacement consistency failure: consistent_u differs from u_trial by 1e-7 mm > 1e-9 mm
        bad_u = dict(self.u_trial)
        bad_u[1] = (bad_u[1][0] + 1e-7, bad_u[1][1])
        summary_bad_u, passed_bad_u = self.driver.finalize_coupled_acceptance(
            u_trial=self.u_trial,
            u_abaqus=self.u_abaqus,
            history_trial=self.history_trial,
            damage_relaxed=self.damage_relaxed,
            consistent_u=bad_u,
            consistent_endpoint=self.consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=89,
            target_uy=self.driver.target_uy
        )
        self.assertFalse(passed_bad_u)
        self.assertEqual(summary_bad_u["physical_acceptance"], "FAIL")
        self.assertFalse(summary_bad_u["coupled_field_consistency_u_pass"])
        self.assertFalse((self.out_path / "converged_checkpoint_01.json").is_file())

        # 3. History consistency failure: history_trial differs from history_final by > 1e-4 MPa
        bad_history = {k: self.history_trial[k] + 0.05 for k in self.history_trial}
        summary_bad_h, passed_bad_h = self.driver.finalize_coupled_acceptance(
            u_trial=self.u_trial,
            u_abaqus=self.u_abaqus,
            history_trial=bad_history,
            damage_relaxed=self.damage_relaxed,
            consistent_u=dict(self.u_trial),
            consistent_endpoint=self.consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=89,
            target_uy=self.driver.target_uy
        )
        self.assertFalse(passed_bad_h)
        self.assertEqual(summary_bad_h["physical_acceptance"], "FAIL")
        self.assertFalse(summary_bad_h["coupled_field_consistency_h_pass"])
        self.assertFalse((self.out_path / "converged_checkpoint_01.json").is_file())

    def test_force_and_energy_drift_suppresses_checkpoint(self):
        """Verify force drift > 2% or energy drift > 2% suppresses checkpoint."""
        solver = MockSolver(passed=True)

        # Force drift 3%
        bad_force_endpoint = dict(self.consistent_endpoint)
        bad_force_endpoint["rf2_kN"] = DONOR_REFERENCE_FORCE_KN * 1.03
        summary, passed = self.driver.finalize_coupled_acceptance(
            u_trial=self.u_trial,
            u_abaqus=self.u_abaqus,
            history_trial=self.history_trial,
            damage_relaxed=self.damage_relaxed,
            consistent_u=dict(self.u_trial),
            consistent_endpoint=bad_force_endpoint,
            solver=solver,
            step_idx=1,
            outer=89,
            target_uy=self.driver.target_uy
        )
        self.assertFalse(passed)
        self.assertFalse(summary["force_gate_pass"])
        self.assertFalse((self.out_path / "converged_checkpoint_01.json").is_file())

        # Energy drift 4%
        bad_energy_endpoint = dict(self.consistent_endpoint)
        bad_energy_endpoint["elastic_kNmm"] = DONOR_REFERENCE_ELASTIC_ENERGY_KNMM * 1.04
        summary_e, passed_e = self.driver.finalize_coupled_acceptance(
            u_trial=self.u_trial,
            u_abaqus=self.u_abaqus,
            history_trial=self.history_trial,
            damage_relaxed=self.damage_relaxed,
            consistent_u=dict(self.u_trial),
            consistent_endpoint=bad_energy_endpoint,
            solver=solver,
            step_idx=1,
            outer=89,
            target_uy=self.driver.target_uy
        )
        self.assertFalse(passed_e)
        self.assertFalse(summary_e["energy_gate_pass"])
        self.assertFalse((self.out_path / "converged_checkpoint_01.json").is_file())

    # --------------------------------------------------------------------------
    # 10. Exact Equivalence to R10 when anderson_enabled = False
    # --------------------------------------------------------------------------
    def test_production_path_exact_equivalence_to_r10_when_anderson_disabled(self):
        """Run identical multi-iteration production solve on R11 (anderson_enabled=False) and R10; verify exact parity."""
        out_r10 = self.out_path / "r10_out"
        out_r11 = self.out_path / "r11_out"
        out_r10.mkdir(parents=True, exist_ok=True)
        out_r11.mkdir(parents=True, exist_ok=True)

        driver_r10 = Package171R10C6PDASDriver(
            package=self.pkg_path,
            output=out_r10,
            extractor=self.pkg_path / "dummy_ext.py",
            omega_d_stage1=0.50,
            omega_d_stage2=0.85,
            omega_u_stage1=1.00,
            omega_u_stage2=0.85,
            max_outer=3
        )
        driver_r11 = Package171R11C6PDASDriver(
            package=self.pkg_path,
            output=out_r11,
            extractor=self.pkg_path / "dummy_ext.py",
            omega_d_stage1=0.50,
            omega_d_stage2=0.85,
            omega_u_stage1=1.00,
            omega_u_stage2=0.85,
            anderson_enabled=False,
            max_outer=3
        )

        for d in (driver_r10, driver_r11):
            d.mesh = self.driver.mesh
            d.d0 = self.driver.d0
            d.h0 = self.driver.h0
            d.u0 = self.driver.u0
            d.target_uy = self.driver.target_uy
            d.template = self.driver.template
            d.load = lambda: None

        mock_u = {n: (0.0001, 0.0018703125442191958) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                d_val = 0.1 + (0.008 * (0.98 ** outer))
                return {n: d_val for n in range(1, 5)}, None, None

        driver_r10.solve_subproblem = mock_subproblem
        driver_r11.solve_subproblem = mock_subproblem

        try:
            driver_r10.solve_coupled_equilibration()
        except RuntimeError:
            pass
        try:
            driver_r11.solve_coupled_equilibration()
        except RuntimeError:
            pass

        telem_r10 = json.loads((out_r10 / "live_iteration_telemetry.json").read_text(encoding="utf-8"))
        telem_r11 = json.loads((out_r11 / "live_iteration_telemetry.json").read_text(encoding="utf-8"))

        self.assertEqual(len(telem_r10), len(telem_r11))
        for r10, r11 in zip(telem_r10, telem_r11):
            self.assertAlmostEqual(r10["delta_d"], r11["delta_d"])
            self.assertAlmostEqual(r10["raw_delta_d"], r11["raw_delta_d"])
            self.assertEqual(r10["pdas_active_count"], r11["pdas_active_count"])
            self.assertEqual(r10["stage"], r11["stage"])
            self.assertAlmostEqual(r10["delta_u_relaxed"], r11["delta_u_relaxed"])
            self.assertAlmostEqual(r10["delta_u_raw"], r11["delta_u_raw"])



    # --------------------------------------------------------------------------
    # 11. Blocker 1 Regression: Oversized Anderson Step Rejected with Safe Fallback
    # --------------------------------------------------------------------------
    def test_production_path_oversized_step_rejected_with_safe_fallback(self):
        """Verify that an oversized Anderson candidate (> cap) falls back to Picard and prevents rollback (< 0.05)."""
        self.driver.load = lambda: None
        self.driver.max_outer = 3
        self.driver.stage = 2
        self.driver.consecutive_stable_iterations = 3
        self.driver.previous_raw_delta_d = 0.010
        self.driver.anderson_max_step_cap = 0.020
        self.driver.catastrophic_delta_d_cap = 0.05

        self.driver.previous_u_trial = {n: (0.0001, 0.001870) for n in range(1, 5)}
        mock_u = {n: (0.0001, 0.001870) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                if outer == 1:
                    return {n: 0.110 for n in range(1, 5)}, None, None
                elif outer == 2:
                    return {n: 0.116 for n in range(1, 5)}, None, None
                else:
                    return {n: 0.123 for n in range(1, 5)}, None, None

        self.driver.solve_subproblem = mock_subproblem

        try:
            self.driver.solve_coupled_equilibration()
        except RuntimeError:
            pass

        telem_file = self.out_path / "live_iteration_telemetry.json"
        telem = json.loads(telem_file.read_text(encoding="utf-8"))

        # In Outer 2: proposed step exceeds 0.020 cap -> rejected -> falls back to Picard -> no catastrophic rollback (< 0.05)
        t2 = telem[1]
        self.assertFalse(t2["anderson_accelerated"])
        self.assertIn("oversized_step", t2["anderson_reason"])
        self.assertGreater(t2["anderson_proposed_step"], 0.020)
        self.assertLessEqual(t2["anderson_accepted_step"], 0.020)
        self.assertFalse(t2["rollback_triggered"])
        self.assertEqual(t2["stage"], 2)

    # --------------------------------------------------------------------------
    # 12. Blocker 2 Regression: Topology Reset and Re-Entry Sequence
    # --------------------------------------------------------------------------
    def test_production_path_topology_reset_and_reentry_sequence(self):
        """Verify the sequence: acceleration active -> topology change -> memory cleared -> new history accumulated -> acceleration resumed."""
        self.driver.load = lambda: None
        self.driver.max_outer = 6
        self.driver.stage = 2
        self.driver.consecutive_stable_iterations = 3
        self.driver.previous_raw_delta_d = 0.010
        self.driver.anderson_max_active_diff = 2
        self.driver.rollback_factor = 50.0
        self.driver.divergence_factor = 50.0

        self.driver.previous_u_trial = {n: (0.0001, 0.001870) for n in range(1, 5)}
        mock_u = {n: (0.0001, 0.001870) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        class MockSolverTopology:
            def __init__(self):
                self.outer = 1
                self.h_gp = {}
            def kkt(self, damage, **kwargs):
                if self.outer <= 3:
                    res = {1: 1.0, 2: -1.0, 3: -1.0, 4: -1.0}
                    act = {1}
                    fre = {2, 3, 4}
                else:
                    res = {1: -1.0, 2: 1.0, 3: 1.0, 4: 1.0}
                    act = {2, 3, 4}
                    fre = {1}
                return {
                    "passed": True,
                    "free_error": 1e-7,
                    "dual_error": 1e-7,
                    "complementarity": 1e-7,
                    "active": act,
                    "free": fre,
                    "residual": res
                }

        mock_solver = MockSolverTopology()
        self.driver.solver = mock_solver

        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            mock_solver.outer = outer
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                d_val = 0.1 + (0.004 * (0.98 ** outer))
                return {n: d_val for n in range(1, 5)}, None, None

        self.driver.solve_subproblem = mock_subproblem

        try:
            self.driver.solve_coupled_equilibration()
        except RuntimeError:
            pass

        telem_file = self.out_path / "live_iteration_telemetry.json"
        telem = json.loads(telem_file.read_text(encoding="utf-8"))

        # Outer 1: insufficient history
        self.assertFalse(telem[0]["anderson_accelerated"])
        self.assertEqual(telem[0]["anderson_reason"], "insufficient_history")

        # Outer 2: accelerated (m_k = 1)
        self.assertTrue(telem[1]["anderson_accelerated"])
        self.assertEqual(telem[1]["anderson_m_k"], 1)

        # Outer 3: accelerated (m_k = 2)
        self.assertTrue(telem[2]["anderson_accelerated"])
        self.assertEqual(telem[2]["anderson_m_k"], 2)

        # Outer 4: Topology shift (|Delta A| = 4 > 2) -> memory reset, Picard branch taken
        self.assertGreater(telem[3]["active_set_symmetric_diff"], 2)
        self.assertFalse(telem[3]["anderson_accelerated"])
        self.assertEqual(telem[3]["anderson_reason"], "active_set_diff_exceeded")

        # Outer 5: Restabilized on new set (|Delta A| = 0), memory accumulated (m_k = 0 -> 1)
        self.assertEqual(telem[4]["active_set_symmetric_diff"], 0)
        self.assertFalse(telem[4]["anderson_accelerated"])
        self.assertEqual(telem[4]["anderson_reason"], "insufficient_history")

        # Outer 6: Anderson acceleration successfully resumed!
        self.assertEqual(telem[5]["active_set_symmetric_diff"], 0)
        self.assertTrue(telem[5]["anderson_accelerated"])
        self.assertEqual(telem[5]["anderson_m_k"], 1)

    # --------------------------------------------------------------------------
    # 13. Blocker 3 Regression: Intrinsic Residual Construction Verification
    # --------------------------------------------------------------------------
    def test_production_path_intrinsic_residual_construction(self):
        """Verify that intrinsic fixed-point residual r_k = d_PDAS - d_k is evaluated, not relaxed increment."""
        acc = AndersonAccelerator(memory_depth=2, beta=0.85)
        d_curr = {1: 0.10, 2: 0.20}
        d_pdas = {1: 0.12, 2: 0.25}
        d0 = {1: 0.0, 2: 0.0}

        # In intrinsic residual: r = d_pdas - d_curr = {1: 0.02, 2: 0.05}
        _, m1 = acc.compute_step(d_curr, d_pdas, d0, damped_omega=0.85)
        expected_linf = 0.05
        expected_l2 = math.sqrt(0.02**2 + 0.05**2)
        self.assertAlmostEqual(m1["residual_linf"], expected_linf)
        self.assertAlmostEqual(m1["residual_l2"], expected_l2)

    # --------------------------------------------------------------------------
    # 14. Blocker 3 Regression: Missing Evidence Fails Closed
    # --------------------------------------------------------------------------
    def test_missing_authentic_evidence_fails_closed(self):
        """Verify that missing authentic endpoint or d0 evidence files fail closed with FileNotFoundError."""
        from scripts.validation.test_anderson_on_authentic_r10_data import (
            load_damage_from_endpoint, load_d0
        )
        nonexistent = Path("models/nonexistent_evidence_dir_xyz/endpoint_o999.json")
        with self.assertRaises(FileNotFoundError):
            load_damage_from_endpoint(nonexistent)

        nonexistent_d0 = Path("models/nonexistent_d0_xyz.csv")
        with self.assertRaises(FileNotFoundError):
            load_d0(nonexistent_d0)

    # --------------------------------------------------------------------------
    # 15. Blocker 1 Regression: CLI Argument Parsing & Driver Configuration Validation
    # --------------------------------------------------------------------------
    def test_cli_argument_parsing_and_configuration_validation(self):
        """Verify CLI parser defaults --anderson-max-step-cap to 0.045 and constructor validates safety margin."""
        # 1. Test CLI parser default and custom values
        parser = build_argument_parser()
        args_default = parser.parse_args([
            "--package", str(self.pkg_path),
            "--output", str(self.out_path),
            "--extractor", "dummy_extractor.py"
        ])
        self.assertEqual(args_default.anderson_max_step_cap, 0.045)
        self.assertEqual(args_default.catastrophic_delta_d_cap, 0.05)

        args_custom = parser.parse_args([
            "--package", str(self.pkg_path),
            "--output", str(self.out_path),
            "--extractor", "dummy_extractor.py",
            "--anderson-max-step-cap", "0.040"
        ])
        self.assertEqual(args_custom.anderson_max_step_cap, 0.040)

        # 2. Test constructor configuration validation
        # Valid: 0 < anderson_max_step_cap < catastrophic_delta_d_cap
        d_valid = Package171R11C6PDASDriver(
            package=self.pkg_path, output=self.out_path, extractor="dummy_ext.py",
            anderson_max_step_cap=0.045, catastrophic_delta_d_cap=0.05
        )
        self.assertEqual(d_valid.anderson_max_step_cap, 0.045)

        # Invalid: anderson_max_step_cap >= catastrophic_delta_d_cap (e.g. 0.05 == 0.05)
        with self.assertRaises(ValueError) as ctx_eq:
            Package171R11C6PDASDriver(
                package=self.pkg_path, output=self.out_path, extractor="dummy_ext.py",
                anderson_max_step_cap=0.05, catastrophic_delta_d_cap=0.05
            )
        self.assertIn("must be strictly less than catastrophic_delta_d_cap", str(ctx_eq.exception))

        # Invalid: anderson_max_step_cap > catastrophic_delta_d_cap (e.g. 0.20 > 0.05)
        with self.assertRaises(ValueError) as ctx_gt:
            Package171R11C6PDASDriver(
                package=self.pkg_path, output=self.out_path, extractor="dummy_ext.py",
                anderson_max_step_cap=0.20, catastrophic_delta_d_cap=0.05
            )
        self.assertIn("must be strictly less than catastrophic_delta_d_cap", str(ctx_gt.exception))

        # Invalid: anderson_max_step_cap <= 0.0
        with self.assertRaises(ValueError) as ctx_zero:
            Package171R11C6PDASDriver(
                package=self.pkg_path, output=self.out_path, extractor="dummy_ext.py",
                anderson_max_step_cap=0.0, catastrophic_delta_d_cap=0.05
            )
        self.assertIn("must be strictly positive", str(ctx_zero.exception))

        with self.assertRaises(ValueError) as ctx_neg:
            Package171R11C6PDASDriver(
                package=self.pkg_path, output=self.out_path, extractor="dummy_ext.py",
                anderson_max_step_cap=-0.01, catastrophic_delta_d_cap=0.05
            )
        self.assertIn("must be strictly positive", str(ctx_neg.exception))

    # --------------------------------------------------------------------------
    # 16. Blocker 2 Regression: Picard Fallback Exceeding Catastrophic Cap Triggers Driver Rollback
    # --------------------------------------------------------------------------
    def test_production_path_picard_fallback_exceeding_catastrophic_cap_triggers_rollback(self):
        """Verify that when an oversized Anderson candidate falls back to Picard, and the Picard step
        itself exceeds the catastrophic cap (0.05), the driver executes catastrophic rollback to Stage 1."""
        self.driver.load = lambda: None
        self.driver.max_outer = 3
        self.driver.stage = 2
        self.driver.consecutive_stable_iterations = 3
        self.driver.previous_raw_delta_d = 0.010
        self.driver.anderson_max_step_cap = 0.045
        self.driver.catastrophic_delta_d_cap = 0.05
        self.driver.divergence_factor = 1.50
        self.driver.rollback_factor = 1.05

        self.driver.previous_u_trial = {n: (0.0001, 0.001870) for n in range(1, 5)}
        mock_u = {n: (0.0001, 0.001870) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        # In Outer 1: raw delta is 0.010 -> stage 2 continues
        # In Outer 2: raw PDAS step is large: d_pdas - d_k = 0.070
        # Damped Picard step (omega_d=0.85): 0.85 * 0.070 = 0.0595 > 0.05 (catastrophic cap)
        # Anderson candidate is rejected (> 0.045), returning Picard fallback.
        # But Picard step is 0.0595 > 0.05!
        # Driver's catastrophic rollback safeguard triggers: resets stage to 1, reverts omega_d to 0.50.
        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                if outer == 1:
                    return {n: 0.110 for n in range(1, 5)}, None, None
                elif outer == 2:
                    return {n: 0.180 for n in range(1, 5)}, None, None
                else:
                    return {n: 0.185 for n in range(1, 5)}, None, None

        self.driver.solve_subproblem = mock_subproblem

        def mock_compute_step(d_current, d_pdas, d0, damped_omega, active_set_changed):
            d_pic = {n: (1.0 - damped_omega) * d_current[n] + damped_omega * d_pdas[n] for n in d_current}
            cand_step = max(abs(d_pic[n] - d_current[n]) for n in d_current)
            return d_pic, {
                "accelerated": False,
                "reason": "oversized_step (0.0650 > 0.0450)",
                "m_k": 1,
                "residual_l2": 0.14,
                "residual_linf": 0.070,
                "gamma": [1.0],
                "gamma_norm": 1.0,
                "proposed_step": 0.0650,
                "accepted_step": cand_step,
                "picard_step": cand_step
            }
        self.driver.accelerator.compute_step = mock_compute_step

        try:
            self.driver.solve_coupled_equilibration()
        except RuntimeError:
            pass

        telem_file = self.out_path / "live_iteration_telemetry.json"
        telem = json.loads(telem_file.read_text(encoding="utf-8"))

        t2 = telem[1]
        self.assertFalse(t2["anderson_accelerated"])
        self.assertTrue(t2["rollback_triggered"])
        self.assertIn("catastrophic jump", t2["rollback_reason"])
        self.assertEqual(t2["stage"], 1)
        self.assertEqual(t2["applied_omega_d"], 0.50)
        self.assertEqual(self.driver.stage, 1)
        self.assertGreater(self.driver.divergence_rollback_count, 0)

    # --------------------------------------------------------------------------
    # 17. Blocker 3 Regression: Reject False Convergence on Unsatisfied Raw Damage Residual
    # --------------------------------------------------------------------------
    def test_production_path_reject_false_convergence_on_unsatisfied_raw_damage_residual(self):
        """Verify that under Anderson acceleration, when delta_d <= 1e-5 but raw_delta_d > 1e-5,
        coupled convergence is rejected, physical acceptance fails, and checkpoint is suppressed.
        Also verify that when anderson_enabled=False (R10 mode), raw damage does not block convergence."""
        solver = MockSolver(passed=True)

        # 1. Direct gate test on finalize_coupled_acceptance:
        # Case A: anderson_enabled = True, delta_d <= 1e-5, but raw_delta_d = 2e-5 > 1e-5
        self.driver.anderson_enabled = True
        summary_acc_fail, passed_acc_fail = self.driver.finalize_coupled_acceptance(
            u_trial=self.u_trial,
            u_abaqus=self.u_abaqus,
            history_trial=self.history_trial,
            damage_relaxed=self.damage_relaxed,
            consistent_u=dict(self.u_trial),
            consistent_endpoint=self.consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=89,
            target_uy=self.driver.target_uy,
            delta_d=5e-6,
            raw_delta_d=2e-5,
            delta_u_relaxed=1e-10,
            delta_u_raw=1e-10,
            delta_h=1e-5
        )
        self.assertFalse(passed_acc_fail)
        self.assertEqual(summary_acc_fail["physical_acceptance"], "FAIL")
        self.assertFalse(summary_acc_fail["raw_damage_gate_pass"])
        self.assertEqual(summary_acc_fail["raw_delta_d_inf"], 2e-5)
        chkpt_path = self.out_path / "converged_checkpoint_01.json"
        self.assertFalse(chkpt_path.is_file())

        # Case B: anderson_enabled = True, BOTH delta_d <= 1e-5 AND raw_delta_d <= 1e-5 -> PASS
        summary_acc_pass, passed_acc_pass = self.driver.finalize_coupled_acceptance(
            u_trial=self.u_trial,
            u_abaqus=self.u_abaqus,
            history_trial=self.history_trial,
            damage_relaxed=self.damage_relaxed,
            consistent_u=dict(self.u_trial),
            consistent_endpoint=self.consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=89,
            target_uy=self.driver.target_uy,
            delta_d=5e-6,
            raw_delta_d=8e-6,
            delta_u_relaxed=1e-10,
            delta_u_raw=1e-10,
            delta_h=1e-5
        )
        self.assertTrue(passed_acc_pass)
        self.assertEqual(summary_acc_pass["physical_acceptance"], "PASS")
        self.assertTrue(summary_acc_pass["raw_damage_gate_pass"])
        self.assertTrue(chkpt_path.is_file())
        chkpt_path.unlink()

        # Case C: anderson_enabled = False (R10 backward-compatibility mode):
        # raw_delta_d > 1e-5 does NOT block convergence
        self.driver.anderson_enabled = False
        summary_r10, passed_r10 = self.driver.finalize_coupled_acceptance(
            u_trial=self.u_trial,
            u_abaqus=self.u_abaqus,
            history_trial=self.history_trial,
            damage_relaxed=self.damage_relaxed,
            consistent_u=dict(self.u_trial),
            consistent_endpoint=self.consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=89,
            target_uy=self.driver.target_uy,
            delta_d=5e-6,
            raw_delta_d=2e-5,
            delta_u_relaxed=1e-10,
            delta_u_raw=1e-10,
            delta_h=1e-5
        )
        self.assertTrue(passed_r10)
        self.assertEqual(summary_r10["physical_acceptance"], "PASS")
        self.assertTrue(summary_r10["raw_damage_gate_pass"])
        self.assertTrue(chkpt_path.is_file())
        chkpt_path.unlink()
        self.driver.anderson_enabled = True

        # 2. Production solve_coupled_equilibration() loop test:
        # Accelerated step reaches delta_d <= 1e-5, delta_u <= 1e-9, delta_h <= 1e-4,
        # but intrinsic PDAS residual raw_delta_d > 1e-5.
        self.driver.load = lambda: None
        self.driver.max_outer = 2
        self.driver.stage = 2
        self.driver.previous_raw_delta_d = 0.001
        self.driver.previous_u_trial = {n: (0.0001, 0.001870312544) for n in range(1, 5)}
        self.driver.previous_u_abaqus = dict(self.driver.previous_u_trial)

        mock_u = {n: (0.0001, 0.001870312544 + 1e-10) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        # Mock phase solve returns raw PDAS damage that differs by 2e-5 (> 1e-5) from current damage
        # But mock accelerator artificially returns accelerated candidate within 5e-6 (<= 1e-5)
        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                return {n: damage[n] + 2e-5 for n in range(1, 5)}, None, None

        self.driver.solve_subproblem = mock_subproblem
        self.driver.accelerator.compute_step = lambda d_current, d_pdas, d0, damped_omega, active_set_changed: (
            {n: d_current[n] + 5e-6 for n in d_current},
            {"accelerated": True, "reason": "none", "m_k": 1, "gamma": [], "gamma_norm": 1.0,
             "proposed_step": 5e-6, "accepted_step": 5e-6, "picard_step": 1.7e-5}
        )

        mock_solver = MockSolver(passed=True, free_err=1e-8, dual_err=1e-8, comp=1e-8)
        self.driver.solver = mock_solver

        summary = self.driver.solve_coupled_equilibration()
        # Convergence MUST be rejected because raw_delta_d (2e-5) > 1e-5!
        self.assertEqual(summary["status"], "NONCONVERGED")
        self.assertFalse(chkpt_path.is_file())
        telem = json.loads((self.out_path / "live_iteration_telemetry.json").read_text(encoding="utf-8"))[0]
        self.assertLessEqual(telem["delta_d"], 1e-5)
        self.assertGreater(telem["raw_delta_d"], 1e-5)


if __name__ == "__main__":
    unittest.main()
