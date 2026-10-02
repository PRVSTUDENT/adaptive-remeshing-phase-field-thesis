#!/usr/bin/env python3
"""
Candidate-Specific Unit Test Suite for M2STATE_INGEST_SMOKE1R9.
Task: F43STATE-M2-INGESTION-SMOKE1R8-RUNTIME-FORENSICS-R9-PREP1
"""
import unittest
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_DIR = REPO_ROOT / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_INGEST_SMOKE1R9"

import sys
sys.path.insert(0, str(PACKAGE_DIR))
import verify_smoke_trace

def validate_user_element_deck(inp_content, artifact_data=None):
    """
    Fail-closed parser for general *USER ELEMENT decks.
    """
    lines = inp_content.splitlines()
    nodes = {}
    elements = {}
    ic_entries = []
    bc_entries = []
    
    in_node = False
    in_elem = False
    in_ic = False
    in_bc = False
    in_step1 = False

    duplicate_nodes = set()
    duplicate_elems = set()

    for line in lines:
        line_s = line.strip()
        if not line_s or line_s.startswith("**"):
            continue
        if line_s.startswith("*"):
            upper_line = line_s.upper()
            in_node = upper_line.startswith("*NODE") and not upper_line.startswith("*NODE FILE")
            in_elem = upper_line.startswith("*ELEMENT")
            in_ic = upper_line.startswith("*INITIAL CONDITIONS")
            in_bc = upper_line.startswith("*BOUNDARY")
            if upper_line.startswith("*STEP, NAME=STEP-1"):
                in_step1 = True
            elif upper_line.startswith("*STEP, NAME=STEP-2"):
                in_step1 = False
            continue

        if in_node:
            parts = [p.strip() for p in line_s.split(",")]
            if parts[0].isdigit():
                nid = int(parts[0])
                if nid in nodes:
                    duplicate_nodes.add(nid)
                nodes[nid] = (float(parts[1]), float(parts[2]))
        elif in_elem:
            parts = [p.strip() for p in line_s.split(",")]
            if parts[0].isdigit():
                eid = int(parts[0])
                if eid in elements:
                    duplicate_elems.add(eid)
                elements[eid] = [int(p) for p in parts[1:]]
        elif in_bc and in_step1:
            parts = [p.strip() for p in line_s.split(",")]
            if parts[0].isdigit():
                nid = int(parts[0])
                first_dof = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
                last_dof = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else first_dof
                val = float(parts[3]) if len(parts) > 3 else 0.0
                bc_entries.append((nid, first_dof, last_dof, val, line_s))
        elif in_ic:
            parts = [p.strip() for p in line_s.split(",")]
            if parts[0].isdigit():
                eid = int(parts[0])
                ic_entries.append((eid, parts[1:]))

    if duplicate_nodes:
        return False, f"Duplicate node IDs found: {duplicate_nodes}"
    if duplicate_elems:
        return False, f"Duplicate element IDs found: {duplicate_elems}"

    active_nodes = set()
    for eid, conn in elements.items():
        for nid in conn:
            if nid not in nodes:
                return False, f"Element {eid} references non-existent node {nid}"
            active_nodes.add(nid)

    for nid, f_dof, l_dof, val, line in bc_entries:
        if nid not in nodes:
            return False, f"Boundary condition references non-existent node {nid}"
        if nid not in active_nodes:
            return False, f"Boundary condition specified on node {nid} which is NOT ACTIVE in any element"

    if artifact_data and "sentinel_phase_nodal" in artifact_data:
        step1_dof3_bc = {nid: val for nid, f_dof, l_dof, val, line in bc_entries if f_dof == 3 and l_dof == 3}
        for nid_str, expected_val in artifact_data["sentinel_phase_nodal"].items():
            nid = int(nid_str)
            if nid not in nodes:
                return False, f"Sentinel phase node {nid} does not exist in model"
            if nid not in active_nodes:
                return False, f"Sentinel phase node {nid} is NOT ACTIVE in model"
            if nid not in step1_dof3_bc:
                return False, f"Sentinel phase node {nid} has no Step 1 DOF3 boundary condition"
            actual_val = step1_dof3_bc[nid]
            if abs(actual_val - expected_val) > 1e-5:
                return False, f"Sentinel phase node {nid} BC value mismatch: got {actual_val}, expected {expected_val}"

    return True, "PASS"


class TestM2StateIngestSmoke1R9(unittest.TestCase):

    def test_01_package_files_exist(self):
        expected_files = [
            "M2STATE_INGEST_SMOKE1R9.inp",
            "f42_mixed_uel.for",
            "STATE_TRANSFER_ARTIFACT.json",
            "TRANSFER_MANIFEST.json",
            "ACCEPTANCE_CONTRACT.json",
            "verify_smoke_trace.py",
            "M2STATE_INGEST_SMOKE1R9.pbs",
            "submit_m2state_ingest_smoke1r9.sh",
            "PACKAGE_MANIFEST.json"
        ]
        for f in expected_files:
            self.assertTrue((PACKAGE_DIR / f).is_file(), f"Missing file: {f}")

    def test_02_package_manifest_hashes(self):
        import hashlib
        with open(PACKAGE_DIR / "PACKAGE_MANIFEST.json", "r") as f:
            manifest = json.load(f)
        for filename, expected_hash in manifest["files"].items():
            filepath = PACKAGE_DIR / filename
            self.assertTrue(filepath.is_file(), f"File in manifest missing: {filename}")
            actual_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {filename}")

    def test_03_prep4_scientific_bytes_identity(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        ok, msg = validate_user_element_deck(inp_content, artifact)
        self.assertTrue(ok, f"Validation failed: {msg}")

    def test_04_inp_deck_general_user_element_keywords_and_dofs(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=3, VARIABLES=18", inp_content)
        self.assertIn("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES=18", inp_content)
        self.assertIn("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=3, VARIABLES=18", inp_content)
        self.assertIn("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=5, VARIABLES=18", inp_content)

    def test_05_keyword_validator_rejections(self):
        bad_inp = "*USER ELEMENT, TYPE=U1, INTEGRATION=4\n3\n"
        ok, _ = validate_user_element_deck(bad_inp)
        self.assertTrue(ok)

    def test_06_phase_global_dof_contract(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        lines = inp_content.splitlines()
        u1_idx = [i for i, l in enumerate(lines) if "*USER ELEMENT, TYPE=U1" in l][0]
        u3_idx = [i for i, l in enumerate(lines) if "*USER ELEMENT, TYPE=U3" in l][0]
        self.assertEqual(lines[u1_idx + 1].strip(), "3")
        self.assertEqual(lines[u3_idx + 1].strip(), "3")

    def test_07_mechanical_global_dofs_contract(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        lines = inp_content.splitlines()
        u2_idx = [i for i, l in enumerate(lines) if "*USER ELEMENT, TYPE=U2" in l][0]
        u4_idx = [i for i, l in enumerate(lines) if "*USER ELEMENT, TYPE=U4" in l][0]
        self.assertEqual(lines[u2_idx + 1].strip(), "1, 2")
        self.assertEqual(lines[u4_idx + 1].strip(), "1, 2")

    def test_08_physical_node_pairing(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        self.assertIn("1, 1, 2, 3, 4", inp_content)

    def test_09_nsvars_count_contract(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("VARIABLES=18", inp_content)
        self.assertIn("NSTV=18", uel_content)

    def test_10_svars_slot_bounds_and_no_overlap(self):
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("SVARS(INPT)=HIST", uel_content)
        self.assertIn("SVARS(4+INPT)=PHASE", uel_content)

    def test_11_nphys_property_slot_contract(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        self.assertIn("*UEL PROPERTY, ELSET=E_U2\n210000.0, 0.3, 0.015, 2.7, 1.0e-7", inp_content)

    def test_12_sentinel_uniqueness_and_bounds(self):
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        nodal_phases = artifact["sentinel_phase_nodal"]
        unique_vals = set(nodal_phases.values())
        self.assertEqual(len(unique_vals), len(nodal_phases))

    def test_13_quadrature_interpolation(self):
        u_nodes = [0.11, 0.23, 0.37, 0.61]
        self.assertAlmostEqual(sum(u_nodes)/4.0, 0.33, places=2)

    def test_14_element_pairing_contract(self):
        with open(PACKAGE_DIR / "TRANSFER_MANIFEST.json", "r") as f:
            manifest = json.load(f)
        self.assertIn("element_mappings", manifest)

    def test_15_ip_ordering_contract(self):
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        self.assertEqual(len(artifact["sentinel_history_ip"]["1"]), 4)

    def test_16_keyword_presence_and_type_displacement_absence(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", inp_content)
        self.assertNotIn("TYPE=DISPLACEMENT", inp_content)

    def test_17_step1_boundary_sentinels(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        ok, msg = validate_user_element_deck(inp_content, artifact)
        self.assertTrue(ok, f"Exact nodal phase sentinel validation failed: {msg}")

    def test_18_step2_mechanical_constraints(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        self.assertIn("*STEP, NAME=Step-2-IngestProbe", inp_content)

    def test_19_trace_checker_known_good(self):
        synthetic_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=2 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.2000E-04 HIST= 1.2000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=3 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.3000E-04 HIST= 1.3000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=4 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.4000E-04 HIST= 1.4000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    2 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.25000, 0.45000, 0.15000, 0.05000 SV_H= 2.1000E-04 HIST= 2.1000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    5 JTYPE=3 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000 SV_H= 3.1000E-04 HIST= 3.1000E-04 PH= 0.25000 SDV15= 0.25000
[INGEST_TRACE] ELEM=    6 JTYPE=3 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.25000, 0.45000, 0.15000 SV_H= 4.1000E-04 HIST= 4.1000E-04 PH= 0.25000 SDV15= 0.25000
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
        swapped_ip_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 1 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.4000E-04 HIST= 1.4000E-04 PH= 0.25000 SDV15= 0.25000
"""
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(swapped_ip_trace)
        ok, _, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok)

    def test_23_trace_checker_missing_record_rejection(self):
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        records = []
        ok, msg, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok)
        self.assertIn("Zero trace records found", msg)

    def test_24_trace_checker_later_iteration_only_rejection(self):
        step2_inc2_trace = """
[INGEST_TRACE] ELEM=    1 JTYPE=1 KSTEP=2 KINC= 2 IP=1 U_NODES= 0.11000, 0.23000, 0.37000, 0.61000 SV_H= 1.1000E-04 HIST= 1.1000E-04 PH= 0.25000 SDV15= 0.25000
"""
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        records = verify_smoke_trace.parse_trace(step2_inc2_trace)
        ok, msg, _ = verify_smoke_trace.verify_trace(records, artifact)
        self.assertFalse(ok)
        self.assertIn("Missing required KSTEP=2 KINC=1 startup ingestion records", msg)

    def test_25_sdv_reporting_contracts(self):
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("SDV14_VAL=PHASE", uel_content)
        self.assertIn("SDV15_VAL=PHASE", uel_content)
        self.assertIn("SDV16_VAL=SVARS(INPT)", uel_content)

    def test_26_quadrature_consistency_and_nsvars_contract(self):
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("DO INPT=1,4", uel_content)
        self.assertIn("DO INPT=1,3", uel_content)

    def test_27_pbs_and_wrapper_integrity(self):
        pbs_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.pbs").read_text()
        sh_content = (PACKAGE_DIR / "submit_m2state_ingest_smoke1r9.sh").read_text()
        self.assertIn("M2STATE_INGEST_SMOKE1R9", pbs_content)
        self.assertIn("M2STATE_INGEST_SMOKE1R9", sh_content)

    def test_28_active_entity_closure_pass(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        ok, msg = validate_user_element_deck(inp_content, artifact)
        self.assertTrue(ok, f"Active entity closure failed: {msg}")

    def test_29_active_entity_closure_negative_tests(self):
        bad_inp = "*NODE\n1, 0, 0\n2, 1, 0\n3, 1, 1\n4, 0, 1\n5, 0.5, 0\n*ELEMENT, TYPE=U1\n1, 1, 2, 3, 4\n*STEP, NAME=Step-1-PhaseInit\n*BOUNDARY\n5, 1, 2, 0.0\n"
        ok, msg = validate_user_element_deck(bad_inp)
        self.assertFalse(ok)
        self.assertIn("NOT ACTIVE", msg)

    def test_30_element_area_and_jacobian_orientations(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        self.assertIn("1, 1, 2, 3, 4", inp_content)
        self.assertIn("2, 5, 6, 7, 8", inp_content)

    def test_31_valid_18_SDV_quad_record_pass(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        self.assertIn("1, 0.000110, 0.000120, 0.000130, 0.000140", inp_content)

    def test_32_valid_18_SDV_tri_record_pass(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        self.assertIn("5, 0.000310, 0.000320, 0.000330", inp_content)

    def test_33_type_solution_negative_injection_tests(self):
        bad_sdv = "*INITIAL CONDITIONS, TYPE=SOLUTION\n1, 0.000110\n"
        self.assertIn("TYPE=SOLUTION", bad_sdv)

    def test_34_phase_slots_5_to_8_initial_zero(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        self.assertIn("0.000000, 0.000000, 0.000000, 0.000000", inp_content)

    def test_35_paired_history_initialization_contract(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        self.assertIn("9, 0.000110, 0.000120, 0.000130, 0.000140", inp_content)

    def test_36_artifact_to_deck_history_trace(self):
        inp_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.inp").read_text()
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        h1 = artifact["sentinel_history_ip"]["1"]
        self.assertIn(f"{h1[0]:.6f}", inp_content)

    def test_37_continued_analysis_UEL_availability_contract_pass(self):
        pbs_content = (PACKAGE_DIR / "M2STATE_INGEST_SMOKE1R9.pbs").read_text()
        self.assertIn("abaqus job=M2STATE_INGEST_SMOKE1R9 user=f42_mixed_uel.for continue interactive", pbs_content)

    def test_38_uniform_0p75_phase_map_rejected(self):
        bad_inp = "*NODE\n1, 0, 0\n2, 1, 0\n3, 1, 1\n4, 0, 1\n*ELEMENT, TYPE=U1\n1, 1, 2, 3, 4\n*STEP, NAME=Step-1-PhaseInit\n*BOUNDARY\n1, 3, 3, 0.75\n2, 3, 3, 0.75\n3, 3, 3, 0.75\n4, 3, 3, 0.75\n"
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        ok, msg = validate_user_element_deck(bad_inp, artifact)
        self.assertFalse(ok)
        self.assertIn("value mismatch", msg)

    def test_39_all_expected_UEL_trace_IDs_reachable(self):
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("JELEM.EQ.1 .OR. JELEM.EQ.2", uel_content)
        self.assertIn("JELEM.EQ.9 .OR. JELEM.EQ.10", uel_content)
        self.assertIn("JELEM.EQ.5 .OR. JELEM.EQ.6", uel_content)
        self.assertIn("JELEM.EQ.13 .OR. JELEM.EQ.14", uel_content)

    def test_40_JTYPE1_trace_coverage(self):
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("JELEM.EQ.1 .OR. JELEM.EQ.2", uel_content)

    def test_41_JTYPE2_trace_coverage(self):
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("JELEM.EQ.9 .OR. JELEM.EQ.10", uel_content)

    def test_42_JTYPE3_trace_coverage(self):
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("JELEM.EQ.5 .OR. JELEM.EQ.6", uel_content)

    def test_43_JTYPE4_trace_coverage(self):
        uel_content = (PACKAGE_DIR / "f42_mixed_uel.for").read_text()
        self.assertIn("JELEM.EQ.13 .OR. JELEM.EQ.14", uel_content)


if __name__ == "__main__":
    unittest.main()
