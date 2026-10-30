"""Counterexamples recorded during independent Package 148 registration review.

These tests document current defects; they do not qualify production execution.
"""
import unittest
from types import SimpleNamespace
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    PDASReEquilibrationSolver, AbaqusPDASIterationController, StageC1GateEvaluator,
)


class RegistrationReviewCounterexamples(unittest.TestCase):
    def test_current_convergence_accepts_nonzero_free_residual(self):
        solver = PDASReEquilibrationSolver(
            SimpleNamespace(nodes={1: (0, 0)}, elements={}), {1: 0.2}, {})
        solver.assemble_system = lambda: ({1: 1.0}, {}, {1: 2.0})
        result = solver.run_re_equilibration()
        self.assertTrue(result['converged'])
        self.assertEqual(result['final_record']['comp_err'], 1.0)

    def test_current_output_update_accepts_empty_damage(self):
        result = AbaqusPDASIterationController('.').update_active_set_from_abaqus(
            {}, {1: 0.2}, {1})
        self.assertTrue(result['no_healing'])
        self.assertEqual(result['active_flips'], 0)

    def test_current_gate_accepts_negative_damage_maximum(self):
        result = StageC1GateEvaluator().evaluate_gates(
            0.1873079389333725, 0.00021270454, 0.0, -0.5)
        self.assertTrue(result['pass_all'])


if __name__ == '__main__':
    unittest.main()
