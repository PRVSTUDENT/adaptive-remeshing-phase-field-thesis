import os, json, hashlib, unittest

REPO_DIR = r"D:\Master thesis\Adaptive remeshing"

class TestMode1F1581Package55And56(unittest.TestCase):

    def test_01_production_and_experimental_uel_hashes(self):
        prod_uel = os.path.join(REPO_DIR, "models", "pandey_kumar_mode1", "15_energy_qualification_small", "f42_mixed_uel.for")
        with open(prod_uel, "rb") as f:
            h_prod = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(h_prod.lower(), "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6")

        exp_uel = os.path.join(REPO_DIR, "models", "pandey_kumar_mode1", "experimental_offset_uel", "f42_experimental_offset_uel.for")
        with open(exp_uel, "rb") as f:
            h_exp = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(h_exp.lower(), "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d")

    def test_02_package55_continuous_reference_metrics(self):
        eval_path = os.path.join(REPO_DIR, "models", "pandey_kumar_mode1", "55_continuous_650_element_forward_reference", "evidence_1415067", "JOB_1415067_EVALUATION.json")
        self.assertTrue(os.path.exists(eval_path))
        with open(eval_path, "r") as f:
            data = json.load(f)
        self.assertEqual(data["exit_code"], 0)
        self.assertEqual(data["pbs_job_id"], "1415067.mmaster02")
        self.assertEqual(data["mesh_properties"]["elements"], 650)
        self.assertEqual(data["mesh_properties"]["nodes"], 713)
        self.assertEqual(data["increments"]["total_increments"], 72)
        self.assertAlmostEqual(data["checkpoints"]["checkpoint_u00270"]["u_mm"], 0.00270, places=5)
        self.assertAlmostEqual(data["checkpoints"]["endpoint_u00290"]["u_mm"], 0.00290, places=5)

    def test_03_package56_samemesh_reconstruction_metrics(self):
        eval_path = os.path.join(REPO_DIR, "models", "pandey_kumar_mode1", "56_method_c_samemesh_reconstruction", "evidence_1415069", "JOB_1415069_EVALUATION.json")
        self.assertTrue(os.path.exists(eval_path))
        with open(eval_path, "r") as f:
            data = json.load(f)
        self.assertEqual(data["exit_code"], 0)
        self.assertEqual(data["pbs_job_id"], "1415069.mmaster02")
        self.assertEqual(data["reconstruction_parity_u00270"]["step1_iterations"], 2)
        self.assertEqual(data["reconstruction_parity_u00270"]["step1_cutbacks"], 0)
        self.assertEqual(data["continuation_parity_u00290"]["step2_cutbacks"], 0)

    def test_04_forward_continuation_exact_parity(self):
        eval_path = os.path.join(REPO_DIR, "models", "pandey_kumar_mode1", "56_method_c_samemesh_reconstruction", "evidence_1415069", "JOB_1415069_EVALUATION.json")
        with open(eval_path, "r") as f:
            data = json.load(f)
        cont = data["continuation_parity_u00290"]
        # Exact parity at u = 0.00290 mm
        self.assertAlmostEqual(cont["reference_rf2_n"], cont["continued_rf2_n"], places=3)
        self.assertAlmostEqual(cont["reference_e_frac_knmm"], cont["continued_e_frac_knmm"], places=7)
        self.assertAlmostEqual(cont["reference_e_tot_knmm"], cont["continued_e_tot_knmm"], places=7)
        self.assertLess(abs(cont["delta_rf2_pct"]), 0.01)
        self.assertLess(abs(cont["delta_e_tot_pct"]), 0.01)

    def test_05_irreversibility_healing_resolved_on_same_mesh(self):
        eval_path = os.path.join(REPO_DIR, "models", "pandey_kumar_mode1", "56_method_c_samemesh_reconstruction", "evidence_1415069", "JOB_1415069_EVALUATION.json")
        with open(eval_path, "r") as f:
            data = json.load(f)
        recon = data["reconstruction_parity_u00270"]
        # In Package 53 min delta_d was -0.0810. In Package 56 it is -0.00012
        self.assertGreater(recon["min_delta_d"], -0.001)
        # Total energy preserved within 0.05%
        self.assertLess(abs(recon["delta_e_tot_pct"]), 0.05)
        # Fracture energy preserved within 0.10%
        self.assertLess(abs(recon["delta_e_frac_pct"]), 0.10)

if __name__ == "__main__":
    unittest.main()
