import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "runs/hpc/stage_f/f16_queue_access_qualification_and_wave_b_r3_preparation"
CTL = ROOT / "models/generated/mode_ii/f16_controlled_rollback_control_r3"
FORCE = ROOT / "models/generated/mode_ii/f16_controlled_rollback_forced_r3"
REG = ROOT / "models/generated/mode_ii/f16_native_adaptive_region_resolution_r3"
ORCH = ROOT / "scripts/hpc/stage_f/submit_f16_wave_b_r3.sh"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class F16R3QueueReplacementTests(unittest.TestCase):
    def test_installed_queue_contract(self):
        audit = json.loads((RUN / "PBS_QUEUE_ACCESS_AUDIT.json").read_text())
        self.assertEqual(audit["classification"], "entry_route_queue_required")
        self.assertEqual(audit["entry_imfdfkmq"]["queue_type"], "Route")
        self.assertIn("normal_imfdfkmq", audit["entry_imfdfkmq"]["route_destinations"])
        self.assertTrue(audit["normal_imfdfkmq"]["from_route_only"])
        self.assertFalse(audit["normal_imfdfkmq"]["user_group_match"])

    def test_unique_names_and_route_directives(self):
        expected = ((CTL, "M2IRRROLLCTL3"), (FORCE, "M2IRRROLLFORCE3"), (REG, "M2RMREG3"))
        names = []
        for package, name in expected:
            pbs = next(package.glob("*.pbs"))
            text = pbs.read_text()
            self.assertIn("#PBS -N " + name, text)
            self.assertIn("#PBS -q entry_imfdfkmq", text)
            self.assertNotIn("#PBS -q normal_imfdfkmq", text)
            names.append(name)
        self.assertEqual(len(names), len(set(names)))

    def test_scientific_hashes_unchanged(self):
        self.assertEqual(sha(CTL / "runtime/M2IRR_F16.for"), "8d30f10b8c668b9b1e256aeb389e9cf53e38d03fec4e1650bf1e30d975da133a")
        self.assertEqual(sha(CTL / "runtime/M2IRR_F16.inp"), "a84df34a2bdbfbd55d7f2642082710f1d410cd8480637f9da9aa47c107beed3b")
        self.assertEqual((CTL / "runtime/M2IRR_F16.for").read_bytes(), (FORCE / "runtime/M2IRR_F16.for").read_bytes())
        self.assertEqual((CTL / "runtime/M2IRR_F16.inp").read_bytes(), (FORCE / "runtime/M2IRR_F16.inp").read_bytes())
        self.assertEqual(sha(REG / "runtime/source_deck.inp"), "a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2")

    def test_new_pbs_hashes(self):
        self.assertEqual(sha(CTL / "M2IRRROLLCTL3.pbs"), "32b2813bd0eda812853b654be84b939e9f21ed988a57d3b2a23882f847e6f2aa")
        self.assertEqual(sha(FORCE / "M2IRRROLLFORCE3.pbs"), "1916a80b6938fddca5a4a87466b35b0d54dfc0366ffe741841599e2990e7a210")
        self.assertEqual(sha(REG / "M2RMREG3.pbs"), "dcca83868e894c1e7226487d7560cfdf20ddf6906964943aa12437ab6e51bbe1")

    def test_attempt_counter_and_withheld_lane_regression(self):
        text = ORCH.read_text()
        self.assertEqual(text.count("attempts=$((attempts+1))"), 1)
        submit_body = text[text.index("submit_one()") : text.index("submit_one \"$RUN_DIR/control\"")]
        self.assertLess(submit_body.index("attempts=$((attempts+1))"), submit_body.index("qsub "))
        withheld = text[text.index("else\n  withheld=$((withheld+1))") :]
        self.assertNotIn("attempts=$((attempts+1))", withheld)
        self.assertIn("withheld_lanes", text)

    def test_dependency_only_from_valid_control_id(self):
        text = ORCH.read_text()
        self.assertIn("dependency=\"afterany:$ctl_id\"", text)
        self.assertRegex(text, re.compile(r"ctl_rc.*grep -Eq '\^\[0-9\]", re.S))
        self.assertIn("valid M2IRRROLLCTL3 PBS ID unavailable", text)

    def test_limits_and_prohibitions(self):
        plan = json.loads((RUN / "F16_R3_BATCH_PLAN.json").read_text())
        self.assertEqual(plan["maximum_future_submissions"], 3)
        self.assertEqual(plan["maximum_simultaneously_running_jobs"], 2)
        for key in ("retry", "same_session_replacement", "direct_qsub", "qdel", "qmove"):
            self.assertFalse(plan[key])
        for package in (CTL, FORCE, REG):
            pbs = next(package.glob("*.pbs")).read_text()
            self.assertNotIn("qsub ", pbs)
            self.assertNotIn("qdel ", pbs)
            self.assertNotIn("qmove ", pbs)

    def test_notification_contract_unchanged(self):
        wrapper_hash = "e51843b0c3173b0b2ce0aee8add763356e0b273dc55a136d9ec07e8f7f940bfe"
        for package in (CTL, FORCE, REG):
            self.assertEqual(sha(package / "runtime/job_notifications.sh"), wrapper_hash)
            pbs = next(package.glob("*.pbs")).read_text()
            self.assertIn("notify_start || exit 5", pbs)
            self.assertIn("notification_install_terminal_trap", pbs)
            self.assertIn("#PBS -m abe", pbs)

    def test_all_json_parses_and_no_execution(self):
        for path in list(RUN.glob("*.json")) + list(CTL.glob("*.json")) + list(FORCE.glob("*.json")) + list(REG.glob("*.json")):
            json.loads(path.read_text())
        audit = json.loads((RUN / "F16_R3_NO_EXECUTION_AUDIT.json").read_text())
        self.assertEqual(audit["qsub_attempts"], 0)
        self.assertFalse(audit["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
