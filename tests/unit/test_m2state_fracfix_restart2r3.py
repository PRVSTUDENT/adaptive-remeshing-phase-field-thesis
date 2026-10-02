#!/usr/bin/env python3
import os
import sys
import json
import unittest
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
R2R3_DIR = REPO_ROOT / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_FRACFIX_RESTART2R3"
R2R2_DIR = REPO_ROOT / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_FRACFIX_RESTART2R2"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

class TestM2StateFracfixRestart2R3(unittest.TestCase):

    def test_01_package_manifest_byte_integrity(self):
        manifest_path = R2R3_DIR / "PACKAGE_MANIFEST.json"
        self.assertTrue(manifest_path.exists(), "PACKAGE_MANIFEST.json must exist")
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        files = data.get("file_hashes", data.get("files", {}))
        self.assertEqual(len(files), 12, "Must contain exactly 12 package files")
        for fname, exp_hash in files.items():
            fpath = R2R3_DIR / fname
            self.assertTrue(fpath.exists(), f"File {fname} missing from package")
            act_hash = sha256_file(fpath)
            self.assertEqual(act_hash, exp_hash, f"Hash mismatch for {fname}")

    def test_02_scientific_formulation_and_mesh_identity(self):
        r2r3_inp = (R2R3_DIR / "M2STATE_FRACFIX_RESTART2R3.inp").read_text(encoding="utf-8")
        r2r2_inp = (R2R2_DIR / "M2STATE_FRACFIX_RESTART2R2.inp").read_text(encoding="utf-8")
        self.assertEqual(r2r3_inp, r2r2_inp, "R2R3 input deck must be byte-for-byte identical to R2R2")

    def test_03_active_dof_abi_contract(self):
        inp_text = (R2R3_DIR / "M2STATE_FRACFIX_RESTART2R3.inp").read_text(encoding="utf-8")
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM\n3", inp_text)
        self.assertIn("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM\n1, 2", inp_text)
        self.assertIn("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM\n3", inp_text)
        self.assertIn("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM\n1, 2", inp_text)

    def test_04_npredf_zero_and_predef_safety(self):
        fort_code = (R2R3_DIR / "f42_mixed_uel.for").read_text(encoding="utf-8")
        self.assertNotIn("PREDEF(1,1,1) =", fort_code)
        self.assertNotIn("PREDEF(1,KPT,I) =", fort_code)

    def test_05_state_trace_safety(self):
        fort_code = (R2R3_DIR / "f42_mixed_uel.for").read_text(encoding="utf-8")
        self.assertIn("IF (JTYPE.EQ.2 .OR. JTYPE.EQ.4) THEN", fort_code)
        self.assertIn("ELSE IF (JTYPE.EQ.1 .OR. JTYPE.EQ.3) THEN", fort_code)

    def test_06_pbs_module_and_fail_closed_toolchain(self):
        pbs_text = (R2R3_DIR / "M2STATE_FRACFIX_RESTART2R3.pbs").read_text(encoding="utf-8")
        self.assertIn("module load gcc/11.4.0", pbs_text)
        self.assertIn("module load intel/2024.2.0", pbs_text)
        self.assertIn("module load abaqus/2023", pbs_text)
        self.assertIn("module load python/gcc/11.4.0/3.11.7", pbs_text)
        self.assertIn("command -v ifort", pbs_text)
        self.assertIn("ifort --version", pbs_text)
        self.assertIn("command -v abaqus", pbs_text)
        self.assertIn("abaqus information=release", pbs_text)
        self.assertIn("python3 validate_package_manifest.py", pbs_text)
        self.assertNotIn("|| module load abaqus/2023", pbs_text)

    def test_07_job_1389063_environment_regression(self):
        r2r2_pbs = (R2R2_DIR / "M2STATE_FRACFIX_RESTART2R2.pbs").read_text(encoding="utf-8")
        self.assertNotIn("module load intel/2024.2.0", r2r2_pbs, "R2R2 PBS lacked Intel module")
        self.assertNotIn("command -v ifort", r2r2_pbs, "R2R2 PBS lacked pre-Abaqus compiler verification")

        r2r3_pbs = (R2R3_DIR / "M2STATE_FRACFIX_RESTART2R3.pbs").read_text(encoding="utf-8")
        self.assertIn("module load intel/2024.2.0", r2r3_pbs, "R2R3 PBS must include Intel module")
        self.assertIn("command -v ifort", r2r3_pbs, "R2R3 PBS must verify ifort exists")

    def test_08_pbs_resource_and_notification_contract(self):
        pbs_text = (R2R3_DIR / "M2STATE_FRACFIX_RESTART2R3.pbs").read_text(encoding="utf-8")
        self.assertIn("#PBS -N M2STATE_FRACFIX_RESTART2R3", pbs_text)
        self.assertIn("#PBS -l select=1:ncpus=1:mpiprocs=1:mem=16gb", pbs_text)
        self.assertIn("#PBS -l walltime=24:00:00", pbs_text)
        self.assertIn("#PBS -q entry_imfdfkmq", pbs_text)
        self.assertIn("#PBS -m abe", pbs_text)
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs_text)
        self.assertIn("notification_install_terminal_trap", pbs_text)
        self.assertIn("notify_start", pbs_text)

    def test_09_guarded_wrapper_contract(self):
        wrapper_text = (R2R3_DIR / "submit_m2state_fracfix_restart2r3.sh").read_text(encoding="utf-8")
        self.assertIn("--dry-run", wrapper_text)
        self.assertIn("--execute", wrapper_text)
        self.assertIn("qsub M2STATE_FRACFIX_RESTART2R3.pbs", wrapper_text)
        self.assertIn("validate_package_manifest.py", wrapper_text)

    def test_10_scientific_checker_hardening(self):
        checker_text = (R2R3_DIR / "verify_restart2r3_science.py").read_text(encoding="utf-8")
        self.assertIn("verify_inp_abi", checker_text)
        self.assertIn("NaN", checker_text)
        self.assertIn("Inf", checker_text)

if __name__ == "__main__":
    unittest.main()
