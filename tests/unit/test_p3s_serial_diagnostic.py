from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = load_module("p3s_validator", "scripts/validation/validate_p3s_serial_diagnostic.py")
preflight = load_module("p3s_preflight", "scripts/validation/validate_p3s_submission_preflight.py")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def authorization(**updates: object) -> dict[str, object]:
    data: dict[str, object] = {
        "classification": "stage_p3_serial_diagnostic_prepared",
        "p3s_preparation_complete": True,
        "p3s_submission_authorized": False,
        "maximum_p3s_submissions": 1,
        "p3s_submissions_used": 0,
        "automatic_retry_authorized": False,
        "p3t4_authorized": False,
        "mpi_authorized": False,
        "hybrid_authorized": False,
        "production_h1_authorized": False,
        "d3d_a1_reopening_authorized": False,
        "d3e_authorized": False,
    }
    data.update(updates)
    return data


class PreflightTests(unittest.TestCase):
    def test_missing_authorization_blocks(self) -> None:
        with self.assertRaises(ValueError):
            preflight.validate_authorization(Path("missing.json"), True)

    def test_false_authorization_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            path.write_text(json.dumps(authorization()), encoding="utf-8")
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)

    def test_malformed_authorization_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)

    def test_second_submission_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            path.write_text(
                json.dumps(authorization(p3s_submission_authorized=True, p3s_submissions_used=1)),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)

    def test_missing_hash_and_hash_mismatch_block(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("P3S_serial_diagnostic.inp", "p3_instrumented_commonblock.for", "d2_transfer_table.inc"):
                (root / name).write_text("x", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"compute_git_required": False}), encoding="utf-8")
            with self.assertRaises(ValueError):
                preflight.validate_manifest(manifest, root)
            manifest.write_text(
                json.dumps(
                    {
                        "deck_sha256": "0" * 64,
                        "source_sha256": "0" * 64,
                        "transfer_sha256": "0" * 64,
                        "compute_git_required": False,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                preflight.validate_manifest(manifest, root)

    def test_downstream_authorizations_remain_false(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "auth.json"
            path.write_text(
                json.dumps(authorization(p3s_submission_authorized=True, p3t4_authorized=True)),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                preflight.validate_authorization(path, True)

    def test_pbs_has_no_git_or_odb_wildcard(self) -> None:
        pbs = (ROOT / "scripts/hpc/stage_p/01_p3s_serial_diagnostic.pbs").read_text(encoding="utf-8")
        self.assertNotIn("git ", pbs)
        self.assertNotIn("*.odb", pbs)
        self.assertNotIn("*.sim", pbs)
        self.assertNotIn("*.lck", pbs)


class DiagnosticGateTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> None:
        (root / "P3S_ENVIRONMENT.txt").write_text("rank=0\nthread=0\n", encoding="utf-8")
        (root / "P3S_JOB_RECORD.txt").write_text("job_id=test\n", encoding="utf-8")
        stdout = "\n".join(
            [
                "Begin Compiling Abaqus/Standard User Subroutines",
                "End Compiling Abaqus/Standard User Subroutines",
                "Begin Linking Abaqus/Standard User Subroutines",
                "End Linking Abaqus/Standard User Subroutines",
                "Begin Analysis Input File Processor",
                "End Analysis Input File Processor",
            ]
        )
        (root / "p3s_serial.abaqus_stdout.log").write_text(stdout, encoding="utf-8")
        (root / "p3s_serial.sta").write_text(
            " 1 1 1 1 1 1\nTHE ANALYSIS HAS COMPLETED SUCCESSFULLY\n", encoding="utf-8"
        )
        summary = {
            "callbacks": {"UEXTERNALDB": True, "UEL": True, "UMAT": True},
            "ranks": [0],
            "threads": [0],
            "conflicting_shared_writes": 0,
        }
        (root / "P3S_SHARED_ACCESS_SUMMARY.json").write_text(json.dumps(summary), encoding="utf-8")
        events = []
        for index in range(1, 9):
            for var_id, op_id in ((1, 1), (1, 2), (2, 1), (2, 2), (4, 2)):
                events.append(
                    {
                        "event": "shared_access",
                        "variable_id": var_id,
                        "operation_id": op_id,
                        "routine_id": 1,
                        "shared_index": index,
                        "rank": 0,
                        "thread": 0,
                        "step": 1,
                        "increment": 1,
                        "initialization": 1 if var_id == 4 else 0,
                    }
                )
        fields = list(events[0])
        write_csv(root / "P3S_CALLBACK_EVENTS.csv", fields, events)
        state = []
        for element in range(1, 9):
            state.append(
                {
                    "element": element,
                    "integration_point": 1,
                    **{f"SDV15_F{i}": 0.2 for i in range(4)},
                    **{f"SDV16_F{i}": 0.3 for i in range(4)},
                }
            )
        write_csv(root / "P3S_STATE_OUTPUT.csv", list(state[0]), state)
        write_csv(root / "P3S_RF_U.csv", ["U2", "RF2"], [{"U2": 0.0, "RF2": 0.0}])
        write_csv(
            root / "P3S_ENERGY.csv",
            ["ALLIE", "ALLSE", "ALLWK"],
            [{"ALLIE": 0.0, "ALLSE": 0.0, "ALLWK": 0.0}],
        )

    def run_mutation(self, mutate=None):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        self.make_fixture(root)
        if mutate:
            mutate(root)
        status = validator.validate(root, "test", 0)
        return td, root, status

    def test_pass_creates_marker_only_for_pass(self) -> None:
        td, root, status = self.run_mutation()
        self.addCleanup(td.cleanup)
        self.assertTrue(status["P3S_ok"])
        self.assertTrue((root / "P3S_COMPLETION.ok").is_file())
        self.assertTrue((root / "P3S_INCREMENT_SEQUENCE.json").is_file())

    def test_duplicate_event_and_conflict_fail(self) -> None:
        def mutate(root: Path) -> None:
            with (root / "P3S_CALLBACK_EVENTS.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows.append(dict(rows[0]))
            rows.append({**rows[0], "event": "conflict"})
            write_csv(root / "P3S_CALLBACK_EVENTS.csv", list(rows[0]), rows)

        td, root, status = self.run_mutation(mutate)
        self.addCleanup(td.cleanup)
        self.assertFalse(status["P3S_ok"])
        self.assertEqual(status["classification"], "stage_p3_serial_diagnostic_conflict_detected")
        self.assertFalse((root / "P3S_COMPLETION.ok").exists())

    def test_missing_element_and_ip_coverage_fail(self) -> None:
        def mutate(root: Path) -> None:
            with (root / "P3S_STATE_OUTPUT.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows.pop()
            rows[0]["integration_point"] = "2"
            write_csv(root / "P3S_STATE_OUTPUT.csv", list(rows[0]), rows)

        td, _, status = self.run_mutation(mutate)
        self.addCleanup(td.cleanup)
        self.assertFalse(status["P3S_ok"])

    def test_unexpected_rank_and_thread_fail(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "P3S_SHARED_ACCESS_SUMMARY.json"
            data = json.loads(path.read_text())
            data["ranks"] = [0, 1]
            data["threads"] = [0, 3]
            path.write_text(json.dumps(data))

        td, _, status = self.run_mutation(mutate)
        self.addCleanup(td.cleanup)
        self.assertFalse(status["P3S_ok"])
        self.assertGreater(status["unexpected_mpi_ranks"], 0)
        self.assertGreater(status["unexpected_thread_ids"], 0)

    def test_nonfinite_phase_bound_and_history_decrease_fail(self) -> None:
        def mutate(root: Path) -> None:
            with (root / "P3S_STATE_OUTPUT.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["SDV15_F0"] = "nan"
            rows[1]["SDV15_F1"] = "1.1"
            rows[2]["SDV16_F0"] = "0.4"
            rows[2]["SDV16_F1"] = "0.3"
            write_csv(root / "P3S_STATE_OUTPUT.csv", list(rows[0]), rows)

        td, _, status = self.run_mutation(mutate)
        self.addCleanup(td.cleanup)
        self.assertFalse(status["P3S_ok"])
        self.assertGreater(status["nonfinite_state_records"], 0)
        self.assertGreater(status["phase_bound_violations"], 0)
        self.assertGreater(status["history_decreases"], 0)


if __name__ == "__main__":
    unittest.main()
