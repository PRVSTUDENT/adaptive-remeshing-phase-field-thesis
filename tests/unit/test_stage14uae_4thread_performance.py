import unittest
import os
import json
import hashlib

class TestStage14UAE4ThreadPerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Locate repo root
        cur = os.path.abspath(os.path.dirname(__file__))
        while cur and not os.path.exists(os.path.join(cur, "project_coordination")):
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
        cls.repo_root = cur
        cls.pkg26_dir = os.path.join(cls.repo_root, "models", "pandey_kumar_mode1", "26_stage14_adaptive_candidate_14k_4thread")
        cls.pkg27_dir = os.path.join(cls.repo_root, "models", "pandey_kumar_mode1", "27_stage14_adaptive_candidate_14k_4thread_stage_b")
        cls.report_json_path = os.path.join(cls.pkg26_dir, "MODE1_STAGE14UAE_4THREAD_PERFORMANCE_REPORT.json")
        
        if os.path.exists(cls.report_json_path):
            with open(cls.report_json_path, "r", encoding="utf-8") as f:
                cls.report = json.load(f)
        else:
            cls.report = {}

    def test_01_report_existence_and_verdicts(self):
        self.assertTrue(os.path.exists(self.report_json_path), f"Missing report: {self.report_json_path}")
        self.assertEqual(self.report.get("governing_performance_verdict"), "PERFORMANCE_COMPARISON_CONTENDED__DESCRIPTIVE_ONLY")
        self.assertEqual(self.report.get("numerical_parity_verdict"), "THREAD_PARITY_PASS_OVER_REACHED_RANGE")

    def test_02_node_placement_and_contention(self):
        node_info = self.report.get("node_placement", {})
        self.assertTrue(node_info.get("co_located_on_mnode097", False))
        self.assertIn("mnode097", node_info.get("serial_exec_host", ""))
        self.assertIn("mnode097", node_info.get("thread4_exec_host", ""))

    def test_03_speedup_and_throughput_scaling(self):
        speedup_info = self.report.get("speedup_metrics", {})
        s_sec = speedup_info.get("serial_sec_per_inc", 0.0)
        t_sec = speedup_info.get("thread4_sec_per_inc", 0.0)
        s4 = speedup_info.get("speedup_S4", 0.0)
        e4 = speedup_info.get("parallel_efficiency_E4", 0.0)
        
        self.assertAlmostEqual(s_sec, 3.521, delta=0.01)
        self.assertAlmostEqual(t_sec, 1.524, delta=0.05)
        self.assertGreater(s4, 2.20)
        self.assertLess(s4, 2.45)
        self.assertAlmostEqual(s4, 2.31, delta=0.10)
        self.assertAlmostEqual(e4, 0.5776, delta=0.03)

    def test_04_stage_b_manifest_and_invariances(self):
        manifest_path = os.path.join(self.pkg27_dir, "MANIFEST.json")
        self.assertTrue(os.path.exists(manifest_path), f"Missing Stage B manifest: {manifest_path}")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        self.assertEqual(manifest.get("qualification_status"), "4THREAD_STAGEB_REPEAT_VALIDATED__WAITING_FOR_STAGEA_TERMINAL_PASS")
        self.assertEqual(manifest.get("num_cpus"), 4)
        self.assertEqual(manifest.get("intended_execution_mode"), "SHARED_MEMORY_THREADS")
        
        # Verify deck and Fortran hashes in package 27
        deck_path = os.path.join(self.pkg27_dir, "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp")
        fortran_path = os.path.join(self.pkg27_dir, "f42_mixed_uel.for")
        
        with open(deck_path, "rb") as f:
            deck_hash = hashlib.sha256(f.read()).hexdigest().lower()
        with open(fortran_path, "rb") as f:
            fortran_hash = hashlib.sha256(f.read()).hexdigest().lower()
            
        self.assertEqual(deck_hash, "26d873fb2e68055c80550d1dd981766bcaf46e13d3d0a7ba6411b63d9c382d35")
        self.assertEqual(fortran_hash, "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6")

    def test_05_active_jobs_progress_sanity(self):
        s_job = self.report.get("serial_1cpu_reference", {})
        t_job = self.report.get("thread4_candidate", {})
        
        self.assertEqual(s_job.get("job_id"), "1409982.mmaster02")
        self.assertEqual(t_job.get("job_id"), "1410006.mmaster02")
        self.assertGreaterEqual(s_job.get("current_step", 0), 2)
        self.assertGreaterEqual(t_job.get("current_step", 0), 1)

    def test_06_publication_figures_exist(self):
        fig_pdf = os.path.join(self.repo_root, "results", "figures", "mode1_gate6b", "fig_mode1_stage14uae_4thread_performance.pdf")
        fig_png = os.path.join(self.repo_root, "results", "figures", "mode1_gate6b", "fig_mode1_stage14uae_4thread_performance.png")
        self.assertTrue(os.path.exists(fig_pdf), f"Missing figure PDF: {fig_pdf}")
        self.assertTrue(os.path.exists(fig_png), f"Missing figure PNG: {fig_png}")

if __name__ == '__main__':
    unittest.main()
