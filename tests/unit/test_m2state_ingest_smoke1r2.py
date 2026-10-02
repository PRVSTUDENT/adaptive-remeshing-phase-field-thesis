#!/usr/bin/env python3
"""
Unit Test Suite for M2STATE_INGEST_SMOKE1R2 Execution Package

Verifies:
1. All package files exist and match PACKAGE_MANIFEST.json SHA256 hashes.
2. Scientific files are 100% byte-identical to PREP4 / R1 qualified sources.
3. Abaqus 2023 *USER ELEMENT keyword parser rejects IPERIODIC and unknown parameters.
4. Comprehensive qualification of user element keywords and ingestion contract suite.
"""

import unittest
import os
import json
import hashlib
import re

PACKAGE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../models/generated/mode_ii/production_state_transfer_batch/M2STATE_INGEST_SMOKE1R2")
)

SUPPORTED_USER_ELEMENT_PARAMS = {"TYPE", "NODES", "INTEGRATION", "PROPERTIES", "I PROPERTIES", "COORDINATES", "VARIABLES", "UNSYMM", "LINEAR", "FILE"}

def validate_user_element_deck(inp_text):
    """
    Parses *USER ELEMENT cards in an input deck and validates keywords.
    Returns (valid: bool, reason: str).
    """
    lines = inp_text.splitlines()
    has_phase_dof = False
    for i, line in enumerate(lines):
        if line.strip().upper().startswith("*USER ELEMENT"):
            parts = line.split(",")[1:]
            seen_params = set()
            for part in parts:
                if "=" in part:
                    p_name = part.split("=")[0].strip().upper()
                else:
                    p_name = part.strip().upper()
                if not p_name:
                    continue
                if p_name not in SUPPORTED_USER_ELEMENT_PARAMS:
                    return False, f"Unsupported parameter '{p_name}' on line {i+1}"
                seen_params.add(p_name)
            
            if "TYPE" not in seen_params:
                return False, f"Missing TYPE parameter on line {i+1}"
            if "NODES" not in seen_params:
                return False, f"Missing NODES parameter on line {i+1}"

            # Check next line for DOFs
            if i + 1 < len(lines):
                dof_line = lines[i+1].strip()
                if dof_line.startswith("*"):
                    return False, f"Missing DOF specification line after *USER ELEMENT on line {i+1}"
                dofs = [int(x.strip()) for x in dof_line.split(",") if x.strip().isdigit()]
                if 3 in dofs:
                    has_phase_dof = True
    
    if not has_phase_dof:
        return False, "Wrong phase dof definition: No element contains DOF 3"
    return True, "PASS"

class TestM2StateIngestSmoke1R2(unittest.TestCase):

    def test_01_package_manifest_hashes(self):
        manifest_path = os.path.join(PACKAGE_DIR, "PACKAGE_MANIFEST.json")
        self.assertTrue(os.path.exists(manifest_path), "PACKAGE_MANIFEST.json missing")
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        for filename, expected_hash in manifest.items():
            filepath = os.path.join(PACKAGE_DIR, filename)
            self.assertTrue(os.path.exists(filepath), f"File {filename} missing in package")
            with open(filepath, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(actual_hash.lower(), expected_hash.lower(), f"Hash mismatch for {filename}")

    def test_02_prep4_scientific_bytes_identity(self):
        # Scientific files must remain 100% byte-identical to PREP4
        expected_hashes = {
            "f42_mixed_uel.for": "96a6b0addf92719716d3f4dae6f1762ea1aec5e32cc526296380546c49dc33e5",
            "STATE_TRANSFER_ARTIFACT.json": "567b71515afb278849fbcecc263f1df8b871e4ea18d6c5fae669694a7a199ba0",
            "TRANSFER_MANIFEST.json": "fac7c0ebbbd9bafe4ca8b5940b11f647c60ddf02786918a11f3db55d15b5d173",
            "ACCEPTANCE_CONTRACT.json": "93b121a56ec63704a43e55db8ac9849de59ae7bd3724745d038382494856c43f",
            "verify_smoke_trace.py": "6f8d5228f69f8b781bef12fd320a7df72b5f3d6c689893ba906a66f0bafcadfe",
        }
        for fname, expected in expected_hashes.items():
            fpath = os.path.join(PACKAGE_DIR, fname)
            with open(fpath, "rb") as f:
                actual = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(actual.lower(), expected.lower(), f"Scientific file {fname} altered!")

    def test_03_inp_deck_user_element_keywords(self):
        inp_path = os.path.join(PACKAGE_DIR, "M2STATE_INGEST_SMOKE1R2.inp")
        with open(inp_path, "r") as f:
            content = f.read()
        
        valid, reason = validate_user_element_deck(content)
        self.assertTrue(valid, f"R2 input deck keyword validation failed: {reason}")
        self.assertNotIn("IPERIODIC", content.upper(), "IPERIODIC must not be present in R2 input deck")

    def test_04_user_element_keyword_preflight_rejections(self):
        valid_deck = "*USER ELEMENT, TYPE=U1, NODES=4, INTEGRATION=4, PROPERTIES=3, COORDINATES=2, VARIABLES=18\n1, 2, 3"
        v, r = validate_user_element_deck(valid_deck)
        self.assertTrue(v)

        # Rejection: IPERIODIC
        deck_iperiodic = "*USER ELEMENT, TYPE=U1, NODES=4, IPERIODIC=0, PROPERTIES=3\n1, 2, 3"
        v, r = validate_user_element_deck(deck_iperiodic)
        self.assertFalse(v)
        self.assertIn("IPERIODIC", r)

        # Rejection: Unknown parameter FOOBAR
        deck_unknown = "*USER ELEMENT, TYPE=U1, NODES=4, FOOBAR=1\n1, 2, 3"
        v, r = validate_user_element_deck(deck_unknown)
        self.assertFalse(v)
        self.assertIn("FOOBAR", r)

        # Rejection: missing TYPE
        deck_notype = "*USER ELEMENT, NODES=4, PROPERTIES=3\n1, 2, 3"
        v, r = validate_user_element_deck(deck_notype)
        self.assertFalse(v)
        self.assertIn("Missing TYPE", r)

        # Rejection: missing NODES
        deck_nonodes = "*USER ELEMENT, TYPE=U1, PROPERTIES=3\n1, 2, 3"
        v, r = validate_user_element_deck(deck_nonodes)
        self.assertFalse(v)
        self.assertIn("Missing NODES", r)

        # Rejection: wrong phase DOF
        deck_wrongdof = "*USER ELEMENT, TYPE=U1, NODES=4, PROPERTIES=3\n1, 2"
        v, r = validate_user_element_deck(deck_wrongdof)
        self.assertFalse(v)
        self.assertIn("wrong phase dof", r.lower())

    def test_05_pbs_and_wrapper_declarations(self):
        pbs_path = os.path.join(PACKAGE_DIR, "M2STATE_INGEST_SMOKE1R2.pbs")
        with open(pbs_path, "r") as f:
            pbs_text = f.read()
        self.assertIn("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023", pbs_text)
        self.assertIn("M2STATE_INGEST_SMOKE1R2", pbs_text)

        wrapper_path = os.path.join(PACKAGE_DIR, "submit_m2state_ingest_smoke1r2.sh")
        with open(wrapper_path, "r") as f:
            wrap_text = f.read()
        self.assertIn("M2STATE_INGEST_SMOKE1R2", wrap_text)
        self.assertIn("check_license_gate.py", wrap_text)

if __name__ == "__main__":
    unittest.main()
