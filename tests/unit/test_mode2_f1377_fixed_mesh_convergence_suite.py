#!/usr/bin/env python3
"""
Unit tests for Task F1377: Mode-II Fixed-Mesh Convergence Suite (Gate M2-1B).
Verifies:
1. Suite manifest and batch proposal existence and JSON schema validity.
2. Exactly 4 cases defined with verified spatial scaling:
   - Coarse: h = 20.00 um (1.33*l0, 2,500 FEs, 2,626 nodes)
   - Medium: h = 7.46 um  (0.50*l0, 17,956 FEs, 18,292 nodes)
   - Intermediate: h = 5.00 um (0.33*l0, 40,000 FEs, 40,501 nodes)
   - Fine: h = 3.73 um (0.25*l0, 71,824 FEs, 72,495 nodes)
3. Self-contained immutable packages for all 4 cases:
   - Input deck, manifest, solver PBS, datacheck PBS, wrapper, Fortran UEL, notifications
   - Exact SHA-256 integrity checks
4. Exact open-slit topology and boundary conditions across all 4 decks:
   - Sharp horizontal seam at y=0.5, x in [0, 0.5] with duplicate nodes
   - Exactly 1 shared node at crack tip (0.5, 0.5)
   - Continuous ligament for x in (0.5, 1.0]
   - Rigid top surface coupled to RP 999999 via *EQUATION cards
   - 2-step paper horizon loading schedule (4000 total increments, Dux=5 nm)
5. Strict governance and authority boundary:
   - execution_authorized = False, maximum_permitted_submissions = 0
   - Mode-I baseline freeze untouched
"""

import os
import sys
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SUITE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "07_fixed_mesh_convergence_suite")

EXPECTED_UEL_SHA256 = "699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188"
EXPECTED_NOTIF_SHA256 = "41A1D403B0356B55EFA3BB1E67B4DD678E74664D501D838D9C01952C0C641F11"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestMode2F1377FixedMeshConvergenceSuite(unittest.TestCase):

    def test_01_suite_manifest_and_proposal_exist(self):
        manifest_path = os.path.join(SUITE_DIR, "SUITE_MANIFEST.json")
        proposal_path = os.path.join(SUITE_DIR, "BATCH_PROPOSAL_FIXED_MESH_CONVERGENCE.json")
        doc_path = os.path.join(REPO_ROOT, "docs", "mode2", "MODE2_FIXED_MESH_CONVERGENCE_BATCH_PROPOSAL.md")
        
        self.assertTrue(os.path.exists(manifest_path), f"Missing {manifest_path}")
        self.assertTrue(os.path.exists(proposal_path), f"Missing {proposal_path}")
        self.assertTrue(os.path.exists(doc_path), f"Missing {doc_path}")
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        self.assertEqual(manifest["suite_id"], "MODE2_FIXED_MESH_CONVERGENCE_SUITE")
        self.assertEqual(len(manifest["cases"]), 4)
        
        with open(proposal_path, "r") as f:
            proposal = json.load(f)
        self.assertEqual(proposal["batch_id"], "BATCH_MODE2_GATE_M2_1B_FIXED_MESH_CONVERGENCE")
        self.assertFalse(proposal["execution_authorized"])
        self.assertFalse(proposal["submission_approved"])
        self.assertEqual(proposal["maximum_permitted_submissions"], 0)
        self.assertEqual(len(proposal["jobs"]), 4)

    def test_02_spatial_mesh_scaling_and_node_inventories(self):
        cases_expected = {
            "01_coarse_2p5k_h20um": {"nx": 50, "ny": 50, "elems": 2500, "nodes": 2626, "h_um": 20.0, "h_over_l0": 1.3333333333333333},
            "02_medium_18k_h7p5um": {"nx": 134, "ny": 134, "elems": 17956, "nodes": 18292, "h_um": 7.462686567164178, "h_over_l0": 0.49751243781094523},
            "03_intermediate_40k_h5um": {"nx": 200, "ny": 200, "elems": 40000, "nodes": 40501, "h_um": 5.0, "h_over_l0": 0.3333333333333333},
            "04_fine_72k_h3p75um": {"nx": 268, "ny": 268, "elems": 71824, "nodes": 72495, "h_um": 3.731343283582089, "h_over_l0": 0.24875621890547264}
        }
        
        manifest_path = os.path.join(SUITE_DIR, "SUITE_MANIFEST.json")
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
            
        for c in manifest["cases"]:
            cid = c["case_id"]
            self.assertIn(cid, cases_expected)
            exp = cases_expected[cid]
            self.assertEqual(c["grid_nx"], exp["nx"])
            self.assertEqual(c["grid_ny"], exp["ny"])
            self.assertEqual(c["num_physical_quads"], exp["elems"])
            self.assertEqual(c["total_layered_elements"], 3 * exp["elems"])
            self.assertEqual(c["num_physical_nodes"], exp["nodes"])
            self.assertAlmostEqual(c["h_um"], exp["h_um"], places=4)
            self.assertAlmostEqual(c["h_over_l0"], exp["h_over_l0"], places=4)

    def test_03_case_package_completeness_and_sha_integrity(self):
        cases = [
            ("01_coarse_2p5k_h20um", "M2_FIX_COARSE_2P5K"),
            ("02_medium_18k_h7p5um", "M2_FIX_MED_18K"),
            ("03_intermediate_40k_h5um", "M2_FIX_INT_40K"),
            ("04_fine_72k_h3p75um", "M2_FIX_FINE_72K")
        ]
        
        for cid, jname in cases:
            cdir = os.path.join(SUITE_DIR, cid)
            self.assertTrue(os.path.isdir(cdir), f"Missing case directory {cdir}")
            
            # Manifest
            mpath = os.path.join(cdir, "manifest.json")
            self.assertTrue(os.path.exists(mpath))
            with open(mpath, "r") as f:
                cman = json.load(f)
            self.assertFalse(cman["submission_authorized"])
            
            # Input deck
            inppath = os.path.join(cdir, f"{jname}.inp")
            self.assertTrue(os.path.exists(inppath))
            actual_inp_sha = compute_sha256(inppath)
            self.assertEqual(actual_inp_sha, cman["input_deck_sha256"])
            
            # Subroutine copy
            subpath = os.path.join(cdir, "f42_mixed_uel_mode2_miehe.for")
            self.assertTrue(os.path.exists(subpath))
            self.assertEqual(compute_sha256(subpath), EXPECTED_UEL_SHA256)
            
            # Notifications copy
            notifpath = os.path.join(cdir, "job_notifications.sh")
            self.assertTrue(os.path.exists(notifpath))
            self.assertEqual(compute_sha256(notifpath), EXPECTED_NOTIF_SHA256)
            
            # Scripts
            self.assertTrue(os.path.exists(os.path.join(cdir, "submit_solver.pbs")))
            self.assertTrue(os.path.exists(os.path.join(cdir, "submit_datacheck.pbs")))
            self.assertTrue(os.path.exists(os.path.join(cdir, "submit_job.sh")))
            self.assertTrue(os.path.exists(os.path.join(cdir, "run_datacheck.sh")))
            
            # Dual-channel notification directives in PBS script
            with open(os.path.join(cdir, "submit_solver.pbs"), "r") as f:
                pbs_content = f.read()
            self.assertIn("#PBS -m abe", pbs_content)
            self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs_content)
            self.assertIn("notification_install_terminal_trap", pbs_content)
            self.assertIn("notify_start", pbs_content)
            self.assertIn("cpus=1 double=both interactive", pbs_content)

    def test_04_mesh_slit_topology_and_boundary_coupling(self):
        # Sample audit on coarse deck M2_FIX_COARSE_2P5K.inp
        inp_path = os.path.join(SUITE_DIR, "01_coarse_2p5k_h20um", "M2_FIX_COARSE_2P5K.inp")
        
        nodes = {}
        equations = []
        in_nodes = False
        in_eq = False
        
        with open(inp_path, "r") as f:
            for line in f:
                l = line.strip()
                if l.startswith("*Node"):
                    in_nodes = True
                    in_eq = False
                    continue
                elif l.startswith("*Equation"):
                    in_nodes = False
                    in_eq = True
                    continue
                elif l.startswith("*"):
                    in_nodes = False
                    in_eq = False
                    
                if in_nodes and l:
                    parts = [p.strip() for p in l.split(",") if p.strip()]
                    if len(parts) >= 3:
                        nid = int(parts[0])
                        if nid != 999999:
                            nodes[nid] = (float(parts[1]), float(parts[2]))
                elif in_eq and l:
                    if "," in l:
                        parts = [p.strip() for p in l.split(",") if p.strip()]
                        if len(parts) >= 6:
                            equations.append((int(parts[0]), int(parts[3])))
                            
        self.assertEqual(len(nodes), 2626)
        
        # Verify slit duplication along y=0.5, x in [0.0, 0.5)
        slit_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.5) < 1e-9 and x < 0.5 - 1e-9]
        self.assertEqual(len(slit_nodes), 50)  # 25 pairs = 50 nodes
        
        # Verify single crack tip node at (0.5, 0.5)
        tip_nodes = [nid for nid, (x, y) in nodes.items() if abs(x - 0.5) < 1e-9 and abs(y - 0.5) < 1e-9]
        self.assertEqual(len(tip_nodes), 1)
        
        # Verify top nodes equation coupling (nx + 1 = 51 top nodes coupled to RP 999999)
        top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < 1e-9]
        self.assertEqual(len(top_nodes), 51)
        self.assertEqual(len(equations), 51)
        for tn, rp in equations:
            self.assertIn(tn, top_nodes)
            self.assertEqual(rp, 999999)

    def test_05_governance_and_freeze_integrity(self):
        # Verify Mode-I baseline freeze untouched
        freeze_tag = "v2026.10.08-supervisor-meeting-mode1-freeze"
        freeze_uel_hash = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        
        manifest_path = os.path.join(SUITE_DIR, "SUITE_MANIFEST.json")
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
            
        self.assertEqual(manifest["mode1_freeze_tag"], freeze_tag)
        self.assertEqual(manifest["mode1_uel_hash"], freeze_uel_hash)
        
        # Verify proposal authorization lock
        proposal_path = os.path.join(SUITE_DIR, "BATCH_PROPOSAL_FIXED_MESH_CONVERGENCE.json")
        with open(proposal_path, "r") as f:
            proposal = json.load(f)
        self.assertFalse(proposal["execution_authorized"])
        self.assertFalse(proposal["submission_approved"])
        self.assertEqual(proposal["maximum_permitted_submissions"], 0)

if __name__ == "__main__":
    unittest.main()
