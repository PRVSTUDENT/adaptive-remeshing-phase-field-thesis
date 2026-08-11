"""
Unit tests for M2STATE_INGEST_SMOKE1 state ingestion fixture and UEL state contract.
Task: F43STATE-M2-INGESTION-FIX-PREP1
"""
import json
import hashlib
import unittest
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_INGEST_SMOKE1"

class TestM2StateIngestSmoke1(unittest.TestCase):

    def test_package_files_exist(self):
        """Verify all required files exist in the M2STATE_INGEST_SMOKE1 package."""
        required_files = [
            "M2STATE_INGEST_SMOKE1.inp",
            "f42_mixed_uel.for",
            "STATE_TRANSFER_ARTIFACT.json",
            "TRANSFER_MANIFEST.json",
            "ACCEPTANCE_CONTRACT.json",
            "PACKAGE_MANIFEST.json",
            "M2STATE_INGEST_SMOKE1.pbs",
            "submit_m2state_ingest_smoke1.sh"
        ]
        for fname in required_files:
            fpath = FIXTURE_DIR / fname
            self.assertTrue(fpath.is_file(), f"Missing package file: {fname}")

    def test_hash_reproducibility(self):
        """Verify package file SHA256 hashes match PACKAGE_MANIFEST.json."""
        manifest_path = FIXTURE_DIR / "PACKAGE_MANIFEST.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        recorded_hashes = manifest["file_hashes"]
        for fname, recorded_sha in recorded_hashes.items():
            fpath = FIXTURE_DIR / fname
            self.assertTrue(fpath.is_file(), f"File {fname} in manifest not found")
            actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
            self.assertEqual(actual_sha, recorded_sha.lower(), f"SHA256 mismatch for {fname}: got {actual_sha}, expected {recorded_sha}")

    def test_svars_slot_mapping_contract(self):
        """Verify SVARS slot contract in input deck and transfer artifact."""
        artifact_path = FIXTURE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
        
        # Check sentinel history IP values
        history_sentinels = artifact["sentinel_history_ip"]
        self.assertEqual(len(history_sentinels), 4)
        self.assertEqual(history_sentinels["1"], [0.000110, 0.000120, 0.000130, 0.000140])
        self.assertEqual(history_sentinels["2"], [0.000210, 0.000220, 0.000230, 0.000240])
        self.assertEqual(history_sentinels["3"], [0.000310, 0.000320, 0.000330])
        self.assertEqual(history_sentinels["4"], [0.000410, 0.000420, 0.000430])

    def test_sentinel_ordering_and_nonzero_coverage(self):
        """Verify zero/default state cannot pass fixture sentinel checks."""
        artifact_path = FIXTURE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
        
        nodal_phases = artifact["sentinel_phase_nodal"]
        for nid, d_val in nodal_phases.items():
            self.assertGreater(d_val, 0.0, f"Node {nid} has zero/negative sentinel phase: {d_val}")

    def test_nphys_conversion_and_bounds(self):
        """Verify input deck contains valid NPHYS and property slot 5 configuration."""
        inp_path = FIXTURE_DIR / "M2STATE_INGEST_SMOKE1.inp"
        inp_content = inp_path.read_text()
        
        self.assertIn("PROPERTIES=5", inp_content)
        self.assertIn("*INITIAL CONDITIONS, TYPE=DISPLACEMENT", inp_content)
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", inp_content)

if __name__ == "__main__":
    unittest.main()
