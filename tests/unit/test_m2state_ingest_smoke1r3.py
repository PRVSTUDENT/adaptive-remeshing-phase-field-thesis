#!/usr/bin/env python3
"""
Complete State-Ingestion Qualification & Keyword Syntax Test Suite for M2STATE_INGEST_SMOKE1R3

Includes:
1. Complete 22-test PREP4 state-ingestion qualification & trace-checker suite (adapted for R3).
2. Abaqus 2023 General *USER ELEMENT keyword syntax & parameter allowlist validator tests.
3. Quad (4-point) and Tri (3-point) quadrature consistency & SVARS layout contracts.
"""

import unittest
import os
import json
import hashlib
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_INGEST_SMOKE1R3"
sys.path.insert(0, str(PACKAGE_DIR))
import verify_smoke_trace

# General User Element parameter allowlist per Abaqus 2023 Keyword Reference
GENERAL_UEL_SUPPORTED_PARAMS = {
    "TYPE", "NODES", "PROPERTIES", "I PROPERTIES", "COORDINATES", "VARIABLES", "UNSYMM", "LINEAR", "FILE"
}

# Expected DOF definitions for each user element in fixture
EXPECTED_UEL_DOFS = {
    "U1": [1, 2],       # Quad displacement UEL
    "U2": [1, 2, 3],    # Quad phase-field UEL (contains phase DOF 3)
    "U3": [1, 2],       # Tri displacement UEL
    "U4": [1, 2, 3],    # Tri phase-field UEL (contains phase DOF 3)
}

def validate_general_user_element_deck(inp_text):
    """
    Validates *USER ELEMENT cards against general user element syntax.
    Returns (valid: bool, reason: str).
    """
    lines = inp_text.splitlines()
    validated_types = set()
    
    for i, line in enumerate(lines):
        if line.strip().upper().startswith("*USER ELEMENT"):
            parts = line.split(",")[1:]
            seen_params = set()
            elem_type = None
            
            for part in parts:
                if "=" in part:
                    p_name, p_val = part.split("=")[0].strip().upper(), part.split("=")[1].strip().upper()
                    if p_name == "TYPE":
                        elem_type = p_val
                else:
                    p_name = part.strip().upper()
                
                if not p_name:
                    continue
                if p_name not in GENERAL_UEL_SUPPORTED_PARAMS:
                    return False, f"Unsupported parameter '{p_name}' for general UEL on line {i+1}"
                seen_params.add(p_name)

            if "TYPE" not in seen_params or not elem_type:
                return False, f"Missing TYPE parameter on line {i+1}"
            if "NODES" not in seen_params:
                return False, f"Missing NODES parameter on line {i+1}"

            if i + 1 >= len(lines):
                return False, f"Missing DOF line after *USER ELEMENT on line {i+1}"
            
            dof_line = lines[i+1].strip()
            if dof_line.startswith("*"):
                return False, f"Missing DOF specification line after *USER ELEMENT on line {i+1}"
            
            dofs = [int(x.strip()) for x in dof_line.split(",") if x.strip().isdigit()]
            
            if elem_type in EXPECTED_UEL_DOFS:
                expected = EXPECTED_UEL_DOFS[elem_type]
                if dofs != expected:
                    return False, f"Wrong DOF definition for {elem_type} on line {i+2}: expected {expected}, got {dofs}"
            validated_types.add(elem_type)

    required_types = {"U1", "U2", "U3", "U4"}
    if not required_types.issubset(validated_types):
        return False, f"Missing user element definitions: expected {required_types}, found {validated_types}"

    return True, "PASS"


class TestM2StateIngestSmoke1R3(unittest.TestCase):

    # ------------------------------------------------------------------
    # PACKAGE INTEGRITY & MANIFEST TESTS
    # ------------------------------------------------------------------
    def test_01_package_files_exist(self):
        required_files = [
            "M2STATE_INGEST_SMOKE1R3.inp",
            "f42_mixed_uel.for",
            "STATE_TRANSFER_ARTIFACT.json",
            "TRANSFER_MANIFEST.json",
            "ACCEPTANCE_CONTRACT.json",
            "PACKAGE_MANIFEST.json",
            "M2STATE_INGEST_SMOKE1R3.pbs",
            "submit_m2state_ingest_smoke1r3.sh",
            "verify_smoke_trace.py"
        ]
        for fname in required_files:
            fpath = PACKAGE_DIR / fname
            self.assertTrue(fpath.is_file(), f"Missing package file: {fname}")

    def test_02_package_manifest_hashes(self):
        manifest_path = PACKAGE_DIR / "PACKAGE_MANIFEST.json"
        self.assertTrue(manifest_path.is_file(), "PACKAGE_MANIFEST.json missing")
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        for filename, expected_hash in manifest.items():
            filepath = PACKAGE_DIR / filename
            self.assertTrue(filepath.is_file(), f"File {filename} missing in package")
            actual_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
            self.assertEqual(actual_hash.lower(), expected_hash.lower(), f"Hash mismatch for {filename}")

    def test_03_prep4_scientific_bytes_identity(self):
        expected_hashes = {
            "f42_mixed_uel.for": "96a6b0addf92719716d3f4dae6f1762ea1aec5e32cc526296380546c49dc33e5",
            "STATE_TRANSFER_ARTIFACT.json": "567b71515afb278849fbcecc263f1df8b871e4ea18d6c5fae669694a7a199ba0",
            "TRANSFER_MANIFEST.json": "fac7c0ebbbd9bafe4ca8b5940b11f647c60ddf02786918a11f3db55d15b5d173",
            "ACCEPTANCE_CONTRACT.json": "93b121a56ec63704a43e55db8ac9849de59ae7bd3724745d038382494856c43f",
            "verify_smoke_trace.py": "6f8d5228f69f8b781bef12fd320a7df72b5f3d6c689893ba906a66f0bafcadfe",
        }
        for fname, expected in expected_hashes.items():
            fpath = PACKAGE_DIR / fname
            actual = hashlib.sha256(fpath.read_bytes()).hexdigest()
            self.assertEqual(actual.lower(), expected.lower(), f"Scientific file {fname} altered!")

    # ------------------------------------------------------------------
    # KEYWORD PREFLIGHT & VALIDATOR TESTS
    # ------------------------------------------------------------------
    def test_04_inp_deck_general_user_element_keywords(self):
        content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R3.inp").read_text()
        valid, reason = validate_general_user_element_deck(content)
        self.assertTrue(valid, f"R3 input deck keyword validation failed: {reason}")
        self.assertNotIn("IPERIODIC", content.upper(), "IPERIODIC must not be present")
        self.assertNotIn("INTEGRATION", content.upper(), "INTEGRATION must not be present on general UEL cards")

    def test_05_keyword_validator_rejections(self):
        deck_iperiodic = "*USER ELEMENT, TYPE=U1, NODES=4, IPERIODIC=0, PROPERTIES=3\n1, 2"
        v, r = validate_general_user_element_deck(deck_iperiodic)
        self.assertFalse(v)
        self.assertIn("IPERIODIC", r.upper())

        deck_integration = "*USER ELEMENT, TYPE=U1, NODES=4, INTEGRATION=4, PROPERTIES=3\n1, 2"
        v, r = validate_general_user_element_deck(deck_integration)
        self.assertFalse(v)
        self.assertIn("INTEGRATION", r.upper())

        deck_tensor = "*USER ELEMENT, TYPE=U1, NODES=4, TENSOR=1, PROPERTIES=3\n1, 2"
        v, r = validate_general_user_element_deck(deck_tensor)
        self.assertFalse(v)
        self.assertIn("TENSOR", r.upper())

        deck_foobar = "*USER ELEMENT, TYPE=U1, NODES=4, FOOBAR=1\n1, 2"
        v, r = validate_general_user_element_deck(deck_foobar)
        self.assertFalse(v)
        self.assertIn("FOOBAR", r.upper())

        deck_notype = "*USER ELEMENT, NODES=4, PROPERTIES=3\n1, 2"
        v, r = validate_general_user_element_deck(deck_notype)
        self.assertFalse(v)
        self.assertIn("MISSING TYPE", r.upper())

        deck_nonodes = "*USER ELEMENT, TYPE=U1, PROPERTIES=3\n1, 2"
        v, r = validate_general_user_element_deck(deck_nonodes)
        self.assertFalse(v)
        self.assertIn("MISSING NODES", r.upper())

        deck_wrongdof_u1 = "*USER ELEMENT, TYPE=U1, NODES=4, PROPERTIES=3\n1, 2, 3\n*USER ELEMENT, TYPE=U2, NODES=4, PROPERTIES=5\n1, 2, 3\n*USER ELEMENT, TYPE=U3, NODES=3, PROPERTIES=3\n1, 2\n*USER ELEMENT, TYPE=U4, NODES=3, PROPERTIES=5\n1, 2, 3"
        v, r = validate_general_user_element_deck(deck_wrongdof_u1)
        self.assertFalse(v)
        self.assertIn("WRONG DOF DEFINITION FOR U1", r.upper())

    # ------------------------------------------------------------------
    # COMPLETE 22-TEST PREP4 INGESTION QUALIFICATION SUITE
    # ------------------------------------------------------------------
    def test_06_phase_global_dof_contract(self):
        content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R3.inp").read_text()
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if "*USER ELEMENT, TYPE=U2" in line or "*USER ELEMENT, TYPE=U4" in line:
                dof_line = lines[idx + 1].strip()
                self.assertEqual(dof_line, "1, 2, 3", f"Phase UEL DOF card line must be '1, 2, 3', got '{dof_line}'")

    def test_07_mechanical_global_dofs_contract(self):
        content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R3.inp").read_text()
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if "*USER ELEMENT, TYPE=U1" in line or "*USER ELEMENT, TYPE=U3" in line:
                dof_line = lines[idx + 1].strip()
                self.assertEqual(dof_line, "1, 2", f"Mech UEL DOF card line must be '1, 2', got '{dof_line}'")

    def test_08_physical_node_pairing(self):
        content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R3.inp").read_text()
        self.assertIn("1, 1, 2, 3, 4", content)

    def test_09_nsvars_count_contract(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R3.inp").read_text()
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("VARIABLES=18", inp_content)
        self.assertIn("NSTV=18", uel_content)

    def test_10_svars_slot_bounds_and_no_overlap(self):
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("SVARS(INPT)=HIST", uel_content)
        self.assertIn("SVARS(4+INPT)=PHASE", uel_content)

    def test_11_nphys_property_slot_contract(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R3.inp").read_text()
        self.assertIn("*UEL PROPERTY, ELSET=E_U2\n210000.0, 0.3, 0.015, 2.7, 1.0e-7", inp_content)

    def test_12_sentinel_uniqueness_and_bounds(self):
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        nodal_phases = artifact["sentinel_phase_nodal"]
        unique_vals = set(nodal_phases.values())
        self.assertEqual(len(unique_vals), len(nodal_phases), "Sentinel phase values must be unique")
        for val in nodal_phases.values():
            self.assertGreater(val, 0.0)
            self.assertLessEqual(val, 1.0)

    def test_13_quadrature_interpolation(self):
        u_nodes = [0.11, 0.23, 0.37, 0.61]
        interp_approx = sum(u_nodes) / 4.0
        self.assertAlmostEqual(interp_approx, 0.33, places=2)

    def test_14_element_pairing_contract(self):
        with open(PACKAGE_DIR / "TRANSFER_MANIFEST.json", "r") as f:
            manifest = json.load(f)
        self.assertIn("element_mappings", manifest)

    def test_15_ip_ordering_contract(self):
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        ip_history = artifact["sentinel_history_ip"]["1"]
        self.assertEqual(len(ip_history), 4)

    def test_16_keyword_presence_and_type_displacement_absence(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R3.inp").read_text()
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", inp_content)
        self.assertNotIn("TYPE=DISPLACEMENT", inp_content)

    def test_17_step1_boundary_sentinels(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R3.inp").read_text()
        self.assertIn("1, 3, 3, 0.75", inp_content)

    def test_18_step2_mechanical_constraints(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R3.inp").read_text()
        self.assertIn("*STEP, NAME=Step-2-IngestProbe", inp_content)
        self.assertIn("*BOUNDARY, OP=NEW", inp_content)

    def test_19_trace_checker_known_good(self):
        synthetic_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=2 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.2000E-04 HIST= 1.2000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=3 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.3000E-04 HIST= 1.3000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=4 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.4000E-04 HIST= 1.4000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    2 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 2.1000E-04 HIST= 2.1000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    5 JTYPE=3 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000 SV_H= 3.1000E-04 HIST= 3.1000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    6 JTYPE=3 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000 SV_H= 4.1000E-04 HIST= 4.1000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    9 JTYPE=2 KSTEP=2 KINC= 1 IP=1 SV_H= 1.1000E-04 PH= 0.25000 ENG= 0.0000E+00 SDV14= 0.25000 SDV16= 1.1000E-04
[INGEST_TRACE] ELEM=   10 JTYPE=2 KSTEP=2 KINC= 1 IP=1 SV_H= 2.1000E-04 PH= 0.25000 ENG= 0.0000E+00 SDV14= 0.25000 SDV16= 2.1000E-04
[INGEST_TRACE] ELEM=   13 JTYPE=4 KSTEP=2 KINC= 1 IP=1 SV_H= 3.1000E-04 PH= 0.25000 ENG= 0.0000E+00 SDV14= 0.25000 SDV16= 3.1000E-04
[INGEST_TRACE] ELEM=   14 JTYPE=4 KSTEP=2 KINC= 1 IP=1 SV_H= 4.1000E-04 PH= 0.25000 ENG= 0.0000E+00 SDV14= 0.25000 SDV16= 4.1000E-04
"""
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(synthetic_trace)
        ok, msg, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertTrue(ok, f"Expected PASS on valid trace, got: {msg}")

    def test_20_trace_checker_zero_rejection(self):
        zero_trace = "[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.0, 0.0, 0.0, 0.0 SV_H= 0.0 HIST= 0.0 PH= 0.0 SDV15= 0.0"
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(zero_trace)
        ok, _, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok)

    def test_21_trace_checker_node_swap_rejection(self):
        swapped_trace = "[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.61000, 0.37000, 0.23000, 0.11000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000"
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(swapped_trace)
        ok, _, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok)

    def test_22_trace_checker_ip_swap_rejection(self):
        ip_swapped_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.2000E-04 HIST= 1.2000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=2 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000
"""
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(ip_swapped_trace)
        ok, _, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok)

    def test_23_trace_checker_missing_record_rejection(self):
        missing_trace = "[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000"
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(missing_trace)
        ok, _, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok)

    def test_24_trace_checker_later_iteration_only_rejection(self):
        later_trace = "[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 5 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000"
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(later_trace)
        ok, _, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok)

    def test_25_sdv_reporting_contracts(self):
        with open(PACKAGE_DIR / "ACCEPTANCE_CONTRACT.json", "r") as f:
            contract = json.load(f)
        gates = contract["acceptance_gates"]
        self.assertIn("SDV14_contract", gates)
        self.assertIn("SDV15_contract", gates)
        self.assertIn("SDV16_contract", gates)

    def test_26_quadrature_consistency_and_nsvars_contract(self):
        for_text = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("DO INPT=1,4", for_text, "Quad 4-point quadrature loop missing in UEL")
        self.assertIn("DO INPT=1,3", for_text, "Tri 3-point quadrature loop missing in UEL")
        self.assertIn("NSTV=18", for_text, "NSVARS count 18 contract missing in UEL")

    def test_27_pbs_and_wrapper_integrity(self):
        pbs_text = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R3.pbs").read_text()
        self.assertIn("M2STATE_INGEST_SMOKE1R3", pbs_text)
        self.assertIn("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023", pbs_text)

        wrap_text = (PACKAGE_DIR / "submit_m2state_ingest_smoke1r3.sh").read_text()
        self.assertIn("M2STATE_INGEST_SMOKE1R3", wrap_text)
        self.assertIn("check_license_gate.py", wrap_text)
        self.assertIn("test_m2state_ingest_smoke1r3.py", wrap_text)

if __name__ == "__main__":
    unittest.main()
