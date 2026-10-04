#!/usr/bin/env python3
"""
Unit test suite for Gate-6B Mode-I Stage 14U-R/S:
Temporal-Convergence Protocol Freeze, Source-Identity Audit, and Refined Candidate Preflight.

Verifies:
1. Exact line-by-line mesh, node, element, and equation invariance between Package 25 and Package 26.
2. Exact UEL Property ABI and material parameter invariance (l0=0.0075, Gc=0.0027, E=210.0, nu=0.3, k=1.0e-7, N_elem=14483.0).
3. Exact 2x temporal refinement parameterization in Step 1 (dt=2.5e-4, INC=5000, du=1.25 nm) and Step 2 (dt=1.0e-4, INC=12000, du=0.50 nm).
4. Step-2 solver controls invariance (*CONTROLS, PARAMETERS=TIME INCREMENTATION: 4, 10, 9, 20, 10, 4, 0, 10).
5. Exact deck-diff containment proof (strictly 4 modified lines between Package 25 and 26 solve decks).
6. Datacheck deck structure (INC=1 for rapid cluster verification).
7. Package manifest integrity, file hash validity, and execution-guard boundary.
8. Bit-identical UEL Fortran subroutine (SHA-256 CE8D5EDC...) and notification helper presence.
9. Canonical N=400 K0 grid sampling rule and descriptive classification scheme in protocol reports.
"""

import os
import unittest
import hashlib
import json

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG25_DIR = os.path.join(WORKSPACE_ROOT, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k")
PKG26_DIR = os.path.join(WORKSPACE_ROOT, "models", "pandey_kumar_mode1", "26_stage14_temporal_refined_candidate_2x")

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().upper()

class TestStage14URTemporalConvergencePreflight(unittest.TestCase):

    def setUp(self):
        self.pkg25_deck = os.path.join(PKG25_DIR, "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp")
        self.pkg26_deck = os.path.join(PKG26_DIR, "PK_MODE1_STAGE14_ADAPT_14K_TEMPORAL_2X.inp")
        self.pkg26_dc = os.path.join(PKG26_DIR, "PK_M1_14K_TEMPORAL_2X_DATACHECK.inp")
        self.pkg26_manifest = os.path.join(PKG26_DIR, "PACKAGE_MANIFEST.json")
        self.pkg26_uel = os.path.join(PKG26_DIR, "f42_mixed_uel.for")
        self.pkg26_notify = os.path.join(PKG26_DIR, "job_notifications.sh")
        self.pkg26_report_json = os.path.join(PKG26_DIR, "MODE1_STAGE14UR_TEMPORAL_CONVERGENCE_PROTOCOL_REPORT.json")

        self.assertTrue(os.path.isfile(self.pkg25_deck), f"Missing {self.pkg25_deck}")
        self.assertTrue(os.path.isfile(self.pkg26_deck), f"Missing {self.pkg26_deck}")
        self.assertTrue(os.path.isfile(self.pkg26_dc), f"Missing {self.pkg26_dc}")
        self.assertTrue(os.path.isfile(self.pkg26_manifest), f"Missing {self.pkg26_manifest}")
        self.assertTrue(os.path.isfile(self.pkg26_uel), f"Missing {self.pkg26_uel}")
        self.assertTrue(os.path.isfile(self.pkg26_notify), f"Missing {self.pkg26_notify}")
        self.assertTrue(os.path.isfile(self.pkg26_report_json), f"Missing {self.pkg26_report_json}")

    def test_01_deck_diff_line_by_line_invariance(self):
        """Verify that ONLY the temporal discretization lines differ between Package 25 and 26."""
        with open(self.pkg25_deck, "r", encoding="ascii") as f:
            lines25 = f.readlines()
        with open(self.pkg26_deck, "r", encoding="ascii") as f:
            lines26 = f.readlines()

        self.assertEqual(len(lines25), len(lines26), "Deck line counts must be identical")

        diffs = []
        for idx, (l25, l26) in enumerate(zip(lines25, lines26), start=1):
            if l25 != l26:
                diffs.append((idx, l25.strip(), l26.strip()))

        # Exactly 4 lines should differ: Step 1 *STEP, Step 1 *STATIC, Step 2 *STEP, Step 2 *STATIC
        self.assertEqual(len(diffs), 4, f"Expected exactly 4 differing lines, got {len(diffs)}: {diffs}")

        # Check diff details
        step1_step_diff = diffs[0]
        step1_static_diff = diffs[1]
        step2_step_diff = diffs[2]
        step2_static_diff = diffs[3]

        self.assertIn("*STEP, NAME=Step-1, NLGEOM=NO, INC=2500", step1_step_diff[1])
        self.assertIn("*STEP, NAME=Step-1, NLGEOM=NO, INC=5000", step1_step_diff[2])

        self.assertIn("5.0E-4, 1.0, 1.0E-9, 5.0E-4", step1_static_diff[1])
        self.assertIn("2.5E-4, 1.0, 1.0E-9, 2.5E-4", step1_static_diff[2])

        self.assertIn("*STEP, NAME=Step-2, NLGEOM=NO, INC=6000", step2_step_diff[1])
        self.assertIn("*STEP, NAME=Step-2, NLGEOM=NO, INC=12000", step2_step_diff[2])

        self.assertIn("2.0E-4, 1.0, 1.0E-9, 2.0E-4", step2_static_diff[1])
        self.assertIn("1.0E-4, 1.0, 1.0E-9, 1.0E-4", step2_static_diff[2])

    def test_02_mesh_and_node_invariance(self):
        """Verify underlying element counts, layered counts, and node counts."""
        with open(self.pkg26_deck, "r", encoding="ascii") as f:
            text = f.read()

        # Check node count markers
        self.assertIn("14456, 0.0000000000, 0.5000000000", text)
        self.assertIn("*NODE", text)
        self.assertIn("999999, 0.5000000000, 1.0000000000", text)

        # Check UEL property ABI
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM", text)
        self.assertIn("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM", text)
        self.assertIn("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM", text)
        self.assertIn("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM", text)
        self.assertIn("0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0", text)

    def test_03_step2_solver_controls_invariance(self):
        """Verify Step 2 time incrementation cutback controls are preserved."""
        with open(self.pkg26_deck, "r", encoding="ascii") as f:
            lines = f.readlines()

        step2_found = False
        controls_found = False
        for i, line in enumerate(lines):
            if line.strip().startswith("*STEP, NAME=Step-2"):
                step2_found = True
                for j in range(i, min(i + 20, len(lines))):
                    if "*CONTROLS, PARAMETERS=TIME INCREMENTATION" in lines[j]:
                        self.assertEqual(lines[j+1].strip(), "4, 10, 9, 20, 10, 4, 0, 10")
                        controls_found = True
                        break

        self.assertTrue(step2_found, "Step-2 must exist")
        self.assertTrue(controls_found, "Stage 14U solver controls must exist in Step-2")

    def test_04_displacement_boundary_endpoints(self):
        """Verify boundary condition endpoints u1=0.0050 mm and u2=0.0100 mm."""
        with open(self.pkg26_deck, "r", encoding="ascii") as f:
            lines = f.readlines()

        step1_rp = False
        step2_rp = False
        in_step1 = False
        in_step2 = False

        for line in lines:
            if line.strip().startswith("*STEP, NAME=Step-1"):
                in_step1 = True
                in_step2 = False
            elif line.strip().startswith("*STEP, NAME=Step-2"):
                in_step1 = False
                in_step2 = True
            elif line.strip().startswith("*END STEP"):
                in_step1 = False
                in_step2 = False

            if in_step1 and "N_RP, 2, 2, 0.0050" in line:
                step1_rp = True
            if in_step2 and "N_RP, 2, 2, 0.0100" in line:
                step2_rp = True

        self.assertTrue(step1_rp, "Step 1 N_RP endpoint must be 0.0050 mm")
        self.assertTrue(step2_rp, "Step 2 N_RP endpoint must be 0.0100 mm")

    def test_05_datacheck_deck_properties(self):
        """Verify that datacheck deck has INC=1 in both steps and is otherwise identical."""
        with open(self.pkg26_deck, "r", encoding="ascii") as f:
            lines_full = f.readlines()
        with open(self.pkg26_dc, "r", encoding="ascii") as f:
            lines_dc = f.readlines()

        self.assertEqual(len(lines_full), len(lines_dc))

        dc_diffs = []
        for idx, (lf, ldc) in enumerate(zip(lines_full, lines_dc), start=1):
            if lf != ldc:
                dc_diffs.append((idx, lf.strip(), ldc.strip()))

        self.assertEqual(len(dc_diffs), 2, f"Expected exactly 2 diffs for datacheck deck, got {len(dc_diffs)}: {dc_diffs}")
        self.assertIn("INC=5000", dc_diffs[0][1])
        self.assertIn("INC=1", dc_diffs[0][2])
        self.assertIn("INC=12000", dc_diffs[1][1])
        self.assertIn("INC=1", dc_diffs[1][2])

    def test_06_package_manifest_and_hashes(self):
        """Verify package manifest schema, file hashes, and submission guard."""
        with open(self.pkg26_manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["package_name"], "26_stage14_temporal_refined_candidate_2x")
        self.assertEqual(manifest["mesh_specification"]["underlying_elements"], 14483)
        self.assertEqual(manifest["mesh_specification"]["total_nodes"], 14456)
        self.assertEqual(manifest["execution_state"]["submission_authorized"], False)
        self.assertEqual(manifest["execution_state"]["submission_status"], "WITHHELD__AWAITING_BASELINE_1409982_TERMINAL_EVALUATION")

        # Verify live hashes against declared manifest hashes
        for filename, info in manifest["files"].items():
            filepath = os.path.join(PKG26_DIR, filename)
            self.assertTrue(os.path.isfile(filepath), f"File {filename} declared in manifest missing")
            actual_sha = get_sha256(filepath)
            self.assertEqual(actual_sha, info["sha256"], f"SHA256 mismatch for {filename}: {actual_sha} vs {info['sha256']}")

    def test_07_fortran_subroutine_identity(self):
        """Verify UEL Fortran subroutine is bit-identical between Package 25 and Package 26 (SHA-256 CE8D5EDC...)."""
        expected_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        sha25 = get_sha256(os.path.join(PKG25_DIR, "f42_mixed_uel.for"))
        sha26 = get_sha256(self.pkg26_uel)
        self.assertEqual(sha25, expected_sha, f"Package 25 subroutine hash mismatch: {sha25}")
        self.assertEqual(sha26, expected_sha, f"Package 26 subroutine hash mismatch: {sha26}")
        self.assertEqual(sha25, sha26, "Subroutine f42_mixed_uel.for must be bit-identical across packages")

    def test_08_canonical_k0_sampling_and_classification_scheme(self):
        """Verify protocol report specifies canonical N=400 K0 sampling and descriptive classifications."""
        with open(self.pkg26_report_json, "r", encoding="utf-8") as f:
            rep = json.load(f)

        metrics = {m["name"]: m for m in rep["predeclared_comparison_protocol"]["comparison_metrics"]}
        self.assertIn("Global Structural Stiffness K0", metrics)
        k0_metric = metrics["Global Structural Stiffness K0"]

        # Ensure canonical N=400 sampling rule
        self.assertIn("N=400", k0_metric["evaluation_rule"])
        self.assertNotIn("N=800", k0_metric["evaluation_rule"])
        self.assertIn("400-point grid", k0_metric["evaluation_rule"])

        # Ensure descriptive classification scheme without newly invented percentage thresholds
        physical_metrics = [
            "Global Structural Stiffness K0",
            "Peak Reaction Force F_max",
            "Displacement at Peak Load u_peak",
            "Pointwise Force at 10 Matched States",
            "Continuous Spatial Ligament Damage Profile d(x, y=0.5 mm)",
            "Crack Tip Position x_tip",
            "Energy Balance Integrals"
        ]
        for m_name in physical_metrics:
            self.assertIn(m_name, metrics, f"Missing metric {m_name}")
            m_data = metrics[m_name]
            self.assertIn("classification_scheme", m_data, f"Metric {m_name} missing classification_scheme")
            self.assertNotIn("<= 1.0%", m_data["classification_scheme"])
            self.assertNotIn("<= 3.0%", m_data["classification_scheme"])
            self.assertIn("STABLE", m_data["classification_scheme"])
            self.assertIn("TEMPORALLY_SENSITIVE", m_data["classification_scheme"])
            self.assertIn("NOT_YET_QUALIFIED", m_data["classification_scheme"])

if __name__ == "__main__":
    unittest.main()
