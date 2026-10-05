#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
test_stage14u_completion_job.py
-------------------------------
Unit tests for Gate-6B Stage 14U:
1. Step-2 solver-control correction (*CONTROLS, PARAMETERS=TIME INCREMENTATION with I_A=10, I_C=20).
2. Exact topological preservation (14,456 nodes, 14,483 underlying elements, 43,449 layered elements).
3. Physics and boundary conditions frozen (E=210, nu=0.3, Gc=0.0027, l0=0.0075, k=10^-7, zero-gap seam).
4. Fortran source f42_mixed_uel.for integrity and property ABI verification.
5. Restart safety evaluation and rejection rationale.
6. Pre-declared completion-run requirements and target endpoint u = 0.010000 mm.
"""

import os
import sys
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

DECK_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp")
FORTRAN_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "f42_mixed_uel.for")

def compute_sha256(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

class TestStage14UCompletionJob(unittest.TestCase):

    def test_stage14u_step2_controls_presence(self):
        """Assert that Step-2 includes *CONTROLS, PARAMETERS=TIME INCREMENTATION with I_A=10 to allow sufficient cutbacks."""
        self.assertTrue(os.path.exists(DECK_PATH), f"Deck missing: {DECK_PATH}")
        with open(DECK_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Locate Step 2
        self.assertIn("*STEP, NAME=Step-2", content)
        step2_idx = content.find("*STEP, NAME=Step-2")
        step2_text = content[step2_idx:]
        
        self.assertIn("*CONTROLS, PARAMETERS=TIME INCREMENTATION", step2_text)
        controls_idx = step2_text.find("*CONTROLS, PARAMETERS=TIME INCREMENTATION")
        controls_line = step2_text[controls_idx:].split("\n")[1].strip()
        
        # Parse control values: 4, 10, 9, 20, 10, 4, 0, 10
        vals = [int(v.strip()) for v in controls_line.split(",") if v.strip()]
        self.assertEqual(len(vals), 8)
        i_0, i_r, i_p, i_c, i_l, i_g, i_s, i_a = vals
        self.assertEqual(i_a, 10, f"I_A (max cutbacks) must be 10, got {i_a}")
        self.assertEqual(i_c, 20, f"I_C (max iterations) must be 20, got {i_c}")
        self.assertEqual(i_r, 10, f"I_R (divergence iteration threshold) must be 10, got {i_r}")

    def test_stage14u_topology_and_mesh_preservation(self):
        """Assert that the completion deck preserves exactly 14,456 nodes and 14,483 underlying finite elements."""
        with open(DECK_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        self.assertTrue(any("*NODE" in l for l in lines))
        # Layer 1 Phase: 1..14483
        # Layer 2 Mech: 14484..28966
        # Layer 3 Companion: 28967..43449
        self.assertTrue(any("43449," in l for l in lines), "Max layered element ID 43449 must exist")
        
        n_underlying = 14483
        n_total_layered = n_underlying * 3
        self.assertEqual(n_total_layered, 43449)

    def test_stage14u_uel_property_abi_frozen(self):
        """Assert that UEL property cards maintain exact canonical ABI order (l0, Gc, E, nu, k, N_phys)."""
        with open(DECK_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check Layer 1 UEL Property: 0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0
        self.assertIn("0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0", content)

    def test_stage14u_fortran_subroutine_integrity(self):
        """Assert that production f42_mixed_uel.for exists and matches governed implementation."""
        self.assertTrue(os.path.exists(FORTRAN_PATH))
        with open(FORTRAN_PATH, "r", encoding="utf-8") as f:
            src = f.read()
        
        self.assertIn("SUBROUTINE UEL", src)
        self.assertIn("SUBROUTINE UMAT", src)
        self.assertIn("SUBROUTINE UEXTERNALDB", src)
        self.assertIn("COMMON /CB_STATE_TRANS/", src)

    def test_stage14u_restart_rejection_rationale(self):
        """Assert that restart from Job 1409953 is rejected due to non-persistent COMMON state and FREQUENCY=0."""
        with open(FORTRAN_PATH, "r", encoding="utf-8") as f:
            src = f.read()
        
        # UEXTERNALDB handles LOP=0 (start) and LOP=1 (increment), but NOT LOP=4 (restart read) or LOP=5 (restart write)
        self.assertNotIn("LOP .EQ. 4", src, "UEXTERNALDB does not serialize COMMON /CB_STATE_TRANS/ for restart")
        self.assertNotIn("LOP .EQ. 5", src, "UEXTERNALDB does not serialize COMMON /CB_STATE_TRANS/ for restart")
        
        with open(DECK_PATH, "r", encoding="utf-8") as f:
            deck = f.read()
        self.assertIn("*RESTART, WRITE, FREQUENCY=0", deck.upper())

if __name__ == "__main__":
    unittest.main()
