"""Offline, authentic-artifact regressions for ONE serializer correction hypothesis."""
import json
from pathlib import Path
import unittest

import numpy as np
from scipy.sparse import eye

from scripts.validation.diagnose_package148_r4_kkt import (
    solution_cards, fixed_field_decode, kkt_metrics, counterfactual_pdas,
)

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'results/validation/package148_r4_kkt'


class StateCardDiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name in ('reconstruction.json','state_card_fixture.json'):
            if not (DATA/name).is_file():
                raise RuntimeError('Missing independently reconstructed evidence '+name)
        cls.result=json.loads((DATA/'reconstruction.json').read_text())
        cls.cases=json.loads((DATA/'state_card_fixture.json').read_text())['elements']

    def test_all_eighteen_distinct_sentinels_round_trip(self):
        state=list(range(1,19))
        text=solution_cards(91,state)
        self.assertEqual([len(line.split(',')) for line in text.splitlines()],[8,8,3])
        eid,decoded=fixed_field_decode(text)
        self.assertEqual(eid,91)
        self.assertEqual(decoded,state)

    def test_real_legacy_first_line_overflow_is_rejected(self):
        for case in self.cases:
            with self.subTest(element=case['element']), self.assertRaises(ValueError):
                fixed_field_decode(case['original_card'])

    def test_real_bad_card_shifts_history_and_drops_fourth_slot(self):
        for case in self.cases:
            _,decoded=fixed_field_decode(case['original_card'],strict=False)
            self.assertEqual(decoded,case['decoded'])
            h=case['intended'][8:12]
            self.assertEqual(decoded[8:12],h[1:]+[0.])

    def test_real_corrected_cards_preserve_every_state_and_gp_order(self):
        for case in self.cases:
            _,decoded=fixed_field_decode(solution_cards(case['element'],case['intended']))
            self.assertEqual(decoded,case['intended'])
            self.assertEqual(decoded[8:12],case['intended'][8:12])

    def test_bad_card_predicts_authentic_odb_history(self):
        for case in self.cases:
            predicted=[float(np.float32(max(h,p))) for h,p in zip(case['decoded'][8:12],case['mechanical_psi'])]
            self.assertEqual(predicted,case['observed_history'])
        self.assertEqual(self.result['observed_history_audit']['shift_prediction_float32_exact_count'],28224)

    def test_all_twenty_linear_solves_match_shifted_operator_not_intended_one(self):
        rows=self.result['iterations']
        self.assertEqual([r['iteration'] for r in rows],list(range(1,21)))
        self.assertTrue(all(r['shifted_operator_bc_free_error']<2e-12 for r in rows))
        self.assertTrue(all(r['bc_free_error']>1e-8 for r in rows))
        self.assertTrue(all(not r['passed'] for r in rows))
        self.assertTrue(all(r['prediction_matches_used'] for r in rows[1:]))

    def test_free_residual_alone_would_falsely_accept_healing(self):
        for r in self.result['iterations']:
            self.assertLess(r['free_error'],1e-6)
            self.assertLess(r['complementarity'],1e-6)
            self.assertGreater(r['primal_violations'],0)
            self.assertGreater(r['dual_violations'],0)
            self.assertFalse(r['passed'])

    def test_oscillation_does_not_approach_damage_tolerance(self):
        rows=self.result['iterations']
        self.assertTrue(all(abs(r['damage_change_inf']-.0350491)<1e-10 for r in rows))
        self.assertLess(rows[0]['min_gap'],-.035)
        self.assertGreater(rows[-1]['next_membership_change'],3000)

    def test_correct_operator_replay_converges_with_unchanged_tolerances(self):
        for name in ('high_precision','dat_eight_significant_digits'):
            replay=self.result['serializer_only_counterfactual'][name]
            self.assertTrue(replay['converged'])
            self.assertEqual(len(replay['iterations']),8)
            last=replay['iterations'][-1]
            self.assertLessEqual(last['dual_error'],1e-9)
            self.assertLessEqual(last['free_error'],1e-6)
            self.assertGreaterEqual(last['min_gap'],-1e-6)

    def test_kkt_sign_and_obstacle_on_known_convex_quadratic(self):
        matrix=eye(2,format='csr')
        baseline=np.array([.4,.1]); force=np.array([.2,.5])
        # Exact minimizer: first node constrained with positive multiplier;
        # second is free. No damage clipping is used by the replay.
        replay=counterfactual_pdas(matrix,force,baseline,baseline)
        np.testing.assert_allclose(replay['damage'],[.4,.5],atol=1e-15)
        self.assertTrue(replay['converged'])
        metrics,_,_,_=kkt_metrics(matrix,np.array([.6,.5]),baseline,baseline,np.array([True,True]))
        self.assertGreater(metrics['dual_error'],0)
        self.assertFalse(metrics['passed'])

    def test_invalid_state_vectors_fail_closed(self):
        for state in ([0.]*17,[0.]*19,[float('nan')]*18,[float('inf')]*18):
            with self.assertRaises(ValueError):solution_cards(1,state)


if __name__=='__main__':
    unittest.main()
