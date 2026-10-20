"""Manufactured numerical checks only; authentic investigation is not run here."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts/validation'))
import probe_mode1_f1597_mechanical_history as probe


class MechanicalHistoryTests(unittest.TestCase):
    def setUp(self):
        self.xy = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])
        self.props = [.1, .2, 210., .3, 1e-7, 1]
        self.d = np.zeros(4)

    def test_rigid_motion_and_tangent_symmetry(self):
        k, force, h = probe.mechanical_element(self.xy, np.tile([.1, -.2], 4), self.d, self.props)
        np.testing.assert_allclose(force, 0, atol=1e-13)
        np.testing.assert_allclose(h, 0, atol=1e-28)
        np.testing.assert_allclose(k, k.T, atol=1e-13)

    def test_affine_tension_matches_analytic_force_and_energy(self):
        strain = .001
        u = np.array([0, 0, strain, 0, strain, 0, 0, 0])
        _, f, driving = probe.mechanical_element(self.xy, u, self.d, self.props)
        lam = 210*.3/(1.3*.4); mu = 210/2.6
        sx = (lam+2*mu)*strain*(1+1e-7); sy = lam*strain*(1+1e-7)
        np.testing.assert_allclose(f, np.array([-sx,-sy,sx,-sy,sx,sy,-sx,sy])/2, atol=1e-13)
        np.testing.assert_allclose(driving, (.5*lam+mu)*strain**2, atol=1e-16)

    def test_transaction_preserves_committed_and_restores_on_retry(self):
        h = np.array([1., 2., 3., 4.]); driving = np.array([2., 1., 5., 0.])
        trial, committed, accepted, retry = probe.history_transaction(h, driving)
        np.testing.assert_array_equal(trial, [2, 2, 5, 4])
        np.testing.assert_array_equal(committed, h)
        np.testing.assert_array_equal(accepted, trial)
        np.testing.assert_array_equal(retry, h)
        # Iterative trial max retains overshoot until a retry restores committed.
        np.testing.assert_array_equal(probe.history_transaction(trial, np.zeros(4))[0], trial)

    def test_history_update_changes_phase_order_without_replaying_kkt(self):
        nodes = {i+1: xy for i, xy in enumerate(self.xy)}
        u = np.array([0, 0, .01, 0, .01, 0, 0, 0])
        offsets = {1: np.r_[u, np.zeros(4), np.zeros(4)]}
        with patch('probe_mode1_f1597_kkt.probe', side_effect=AssertionError('retired operation')):
            m, discrepancy = probe.analyze(nodes, {1: [1,2,3,4]}, offsets, self.props, {(1,1),(1,2)})
        self.assertGreater(m['history_increase_inf_kN_mm2'], 0)
        self.assertGreater(m['phase_call_order_delta_inf_kN'], 0)
        self.assertEqual(discrepancy['classification'], 'HISTORY_UPDATE_AT_MAPPED_STATE')
        self.assertLess(m['mechanical_fd_relative_error'], 1e-7)

    def test_inverted_jacobian_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Jacobian'):
            probe.mechanical_element(self.xy[::-1], np.zeros(8), self.d, self.props)

    def test_high_history_is_preserved(self):
        _, _, driving = probe.mechanical_element(self.xy, np.zeros(8), self.d, self.props)
        np.testing.assert_array_equal(probe.history_transaction(np.ones(4), driving)[0], np.ones(4))


if __name__ == '__main__':
    unittest.main()
