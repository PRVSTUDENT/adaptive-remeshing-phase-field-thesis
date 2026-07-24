from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/validation"))


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = load("p3sb_validator", "scripts/validation/validate_p3sb_baseline_serial.py")
preflight = load("p3sb_preflight", "scripts/validation/validate_p3sb_submission_preflight.py")
consumer = load("p3sb_consumer", "scripts/validation/consume_p3sb_authorization.py")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def authorization(**updates: object) -> dict[str, object]:
    data: dict[str, object] = {
        "classification": "stage_p3sb_baseline_serial_prepared",
        "p3sb_preparation_complete": True,
        "p3sb_submission_authorized": False,
        "maximum_p3sb_submissions": 1,
        "p3sb_submissions_used": 0,
        "automatic_retry_authorized": False,
        "p3sm_authorized": False,
        "p3t4_authorized": False,
        "mpi_authorized": False,
        "hybrid_authorized": False,
        "p4_authorized": False,
        "production_h1_authorized": False,
        "d3d_a1_reopening_authorized": False,
        "d3e_authorized": False,
    }
    data.update(updates)
    if data.get("p3sb_submission_authorized") is True and "classification" not in updates:
        data["classification"] = "stage_p3sb_baseline_serial_authorized"
    return data


class AuthorizationTests(unittest.TestCase):
    def test_missing_false_and_malformed_authorization_block(self) -> None:
        with self.assertRaises(ValueError):
            preflight.validate_authorization(Path("missing.json"), True)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            path.write_text(json.dumps(authorization()), encoding="utf-8")
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)

    def test_consumed_and_second_submission_block(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            path.write_text(
                json.dumps(authorization(
                    p3sb_submission_authorized=True, p3sb_submissions_used=1
                )),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)

    def test_valid_job_consumes_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            path.write_text(
                json.dumps(authorization(p3sb_submission_authorized=True)),
                encoding="utf-8",
            )
            result = consumer.consume(path, "1381001.mmaster02", "a" * 40)
            self.assertEqual(result["p3sb_submissions_used"], 1)
            self.assertFalse(result["p3sb_submission_authorized"])
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)

    def test_failed_submission_does_not_consume(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            original = authorization(p3sb_submission_authorized=True)
            path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaises(ValueError):
                consumer.consume(path, "invalid", "a" * 40)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), original)

    def test_downstream_authority_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            path.write_text(
                json.dumps(authorization(
                    p3sb_submission_authorized=True, p3sm_authorized=True
                )),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)

    def test_hash_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in (
                "P3SB_baseline_serial.inp", "p3sb_baseline_uel.for",
                "d2_transfer_table.inc",
            ):
                (root / name).write_text("x", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "deck_sha256": "0" * 64,
                "source_sha256": "0" * 64,
                "transfer_sha256": "0" * 64,
                "compute_git_required": False,
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                preflight.validate_manifest(manifest, root)


class StaticLaneTests(unittest.TestCase):
    def test_package_identity_hashes_match_references(self) -> None:
        package = ROOT / "models/parallelization/p3sb_baseline_eight_element_serial"
        manifest = json.loads((package / "P3SB_PACKAGE_MANIFEST.json").read_text())
        pairs = (
            ("deck", package / "P3SB_baseline_serial.inp",
             ROOT / "runs/hpc/stage_p/p3s_serial_diagnostic/raw_failure_evidence/p3s_serial.inp"),
            ("source", package / "p3sb_baseline_uel.for",
             ROOT / "models/state_transfer/d2_tiny_transfer/executable/d2_tiny_transfer_uel.for"),
            ("transfer_table", package / "d2_transfer_table.inc",
             ROOT / "runs/hpc/stage_p/p3s_serial_diagnostic/raw_failure_evidence/P3S_STAGED_TRANSFER_TABLE.inc"),
        )
        for key, candidate, reference in pairs:
            self.assertEqual(candidate.read_bytes(), reference.read_bytes())
            self.assertEqual(
                hashlib.sha256(candidate.read_bytes()).hexdigest(),
                manifest[key]["sha256"],
            )

    def test_committed_authorization_is_false(self) -> None:
        path = ROOT / "runs/hpc/stage_p/p3sb_baseline_serial/P3SB_AUTHORIZATION.json"
        data = preflight.validate_authorization(path, require_submit=False)
        self.assertFalse(data["p3sb_submission_authorized"])
        for key in preflight.REQUIRED_FALSE:
            self.assertFalse(data[key])

    def test_queue_and_resources_are_frozen(self) -> None:
        pbs = (ROOT / "scripts/hpc/stage_p/02_p3sb_baseline_serial.pbs").read_text()
        submitter = (ROOT / "scripts/hpc/stage_p/submit_p3sb_baseline_serial.sh").read_text()
        self.assertIn("#PBS -q entry_imfdfkmq", pbs)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", pbs)
        self.assertIn("#PBS -l walltime=00:30:00", pbs)
        self.assertIn('QUEUE="${QUEUE:-entry_imfdfkmq}"', submitter)
        self.assertIn("cpus=1", pbs)
        self.assertIn("mpi_ranks=1", pbs)
        self.assertIn("omp_threads=1", pbs)
        self.assertIn("OMP_NUM_THREADS=1", pbs)
        self.assertIn("mp_mode=threads", pbs)

    def test_compute_script_has_no_repository_or_wildcard_copy(self) -> None:
        pbs = (ROOT / "scripts/hpc/stage_p/02_p3sb_baseline_serial.pbs").read_text()
        self.assertNotIn("git ", pbs)
        for token in ("*.odb", "*.sim", "*.lck", "core*"):
            self.assertNotIn(token, pbs)

    def test_submitter_uses_notification_wrapper_not_direct_qsub(self) -> None:
        submitter = (ROOT / "scripts/hpc/stage_p/submit_p3sb_baseline_serial.sh").read_text()
        self.assertIn("qsub_with_submitted_notify.sh", submitter)
        self.assertNotIn('JOB_ID="$(qsub ', submitter)

    def test_diagnostic_symbols_absent(self) -> None:
        source = (
            ROOT / "models/parallelization/p3sb_baseline_eight_element_serial/"
            "p3sb_baseline_uel.for"
        ).read_text().upper()
        for token in (
            "UEXTERNALDB", "GETRANK", "GETTHREADID", "MUTEXINIT",
            "MUTEXLOCK", "MUTEXUNLOCK", "KP2TRACE", "KP3READ",
            "KP3BEGINWRITE", "KP3ENDWRITE", "KP2DIAG", "KP3ACCESS",
        ):
            self.assertNotIn(token, source)

    def test_fixed_form_code_stays_within_column_72(self) -> None:
        source = (
            ROOT / "models/parallelization/p3sb_baseline_eight_element_serial/"
            "p3sb_baseline_uel.for"
        ).read_text().splitlines()
        invalid = [
            number
            for number, line in enumerate(source, 1)
            if line and line[0] not in "Cc*!" and len(line) > 72
        ]
        self.assertEqual(invalid, [])


class ValidationTests(unittest.TestCase):
    def fixture(self, root: Path) -> None:
        package = ROOT / "models/parallelization/p3sb_baseline_eight_element_serial"
        (root / "P3SB_ENVIRONMENT.txt").write_text("cpus=1\n", encoding="utf-8")
        (root / "P3SB_JOB_RECORD.txt").write_text(
            "odb_readable=true\n", encoding="utf-8"
        )
        (root / "p3sb_baseline.abaqus_stdout.log").write_text("\n".join([
            "Begin Compiling Abaqus/Standard User Subroutines",
            "End Compiling Abaqus/Standard User Subroutines",
            "Begin Linking Abaqus/Standard User Subroutines",
            "End Linking Abaqus/Standard User Subroutines",
            "Begin Analysis Input File Processor",
            "End Analysis Input File Processor",
        ]), encoding="utf-8")
        (root / "p3sb_baseline.sta").write_text(
            " 1 1 1 1 1 1\nTHE ANALYSIS HAS COMPLETED SUCCESSFULLY\n",
            encoding="utf-8",
        )
        transferred = validator.parse_transfer(package / "d2_transfer_table.inc")
        rows = []
        for physical, history in transferred.items():
            for ip in range(1, 5):
                row = {
                    "visualization_element": physical + 16,
                    "physical_element": physical,
                    "integration_point": ip,
                    "element_type": "CPS4",
                }
                for frame, phase, h_value in (
                    (0, 0.2, history), (1, 0.2, history), (2, 0.3, history + 0.01)
                ):
                    row[f"SDV15_F{frame}"] = phase
                    row[f"SDV16_F{frame}"] = h_value
                rows.append(row)
        write_csv(root / "P3SB_STATE_OUTPUT.csv", list(rows[0]), rows)
        write_csv(
            root / "P3SB_RF_U.csv",
            ["frame", "step", "increment_number", "step_time", "U2", "RF2"],
            [{"frame": "F0", "step": "D2A_INIT", "increment_number": 1,
              "step_time": 1.0, "U2": 0.0, "RF2": 0.0}],
        )
        write_csv(
            root / "P3SB_ENERGY.csv",
            ["frame", "step", "increment_number", "step_time", "ALLIE", "ALLSE", "ALLWK"],
            [{"frame": "F0", "step": "D2A_INIT", "increment_number": 1,
              "step_time": 1.0, "ALLIE": 0.0, "ALLSE": 0.0, "ALLWK": 0.0}],
        )

    def run_case(self, mutation=None):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        self.fixture(root)
        if mutation:
            mutation(root)
        package = ROOT / "models/parallelization/p3sb_baseline_eight_element_serial"
        status = validator.validate(
            root, package / "P3SB_baseline_serial.inp",
            package / "d2_transfer_table.inc", "test", 0
        )
        return temporary, root, status

    def test_pass_creates_marker_and_increment_sequence(self) -> None:
        td, root, status = self.run_case()
        self.addCleanup(td.cleanup)
        self.assertTrue(status["P3SB_ok"])
        self.assertTrue((root / "P3SB_COMPLETION.ok").is_file())
        self.assertTrue((root / "P3SB_INCREMENT_SEQUENCE.json").is_file())
        self.assertEqual(status["expected_integration_points_per_element"], 4)

    def mutate_state(self, root: Path, change) -> None:
        path = root / "P3SB_STATE_OUTPUT.csv"
        rows = read_rows(path)
        change(rows)
        write_csv(path, list(rows[0]), rows)

    def test_missing_element_coverage_fails(self) -> None:
        td, root, status = self.run_case(
            lambda path: self.mutate_state(path, lambda rows: rows.__setitem__(
                slice(None), [row for row in rows if row["physical_element"] != "8"]
            ))
        )
        self.addCleanup(td.cleanup)
        self.assertFalse(status["P3SB_ok"])
        self.assertGreater(status["missing_visualization_elements"], 0)
        self.assertFalse((root / "P3SB_COMPLETION.ok").exists())

    def test_missing_ip_coverage_fails(self) -> None:
        td, _, status = self.run_case(
            lambda path: self.mutate_state(path, lambda rows: rows.pop())
        )
        self.addCleanup(td.cleanup)
        self.assertGreater(status["missing_integration_points"], 0)

    def test_nonfinite_and_phase_bound_fail(self) -> None:
        def change(rows):
            rows[0]["SDV15_F0"] = "nan"
            rows[1]["SDV15_F1"] = "1.1"
        td, _, status = self.run_case(
            lambda path: self.mutate_state(path, change)
        )
        self.addCleanup(td.cleanup)
        self.assertFalse(status["P3SB_ok"])
        self.assertGreater(status["nonfinite_values"], 0)
        self.assertGreater(status["phase_bound_violations"], 0)

    def test_phase_and_history_decrease_fail(self) -> None:
        def change(rows):
            rows[0]["SDV15_F1"] = "0.1"
            rows[1]["SDV16_F1"] = "0.0"
        td, _, status = self.run_case(
            lambda path: self.mutate_state(path, change)
        )
        self.addCleanup(td.cleanup)
        self.assertGreater(status["phase_irreversibility_violations"], 0)
        self.assertGreater(status["history_monotonicity_violations"], 0)

    def test_transfer_mismatch_fails(self) -> None:
        td, _, status = self.run_case(
            lambda path: self.mutate_state(
                path, lambda rows: rows[0].__setitem__("SDV16_F0", "9.0")
            )
        )
        self.addCleanup(td.cleanup)
        self.assertGreater(status["transfer_table_mismatches"], 0)

    def test_missing_rf_or_energy_fails(self) -> None:
        def mutate(path):
            (path / "P3SB_RF_U.csv").unlink()
            write_csv(path / "P3SB_ENERGY.csv", ["ALLIE", "ALLSE", "ALLWK"], [])
        td, _, status = self.run_case(mutate)
        self.addCleanup(td.cleanup)
        self.assertFalse(status["P3SB_ok"])

    def test_empty_increment_sequence_fails(self) -> None:
        td, root, status = self.run_case(
            lambda path: (path / "p3sb_baseline.sta").write_text(
                "THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n", encoding="utf-8"
            )
        )
        self.addCleanup(td.cleanup)
        self.assertEqual(status["increment_records"], 0)
        self.assertFalse((root / "P3SB_COMPLETION.ok").exists())


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
