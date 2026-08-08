import os
import sys
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge")
MANIFEST_PATH = os.path.join(PACKAGE_DIR, "F43REM3_NATIVE_MANIFEST.json")
WRAPPER_PATH = os.path.join(PACKAGE_DIR, "submit_f43rem3_native.sh")
PBS_PATH = os.path.join(PACKAGE_DIR, "F43REM3_NATIVE.pbs")
VALIDATOR_PATH = os.path.join(PACKAGE_DIR, "validate_f43rem3_native.py")
CRITERIA_PATH = os.path.join(PACKAGE_DIR, "F43REM3_ACCEPTANCE_CRITERIA.json")
DRIVER_PATH = os.path.join(PACKAGE_DIR, "remesh_mode_ii_native_cae.py")
CONFIG_PATH = os.path.join(PACKAGE_DIR, "f43_remeshing_rule_config.json")
SCI_COMP_PATH = os.path.join(PACKAGE_DIR, "evidence", "1385461.mmaster02", "F43PRE3_SCIENTIFIC_COMPARISON.json")

class TestStageF43REM3Native(unittest.TestCase):

    def setUp(self):
        with open(MANIFEST_PATH, "r") as f:
            self.manifest = json.load(f)
        with open(PBS_PATH, "r") as f:
            self.pbs = f.read()
        with open(WRAPPER_PATH, "r") as f:
            self.wrapper = f.read()
        with open(CRITERIA_PATH, "r") as f:
            self.criteria = json.load(f)
        with open(DRIVER_PATH, "r") as f:
            self.driver = f.read()
        with open(CONFIG_PATH, "r") as f:
            self.config = json.load(f)
        with open(SCI_COMP_PATH, "r") as f:
            self.sci_comp = json.load(f)

    def test_A_manifest_and_acceptance_criteria_hashes(self):
        self.assertEqual(self.manifest["source_cae_sha256"], "0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa")
        self.assertEqual(self.manifest["predecessor_odb_sha256"], "9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1")
        self.assertEqual(self.manifest["predecessor_odb_job_id"], "1385461.mmaster02")
        self.assertNotEqual(self.manifest["predecessor_odb_job_id"], "1385392.mmaster02", "PRE2 ODB 1385392 must not be used as native remesh predecessor")

    def test_B_remesh_parameters_and_config_consistency(self):
        params = self.manifest["remesh_parameters"]
        cfg_rule = self.config["remeshing_rule_configuration"]

        self.assertEqual(params["min_element_size_mm"], 0.0075)
        self.assertEqual(params["max_element_size_mm"], 0.03)
        self.assertEqual(params["refinement_factor"], 0.5)
        self.assertEqual(params["error_target"], 0.05)
        self.assertEqual(params["coarsening_policy"], "DISALLOW_COARSENING")
        self.assertEqual(params["max_remeshing_passes"], 1)

        # Reconciled config matches manifest
        self.assertEqual(cfg_rule["min_element_size_mm"], params["min_element_size_mm"])
        self.assertEqual(cfg_rule["max_element_size_mm"], params["max_element_size_mm"])
        self.assertEqual(cfg_rule["refinement_factor"], params["refinement_factor"])
        self.assertEqual(cfg_rule["error_target"], params["error_target"])
        self.assertEqual(cfg_rule["coarsening_policy"], params["coarsening_policy"])
        self.assertEqual(cfg_rule["max_remeshing_passes"], params["max_remeshing_passes"])

    def test_C_pbs_mail_directives_and_governance(self):
        self.assertIn("#PBS -N F43REM3_NATIVE", self.pbs)
        self.assertIn("#PBS -m abe", self.pbs)
        self.assertIn("pr21vyci@mailserver.tu-freiberg.de", self.pbs)
        self.assertIn("Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de", self.pbs)
        self.assertIn("abaqus cae noGUI=remesh_mode_ii_native_cae.py", self.pbs)

    def test_D_wrapper_qsub_and_qstat_contract(self):
        self.assertIn("qsub -m abe -M", self.wrapper)
        self.assertIn("qstat -f", self.wrapper)
        self.assertIn("AUTOMATIC_RETRY", self.wrapper)
        self.assertIn("MAX_SUBMISSIONS", self.wrapper)

    def test_E_static_validator(self):
        sys.path.insert(0, PACKAGE_DIR)
        import validate_f43rem3_native
        res = validate_f43rem3_native.validate_f43rem3_native(PACKAGE_DIR)
        self.assertTrue(res["overall_passed"], f"F43REM3_NATIVE static validator failed: {res['failures']}")

    def test_F_wrong_predecessor_odb_sha_fails(self):
        self.assertIn("expected_odb_sha", self.driver)
        self.assertIn("actual_odb_sha != expected_odb_sha", self.driver)
        self.assertIn("Predecessor ODB SHA mismatch", self.driver)

    def test_G_pre2_odb_rejected_as_predecessor(self):
        pre2_sha = "85339f45937cf5d2c57f169fa71b3e55f066082e6525aa3c20a370f058c4cf72"
        pre3_sha = self.manifest["predecessor_odb_sha256"]
        self.assertNotEqual(pre2_sha, pre3_sha)

    def test_H_wrong_cae_sha_fails(self):
        self.assertIn("expected_cae_sha", self.driver)
        self.assertIn("actual_cae_sha != expected_cae_sha", self.driver)
        self.assertIn("Source CAE SHA mismatch", self.driver)

    def test_I_source_cae_opened_in_place_rejected(self):
        self.assertIn("_runtime_work_copy.cae", self.driver)
        self.assertIn("after_source_sha != expected_cae_sha", self.driver)
        self.assertIn("Source CAE was modified in-place", self.driver)

    def test_J_missing_miseseri_fails(self):
        self.assertEqual(self.criteria["native_remeshing_acceptance_criteria"]["miseseri_consumed_from_predecessor_odb"], True)
        self.assertIn('errorIndicator="MISESERI"', self.driver)

    def test_K_wrong_abaqus_launcher_rejected(self):
        self.assertIn("abaqus cae noGUI=remesh_mode_ii_native_cae.py", self.pbs)
        self.assertNotIn("abaqus python remesh_mode_ii_native_cae.py", self.pbs)

    def test_L_wrong_working_directory_rejected(self):
        self.assertIn(': "${PBS_O_WORKDIR:?PBS_O_WORKDIR is required}"', self.pbs)
        self.assertIn('cd "${WORKDIR}" || exit 1', self.pbs)

    def test_M_automatic_retry_enabled_rejected(self):
        self.assertIn('[ "${AUTOMATIC_RETRY:-false}" = "true" ]', self.wrapper)
        self.assertIn("Automatic retry is strictly prohibited", self.wrapper)

    def test_N_max_submissions_greater_than_one_rejected(self):
        self.assertIn('[ "${MAX_SUBMISSIONS}" -ne 1 ]', self.wrapper)
        self.assertIn("MAX_SUBMISSIONS must equal 1", self.wrapper)

    def test_O_notification_config_secret_leakage_prevented(self):
        self.assertNotIn("notifications.json", self.pbs)
        self.assertNotIn("TELEGRAM_BOT_TOKEN", self.pbs)
        self.assertNotIn("TELEGRAM_CHAT_ID", self.pbs)
        self.assertNotIn("TELEGRAM_BOT_TOKEN", self.wrapper)
        self.assertNotIn("TELEGRAM_CHAT_ID", self.wrapper)

    def test_P_missing_mail_recipients_detected(self):
        self.assertIn("EMAIL_RECIPIENTS", self.wrapper)
        self.assertIn("pr21vyci@mailserver.tu-freiberg.de", self.wrapper)
        self.assertIn("Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de", self.wrapper)

    def test_Q_wrong_remesh_parameters_rejected(self):
        params = self.manifest["remesh_parameters"]
        self.assertLess(params["min_element_size_mm"], params["max_element_size_mm"])
        self.assertGreater(params["refinement_factor"], 0.0)
        self.assertLess(params["refinement_factor"], 1.0)
        self.assertGreater(params["error_target"], 0.0)

    def test_R_reaction_force_physical_definition_and_equilibrium(self):
        # Physical reaction force verification
        self.assertTrue(self.sci_comp["reaction_force_definition_corrected"])
        self.assertTrue(self.sci_comp["previous_SCI1_double_counted_RF"])
        self.assertEqual(self.sci_comp["equilibrium_check"], "PASS")

        pre2_rf = self.sci_comp["pre2_final_RF"]
        pre3_rf = self.sci_comp["pre3_final_RF"]

        # Expected historical magnitude ~46.12937 N
        self.assertAlmostEqual(pre2_rf, 46.129372, places=4)
        self.assertAlmostEqual(pre3_rf, 46.141109, places=4)

        # Relative errors remain <= 5%
        self.assertLess(self.sci_comp["final_RF_relative_error_percent"], 5.0)
        self.assertLess(self.sci_comp["peak_RF_relative_error_percent"], 5.0)
        self.assertLess(self.sci_comp["RF_U_normalized_L2_percent"], 5.0)

    def test_S_coarsening_and_pass_count_governance(self):
        # Pass count and coarsening reconciled
        self.assertEqual(self.manifest["remesh_parameters"]["max_remeshing_passes"], 1)
        self.assertEqual(self.manifest["remesh_parameters"]["coarsening_policy"], "DISALLOW_COARSENING")
        self.assertEqual(self.criteria["native_remeshing_acceptance_criteria"]["coarsening_policy"], "DISALLOW_COARSENING")
        self.assertEqual(self.criteria["native_remeshing_acceptance_criteria"]["max_remeshing_passes"], 1)

    def test_T_working_directory_fallback_and_file_discovery_logic(self):
        self.assertIn("if '__file__' in globals() and __file__:", self.driver)
        self.assertIn("script_dir = os.getcwd()", self.driver)
        self.assertIn("file_defined = False", self.driver)
        self.assertIn("fallback_used = True", self.driver)
        self.assertIn("from abaqusConstants import OFF", self.driver)

    def test_U_kernel_probe_mode_contract(self):
        self.assertIn("F43REM3_KERNEL_PROBE_ONLY", self.driver)
        self.assertIn("F43REM3_KERNEL_PROBE_STATUS.json", self.driver)
        self.assertIn('"native_remesh_called": False', self.driver)
        self.assertIn('"source_CAE_copy_open": "PASS"', self.driver)
        self.assertIn('"model_inventory": "PASS"', self.driver)
        self.assertIn('"remeshing_rule_inventory": "PASS"', self.driver)
        self.assertIn('"predecessor_ODB_available": "PASS"', self.driver)

    def test_V_failed_job_1385466_governance_classification(self):
        hpc_ledger_path = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
        with open(hpc_ledger_path, "r") as f:
            ledger_text = f.read()
        self.assertIn("1385466.mmaster02", ledger_text)
        self.assertIn("f43rem3_native_cae_file_variable_undefined_error", ledger_text)

    def test_W_step_target_and_openodb_syntax(self):
        self.assertIn('analysis_step_name = [s for s in cae_model_steps if s != "Initial"][0]', self.driver)
        self.assertIn('stepName=step_name', self.driver)
        self.assertIn('odb = openOdb(predecessor_odb_path, readOnly=True)', self.driver)
        self.assertNotIn('openOdb(pathName=', self.driver)
        self.assertIn('"model_steps": cae_model_steps', self.driver)
        self.assertIn('"analysis_step_name": analysis_step_name', self.driver)
        self.assertIn('"predecessor_odb_analysis_step": odb_analysis_step', self.driver)


if __name__ == "__main__":
    unittest.main()
