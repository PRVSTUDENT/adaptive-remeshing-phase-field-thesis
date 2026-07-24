from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/validation"))
sys.path.insert(0, str(ROOT / "scripts/postprocessing"))


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


base = load("p3sb_base_for_sm0", "scripts/validation/validate_p3sb_baseline_serial.py")
validator = load("p3sm0_validator", "scripts/validation/validate_p3sm0_serial.py")
preflight = load("p3sm0_preflight", "scripts/validation/validate_p3sm0_submission_preflight.py")
consumer = load("p3sm0_consumer", "scripts/validation/consume_p3sm0_authorization.py")
parser = load("p3sm0_parser", "scripts/postprocessing/parse_p3sm0_callback_log.py")

ORIGINAL = ROOT / "runs/hpc/stage_p/p3sb_baseline_serial"
PACKAGE = ROOT / "models/parallelization/p3sm0_minimal_callback_serial"
BASE_PACKAGE = ROOT / "models/parallelization/p3sb_baseline_eight_element_serial"


def authorization(**updates: object) -> dict[str, object]:
    data: dict[str, object] = {
        "classification": "stage_p3sm0_minimal_callback_serial_prepared",
        "p3sm0_preparation_complete": True,
        "p3sm0_submission_authorized": False,
        "maximum_p3sm0_submissions": 1,
        "p3sm0_submissions_used": 0,
        "automatic_retry_authorized": False,
        "p3sm1_authorized": False,
        "p3t4_authorized": False,
        "mpi_authorized": False,
        "hybrid_authorized": False,
        "p4_authorized": False,
        "production_h1_authorized": False,
        "d3d_a1_reopening_authorized": False,
        "d3e_authorized": False,
    }
    data.update(updates)
    if data.get("p3sm0_submission_authorized") is True and "classification" not in updates:
        data["classification"] = "stage_p3sm0_minimal_callback_serial_authorized"
    return data


def copy_replay(root: Path) -> None:
    for name in (
        "P3SB_ENVIRONMENT.txt", "P3SB_JOB_RECORD.txt", "P3SB_STATE_OUTPUT.csv",
        "P3SB_RF_U.csv", "P3SB_ENERGY.csv", "p3sb_baseline.abaqus_stdout.log",
        "p3sb_baseline.sta",
    ):
        shutil.copyfile(ORIGINAL / name, root / name)


class OfflineAuditTests(unittest.TestCase):
    def test_original_status_hash_and_marker_absence(self) -> None:
        self.assertEqual(
            hashlib.sha256((ORIGINAL / "P3SB_STATUS.json").read_bytes()).hexdigest(),
            "54d15323295cf712f50a26e5194b28a61826a3803374c4342b61ca8c546653de",
        )
        self.assertFalse((ORIGINAL / "P3SB_COMPLETION.ok").exists())

    def run_replay(self, mutate=None):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        copy_replay(root)
        if mutate:
            mutate(root)
        result = base.validate(
            root, BASE_PACKAGE / "P3SB_baseline_serial.inp",
            BASE_PACKAGE / "d2_transfer_table.inc", "1378094.mmaster02", 0
        )
        return temporary, root, result

    def test_finalized_logs_pass_unchanged_validator(self) -> None:
        td, root, result = self.run_replay()
        self.addCleanup(td.cleanup)
        self.assertTrue(result["P3SB_ok"])
        self.assertEqual(result["increment_records"], 13)
        self.assertTrue((root / "P3SB_COMPLETION.ok").is_file())

    def test_missing_stdout_and_sta_fail(self) -> None:
        for name in ("p3sb_baseline.abaqus_stdout.log", "p3sb_baseline.sta"):
            td, _, result = self.run_replay(lambda root, n=name: (root / n).unlink())
            self.addCleanup(td.cleanup)
            self.assertFalse(result["P3SB_ok"])

    def test_empty_increment_sequence_fails(self) -> None:
        td, _, result = self.run_replay(
            lambda root: (root / "p3sb_baseline.sta").write_text(
                "THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n", encoding="utf-8"
            )
        )
        self.addCleanup(td.cleanup)
        self.assertEqual(result["increment_records"], 0)
        self.assertFalse(result["P3SB_ok"])

    def test_altered_scientific_csv_fails(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "P3SB_STATE_OUTPUT.csv"
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["SDV15_F0"] = "9.0"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
        td, _, result = self.run_replay(mutate)
        self.addCleanup(td.cleanup)
        self.assertFalse(result["P3SB_ok"])


class PackageAndLaneTests(unittest.TestCase):
    def test_source_contains_only_minimal_callback_capabilities(self) -> None:
        source = (PACKAGE / "p3sm0_minimal_callback.for").read_text().upper()
        self.assertIn("SUBROUTINE UEXTERNALDB", source)
        for marker in parser.MARKERS:
            self.assertIn(marker, source)
        for token in validator.FORBIDDEN:
            self.assertNotIn(token, source)

    def test_scientific_source_is_unchanged_outside_hooks(self) -> None:
        candidate = (PACKAGE / "p3sm0_minimal_callback.for").read_text()
        blocks = (
            """      IF (JELEM.EQ.1 .AND. KSTEP.EQ.1 .AND. KINC.EQ.1) THEN
        WRITE(7,*) 'P3SM0_UEL_OBSERVED'
      ENDIF
""",
            """      IF (NOEL.EQ.17 .AND. NPT.EQ.1 .AND.
     1    KSTEP.EQ.1 .AND. KINC.EQ.1) THEN
        WRITE(7,*) 'P3SM0_UMAT_OBSERVED'
      ENDIF
""",
            """      SUBROUTINE UEXTERNALDB(LOP,LRESTART,TIME,DTIME,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      DIMENSION TIME(2)
      IF (LOP.EQ.0) THEN
        WRITE(7,*) 'P3SM0_UEXTERNALDB_LOP0'
      ELSEIF (LOP.EQ.3) THEN
        WRITE(7,*) 'P3SM0_UEXTERNALDB_END'
      ENDIF
      RETURN
      END

""",
        )
        for block in blocks:
            self.assertIn(block, candidate)
            candidate = candidate.replace(block, "")
        self.assertEqual(candidate, (BASE_PACKAGE / "p3sb_baseline_uel.for").read_text())

    def test_fixed_form_column_72(self) -> None:
        lines = (PACKAGE / "p3sm0_minimal_callback.for").read_text().splitlines()
        invalid = [
            number for number, line in enumerate(lines, 1)
            if line and line[0] not in "Cc*!" and len(line) > 72
        ]
        self.assertEqual(invalid, [])

    def test_queue_resources_no_compute_repository_command(self) -> None:
        pbs = (ROOT / "scripts/hpc/stage_p/03_p3sm0_minimal_callback_serial.pbs").read_text()
        submitter = (
            ROOT / "scripts/hpc/stage_p/submit_p3sm0_minimal_callback_serial.sh"
        ).read_text()
        self.assertIn("#PBS -q entry_imfdfkmq", pbs)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", pbs)
        self.assertIn("OMP_NUM_THREADS=1", pbs)
        self.assertIn("mpi_ranks=1", pbs)
        self.assertIn("omp_threads=1", pbs)
        self.assertNotIn("git ", pbs)
        self.assertIn("qsub_with_submitted_notify.sh", submitter)

    def test_validation_inputs_are_copied_before_validator(self) -> None:
        pbs = (ROOT / "scripts/hpc/stage_p/03_p3sm0_minimal_callback_serial.pbs").read_text()
        validate_position = pbs.index(
            'python3 "${P3SM0_STAGE_ROOT}/validate_p3sm0_serial.py"'
        )
        for token in (
            'copy_if_present "${RUN_DIR}/${JOB_NAME}.abaqus_stdout.log"',
            'copy_if_present "${RUN_DIR}/${JOB_NAME}.sta"',
            '"${OUT}/P3SM0_JOB_RECORD.txt"',
        ):
            self.assertLess(pbs.index(token), validate_position)


class AuthorizationTests(unittest.TestCase):
    def test_false_and_consumed_authorization_block(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            path.write_text(json.dumps(authorization()), encoding="utf-8")
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)
            path.write_text(json.dumps(authorization(
                p3sm0_submission_authorized=True, p3sm0_submissions_used=1
            )), encoding="utf-8")
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)

    def test_valid_id_consumes_once_and_invalid_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            initial = authorization(p3sm0_submission_authorized=True)
            path.write_text(json.dumps(initial), encoding="utf-8")
            with self.assertRaises(ValueError):
                consumer.consume(path, "invalid", "a" * 40)
            self.assertEqual(json.loads(path.read_text()), initial)
            result = consumer.consume(path, "1382001.mmaster02", "a" * 40)
            self.assertEqual(result["p3sm0_submissions_used"], 1)
            self.assertFalse(result["p3sm0_submission_authorized"])

    def test_committed_authorization_is_consumed_and_downstream_are_false(self) -> None:
        path = ROOT / "runs/hpc/stage_p/p3sm0_minimal_callback_serial/P3SM0_AUTHORIZATION.json"
        result = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            result["classification"],
            "stage_p3sm0_minimal_callback_serial_submitted",
        )
        self.assertFalse(result["p3sm0_submission_authorized"])
        self.assertEqual(result["maximum_p3sm0_submissions"], 1)
        self.assertEqual(result["p3sm0_submissions_used"], 1)
        self.assertEqual(result["p3sm0_job_id"], "1378099.mmaster02")
        self.assertEqual(
            result["p3sm0_submitted_revision"],
            "572c51eacbf7af79f1ab2ffda93a0ad466fc6eca",
        )
        for key in preflight.REQUIRED_FALSE:
            self.assertFalse(result[key])


class FutureValidatorTests(unittest.TestCase):
    def fixture(self, root: Path) -> None:
        mapping = {
            "P3SB_ENVIRONMENT.txt": "P3SM0_ENVIRONMENT.txt",
            "P3SB_JOB_RECORD.txt": "P3SM0_JOB_RECORD.txt",
            "P3SB_STATE_OUTPUT.csv": "P3SM0_STATE_OUTPUT.csv",
            "P3SB_RF_U.csv": "P3SM0_RF_U.csv",
            "P3SB_ENERGY.csv": "P3SM0_ENERGY.csv",
            "p3sb_baseline.abaqus_stdout.log": "p3sm0_serial.abaqus_stdout.log",
            "p3sb_baseline.sta": "p3sm0_serial.sta",
        }
        for source, target in mapping.items():
            shutil.copyfile(ORIGINAL / source, root / target)
        callback = {
            "counts": {marker: 1 for marker in parser.MARKERS},
            "observed": {marker: True for marker in parser.MARKERS},
            "signal_11_present": False,
        }
        (root / "P3SM0_CALLBACK_SUMMARY.json").write_text(json.dumps(callback), encoding="utf-8")

    def test_pass_marker_is_pass_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            result = validator.validate(
                root, PACKAGE / "P3SM0_serial.inp", PACKAGE / "d2_transfer_table.inc",
                PACKAGE / "p3sm0_minimal_callback.for", "test", 0
            )
            self.assertTrue(result["P3SM0_ok"])
            self.assertTrue((root / "P3SM0_COMPLETION.ok").is_file())
            callback = json.loads((root / "P3SM0_CALLBACK_SUMMARY.json").read_text())
            callback["observed"]["P3SM0_UEXTERNALDB_END"] = False
            (root / "P3SM0_CALLBACK_SUMMARY.json").write_text(json.dumps(callback))
            result = validator.validate(
                root, PACKAGE / "P3SM0_serial.inp", PACKAGE / "d2_transfer_table.inc",
                PACKAGE / "p3sm0_minimal_callback.for", "test", 0
            )
            self.assertFalse(result["P3SM0_ok"])
            self.assertFalse((root / "P3SM0_COMPLETION.ok").exists())


if __name__ == "__main__":
    unittest.main()
