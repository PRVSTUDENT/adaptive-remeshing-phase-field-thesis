import hashlib, json, pathlib, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

class StageF12Tests(unittest.TestCase):
    def setUp(self):
        self.ref = ROOT / "models/generated/mode_ii/f12_irreversibility_rollback_reference"
        self.cut = ROOT / "models/generated/mode_ii/f12_irreversibility_rollback_cutback"
        self.rem = ROOT / "models/generated/mode_ii/f12_native_miseseri_remesh_preparation"
    def test_f11_hash_freeze(self):
        frozen=json.loads((ROOT/"runs/hpc/stage_f/f12_rollback_qualification_and_native_remesh_preparation/FROZEN_HASHES.json").read_text())
        self.assertEqual(frozen["f11_candidate_source_sha256"], "535ecd692bb4f67b0c738a854d745f339413e48f385e91823c6e0a4773addac0")
    def test_rollback_sources_identical(self): self.assertEqual((self.ref/"M2IRR_ROLL.for").read_bytes(), (self.cut/"M2IRR_ROLL.for").read_bytes())
    def test_increment_only_diff(self):
        r=(self.ref/"M2IRR_ROLL.inp").read_text(); c=(self.cut/"M2IRR_ROLL.inp").read_text()
        self.assertEqual(r.replace("0.005, 1.0, 1.0e-8, 0.02", "CONTROL"), c.replace("1.0, 1.0, 1.0e-8, 1.0", "CONTROL"))
    def test_automatic_controls(self): self.assertNotIn("*Static, direct", (self.ref/"M2IRR_ROLL.inp").read_text())
    def test_same_endpoint(self): self.assertIn("1.0, 0.003, 1.5, 0.001, 2.0, 0.006", (self.cut/"M2IRR_ROLL.inp").read_text())
    def test_bounded_log(self):
        s=(self.cut/"M2IRR_ROLL.for").read_text(); self.assertIn("JELEM.LE.2.AND.INPT.LE.2.AND.STEPITER.LE.40", s)
    def test_log_has_lflags_and_svars(self):
        s=(self.cut/"M2IRR_ROLL.for").read_text(); self.assertIn("LFLAGS(1),LFLAGS(3),LFLAGS(4)", s); self.assertIn("SVARS(NSTVTO*(INPT-1)+1)", s)
    def test_analyzer_classifications(self):
        s=(ROOT/"scripts/validation/analyze_stage_f12_rollback.py").read_text(); self.assertIn("penalty_rollback_not_exercised", s); self.assertIn("phase_not_restored", s)
    def test_no_retry_contract(self): self.assertIn('not a["retry_authorized"]', (ROOT/"scripts/hpc/stage_f/submit_stage_f12_three_job_batch.sh").read_text())
    def test_three_job_allowlist(self): self.assertIn('["M2IRRROLLREF", "M2IRRROLLCUT", "M2RMPREP1"]', (ROOT/"scripts/hpc/stage_f/submit_stage_f12_three_job_batch.sh").read_text())
    def test_parent_counters(self): self.assertIn("attempts=$((attempts+1))", (ROOT/"scripts/hpc/stage_f/submit_stage_f12_three_job_batch.sh").read_text())
    def test_runtime_root_no_file(self):
        s=(ROOT/"scripts/remeshing/prepare_stage_f12_native_remesh.py").read_text(); self.assertIn("F12_RUNTIME_DIR", s); self.assertNotIn("__file__", s)
    def test_python2_str_tuple(self): self.assertIn('(str("MISESERI"),)', (ROOT/"scripts/remeshing/prepare_stage_f12_native_remesh_core.py").read_text())
    def test_real_model_rule(self):
        s=(ROOT/"scripts/remeshing/prepare_stage_f12_native_remesh_core.py").read_text(); self.assertIn("ModelFromInputFile", s); self.assertIn("region=MODEL", s)
    def test_zero_execution_paths(self):
        s=(ROOT/"scripts/remeshing/prepare_stage_f12_native_remesh_core.py").read_text(); self.assertNotIn("submit(", s); self.assertNotIn("waitForCompletion", s)
    def test_official_hashes(self):
        m=json.loads((self.rem/"PACKAGE_MANIFEST.json").read_text()); self.assertEqual(m["source_deck_sha256"], "a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2")
    def test_true_slit(self): self.assertEqual(json.loads((self.rem/"PACKAGE_MANIFEST.json").read_text())["true_slit_coincident_pairs"], 15)
    def test_h1_preparation_only(self):
        for name in ("f12_h1_instrumented_baseline_prepared", "f12_h1_instrumented_candidate_prepared"):
            m=json.loads((ROOT/"models/generated/mode_ii"/name/"PACKAGE_MANIFEST.json").read_text()); self.assertEqual(m["status"], "prepared_not_authorized"); self.assertFalse(m["submission_authorized"])
    def test_h1_population(self): self.assertEqual(json.loads((ROOT/"models/generated/mode_ii/f12_h1_instrumented_candidate_prepared/PACKAGE_MANIFEST.json").read_text())["n_elem"], 12064)
    def test_h1_bounds_guards(self): self.assertIn("F12 H1 BOUNDS UMAT", (ROOT/"models/generated/mode_ii/f12_h1_instrumented_candidate_prepared/m2h1_u020.for").read_text())

if __name__ == "__main__": unittest.main()
