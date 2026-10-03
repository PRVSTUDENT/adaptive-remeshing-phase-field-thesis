"""Unit tests for Stage 14K interim adaptive checkpoint audit."""

import json
import os
import unittest


class TestStage14KInterimCheckpoint(unittest.TestCase):
    """Test suite for Stage 14K interim evaluation artifacts and constraints."""

    def setUp(self):
        self.json_report_path = os.path.join(
            "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
            "MODE1_STAGE14K_INTERIM_ADAPTIVE_CHECKPOINT_REPORT.json"
        )
        self.md_report_path = os.path.join(
            "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
            "MODE1_STAGE14K_INTERIM_ADAPTIVE_CHECKPOINT_REPORT.md"
        )
        self.extracted_json_path = os.path.join(
            "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
            "STAGE14_INTERIM_ENERGY_EXTRACTED.json"
        )
        self.fig_dir = os.path.join("results", "figures", "mode1_gate6b")

    def test_interim_json_report_exists_and_valid(self):
        """Verify JSON report exists and parses valid JSON."""
        self.assertTrue(os.path.exists(self.json_report_path), "JSON report must exist")
        with open(self.json_report_path, "r") as f:
            data = json.load(f)
        self.assertEqual(data["audit_metadata"]["task_id"], "F1188-GATE6B-STAGE14K-INTERIM-ADAPTIVE-CHECKPOINT-20261003")
        self.assertEqual(data["audit_metadata"]["interim_verdict"], "INTERIM_ONLY__FINAL_VERDICT_PENDING_TERMINAL_COMPLETION")
        self.assertEqual(data["audit_metadata"]["active_job_id"], "1409947.mmaster02")

    def test_reached_states_boundary_constraint(self):
        """Verify that only reached states are evaluated and unreached states are excluded."""
        with open(self.json_report_path, "r") as f:
            data = json.load(f)
        reached = data["reached_displacement_states_comparison"]["reached_target_displacements_mm"]
        omitted = data["reached_displacement_states_comparison"]["omitted_unreached_target_displacements_mm"]
        
        self.assertEqual(reached, [0.0010, 0.0030, 0.0050, 0.005857, 0.0060, 0.0065, 0.0070])
        self.assertEqual(omitted, [0.0080, 0.0090, 0.0100])
        
        # Verify no record exceeds the reached boundary (0.0070 mm)
        records = data["reached_displacement_states_comparison"]["records"]
        self.assertEqual(len(records), 7)
        for r in records:
            self.assertLessEqual(r["u_target_mm"], 0.0070)

    def test_property_abi_audit_documented(self):
        """Verify the property ABI alignment audit is accurately captured."""
        with open(self.json_report_path, "r") as f:
            data = json.load(f)
        abi = data["property_abi_alignment_audit"]
        self.assertEqual(abi["subroutine_abi_order"], ["E_L0", "E_GC", "E_MOD", "E_NU", "E_K", "N_PHYS"])
        self.assertEqual(abi["adaptive_deck_job_1409947"]["status"], "ABI_PARAMETER_INVERSION_DISCOVERED")
        self.assertAlmostEqual(abi["adaptive_deck_job_1409947"]["decoded_parameters_by_f42"]["E_kN_per_mm2"], 0.0075, places=4)
        self.assertAlmostEqual(abi["adaptive_deck_job_1409947"]["decoded_parameters_by_f42"]["l0_mm"], 210.0, places=1)

    def test_figures_exist(self):
        """Verify all 4 watermarked figures exist in both PNG and PDF format."""
        fig_basenames = [
            "fig_mode1_stage14k_interim_fu_comparison",
            "fig_mode1_stage14k_interim_energy_evolution",
            "fig_mode1_stage14k_interim_property_abi_audit",
            "fig_mode1_stage14k_interim_damage_localization"
        ]
        for base in fig_basenames:
            png_path = os.path.join(self.fig_dir, base + ".png")
            pdf_path = os.path.join(self.fig_dir, base + ".pdf")
            self.assertTrue(os.path.exists(png_path), f"Figure PNG missing: {png_path}")
            self.assertTrue(os.path.exists(pdf_path), f"Figure PDF missing: {pdf_path}")
            self.assertGreater(os.path.getsize(png_path), 10000, "PNG file should not be empty")
            self.assertGreater(os.path.getsize(pdf_path), 5000, "PDF file should not be empty")


if __name__ == "__main__":
    unittest.main()
