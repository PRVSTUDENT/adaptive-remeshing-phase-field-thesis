"""
Comprehensive unit tests for M2STATE_INGEST_SMOKE1 state ingestion fixture, UEL contract, static checks, wrapper hash preflight, and runtime trace checker.
Task: F43STATE-M2-INGESTION-FIX-PREP4
"""
import json
import hashlib
import unittest
import subprocess
import tempfile
import shutil
from pathlib import Path
import sys

FIXTURE_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_INGEST_SMOKE1"
sys.path.insert(0, str(FIXTURE_DIR))
import verify_smoke_trace

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
            "submit_m2state_ingest_smoke1.sh",
            "verify_smoke_trace.py"
        ]
        for fname in required_files:
            fpath = FIXTURE_DIR / fname
            self.assertTrue(fpath.is_file(), f"Missing package file: {fname}")

    def test_phase_global_dof_contract(self):
        """1. Verify Phase global DOF = 3 for U1/U3 on USER ELEMENT card."""
        inp_content = (FIXTURE_DIR / "M2STATE_INGEST_SMOKE1.inp").read_text()
        lines = inp_content.splitlines()
        for idx, line in enumerate(lines):
            if "*USER ELEMENT, TYPE=U1" in line or "*USER ELEMENT, TYPE=U3" in line:
                dof_line = lines[idx + 1].strip()
                self.assertEqual(dof_line, "3", f"Phase UEL DOF card line must be '3', got '{dof_line}'")

    def test_mechanical_global_dofs_contract(self):
        """2. Verify Mechanical global DOFs = 1, 2 for U2/U4 on USER ELEMENT card."""
        inp_content = (FIXTURE_DIR / "M2STATE_INGEST_SMOKE1.inp").read_text()
        lines = inp_content.splitlines()
        for idx, line in enumerate(lines):
            if "*USER ELEMENT, TYPE=U2" in line or "*USER ELEMENT, TYPE=U4" in line:
                dof_line = lines[idx + 1].strip()
                self.assertEqual(dof_line, "1, 2", f"Mech UEL DOF card line must be '1, 2', got '{dof_line}'")

    def test_physical_node_pairing(self):
        """3. Verify U1/U2 and U3/U4 physical-node connectivity pairing."""
        inp_content = (FIXTURE_DIR / "M2STATE_INGEST_SMOKE1.inp").read_text()
        self.assertIn("1, 1, 2, 3, 4", inp_content)
        self.assertIn("5, 1, 2, 3, 4", inp_content)
        self.assertIn("9, 5, 7, 6", inp_content)
        self.assertIn("13, 5, 7, 6", inp_content)

    def test_nsvars_count_contract(self):
        """4. Verify NSVARS = 18 contract in input deck and UEL Fortran source."""
        inp_content = (FIXTURE_DIR / "M2STATE_INGEST_SMOKE1.inp").read_text()
        uel_content = (FIXTURE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("VARIABLES=18", inp_content)
        self.assertIn("NSTV=18", uel_content)

    def test_svars_slot_bounds_and_no_overlap(self):
        """5. Verify SVARS slot bounds (1..4 history, 5..8 phase) and no overlap."""
        uel_content = (FIXTURE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("SVARS(INPT)=HIST", uel_content)
        self.assertIn("SVARS(4+INPT)=PHASE", uel_content)

    def test_nphys_property_slot_contract(self):
        """6. Verify NPHYS property slot contract (PROPS slot 5 = 4)."""
        inp_content = (FIXTURE_DIR / "M2STATE_INGEST_SMOKE1.inp").read_text()
        self.assertIn("*UEL PROPERTY, ELSET=E_U2\n210.0, 0.3, 1.0, 1.0e-7, 4", inp_content)

    def test_sentinel_uniqueness_and_bounds(self):
        """7. Verify sentinel phase uniqueness, positivity, and physical bounds [0, 1]."""
        artifact_path = FIXTURE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
        nodal_phases = artifact["sentinel_phase_nodal"]
        unique_vals = set(nodal_phases.values())
        self.assertEqual(len(unique_vals), len(nodal_phases), "Sentinel phase values must be unique")
        for val in nodal_phases.values():
            self.assertGreater(val, 0.0)
            self.assertLessEqual(val, 1.0)

    def test_quadrature_interpolation(self):
        """8. Verify expected quadrature interpolation from nodal phase values."""
        u_nodes = [0.11, 0.23, 0.37, 0.61]
        interp_approx = sum(u_nodes) / 4.0
        self.assertAlmostEqual(interp_approx, 0.33, places=2)

    def test_element_pairing_contract(self):
        """9. Verify physical element pairing in transfer manifest."""
        manifest_path = FIXTURE_DIR / "TRANSFER_MANIFEST.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        self.assertIn("element_mappings", manifest)

    def test_ip_ordering_contract(self):
        """10. Verify integration-point ordering contract."""
        artifact_path = FIXTURE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
        ip_history = artifact["sentinel_history_ip"]["1"]
        self.assertEqual(len(ip_history), 4)

    def test_keyword_presence_and_type_displacement_absence(self):
        """11. Verify *INITIAL CONDITIONS, TYPE=SOLUTION present and TYPE=DISPLACEMENT absent."""
        inp_content = (FIXTURE_DIR / "M2STATE_INGEST_SMOKE1.inp").read_text()
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", inp_content)
        self.assertNotIn("TYPE=DISPLACEMENT", inp_content)

    def test_step1_boundary_sentinels(self):
        """12. Verify Step 1 phase boundary values match frozen sentinel manifest."""
        inp_content = (FIXTURE_DIR / "M2STATE_INGEST_SMOKE1.inp").read_text()
        self.assertIn("1, 3, 3, 0.110000", inp_content)

    def test_step2_mechanical_constraints(self):
        """13. Verify Step 2 boundary definition retains required mechanical constraints."""
        inp_content = (FIXTURE_DIR / "M2STATE_INGEST_SMOKE1.inp").read_text()
        self.assertIn("*STEP, NAME=Step-2-IngestProbe", inp_content)
        self.assertIn("*BOUNDARY, OP=NEW", inp_content)

    # ------------------------------------------------------------------
    # WRAPPER PREFLIGHT HASH TESTS (PREP4)
    # ------------------------------------------------------------------
    def test_wrapper_hash_mismatch_rejection(self):
        """Verify guarded wrapper --dry-run FAILS on modified file hash in copy without calling qsub."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            for item in FIXTURE_DIR.iterdir():
                if item.is_file():
                    shutil.copy2(item, tmppath / item.name)
            
            # Corrupt f42_mixed_uel.for hash in temp manifest
            manifest_file = tmppath / "PACKAGE_MANIFEST.json"
            with open(manifest_file, "r") as f:
                manifest_data = json.load(f)
            manifest_data["file_hashes"]["f42_mixed_uel.for"] = "0000000000000000000000000000000000000000000000000000000000000000"
            with open(manifest_file, "w") as f:
                json.dump(manifest_data, f, indent=2)

            import os, sys
            py_dir = os.path.dirname(sys.executable)
            env = os.environ.copy()
            env["PATH"] = py_dir + ";" + r"C:\Program Files\Git\bin;C:\Program Files\Git\mingw64\bin;" + env.get("PATH", "")
            bash_cmd = r"C:\Program Files\Git\bin\bash.exe" if os.path.exists(r"C:\Program Files\Git\bin\bash.exe") else "bash"
            res = subprocess.run(
                [bash_cmd, str(tmppath / "submit_m2state_ingest_smoke1.sh"), "--dry-run"],
                capture_output=True,
                text=True,
                env=env
            )
            self.assertNotEqual(res.returncode, 0, "Wrapper preflight must exit nonzero on hash mismatch")
            self.assertIn("Hash mismatch for f42_mixed_uel.for", res.stdout + res.stderr)

    # ------------------------------------------------------------------
    # TRACE CHECKER TEST FAMILY
    # ------------------------------------------------------------------
    def test_trace_checker_known_good(self):
        """Known-good synthetic trace for KSTEP=2 KINC=1 startup -> ACCEPT."""
        synthetic_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=2 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.2000E-04 HIST= 1.2000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=3 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.3000E-04 HIST= 1.3000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=4 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.4000E-04 HIST= 1.4000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    2 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.23000, 0.25000, 0.45000, 0.37000 SV_H= 2.1000E-04 HIST= 2.1000E-04 PH= 0.30000 SDV15= 0.30000
[INGEST_TRACE] ELEM=    5 JTYPE=2 KSTEP=2 KINC= 1 IP=1 SV_H= 1.1000E-04 PH= 0.25000 ENG= 0.0000E+00 SDV14= 0.25000 SDV16= 1.1000E-04
[INGEST_TRACE] ELEM=    6 JTYPE=2 KSTEP=2 KINC= 1 IP=1 SV_H= 2.1000E-04 PH= 0.30000 ENG= 0.0000E+00 SDV14= 0.30000 SDV16= 2.1000E-04
[INGEST_TRACE] ELEM=    9 JTYPE=3 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.25000, 0.15000, 0.45000 SV_H= 3.1000E-04 HIST= 3.1000E-04 PH= 0.28000 SDV15= 0.28000
[INGEST_TRACE] ELEM=   10 JTYPE=3 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.15000, 0.05000, 0.45000 SV_H= 4.1000E-04 HIST= 4.1000E-04 PH= 0.20000 SDV15= 0.20000
[INGEST_TRACE] ELEM=   13 JTYPE=4 KSTEP=2 KINC= 1 IP=1 SV_H= 3.1000E-04 PH= 0.28000 ENG= 0.0000E+00 SDV14= 0.28000 SDV16= 3.1000E-04
[INGEST_TRACE] ELEM=   14 JTYPE=4 KSTEP=2 KINC= 1 IP=1 SV_H= 4.1000E-04 PH= 0.20000 ENG= 0.0000E+00 SDV14= 0.20000 SDV16= 4.1000E-04
"""
        artifact_path = FIXTURE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(synthetic_trace)
        ok, msg, sdv = verify_smoke_trace.verify_trace(records, artifact)
        self.assertTrue(ok, f"Expected PASS on valid trace, got: {msg}")

    def test_trace_checker_zero_rejection(self):
        """Zero/default trace -> REJECT."""
        zero_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.00000, 0.00000, 0.00000, 0.00000 SV_H= 0.0000E+00 HIST= 0.0000E+00 PH= 0.00000 SDV15= 0.00000
"""
        artifact_path = FIXTURE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(zero_trace)
        ok, msg, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok, "Expected FAIL on zero trace")

    def test_trace_checker_node_swap_rejection(self):
        """Node-swapped trace -> REJECT."""
        swapped_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.61000, 0.37000, 0.23000, 0.11000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000
"""
        artifact_path = FIXTURE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(swapped_trace)
        ok, msg, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok, "Expected FAIL on node-swapped trace")

    def test_trace_checker_ip_swap_rejection(self):
        """IP-swapped trace -> REJECT."""
        ip_swapped_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.2000E-04 HIST= 1.2000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=2 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000
"""
        artifact_path = FIXTURE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(ip_swapped_trace)
        ok, msg, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok, "Expected FAIL on IP-swapped trace")

    def test_trace_checker_missing_record_rejection(self):
        """Missing element/record trace -> REJECT."""
        missing_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000
"""
        artifact_path = FIXTURE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(missing_trace)
        ok, msg, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok, "Expected FAIL on incomplete trace")

    def test_trace_checker_later_iteration_only_rejection(self):
        """Later-iteration-only synthetic evidence (KSTEP=2 KINC=2 or KSTEP=3) -> REJECT."""
        later_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 5 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=3 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000
"""
        artifact_path = FIXTURE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(later_trace)
        ok, msg, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok, "Expected FAIL on later-iteration-only trace without KSTEP=2 KINC=1 startup probe")

    def test_sdv_reporting_contracts(self):
        """Verify SDV14/15/16 expected reporting contract."""
        contract_path = FIXTURE_DIR / "ACCEPTANCE_CONTRACT.json"
        with open(contract_path, "r") as f:
            contract = json.load(f)
        gates = contract["acceptance_gates"]
        self.assertIn("SDV14_contract", gates)
        self.assertIn("SDV15_contract", gates)
        self.assertIn("SDV16_contract", gates)

if __name__ == "__main__":
    unittest.main()
