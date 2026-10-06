#!/usr/bin/env python3
"""
Unit Test Suite for Gate-6B Stage 14U-AL:
Automated Evaluator Freeze, Decision Protocols, and 8-Thread Twin Package Template
----------------------------------------------------------------------------------
Tests:
1. Evaluator A (evaluate_stage14ual_4thread_determinism.py) parsing, metrics, schemas, and verdicts.
2. Evaluator B (evaluate_stage14ual_temporal_refinement.py) parsing, metrics, schemas, and decision branches.
3. Full-range determinism protocol JSON and Markdown integrity.
4. 2x temporal refinement decision protocol JSON and Markdown integrity.
5. Package 29 (8-thread Stage-A twin template) files, hashes, PBS directives, and hold status.
6. Epistemic and causal governance discipline (determinism vs compliance, governed terms).
"""

import os
import sys
import json
import hashlib
import unittest
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class TestStage14UALEvaluatorsAndProtocols(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.stage_b_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "27_stage14_adaptive_candidate_14k_4thread_stage_b")
        cls.temporal_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "26_stage14_temporal_refined_candidate_2x")
        cls.stage_a_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "26_stage14_adaptive_candidate_14k_4thread")
        cls.serial_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k")
        cls.pkg29_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "29_stage14_adaptive_candidate_14k_8thread")
        
        # Load evaluators
        eval_a_path = os.path.join(cls.stage_b_dir, "evaluate_stage14ual_4thread_determinism.py")
        cls.eval_a = load_module_from_path("eval_a", eval_a_path)
        
        eval_b_path = os.path.join(cls.temporal_dir, "evaluate_stage14ual_temporal_refinement.py")
        cls.eval_b = load_module_from_path("eval_b", eval_b_path)
        
    def test_evaluator_a_module_and_functionality(self):
        """Test Evaluator A parsing, stiffness regression, matched states, and report generation."""
        # Test synthetic parsing and K0 calculation
        records = [
            {'step': 1, 'inc': i, 'u2_mm': 0.0000025 * i, 'rf2_kn': 137.909558 * (0.0000025 * i)}
            for i in range(1, 401)
        ]
        k0, intercept, r2, n = self.eval_a.compute_k0(records, max_u=0.0010)
        self.assertIsNotNone(k0)
        self.assertAlmostEqual(k0, 137.909558, places=4)
        self.assertAlmostEqual(intercept, 0.0, places=6)
        self.assertAlmostEqual(r2, 1.0, places=6)
        self.assertEqual(n, 400)
        
        # Test matched state extraction
        matched = self.eval_a.find_matched_state(records, [], 0.001000)
        self.assertEqual(matched['status'], 'REACHED')
        self.assertAlmostEqual(matched['actual_u_mm'], 0.001000, places=6)
        
        # Test unreached state
        unreached = self.eval_a.find_matched_state(records, [], 0.005000)
        self.assertEqual(unreached['status'], 'NOT_REACHED')
        self.assertIsNone(unreached['actual_u_mm'])
        
        # Test full report generation on existing test directories
        report = self.eval_a.evaluate_determinism(self.stage_b_dir, self.stage_a_dir, self.serial_dir)
        self.assertIn('task_id', report)
        self.assertIn('verdict', report)
        self.assertIn('epistemic_boundary', report)
        self.assertTrue(report['epistemic_boundary']['conflation_prevented'])
        self.assertEqual(len(report['predeclared_matched_states']), 9)
        
        # Test markdown generation
        md_text = self.eval_a.generate_markdown(report)
        self.assertIn("Mode-I Gate-6B Stage 14U-AL", md_text)
        self.assertIn("Canonical Structural Stiffness", md_text)
        
    def test_evaluator_b_module_and_functionality(self):
        """Test Evaluator B parsing, decision branch evaluation, and report generation."""
        # Test synthetic parsing and K0 calculation
        records = [
            {'step': 1, 'inc': i, 'u2_mm': 0.00000125 * i, 'rf2_kn': 137.909558 * (0.00000125 * i)}
            for i in range(1, 801)
        ]
        k0, intercept, r2, n = self.eval_b.compute_k0(records, max_u=0.0010)
        self.assertIsNotNone(k0)
        self.assertAlmostEqual(k0, 137.909558, places=4)
        self.assertEqual(n, 800)
        
        # Test evaluation report
        report = self.eval_b.evaluate_temporal_refinement(self.temporal_dir, self.serial_dir)
        self.assertIn('task_id', report)
        self.assertIn('decision_branch', report)
        self.assertIn('action_directive', report)
        self.assertIn('epistemic_governance', report)
        self.assertEqual(report['epistemic_governance']['convergence_mechanism'], 'POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED')
        self.assertEqual(report['epistemic_governance']['ill_conditioning_status'], 'NOT_ESTABLISHED')
        self.assertEqual(report['epistemic_governance']['crack_functional_terminology'], 'IMPLEMENTED_PHASE_FIELD_CRACK_SURFACE_FRACTURE_FUNCTIONAL_E_FRAC')
        
        # Test markdown generation
        md_text = self.eval_b.generate_markdown(report)
        self.assertIn("2x Temporal Refinement Evaluation Report", md_text)
        self.assertIn("Package 28 ($C_n = 0.50$) Submission Status", md_text)
        
    def test_determinism_protocol_documents(self):
        """Verify STAGE14UAL_FULL_RANGE_DETERMINISM_PROTOCOL.json and .md integrity."""
        json_path = os.path.join(self.stage_b_dir, "STAGE14UAL_FULL_RANGE_DETERMINISM_PROTOCOL.json")
        md_path = os.path.join(self.stage_b_dir, "STAGE14UAL_FULL_RANGE_DETERMINISM_PROTOCOL.md")
        
        self.assertTrue(os.path.exists(json_path), "Determinism protocol JSON must exist")
        self.assertTrue(os.path.exists(md_path), "Determinism protocol MD must exist")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        self.assertEqual(data['protocol_version'], 2)
        self.assertEqual(data['evaluated_jobs']['stage_b_repeat'], "1410029.mmaster02")
        self.assertEqual(data['evaluated_jobs']['stage_a_benchmark'], "1410006.mmaster02")
        self.assertEqual(data['evaluated_jobs']['serial_reference'], "1409982.mmaster02")
        self.assertEqual(len(data['predeclared_matched_displacements_mm']), 9)
        self.assertIn("THREAD_PARITY_PASS + THREAD_DETERMINISM_PASS + THREAD_PARALLELIZATION_QUALIFIED_4T", data['verdict_hierarchy']['pass_verdict'])
        self.assertEqual(data['downstream_gating']['package_29_8thread_twin'], "SUBMISSION_AND_DATACHECK_HELD_PENDING_STAGE_B_TERMINAL_PASS")
        
        with open(md_path, 'r') as f:
            content = f.read()
        self.assertIn("Stage-A vs Stage-B Determinism Evaluation", content)
        self.assertIn("Adaptive Candidate vs Fixed Reference Evaluation", content)
        self.assertIn("Terminal Attempt Sequence Comparison Schema", content)
        
    def test_temporal_decision_protocol_documents(self):
        """Verify STAGE14UAL_TEMPORAL_DECISION_PROTOCOL.json and .md integrity."""
        json_path = os.path.join(self.temporal_dir, "STAGE14UAL_TEMPORAL_DECISION_PROTOCOL.json")
        md_path = os.path.join(self.temporal_dir, "STAGE14UAL_TEMPORAL_DECISION_PROTOCOL.md")
        
        self.assertTrue(os.path.exists(json_path), "Temporal protocol JSON must exist")
        self.assertTrue(os.path.exists(md_path), "Temporal protocol MD must exist")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        self.assertEqual(data['protocol_version'], 2)
        self.assertEqual(data['evaluated_job'], "1410027.mmaster02")
        self.assertEqual(data['baseline_reference_job'], "1409982.mmaster02")
        self.assertIn("branch_1", data['predeclared_decision_branches_at_u007889'])
        self.assertIn("branch_2", data['predeclared_decision_branches_at_u007889'])
        self.assertIn("branch_3", data['predeclared_decision_branches_at_u007889'])
        self.assertEqual(data['package_28_gating']['submission_status'], "STRICTLY_HELD_PENDING_TEMPORAL_DECISION_BRANCH_EVALUATION")
        
        with open(md_path, 'r') as f:
            content = f.read()
        self.assertIn("Branch 1: `TEMPORAL_REFINEMENT_CROSSES_BASELINE_FAILURE`", content)
        self.assertIn("Branch 2: `TEMPORAL_REFINEMENT_REFAILS_SAME_MECHANISM`", content)
        self.assertIn("Branch 3: `TEMPORAL_REFINEMENT_CHANGES_FAILURE_PATH`", content)
        
    def test_package_29_8thread_twin_template(self):
        """Verify Package 29 files, SHA-256 hashes, PBS directives, and hold status."""
        inp_path = os.path.join(self.pkg29_dir, "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp")
        for_path = os.path.join(self.pkg29_dir, "f42_mixed_uel.for")
        pbs_path = os.path.join(self.pkg29_dir, "submit_solver.pbs")
        dc_path = os.path.join(self.pkg29_dir, "submit_datacheck.pbs")
        manifest_path = os.path.join(self.pkg29_dir, "PACKAGE_MANIFEST.json")
        card_path = os.path.join(self.pkg29_dir, "PRE_JOB_ANTI_DEVIATION_CARD.md")
        
        self.assertTrue(os.path.exists(inp_path))
        self.assertTrue(os.path.exists(for_path))
        self.assertTrue(os.path.exists(pbs_path))
        self.assertTrue(os.path.exists(dc_path))
        self.assertTrue(os.path.exists(manifest_path))
        self.assertTrue(os.path.exists(card_path))
        
        # Verify SHA-256 hashes
        with open(inp_path, 'rb') as f:
            inp_hash = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(inp_hash, "26D873FB2E68055C80550D1DD981766BCAF46E13D3D0A7BA6411B63D9C382D35")
        
        with open(for_path, 'rb') as f:
            for_hash = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(for_hash, "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6")
        
        # Verify PBS script threading directives
        with open(pbs_path, 'r') as f:
            pbs_text = f.read()
        self.assertTrue("#PBS -l nodes=1:ppn=8" in pbs_text or "#PBS -l select=1:ncpus=8" in pbs_text)
        self.assertIn("cpus=8 mp_mode=threads", pbs_text)
        self.assertIn("job_notifications.sh", pbs_text)
        
        # Verify manifest gating
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        self.assertEqual(manifest['status'], "8THREAD_STAGEA_TWIN_TEMPLATE_PREPARED__SUBMISSION_AND_DATACHECK_HELD_PENDING_STAGEB_DETERMINISM")
        self.assertFalse(manifest['gating_rules']['datacheck_authorized'])
        self.assertFalse(manifest['gating_rules']['submission_authorized'])
        
    def test_epistemic_and_causal_governance(self):
        """Verify strict epistemic terminology and causal decoupling across all artifacts."""
        # Check that determinism protocol clearly separates determinism vs fixed reference compliance
        json_path = os.path.join(self.stage_b_dir, "STAGE14UAL_FULL_RANGE_DETERMINISM_PROTOCOL.json")
        with open(json_path, 'r') as f:
            det_proto = json.load(f)
        self.assertEqual(det_proto['epistemic_and_causal_boundaries']['determinism_scope'], "STRICTLY_BETWEEN_STAGE_A_AND_STAGE_B_REPEATS_ACROSS_DISTINCT_ALLOCATIONS")
        self.assertEqual(det_proto['epistemic_and_causal_boundaries']['compliance_scope'], "COMPARISON_AGAINST_FIXED_REFERENCE_MEASURES_REPRESENTATION_FIDELITY")
        
        # Check that temporal protocol enforces governed terms
        temporal_json = os.path.join(self.temporal_dir, "STAGE14UAL_TEMPORAL_DECISION_PROTOCOL.json")
        with open(temporal_json, 'r') as f:
            temp_proto = json.load(f)
        self.assertEqual(temp_proto['epistemic_and_causal_governance']['convergence_mechanism'], "POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED")
        self.assertEqual(temp_proto['epistemic_and_causal_governance']['ill_conditioning_status'], "NOT_ESTABLISHED")
        self.assertEqual(temp_proto['epistemic_and_causal_governance']['crack_functional_terminology'], "IMPLEMENTED_PHASE_FIELD_CRACK_SURFACE_FRACTURE_FUNCTIONAL_E_FRAC")

if __name__ == "__main__":
    unittest.main()
