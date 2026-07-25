from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


parser = load("p3t4_parser", "scripts/postprocessing/parse_p3t4_diagnostics.py")
preflight = load("p3t4_preflight", "scripts/validation/validate_p3t4_submission_preflight.py")
consumer = load("p3t4_consumer", "scripts/validation/consume_p3t4_authorization.py")
comparator = load("p3t4_comparator", "scripts/validation/compare_p3t4_serial_reference.py")


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "models/parallelization/p3t4_threaded_characterization"
                      / "p3t4_instrumented.for").read_text(encoding="utf-8").upper()

    def body(self, name: str) -> str:
        start = self.source.index("SUBROUTINE " + name)
        end = self.source.find("\n      SUBROUTINE ", start + 1)
        if end < 0:
            end = self.source.find("\n      BLOCK DATA ", start + 1)
        return self.source[start:end]

    def test_qualified_identifiers_and_no_rejected_forms(self):
        self.assertIn("#INCLUDE <SMAASPUSERSUBROUTINES.HDR>", self.source)
        self.assertIn("CALL GETRANK(RANK)", self.source)
        self.assertIn("THREAD=GET_THREAD_ID()", self.source)
        compact = self.source.replace(" ", "")
        self.assertNotIn("RANK=GETRANK()", compact)
        self.assertNotIn("GETTHREADID()", compact)

    def test_identifiers_absent_from_uexternaldb(self):
        external = self.body("UEXTERNALDB")
        self.assertNotIn("GETRANK", external)
        self.assertNotIn("GET_THREAD_ID", external)
        self.assertIn("CALL MUTEXINIT(91)", external)

    def test_mutex_does_not_wrap_scientific_routines(self):
        for name in ("UEL", "UMAT"):
            body = self.body(name)
            self.assertNotIn("MUTEXLOCK", body)
            self.assertNotIn("MUTEXUNLOCK", body)

    def test_all_frozen_diagnostic_markers_are_present(self):
        for marker in (
            "P3T4_FIRST_CALLBACK", "P3T4_ACCESS", "P3T4_BEGIN_WRITE",
            "P3T4_END_WRITE", "P3T4_OWNERSHIP_CHANGE",
            "P3T4_DUPLICATE_INIT", "P3T4_CONFLICT_READ_DURING_WRITE",
            "P3T4_CONFLICT_WRITE_DURING_WRITE",
            "P3T4_FINAL_THREAD_COUNTS", "P3T4_FINAL_CONFLICTS",
        ):
            self.assertIn(marker, self.source)

    def test_fixed_form_column_72(self):
        path = ROOT / "models/parallelization/p3t4_threaded_characterization/p3t4_instrumented.for"
        bad = [(number, len(line)) for number, line in
               enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
               if len(line) > 72 and (not line or line[0].upper() != "C")]
        self.assertEqual(bad, [])

    def test_package_hashes_are_frozen(self):
        package = ROOT / "models/parallelization/p3t4_threaded_characterization"
        manifest = json.loads((package / "P3T4_PACKAGE_MANIFEST.json").read_text())
        for section in ("deck", "source", "transfer_table"):
            item = manifest[section]
            actual = hashlib.sha256((package / item["path"]).read_bytes()).hexdigest()
            self.assertEqual(actual, item["sha256"])


class ParserTests(unittest.TestCase):
    def test_threaded_protocol(self):
        text = "\n".join((
            "P3SM0_UEXTERNALDB_LOP0",
            "P3SM0_UEL_OBSERVED",
            "P3SM0_UMAT_OBSERVED",
            "P3T4_FIRST_CALLBACK UEL_ENTER 0 0 1 0 1 1",
            "P3T4_FIRST_CALLBACK UMAT_ENTER 0 1 17 1 1 1",
            "P3T4_BEGIN_WRITE 2 1 1 1 0 0 0 1 1 1",
            "P3T4_ACCESS 2 2 1 1 1 0 0 0 1 1 1",
            "P3T4_END_WRITE 2 1 0 0",
            "P3T4_FINAL_THREAD_COUNTS 0 0 3 0",
            "P3T4_FINAL_THREAD_COUNTS 0 1 0 2",
            "P3T4_FINAL_CONFLICTS 0 0",
            "P3SM0_UEXTERNALDB_END",
        ))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "job.msg"
            path.write_text(text, encoding="utf-8")
            rows, summary = parser.parse(path)
        self.assertEqual(summary["ranks"], [0])
        self.assertEqual(summary["threads"], [0, 1])
        self.assertEqual(summary["unmatched_begin_end_records"], 0)
        self.assertEqual(summary["concurrent_conflict_count"], 0)
        self.assertTrue(rows)

    def test_conflict_and_unmatched_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "job.msg"
            path.write_text(
                "P3T4_BEGIN_WRITE 2 1 1 1 0 0 0 1 1 0\n"
                "P3T4_CONFLICT_WRITE_DURING_WRITE 2 1 0 1 0 0\n",
                encoding="utf-8",
            )
            _, summary = parser.parse(path)
        self.assertEqual(summary["unmatched_begin_end_records"], 1)
        self.assertEqual(summary["concurrent_conflict_count"], 1)


class AuthorizationAndLaneTests(unittest.TestCase):
    def auth_path(self) -> Path:
        return ROOT / ("runs/hpc/stage_p/p3t4_threaded_characterization/"
                       "P3T4_AUTHORIZATION.json")

    def test_preparation_is_fail_closed(self):
        data = preflight.validate_authorization(self.auth_path(), False)
        self.assertFalse(data["p3t4_submission_authorized"])
        self.assertEqual(data["p3t4_submissions_used"], 0)
        for key in preflight.REQUIRED_FALSE:
            self.assertFalse(data[key])

    def test_submission_rejected_and_consumer_rejects_invalid_job(self):
        with self.assertRaises(ValueError):
            preflight.validate_authorization(self.auth_path(), True)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            data = json.loads(self.auth_path().read_text(encoding="utf-8"))
            data["classification"] = "stage_p3t4_threaded_characterization_authorized"
            data["p3t4_submission_authorized"] = True
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                consumer.consume(path, "bad-job", "a" * 40)

    def test_pbs_resources_and_submitter_are_frozen(self):
        pbs = (ROOT / "scripts/hpc/stage_p/07_p3t4_threaded_characterization.pbs"
               ).read_text(encoding="utf-8")
        submitter = (ROOT / "scripts/hpc/stage_p/submit_p3t4_threaded_characterization.sh"
                     ).read_text(encoding="utf-8")
        for token in ("#PBS -N p3t4_threaded", "#PBS -q entry_imfdfkmq",
                      "select=1:ncpus=4:mem=16gb", "walltime=00:30:00",
                      "export OMP_NUM_THREADS=4", "cpus=4 mp_mode=threads"):
            self.assertIn(token, pbs)
        self.assertIn("P3T4_PREFLIGHT_ONLY", submitter)
        self.assertIn('PREFLIGHT_SUBMIT_ARGS=(--require-submit)', submitter)
        self.assertNotIn("git ", pbs)

    def test_all_result_classifications_are_frozen(self):
        combined = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in (
                "docs/decisions/STAGE_P3T4_PREPARATION_RELEASE.md",
                "scripts/hpc/stage_p/07_p3t4_threaded_characterization.pbs",
                "scripts/validation/validate_p3t4_threaded.py",
            )
        )
        for classification in (
            "stage_p3t4_threaded_characterization_pass",
            "stage_p3t4_threaded_fail_pre_abaqus",
            "stage_p3t4_threaded_fail_compile",
            "stage_p3t4_threaded_fail_link",
            "stage_p3t4_threaded_fail_identifier",
            "stage_p3t4_threaded_fail_mutex",
            "stage_p3t4_threaded_fail_deadlock",
            "stage_p3t4_threaded_fail_callback",
            "stage_p3t4_threaded_fail_validation",
            "stage_p3t4_threading_not_exercised",
            "stage_p3t4_shared_state_conflict_observed",
            "stage_p3t4_scientific_mismatch",
        ):
            self.assertIn(classification, combined)


class ComparatorTests(unittest.TestCase):
    def test_frozen_serial_reference_matches_identical_candidate(self):
        reference = ROOT / "runs/hpc/stage_p/p3sm0_minimal_callback_serial"
        with tempfile.TemporaryDirectory() as td:
            candidate = Path(td)
            for target, source in (
                ("P3T4_STATE_OUTPUT.csv", "P3SM0_STATE_OUTPUT.csv"),
                ("P3T4_RF_U.csv", "P3SM0_RF_U.csv"),
                ("P3T4_ENERGY.csv", "P3SM0_ENERGY.csv"),
                ("P3T4_INCREMENT_SEQUENCE.json", "P3SM0_INCREMENT_SEQUENCE.json"),
            ):
                (candidate / target).write_bytes((reference / source).read_bytes())
            result = comparator.compare(candidate, reference)
        self.assertTrue(result["serial_equivalent"])
        self.assertEqual(result["absolute_tolerance"], 1.0e-12)
        self.assertEqual(result["relative_tolerance"], 1.0e-10)


if __name__ == "__main__":
    unittest.main()
