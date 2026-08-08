import os
import sys
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge")
WRAPPER_PATH = os.path.join(PACKAGE_DIR, "submit_f43pre3_geom.sh")
PBS_PATH = os.path.join(PACKAGE_DIR, "F43PRE3_GEOM.pbs")
VALIDATOR_PATH = os.path.join(REPO_ROOT, "scripts", "validation", "validate_notification_pipeline.py")

class TestF43PRE3R4NotificationContract(unittest.TestCase):

    def test_A_notification_pipeline_validator(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "validation"))
        import validate_notification_pipeline
        res = validate_notification_pipeline.check_notification_pipeline()
        
        self.assertTrue(res["notification_config_found"], "Notification config not found")
        self.assertEqual(res["email_recipient_count"], 2, "Email recipient count must equal 2")
        self.assertTrue(res["email_recipients_valid"], "Email recipients set invalid")
        self.assertTrue(res["telegram_bot_token_present"], "Telegram bot token missing")
        self.assertTrue(res["telegram_chat_id_present"], "Telegram chat ID missing")
        self.assertTrue(res["pbs_mail_points_valid"], "PBS script missing #PBS -m abe")
        self.assertTrue(res["pbs_mail_users_valid"], "PBS script missing #PBS -M with both emails")
        self.assertTrue(res["wrapper_qsub_mail_options_valid"], "Wrapper missing qsub -m abe -M")
        self.assertTrue(res["submission_notification_present"], "Wrapper missing submission notification")
        self.assertTrue(res["completion_notification_present"], "PBS script missing completion notification")
        self.assertTrue(res["failure_notification_present"], "PBS script missing failure notification")
        self.assertTrue(res["email_configuration_verified_from_qstat"], "Wrapper missing qstat mail verification")
        self.assertTrue(res["overall_passed"], "Overall notification pipeline validation failed")

    def test_B_pbs_directives_contain_both_email_addresses(self):
        with open(PBS_PATH, "r") as f:
            pbs_text = f.read()

        self.assertIn("#PBS -m abe", pbs_text)
        self.assertIn("pr21vyci@mailserver.tu-freiberg.de", pbs_text)
        self.assertIn("Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de", pbs_text)

    def test_C_wrapper_qstat_verification_and_mail_options(self):
        with open(WRAPPER_PATH, "r") as f:
            wrapper_text = f.read()

        self.assertIn("qsub -m abe -M", wrapper_text)
        self.assertIn("qstat -f", wrapper_text)
        self.assertIn("Mail_Users|Mail_Points", wrapper_text)

if __name__ == "__main__":
    unittest.main()
