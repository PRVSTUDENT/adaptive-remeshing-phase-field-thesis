#!/usr/bin/env python3
"""
Unit Test Suite for Gate-6B Stage 14U-AM:
Controlled Adaptive Spatial-Resolution Convergence Candidate
------------------------------------------------------------
Tests:
1. Package 30 directory completeness, manifest integrity, and pre-job card.
2. Fortran subroutine hash match (authoritative CE8D5EDC...).
3. Native CAE mesh generation metrics (N_base=57929, 56339 quads, 1590 tris, 57491 nodes).
4. Sizing parameters (minElementSize=0.0005 mm, errorTarget=1.0%, refinementFactor=10, maxElementSize=0.020 mm).
5. 3-Layer deterministic deck reconstruction (173,787 elements, PROPS(6)=57929.0, Stage-14U Step 2 solver controls).
6. Seam topology (97 duplicate node pairs along slit, 1 crack-tip singleton at (0.5, 0.5)).
7. Spatial convergence protocol JSON and Markdown schema integrity.
"""

import os
import sys
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestStage14UAMSpatialCandidate(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.pkg30_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "30_stage14_adaptive_candidate_spatial_fine")
        cls.summary_path = os.path.join(cls.pkg30_dir, "STAGE14AM_SPATIAL_FINE_REMESH_SUMMARY.json")
        cls.manifest_path = os.path.join(cls.pkg30_dir, "PACKAGE_MANIFEST.json")
        cls.card_path = os.path.join(cls.pkg30_dir, "PRE_JOB_ANTI_DEVIATION_CARD.md")
        cls.protocol_json_path = os.path.join(cls.pkg30_dir, "STAGE14UAM_SPATIAL_CONVERGENCE_PROTOCOL.json")
        cls.protocol_md_path = os.path.join(cls.pkg30_dir, "STAGE14UAM_SPATIAL_CONVERGENCE_PROTOCOL.md")
        cls.deck_path = os.path.join(cls.pkg30_dir, "PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.inp")
        cls.uel_path = os.path.join(cls.pkg30_dir, "f42_mixed_uel.for")
        cls.solver_pbs_path = os.path.join(cls.pkg30_dir, "submit_solver.pbs")
        cls.dc_pbs_path = os.path.join(cls.pkg30_dir, "submit_datacheck.pbs")
        
    def test_package_directory_and_required_files(self):
        """Verify that Package 30 contains all required execution, reconstruction, and governance files."""
        self.assertTrue(os.path.isdir(self.pkg30_dir), "Package 30 directory missing!")
        required_files = [
            "PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.inp",
            "PK_M1_14AM_DATACHECK.inp",
            "PK_M1_STAGE14AM_RAW.inp",
            "f42_mixed_uel.for",
            "job_notifications.sh",
            "submit_solver.pbs",
            "submit_datacheck.pbs",
            "submit_stage14u_spatial_fine_solver.sh",
            "run_datacheck_direct.sh",
            "run_stage14uam_spatial_fine_remesh.sh",
            "execute_stage14uam_spatial_fine_remesh.py",
            "build_stage14uam_spatial_fine_deck.py",
            "stage14am_adapted_elements.csv",
            "STAGE14AM_SPATIAL_FINE_REMESH_SUMMARY.json",
            "PACKAGE_MANIFEST.json",
            "PRE_JOB_ANTI_DEVIATION_CARD.md",
            "STAGE14UAM_SPATIAL_CONVERGENCE_PROTOCOL.json",
            "STAGE14UAM_SPATIAL_CONVERGENCE_PROTOCOL.md"
        ]
        for rf in required_files:
            fp = os.path.join(self.pkg30_dir, rf)
            self.assertTrue(os.path.exists(fp), "Missing required file: %s" % rf)
            self.assertGreater(os.path.getsize(fp), 0, "File is empty: %s" % rf)

    def test_fortran_subroutine_hash_invariance(self):
        """Verify that f42_mixed_uel.for matches the authoritative SHA-256 hash."""
        with open(self.uel_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(h.lower(), "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6")

    def test_native_remeshing_summary_and_sizing_contract(self):
        """Verify that native CAE adaptive remeshing produced correct metrics and respected sizing contract."""
        with open(self.summary_path, "r") as f:
            data = json.load(f)
            
        self.assertEqual(data["status"], "STAGE14UAM_SPATIAL_FINE_REMESH_COMPLETED")
        self.assertEqual(data["audit_id"], "GATE6B-STAGE14UAM-CONTROLLED-SPATIAL-CONVERGENCE-20261004")
        
        # Sizing contract checks
        sc = data["sizing_contract"]
        self.assertEqual(sc["sizing_method"], "UNIFORM_ERROR")
        self.assertEqual(sc["error_target_pct"], 1.0)
        self.assertEqual(sc["refinement_factor"], 10)
        self.assertEqual(sc["coarsening_factor"], "NOT_ALLOWED")
        self.assertEqual(sc["min_element_size_mm"], 0.0005)
        self.assertEqual(sc["max_element_size_mm"], 0.020)
        
        # Mesh topology checks
        am = data["adapted_mesh"]
        self.assertEqual(am["total_elements"], 57929)
        self.assertEqual(am["quad_elements"], 56339)
        self.assertEqual(am["tri_elements"], 1590)
        self.assertEqual(am["total_nodes"], 57491)
        
        # h_min / l0 check (l0 = 0.0075 mm)
        h_min = am["h_eq_stats"]["min_mm"]
        self.assertAlmostEqual(h_min, 0.000553465, places=5)
        self.assertLess(h_min / 0.0075, 0.08)
        
        # Seam verification
        sv = data["seam_verification"]
        self.assertEqual(sv["seam_duplicate_pairs"], 97)
        self.assertEqual(sv["seam_singletons"], 1)
        self.assertTrue(sv["tip_singleton_found"])

    def test_production_deck_3layer_reconstruction_and_controls(self):
        """Verify 3-layer reconstruction, UEL properties, equation constraints, and solver controls."""
        with open(self.deck_path, "r") as f:
            content = f.read()
            
        # Element cards
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM", content)
        self.assertIn("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM", content)
        self.assertIn("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM", content)
        self.assertIn("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM", content)
        
        # UEL properties: PROPS(6) = 57929.0
        self.assertIn("0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 57929.0", content)
        
        # Companion UMAT section
        self.assertIn("*SOLID SECTION, ELSET=UMATELEM, MATERIAL=UMAT_MAT", content)
        self.assertIn("*USER MATERIAL, CONSTANTS=2\n210000.0, 0.3", content)
        
        # Step 2 controls
        self.assertIn("*CONTROLS, PARAMETERS=TIME INCREMENTATION\n4, 10, 9, 20, 10, 4, 0, 10", content)
        self.assertIn("*STATIC\n2.0E-4, 1.0, 1.0E-9, 2.0E-4", content)

    def test_spatial_convergence_protocol_schema(self):
        """Verify that the spatial convergence protocol defines the 10 matched states and classification categories."""
        with open(self.protocol_json_path, "r") as f:
            proto = json.load(f)
            
        self.assertEqual(proto["protocol_id"], "GATE6B-STAGE14UAM-SPATIAL-CONVERGENCE-PROTOCOL-20261004")
        self.assertEqual(len(proto["matched_rp_evaluation_states_mm"]), 10)
        self.assertEqual(proto["matched_rp_evaluation_states_mm"][0], 0.0050)
        self.assertEqual(proto["matched_rp_evaluation_states_mm"][-1], 0.0100)
        
        eq = proto["evaluated_quantities"]
        self.assertIn("initial_elastic_stiffness_K0", eq)
        self.assertIn("peak_reaction_force_Fmax", eq)
        self.assertIn("crack_tip_position_xtip", eq)
        self.assertIn("fracture_dissipation_energy_E_frac", eq)
        self.assertIn("energy_bookkeeping_discrepancy_eps_book", eq)
        
        self.assertEqual(eq["initial_elastic_stiffness_K0"]["pre_classification"], "SPATIALLY_STABLE")
        self.assertEqual(eq["peak_reaction_force_Fmax"]["pre_classification"], "SPATIALLY_SENSITIVE")
        self.assertEqual(eq["energy_bookkeeping_discrepancy_eps_book"]["pre_classification"], "NOT_YET_QUALIFIED")

    def test_pbs_directives_and_notification_integration(self):
        """Verify that PBS submission script has mail directives, queue routing, and notification traps."""
        with open(self.solver_pbs_path, "r") as f:
            pbs = f.read()
            
        self.assertIn("#PBS -N PK_M1_14AM_SOLVE", pbs)
        self.assertIn("#PBS -q entry_imfdfkmq", pbs)
        self.assertIn("#PBS -l nodes=1:ppn=1", pbs)
        self.assertIn("#PBS -m abe", pbs)
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs)
        self.assertIn("source ./job_notifications.sh", pbs)
        self.assertIn("notification_install_terminal_trap", pbs)
        self.assertIn("notify_start", pbs)

if __name__ == "__main__":
    unittest.main()
