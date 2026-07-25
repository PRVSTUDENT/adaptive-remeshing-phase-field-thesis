from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts/validation"), str(ROOT / "scripts/postprocessing")]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


parser = load("p3sm1t_parser", "scripts/postprocessing/parse_p3sm1t_callback_log.py")
preflight = load("p3sm1t_preflight", "scripts/validation/validate_p3sm1t_submission_preflight.py")
consumer = load("p3sm1t_consumer", "scripts/validation/consume_p3sm1t_authorization.py")
validator = load("p3sm1t_validator", "scripts/validation/validate_p3sm1t_serial.py")
PACKAGE = ROOT / "models/parallelization/p3sm1t_threadid_serial"
P3SM0 = ROOT / "models/parallelization/p3sm0_minimal_callback_serial"


def auth(**updates):
    data = {
        "classification": "stage_p3sm1t_threadid_serial_prepared",
        "p3sm1t_preparation_complete": True,
        "p3sm1t_submission_authorized": False,
        "maximum_p3sm1t_submissions": 1,
        "p3sm1t_submissions_used": 0,
        **{key: False for key in preflight.REQUIRED_FALSE},
    }
    data.update(updates)
    if data["p3sm1t_submission_authorized"]:
        data["classification"] = "stage_p3sm1t_threadid_serial_authorized"
    return data


class ReferenceAndPackageTests(unittest.TestCase):
    def test_p3sm0_status_and_completion_unchanged(self):
        status = json.loads((ROOT / "runs/hpc/stage_p/p3sm0_minimal_callback_serial/P3SM0_STATUS.json").read_text())
        self.assertEqual(status["classification"], "stage_p3sm0_minimal_callback_serial_pass")
        self.assertEqual(status["job_id"], "1378099.mmaster02")
        self.assertEqual(status["solver_exit"], 0)
        self.assertEqual(status["observed_state_records"], 32)
        self.assertEqual(status["increment_records"], 13)
        self.assertFalse(status["signal_11_present"])
        self.assertTrue((ROOT / "runs/hpc/stage_p/p3sm0_minimal_callback_serial/P3SM0_COMPLETION.ok").is_file())

    def test_deck_and_transfer_identity(self):
        self.assertEqual((PACKAGE / "P3SM1T_serial.inp").read_bytes(),
                         (P3SM0 / "P3SM0_serial.inp").read_bytes())
        self.assertEqual((PACKAGE / "d2_transfer_table.inc").read_bytes(),
                         (P3SM0 / "d2_transfer_table.inc").read_bytes())

    def test_only_four_source_lines_added(self):
        base = (P3SM0 / "p3sm0_minimal_callback.for").read_text().splitlines()
        candidate = (PACKAGE / "p3sm1t_threadid_callback.for").read_text().splitlines()
        additions = [line for line in candidate if line not in base]
        self.assertEqual(additions, [
            "      INTEGER GETTHREADID,THREAD_ID",
            "        WRITE(7,*) 'P3SM1T_BEFORE_GETTHREADID'",
            "        THREAD_ID=GETTHREADID()",
            "        WRITE(7,*) 'P3SM1T_AFTER_GETTHREADID ',THREAD_ID",
        ])

    def test_source_scope_and_forbidden_tokens(self):
        source = (PACKAGE / "p3sm1t_threadid_callback.for").read_text().upper()
        self.assertIn("GETTHREADID()", validator.routine_body(source, "UEL"))
        self.assertNotIn("GETTHREADID", validator.routine_body(source, "UMAT"))
        self.assertNotIn("GETTHREADID", validator.routine_body(source, "UEXTERNALDB"))
        for token in validator.FORBIDDEN:
            self.assertNotIn(token, source)

    def test_fixed_form_column_72(self):
        lines = (PACKAGE / "p3sm1t_threadid_callback.for").read_text().splitlines()
        self.assertEqual([i for i, line in enumerate(lines, 1)
                          if line and line[0] not in "Cc*!" and len(line) > 72], [])

    def test_lane_resources_ordering_and_no_compute_git(self):
        pbs = (ROOT / "scripts/hpc/stage_p/04_p3sm1t_threadid_serial.pbs").read_text()
        self.assertIn("#PBS -q entry_imfdfkmq", pbs)
        self.assertIn("select=1:ncpus=1:mem=16gb", pbs)
        self.assertIn("walltime=00:30:00", pbs)
        self.assertIn("OMP_NUM_THREADS=1", pbs)
        self.assertNotIn("git ", pbs)
        validation = pbs.index('validate_p3sm1t_serial.py"')
        self.assertLess(pbs.index('copy_if_present "${RUN_DIR}/${JOB_NAME}.sta"'), validation)
        self.assertLess(pbs.index('test -f "${required}"'), validation)


class ParserTests(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x.msg"
            path.write_text(text)
            return parser.parse(path)

    def test_zero_and_multiple_zeros_pass_parser_shape(self):
        one = self.parse("P3SM1T_BEFORE_GETTHREADID\nP3SM1T_AFTER_GETTHREADID 0\n")
        self.assertEqual(one["unique_thread_ids"], [0])
        self.assertEqual(one["unmatched_before_calls"], 0)
        many = self.parse(("P3SM1T_BEFORE_GETTHREADID\nP3SM1T_AFTER_GETTHREADID 0\n") * 2)
        self.assertEqual(many["returned_thread_ids"], [0, 0])
        self.assertFalse(many["before_after_count_mismatch"])

    def test_missing_markers_mismatch_and_signal(self):
        before = self.parse("P3SM1T_BEFORE_GETTHREADID\nsignal 11\n")
        self.assertEqual(before["after_count"], 0)
        self.assertEqual(before["unmatched_before_calls"], 1)
        self.assertTrue(before["signal_11_present"])
        after = self.parse("P3SM1T_AFTER_GETTHREADID 0\n")
        self.assertEqual(after["before_count"], 0)
        self.assertTrue(after["before_after_count_mismatch"])

    def test_invalid_and_mixed_ids_are_recorded(self):
        for value in (-1, 1):
            result = self.parse(f"P3SM1T_BEFORE_GETTHREADID\nP3SM1T_AFTER_GETTHREADID {value}\n")
            self.assertEqual(result["returned_thread_ids"], [value])
        mixed = self.parse(("P3SM1T_BEFORE_GETTHREADID\nP3SM1T_AFTER_GETTHREADID 0\n"
                            "P3SM1T_BEFORE_GETTHREADID\nP3SM1T_AFTER_GETTHREADID 1\n"))
        self.assertEqual(mixed["unique_thread_ids"], [0, 1])


class ValidatorTests(unittest.TestCase):
    def fixture(self, root: Path):
        reference = ROOT / "runs/hpc/stage_p/p3sm0_minimal_callback_serial"
        mapping = {
            "P3SM0_ENVIRONMENT.txt": "P3SM1T_ENVIRONMENT.txt",
            "P3SM0_JOB_RECORD.txt": "P3SM1T_JOB_RECORD.txt",
            "P3SM0_STATE_OUTPUT.csv": "P3SM1T_STATE_OUTPUT.csv",
            "P3SM0_RF_U.csv": "P3SM1T_RF_U.csv",
            "P3SM0_ENERGY.csv": "P3SM1T_ENERGY.csv",
            "p3sm0_serial.abaqus_stdout.log": "p3sm1t_serial.abaqus_stdout.log",
            "p3sm0_serial.sta": "p3sm1t_serial.sta",
        }
        for source, target in mapping.items():
            shutil.copyfile(reference / source, root / target)
        summary = {
            "observed": {marker: True for marker in validator.MARKERS},
            "counts": {marker: 1 for marker in validator.MARKERS},
            "before_count": 1, "after_count": 1,
            "returned_thread_ids": [0], "unique_thread_ids": [0],
            "unmatched_before_calls": 0, "signal_11_present": False,
        }
        (root / "P3SM1T_CALLBACK_SUMMARY.json").write_text(json.dumps(summary))

    def validate(self, root):
        return validator.validate(
            root, PACKAGE / "P3SM1T_serial.inp",
            PACKAGE / "d2_transfer_table.inc",
            PACKAGE / "p3sm1t_threadid_callback.for", "synthetic", 0,
        )

    def test_complete_zero_id_fixture_passes_and_marks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            result = self.validate(root)
            self.assertTrue(result["P3SM1T_ok"], result["failures"])
            self.assertTrue((root / "P3SM1T_COMPLETION.ok").is_file())

    def test_marker_mismatch_signal_and_invalid_ids_fail(self):
        mutations = (
            {"before_count": 0},
            {"after_count": 0, "unmatched_before_calls": 1},
            {"signal_11_present": True},
            {"returned_thread_ids": [], "unique_thread_ids": []},
            {"returned_thread_ids": [-1], "unique_thread_ids": [-1]},
            {"returned_thread_ids": [1], "unique_thread_ids": [1]},
            {"returned_thread_ids": [0, 1], "unique_thread_ids": [0, 1],
             "before_count": 2, "after_count": 2},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                self.fixture(root)
                path = root / "P3SM1T_CALLBACK_SUMMARY.json"
                data = json.loads(path.read_text())
                data.update(mutation)
                path.write_text(json.dumps(data))
                self.assertFalse(self.validate(root)["P3SM1T_ok"])
                self.assertFalse((root / "P3SM1T_COMPLETION.ok").exists())

    def test_missing_base_callback_and_scientific_evidence_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            callback = root / "P3SM1T_CALLBACK_SUMMARY.json"
            data = json.loads(callback.read_text())
            data["observed"]["P3SM0_UMAT_OBSERVED"] = False
            callback.write_text(json.dumps(data))
            self.assertFalse(self.validate(root)["P3SM1T_ok"])
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            (root / "P3SM1T_ENERGY.csv").unlink()
            self.assertFalse(self.validate(root)["P3SM1T_ok"])


class AuthorizationTests(unittest.TestCase):
    def write(self, root, data):
        path = root / "auth.json"
        path.write_text(json.dumps(data))
        return path

    def test_false_missing_malformed_and_consumed_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(ValueError):
                preflight.validate_authorization(root / "missing", True)
            malformed = root / "bad"
            malformed.write_text("{")
            with self.assertRaises(ValueError):
                preflight.validate_authorization(malformed, True)
            with self.assertRaises(ValueError):
                preflight.validate_authorization(self.write(root, auth()), True)
            with self.assertRaises(ValueError):
                preflight.validate_authorization(
                    self.write(root, auth(p3sm1t_submission_authorized=True,
                                          p3sm1t_submissions_used=1)), True)

    def test_invalid_job_leaves_unused_valid_consumes_once(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write(Path(td), auth(p3sm1t_submission_authorized=True))
            initial = path.read_bytes()
            with self.assertRaises(ValueError):
                consumer.consume(path, "not-a-job", "a" * 40)
            self.assertEqual(path.read_bytes(), initial)
            result = consumer.consume(path, "123.mmaster02", "a" * 40)
            self.assertEqual(result["p3sm1t_submissions_used"], 1)
            self.assertFalse(result["p3sm1t_submission_authorized"])
            with self.assertRaises(ValueError):
                consumer.consume(path, "124.mmaster02", "a" * 40)

    def test_committed_authorization_and_downstream_false(self):
        data = json.loads((ROOT / "runs/hpc/stage_p/p3sm1t_threadid_serial/P3SM1T_AUTHORIZATION.json").read_text())
        self.assertFalse(data["p3sm1t_submission_authorized"])
        self.assertEqual(data["p3sm1t_submissions_used"], 0)
        for key in preflight.REQUIRED_FALSE:
            self.assertFalse(data[key])


if __name__ == "__main__":
    unittest.main()
