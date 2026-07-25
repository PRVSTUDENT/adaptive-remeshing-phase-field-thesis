import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parser = load(
    "parse_p3sm1r_callback_log",
    "scripts/postprocessing/parse_p3sm1r_callback_log.py",
)
preflight = load(
    "validate_p3sm1r_submission_preflight",
    "scripts/validation/validate_p3sm1r_submission_preflight.py",
)


class SourceIsolationTests(unittest.TestCase):
    def setUp(self):
        self.source = (
            ROOT
            / "models/parallelization/p3sm1r_getrank_serial"
            / "p3sm1r_getrank_callback.for"
        ).read_text(encoding="utf-8").upper()

    def test_exact_documented_call_is_inside_controlled_uel_condition(self):
        uel = self.source[
            self.source.index("SUBROUTINE UEL"):
            self.source.index("SUBROUTINE UMAT")
        ]
        self.assertIn("JELEM.EQ.1 .AND. KSTEP.EQ.1 .AND. KINC.EQ.1", uel)
        self.assertIn("INTEGER KPROCESSNUM", uel)
        self.assertIn("P3SM1R_BEFORE_GETRANK", uel)
        self.assertIn("CALL GETRANK(KPROCESSNUM)", uel)
        self.assertIn("P3SM1R_AFTER_GETRANK ',KPROCESSNUM", uel)

    def test_identifier_is_absent_outside_uel_and_thread_id_is_absent(self):
        before_uel, after_uel = self.source.split("SUBROUTINE UEL", 1)
        _, after_uel = after_uel.split("SUBROUTINE UMAT", 1)
        self.assertNotIn("GETRANK", before_uel + after_uel)
        self.assertNotIn("GET_THREAD_ID", self.source)
        self.assertNotIn("GETTHREADID", self.source)


class SubmitterTests(unittest.TestCase):
    def test_notification_address_does_not_reuse_system_mail_variable(self):
        submitter = (
            ROOT / "scripts/hpc/stage_p/submit_p3sm1r_getrank_serial.sh"
        ).read_text(encoding="utf-8")
        self.assertIn('P3SM1R_MAIL="${P3SM1R_MAIL:-', submitter)
        self.assertNotIn('MAIL="${MAIL:-', submitter)


class ParserTests(unittest.TestCase):
    def test_rank_zero_and_matching_markers(self):
        text = "\n".join((
            "P3SM0_UEXTERNALDB_LOP0",
            "P3SM0_UEL_OBSERVED",
            "P3SM1R_BEFORE_GETRANK",
            "P3SM1R_AFTER_GETRANK 0",
            "P3SM0_UMAT_OBSERVED",
            "P3SM0_UEXTERNALDB_END",
        ))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "job.msg"
            path.write_text(text, encoding="utf-8")
            result = parser.parse(path)
        self.assertEqual(result["before_count"], result["after_count"])
        self.assertEqual(result["returned_process_ids"], [0])
        self.assertEqual(result["unique_process_ids"], [0])
        self.assertFalse(result["before_after_count_mismatch"])


class AuthorizationTests(unittest.TestCase):
    def test_committed_successful_closure_is_consumed(self):
        path = (
            ROOT
            / "runs/hpc/stage_p/p3sm1r_getrank_serial"
            / "P3SM1R_AUTHORIZATION.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["classification"], "stage_p3sm1r_getrank_serial_submitted")
        self.assertFalse(data["p3sm1r_submission_authorized"])
        self.assertEqual(data["maximum_p3sm1r_submissions"], 1)
        self.assertEqual(data["p3sm1r_submissions_used"], 1)
        self.assertEqual(data["p3sm1r_job_id"], "1378241.mmaster02")
        for key in preflight.REQUIRED_FALSE:
            self.assertFalse(data[key])

    def test_submission_preflight_is_blocked_after_consumption(self):
        path = (
            ROOT
            / "runs/hpc/stage_p/p3sm1r_getrank_serial"
            / "P3SM1R_AUTHORIZATION.json"
        )
        with self.assertRaises(ValueError):
            preflight.validate_authorization(path, require_submit=True)


if __name__ == "__main__":
    unittest.main()
