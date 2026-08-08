import os
import sys
import json
import re
import argparse

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge")
WRAPPER_PATH = os.path.join(PACKAGE_DIR, "submit_f43pre3_geom.sh")
PBS_PATH = os.path.join(PACKAGE_DIR, "F43PRE3_GEOM.pbs")
NOTIFY_PY_PATH = os.path.join(REPO_ROOT, "scripts", "hpc", "notify_hpc_event.py")

EXPECTED_RECIPIENTS = {
    "pr21vyci@mailserver.tu-freiberg.de",
    "Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"
}

def check_notification_pipeline():
    results = {
        "notification_config_found": False,
        "email_recipient_count": 0,
        "email_recipients_valid": False,
        "telegram_bot_token_present": False,
        "telegram_chat_id_present": False,
        "pbs_mail_points_valid": False,
        "pbs_mail_users_valid": False,
        "wrapper_qsub_mail_options_valid": False,
        "submission_notification_present": False,
        "completion_notification_present": False,
        "failure_notification_present": False,
        "email_configuration_verified_from_qstat": False,
        "overall_passed": False
    }

    # 1. Config Loader Check
    if os.path.exists(NOTIFY_PY_PATH):
        sys.path.insert(0, os.path.dirname(NOTIFY_PY_PATH))
        try:
            import notify_hpc_event
            token, chat_id, recipients = notify_hpc_event.load_notification_config()
            if token and chat_id:
                results["notification_config_found"] = True
                results["telegram_bot_token_present"] = True
                results["telegram_chat_id_present"] = True
            if recipients:
                rec_list = [r.strip() for r in recipients.split(",") if r.strip()]
                results["email_recipient_count"] = len(rec_list)
                if set(rec_list) == EXPECTED_RECIPIENTS:
                    results["email_recipients_valid"] = True
        except Exception as e:
            print("Config load error:", e, file=sys.stderr)

    # 2. Check F43PRE3_GEOM.pbs
    if os.path.exists(PBS_PATH):
        with open(PBS_PATH, "r") as f:
            pbs_content = f.read()

        if "#PBS -m abe" in pbs_content:
            results["pbs_mail_points_valid"] = True

        if "#PBS -M pr21vyci@mailserver.tu-freiberg.de,Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de" in pbs_content:
            results["pbs_mail_users_valid"] = True

        if "notify_hpc_event.py" in pbs_content and "--mode terminal" in pbs_content:
            results["completion_notification_present"] = True
            results["failure_notification_present"] = True

    # 3. Check submit_f43pre3_geom.sh
    if os.path.exists(WRAPPER_PATH):
        with open(WRAPPER_PATH, "r") as f:
            wrapper_content = f.read()

        if "qsub -m abe -M" in wrapper_content:
            results["wrapper_qsub_mail_options_valid"] = True

        if "qstat -f" in wrapper_content and "Mail_Users|Mail_Points" in wrapper_content:
            results["email_configuration_verified_from_qstat"] = True

        if "notify_hpc_event.py" in wrapper_content and "--mode submission" in wrapper_content:
            results["submission_notification_present"] = True

    # Overall pass criteria
    results["overall_passed"] = all([
        results["notification_config_found"],
        results["email_recipient_count"] == 2,
        results["email_recipients_valid"],
        results["telegram_bot_token_present"],
        results["telegram_chat_id_present"],
        results["pbs_mail_points_valid"],
        results["pbs_mail_users_valid"],
        results["wrapper_qsub_mail_options_valid"],
        results["submission_notification_present"],
        results["completion_notification_present"],
        results["failure_notification_present"],
        results["email_configuration_verified_from_qstat"]
    ])

    return results

if __name__ == "__main__":
    res = check_notification_pipeline()
    print(json.dumps(res, indent=2))
    if not res["overall_passed"]:
        sys.exit(1)
