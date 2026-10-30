"""Regression checks for the three independent Package 148 counterexamples."""
import unittest
from types import SimpleNamespace
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    PDASReEquilibrationSolver, AbaqusPDASIterationController, StageC1GateEvaluator,
)


class RegistrationReviewCounterexamples(unittest.TestCase):
    def test_convergence_rejects_nonzero_free_residual(self):
        solver = PDASReEquilibrationSolver(
            SimpleNamespace(nodes={1: (0, 0)}, elements={}), {1: 0.2}, {})
        solver.assemble_system = lambda: ({1: 1.0}, {}, {1: 2.0})
        result = solver.run_re_equilibration()
        self.assertFalse(result['converged'])
        self.assertEqual(result['final_record']['comp_err'], 1.0)

    def test_output_update_rejects_empty_damage(self):
        with self.assertRaises(ValueError):
            AbaqusPDASIterationController('.').update_active_set_from_abaqus(
                {}, {1: 0.2}, {1})

    def test_gate_rejects_negative_damage_maximum(self):
        result = StageC1GateEvaluator().evaluate_gates(
            0.1873079389333725, 0.00021270454, 0.0, -0.5)
        self.assertFalse(result['pass_all'])


if __name__ == '__main__':
    unittest.main()
