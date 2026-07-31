import hashlib, json, pathlib, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

class StageF13Tests(unittest.TestCase):
    def setUp(self):
        self.ctl=ROOT/"models/generated/mode_ii/f13_rollback_control"
        self.force=ROOT/"models/generated/mode_ii/f13_rollback_forced_cutback"
    def test_f11_hash_freeze(self):
        m=json.loads((self.ctl/"PACKAGE_MANIFEST.json").read_text())
        self.assertEqual(m["f11_candidate_source_sha256"], "535ecd692bb4f67b0c738a854d745f339413e48f385e91823c6e0a4773addac0")
    def test_byte_identical_decks_and_sources(self):
        for f in ("M2IRR_F13.inp","M2IRR_F13.for"):
            self.assertEqual((self.ctl/f).read_bytes(),(self.force/f).read_bytes())
    def test_environment_only_distinction(self):
        a=json.loads((self.ctl/"PACKAGE_MANIFEST.json").read_text()); b=json.loads((self.force/"PACKAGE_MANIFEST.json").read_text())
        self.assertEqual(a["f13_force_cutback"],0); self.assertEqual(b["f13_force_cutback"],1)
    def test_pnewdt_only_branch(self):
        a=json.loads((self.ctl/"SOURCE_AUDIT.json").read_text()); self.assertEqual(a["permitted_branch_writes"],["PNEWDT","bounded diagnostic log"])
    def test_one_shot_threshold_and_window(self):
        s=(self.ctl/"M2IRR_F13.for").read_text(); self.assertIn("DTIME.GT.1.5D-2",s); self.assertIn("TIME(1).LT.4.0D-2",s); self.assertNotIn("SAVE",s)
    def test_explicit_absolute_log_no_fort99(self):
        s=(self.ctl/"M2IRR_F13.for").read_text(); self.assertIn("F13_ROLLBACK_LOG",s); self.assertNotIn("WRITE(99",s)
    def test_bounded_logging(self): self.assertIn("JELEM.LE.23.AND.INPT.LE.4.AND.STEPITER.LE.40",(self.ctl/"M2IRR_F13.for").read_text())
    def test_identical_physics_and_endpoint(self):
        d=(self.ctl/"M2IRR_F13.inp").read_text(); self.assertEqual(d.count("*Static\n0.02, 1.0, 1.0e-8, 0.02"),2); self.assertIn("2.0, 0.006",d)
    def test_source_remesh_limits(self):
        m=json.loads((ROOT/"models/generated/mode_ii/f13_native_miseseri_first_execution/PACKAGE_MANIFEST.json").read_text()); self.assertEqual((m["max_source_solver_executions"],m["max_adaptive_process_executions"],m["max_native_remesh_operations"],m["max_refined_mesh_solver_executions"]),(1,1,1,0))
    def test_miseseri_tuple_and_one_pass(self):
        s=(ROOT/"scripts/remeshing/execute_stage_f13_native_remesh_core.py").read_text(); self.assertIn('(str("MISESERI"),)',s); self.assertIn("model.adaptiveRemesh(odb)",s); self.assertIn("openOdb(path=odb_path, readOnly=True)",s); self.assertNotIn("AdaptivityProcess",s)
    def test_no_candidate_solver_path(self):
        s=(ROOT/"scripts/remeshing/execute_stage_f13_native_remesh_core.py").read_text(); self.assertNotIn(".submit(",s); self.assertNotIn("out_job.submit",s)
    def test_three_job_allowlist_and_parent_accounting(self):
        s=(ROOT/"scripts/hpc/stage_f/submit_stage_f13_three_job_batch.sh").read_text(); self.assertIn('["M2IRRROLLCTL1", "M2IRRROLLFORCE1", "M2RMEXEC1"]',s); self.assertIn("attempts=$((attempts+1))",s); self.assertIn('"$attempts" -le 3',s)
    def test_no_retry_replacement(self):
        s=(ROOT/"scripts/hpc/stage_f/submit_stage_f13_three_job_batch.sh").read_text(); self.assertIn('not a["retry_authorized"]',s); self.assertIn('not a["replacement_authorized"]',s)
    def test_independent_eligibility(self):
        s=(ROOT/"scripts/hpc/stage_f/submit_stage_f13_three_job_batch.sh").read_text(); self.assertEqual(s.count("if eligible"),3)

if __name__ == "__main__": unittest.main()
