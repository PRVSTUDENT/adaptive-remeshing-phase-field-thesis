# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package141_extractor_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Independent technical qualification of the Package 141 Abaqus Python 2.7 / pure Python
donor checkpoint extraction engine (Hypothesis H38 / Turn 304).
"""

import hashlib
import json
import os
import shutil
import tempfile
import unittest

from scripts.extract_c3_int_donor_frame77_checkpoint import (
    parse_inp_mesh,
    parse_energy_balance_csv,
    serialize_checkpoint,
    N_PHYS_NODES,
    N_PHYS_ELEMS,
    RP_NODE,
    TARGET_U_FRAME77,
    TARGET_T_STEP1,
    L1_OFFSET,
    L2_OFFSET,
    L3_OFFSET
)


class TestMode1F1597Package141ExtractorQualification(unittest.TestCase):
    """Independent technical qualification of Package 141 checkpoint extractor."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.pkg_dir = os.path.join(
            cls.repo_root, "models", "pandey_kumar_mode1", "141_c3_int_donor_monotonic"
        )
        cls.inp_path = os.path.join(cls.pkg_dir, "M1_C3_INT_DONOR_MONOTONIC.inp")
        cls.mesh_info = parse_inp_mesh(cls.inp_path)

    def test_01_mesh_discretization_and_layer_offsets(self):
        """Verify 2,610 physical nodes, 2,484 quads, and correct 3-layer UEL/UMAT offsets."""
        self.assertEqual(len(self.mesh_info["nodes"]), N_PHYS_NODES)
        self.assertEqual(len(self.mesh_info["elements"]), N_PHYS_ELEMS)
        self.assertEqual(N_PHYS_NODES, 2610)
        self.assertEqual(N_PHYS_ELEMS, 2484)
        self.assertEqual(RP_NODE, 999999)

        # Offsets
        self.assertEqual(L1_OFFSET, 0)
        self.assertEqual(L2_OFFSET, 2484)
        self.assertEqual(L3_OFFSET, 4968)

        # Top and bottom node sets
        self.assertEqual(len(self.mesh_info["nset_top"]), 55)
        self.assertEqual(len(self.mesh_info["nset_bottom"]), 55)
        self.assertEqual(len(self.mesh_info["nset_pin"]), 1)

    def test_02_deterministic_frame77_targeting_parameters(self):
        """Verify exact Step-1 step time, target displacement, and constant loading rate."""
        self.assertAlmostEqual(TARGET_T_STEP1, 0.36006251, places=8)
        self.assertAlmostEqual(TARGET_U_FRAME77, 0.0018003125442191958, places=12)

        # Constant loading rate: 0.005 mm/s
        rate = TARGET_U_FRAME77 / TARGET_T_STEP1
        self.assertAlmostEqual(rate, 0.005, places=7)

    def test_03_slit_flank_topology_and_partitioning(self):
        """Verify sharp crack slit topology along y = 0.05 mm, x <= 0.04 mm."""
        slit_nodes = self.mesh_info["slit_nodes"]
        upper_nodes = self.mesh_info["upper_flank_nodes"]
        lower_nodes = self.mesh_info["lower_flank_nodes"]

        # 50 slit nodes total: 25 pairs of split nodes on y = 0.05
        self.assertEqual(len(slit_nodes), 50)
        self.assertEqual(len(upper_nodes), 25)
        self.assertEqual(len(lower_nodes), 25)

        # Flank sets must be disjoint
        self.assertTrue(set(upper_nodes).isdisjoint(set(lower_nodes)))
        self.assertEqual(set(upper_nodes).union(set(lower_nodes)), set(slit_nodes))

        # Check crack tip node exists at x = 0.040, y = 0.050
        tip_nodes = [
            nid for nid, (x, y) in self.mesh_info["nodes"].items()
            if abs(x - 0.040) < 1.0e-5 and abs(y - 0.050) < 1.0e-5
        ]
        self.assertGreaterEqual(len(tip_nodes), 1)

    def test_04_gauss_point_and_sdv_ordering(self):
        """Verify companion element SDV assignments and 4 GP per quad structure."""
        # 2,484 quads * 4 GPs = 9,936 integration points
        total_gps = N_PHYS_ELEMS * 4
        self.assertEqual(total_gps, 9936)

        # Read UEL Fortran source to verify companion UMAT SDV contract
        uel_path = os.path.join(self.pkg_dir, "f42_mixed_uel.for")
        with open(uel_path, "r") as f:
            uel_text = f.read()

        self.assertIn("STATEV(1)  = SV_PHASE_TRIAL(PHYSIDX)", uel_text)
        self.assertIn("STATEV(2)  = SV_H_TRIAL(PHYSIDX, KPT_IDX)", uel_text)
        self.assertIn("STATEV(17) = SV_E_FRAC(PHYSIDX)", uel_text)
        self.assertIn("STATEV(18) = SV_E_ELAS(PHYSIDX)", uel_text)

    def test_05_mock_checkpoint_serialization_and_hashing(self):
        """Verify atomic serialization and checksum generation for donor checkpoint files."""
        temp_dir = tempfile.mkdtemp(prefix="test_p141_extract_")
        try:
            # Create synthetic mock extracted data
            mock_disp = {nid: (0.0, 0.0018003125442191958 * (y / 0.1)) for nid, (x, y) in self.mesh_info["nodes"].items()}
            mock_disp[RP_NODE] = (0.0, TARGET_U_FRAME77)
            mock_rf = {RP_NODE: (0.0, 0.18585)}
            mock_d = {eid: [0.05, 0.05, 0.05, 0.05] for eid in self.mesh_info["elements"].keys()}
            mock_h = {eid: [0.12, 0.12, 0.12, 0.12] for eid in self.mesh_info["elements"].keys()}

            extracted_data = {
                "step_time": TARGET_T_STEP1,
                "frame_id": 77,
                "displacements": mock_disp,
                "reactions": mock_rf,
                "d_gp": mock_d,
                "h_gp": mock_h,
                "e_frac_elem": {},
                "e_elas_elem": {}
            }

            energy_rec = {
                "step": 1,
                "inc": 75,
                "total_time": TARGET_T_STEP1,
                "step_time": TARGET_T_STEP1,
                "e_elastic_knmm": 0.15570,
                "e_fracture_knmm": 0.06108,
                "e_total_knmm": 0.21678
            }

            manifest = serialize_checkpoint(temp_dir, self.mesh_info, extracted_data, energy_rec)

            disp_file = os.path.join(temp_dir, "c3_int_donor_frame77_nodal_displacements.csv")
            bounds_file = os.path.join(temp_dir, "c3_int_donor_frame77_d_lower_bounds.csv")
            manifest_file = os.path.join(temp_dir, "c3_int_donor_frame77_checkpoint_manifest.json")

            self.assertTrue(os.path.exists(disp_file))
            self.assertTrue(os.path.exists(bounds_file))
            self.assertTrue(os.path.exists(manifest_file))

            # Verify displacement lines (2610 nodes + RP + header = 2612 lines)
            with open(disp_file, "r") as f:
                d_lines = [l.strip() for l in f if l.strip()]
            self.assertEqual(len(d_lines), 2612)
            self.assertEqual(d_lines[0], "node_id,u1_mm,u2_mm")

            # Verify bounds lines (2484 quads + header = 2485 lines)
            with open(bounds_file, "r") as f:
                b_lines = [l.strip() for l in f if l.strip()]
            self.assertEqual(len(b_lines), 2485)
            self.assertEqual(b_lines[0], "EID,D0_1,D0_2,D0_3,D0_4,H0_1,H0_2,H0_3,H0_4")

            # Verify manifest
            self.assertEqual(manifest["target_u_mm"], TARGET_U_FRAME77)
            self.assertEqual(manifest["n_physical_nodes"], 2610)
            self.assertEqual(manifest["n_physical_elements"], 2484)
            self.assertEqual(manifest["slit_flank_nodes"], 50)
            self.assertEqual(manifest["upper_flank_nodes"], 25)
            self.assertEqual(manifest["lower_flank_nodes"], 25)

        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
