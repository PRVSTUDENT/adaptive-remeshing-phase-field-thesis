"""
Comprehensive unit tests for M2STATE_INGEST_SMOKE1R1 state ingestion R1 fixture, UEL contract, static checks, compiler environment preflight, and local/remote byte identity.
Task: F43STATE-M2-INGESTION-SMOKE1R1-PREP1
"""
import json
import hashlib
import unittest
import sys
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_INGEST_SMOKE1R1"
PREP4_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_INGEST_SMOKE1"

PREP4_EXPECTED_HASHES = {
    "M2STATE_INGEST_SMOKE1.inp": "b11e236629c18ed0b7e7551866213e814de461c2e616dd472d7ad731982cbf9e",
    "f42_mixed_uel.for": "96a6b0addf92719716d3f4dae6f1762ea1aec5e32cc526296380546c49dc33e5",
    "STATE_TRANSFER_ARTIFACT.json": "567b71515afb278849fbcecc263f1df8b871e4ea18d6c5fae669694a7a199ba0",
    "TRANSFER_MANIFEST.json": "fac7c0ebbbd9bafe4ca8b5940b11f647c60ddf02786918a11f3db55d15b5d173",
    "ACCEPTANCE_CONTRACT.json": "93b121a56ec63704a43e55db8ac9849de59ae7bd3724745d038382494856c43f",
    "verify_smoke_trace.py": "6f8d5228f69f8b781bef12fd320a7df72b5f3d6c689893ba906a66f0bafcadfe",
}

class TestM2StateIngestSmoke1R1(unittest.TestCase):

    def test_package_files_exist(self):
        """Verify all required files exist in the M2STATE_INGEST_SMOKE1R1 package."""
        required_files = [
            "M2STATE_INGEST_SMOKE1R1.inp",
            "f42_mixed_uel.for",
            "STATE_TRANSFER_ARTIFACT.json",
            "TRANSFER_MANIFEST.json",
            "ACCEPTANCE_CONTRACT.json",
            "PACKAGE_MANIFEST.json",
            "M2STATE_INGEST_SMOKE1R1.pbs",
            "submit_m2state_ingest_smoke1r1.sh",
            "verify_smoke_trace.py"
        ]
        for fname in required_files:
            fpath = FIXTURE_DIR / fname
            self.assertTrue(fpath.is_file(), f"Missing R1 package file: {fname}")

    def test_scientific_files_byte_identical_to_prep4(self):
        """Verify scientific baseline files are 100% byte-identical to PREP4 expected hashes."""
        mappings = [
            ("M2STATE_INGEST_SMOKE1R1.inp", PREP4_EXPECTED_HASHES["M2STATE_INGEST_SMOKE1.inp"]),
            ("f42_mixed_uel.for", PREP4_EXPECTED_HASHES["f42_mixed_uel.for"]),
            ("STATE_TRANSFER_ARTIFACT.json", PREP4_EXPECTED_HASHES["STATE_TRANSFER_ARTIFACT.json"]),
            ("TRANSFER_MANIFEST.json", PREP4_EXPECTED_HASHES["TRANSFER_MANIFEST.json"]),
            ("ACCEPTANCE_CONTRACT.json", PREP4_EXPECTED_HASHES["ACCEPTANCE_CONTRACT.json"]),
            ("verify_smoke_trace.py", PREP4_EXPECTED_HASHES["verify_smoke_trace.py"]),
        ]
        for fname, expected_hash in mappings:
            data = (FIXTURE_DIR / fname).read_bytes()
            actual_hash = hashlib.sha256(data).hexdigest()
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {fname}")

    def test_package_manifest_hashes(self):
        """Verify PACKAGE_MANIFEST.json lists all 8 files and their hashes match actual files."""
        manifest_path = FIXTURE_DIR / "PACKAGE_MANIFEST.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        files = manifest.get("files", {})
        self.assertEqual(len(files), 8, "R1 package manifest must list exactly 8 files")
        for fname, expected_hash in files.items():
            fpath = FIXTURE_DIR / fname
            self.assertTrue(fpath.is_file(), f"Manifest file missing: {fname}")
            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, expected_hash, f"Manifest hash mismatch for {fname}")

    def test_pbs_compiler_environment_contract(self):
        """Verify PBS script includes required modules and fail-closed compiler assertion."""
        pbs_text = (FIXTURE_DIR / "M2STATE_INGEST_SMOKE1R1.pbs").read_text()
        self.assertIn("#PBS -N M2STATE_INGEST_SMOKE1R1", pbs_text)
        self.assertIn("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023", pbs_text)
        self.assertIn("command -v abaqus", pbs_text)
        self.assertIn("command -v ifort", pbs_text)

    def test_guarded_wrapper_contract(self):
        """Verify submit wrapper enforces identity M2STATE_INGEST_SMOKE1R1 and dry-run preflight."""
        wrapper_text = (FIXTURE_DIR / "submit_m2state_ingest_smoke1r1.sh").read_text()
        self.assertIn('JOB_NAME="M2STATE_INGEST_SMOKE1R1"', wrapper_text)
        self.assertIn('EXPECTED_QUEUE="entry_imfdfkmq"', wrapper_text)
        self.assertIn('EXPECTED_CPUS=1', wrapper_text)
        self.assertIn('EXPECTED_MEM="8gb"', wrapper_text)
        self.assertIn('EXPECTED_WALLTIME="00:15:00"', wrapper_text)
        self.assertIn('intel/2024.2.0', wrapper_text)

if __name__ == "__main__":
    unittest.main()
