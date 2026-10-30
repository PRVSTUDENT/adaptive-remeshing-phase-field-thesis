import json
from pathlib import Path
import unittest


class TestPackage149StageC12Specification(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.spec_path = self.root / 'models/pandey_kumar_mode1/149_c5_package149_stage_c1_2_spec/package149_c1_2_specification.json'

    def test_spec_exists_and_schema_valid(self):
        self.assertTrue(self.spec_path.exists(), f"Spec missing: {self.spec_path}")
        data = json.loads(self.spec_path.read_text(encoding='utf-8'))
        self.assertEqual(data.get('schema'), 1)
        self.assertEqual(data.get('stage'), 'STAGE_C1_2_SEQUENTIAL_CYCLES')
        self.assertEqual(data.get('status'), 'PROVISIONAL_SPECIFICATION_PENDING_R5_ACCEPTANCE')

    def test_displacement_intervals(self):
        data = json.loads(self.spec_path.read_text(encoding='utf-8'))
        intervals = data['displacement_intervals']
        self.assertAlmostEqual(intervals['cycle_1']['u_start_mm'], 0.0050)
        self.assertAlmostEqual(intervals['cycle_1']['u_end_mm'], 0.0055)
        self.assertAlmostEqual(intervals['cycle_2']['u_start_mm'], 0.0055)
        self.assertAlmostEqual(intervals['cycle_2']['u_end_mm'], 0.0060)

    def test_mesh_refinement_invariants(self):
        data = json.loads(self.spec_path.read_text(encoding='utf-8'))
        mesh = data['mesh_transition']
        self.assertEqual(mesh['refinement_policy'], 'REFINEMENT_ONLY_NO_COARSENING_IN_PROCESS_ZONE')
        self.assertLess(mesh['target_h_min_um'], mesh['donor_h_min_um'])

    def test_solution_card_format_matches_r5_783(self):
        data = json.loads(self.spec_path.read_text(encoding='utf-8'))
        card = data['transfer_fields']['gauss_point_history']
        self.assertIn('7+8+3', card['card_format'])
        self.assertEqual(card['mapping'], 'H_1..H_4 -> SVARS(9..12)')

    def test_physical_acceptance_tolerances(self):
        data = json.loads(self.spec_path.read_text(encoding='utf-8'))
        acc = data['acceptance_criteria']
        self.assertLessEqual(acc['reaction_force_relative_tolerance_pct'], 5.0)
        self.assertLessEqual(acc['total_energy_relative_tolerance_pct'], 2.0)
        self.assertEqual(acc['allowed_healing_nodes'], 0)
        self.assertAlmostEqual(acc['irreversibility_tolerance'], -1.0e-6)


if __name__ == '__main__':
    unittest.main()
