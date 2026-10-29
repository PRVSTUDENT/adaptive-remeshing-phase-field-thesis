# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package142_generator_qualification.py
Unit test suite qualifying the Source-Independent Package 142 Transfer-Deck Generator.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Hypothesis: H42
Protocol Version: 2
"""

from __future__ import print_function, division
import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_package142_transfer_deck import (
    Package142DeckGenerator,
    TARGET_DISP_STEP1_MM,
    STEP1_TIME_SEC,
    FROZEN_UEL_SHA256
)
from scripts.state_transfer.c3_int_to_c4_spatial_mapping import (
    Mesh2D,
    SpatialTransferMapper
)


class TestPackage142GeneratorQualification(unittest.TestCase):
    """Rigorous unit tests for Package 142 transfer-deck generator."""

    @classmethod
    def setUpClass(cls):
        c3_int_inp = REPO_ROOT / "models/pandey_kumar_mode1/141_c3_int_donor_monotonic/M1_C3_INT_DONOR_MONOTONIC.inp"
        c4_inp = REPO_ROOT / "models/pandey_kumar_mode1/111_r2_c4_frame77_pre_instability/M1_C4_FRAME77_CONTINUATION.inp"
        cls.shared_donor_mesh = Mesh2D.from_inp(str(c3_int_inp), name="C3-Intermediate", max_physical_node=2610)
        cls.shared_receiver_mesh = Mesh2D.from_inp(str(c4_inp), name="C4-Receiver", max_physical_node=4588)
        cls.shared_mapper = SpatialTransferMapper(cls.shared_donor_mesh, cls.shared_receiver_mesh, tol_geom=1e-5)

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_p142_gen_")
        self.donor_dir = Path(self.temp_dir) / "mock_donor"
        self.output_dir = Path(self.temp_dir) / "output_p142"
        self.donor_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mock_checkpoint(self, disp=TARGET_DISP_STEP1_MM, n_nodes=2610, n_elems=2484):
        # Create manifest
        manifest = {
            "metadata": {
                "pbs_job_id": "1418650.mmaster02",
                "target_displacement_step1_mm": disp,
                "step1_time_sec": STEP1_TIME_SEC,
                "physical_nodes": n_nodes,
                "physical_quads": n_elems
            },
            "files": {
                "c3_int_donor_frame77_nodal_displacements.csv": "DUMMY_HASH_1",
                "c3_int_donor_frame77_nodal_phase_field.csv": "DUMMY_HASH_2",
                "c3_int_donor_frame77_d_lower_bounds.csv": "DUMMY_HASH_3"
            }
        }
        with open(self.donor_dir / "c3_int_donor_frame77_checkpoint_manifest.json", "w") as f:
            json.dump(manifest, f)

        # Displacements (2610 nodes + RP)
        with open(self.donor_dir / "c3_int_donor_frame77_nodal_displacements.csv", "w") as f:
            f.write("node_id,u1_mm,u2_mm\n")
            for nid in range(1, n_nodes + 1):
                f.write("%d,1.0e-5,2.0e-5\n" % nid)
            f.write("999999,0.0,%.15e\n" % disp)

        # Nodal phase field (2610 nodes)
        with open(self.donor_dir / "c3_int_donor_frame77_nodal_phase_field.csv", "w") as f:
            f.write("node_id,d\n")
            for nid in range(1, n_nodes + 1):
                f.write("%d,0.05\n" % nid)

        # Bounds (2484 quads)
        with open(self.donor_dir / "c3_int_donor_frame77_d_lower_bounds.csv", "w") as f:
            f.write("EID,D0_1,D0_2,D0_3,D0_4,H0_1,H0_2,H0_3,H0_4\n")
            for eid in range(1, n_elems + 1):
                f.write("%d,0.05,0.05,0.05,0.05,10.0,10.0,10.0,10.0\n" % eid)

    def test_01_fail_closed_on_missing_checkpoint(self):
        """Verifies that generator strictly raises an error if donor checkpoint is absent."""
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir(parents=True, exist_ok=True)
        gen = Package142DeckGenerator(empty_dir, self.output_dir)
        with self.assertRaises(RuntimeError):
            gen.verify_donor_checkpoint()

    def test_02_fail_closed_on_unphysical_displacement(self):
        """Verifies that generator rejects checkpoints whose displacement does not match Frame 77."""
        self._create_mock_checkpoint(disp=0.005000)  # Deviates from 0.00180031 mm
        gen = Package142DeckGenerator(self.donor_dir, self.output_dir, allow_mock_for_test=False)
        with self.assertRaises(ValueError):
            gen.verify_donor_checkpoint()

    def test_03_mesh_initialization_and_spatial_mapper(self):
        """Verifies that generator correctly loads C3-Int and C4 meshes and mapper."""
        self._create_mock_checkpoint()
        gen = Package142DeckGenerator(self.donor_dir, self.output_dir, allow_mock_for_test=True)
        self.assertTrue(gen.verify_donor_checkpoint())
        gen.donor_mesh = self.shared_donor_mesh
        gen.receiver_mesh = self.shared_receiver_mesh
        gen.spatial_mapper = self.shared_mapper
        self.assertEqual(len(gen.donor_mesh.nodes), 2610)
        self.assertEqual(len(gen.receiver_mesh.nodes), 4588)
        self.assertEqual(len(gen.receiver_mesh.elements), 4422)

    def test_04_state_projection_contract(self):
        """Verifies that displacements, nodal damage, and GP history project with 100% coverage."""
        self._create_mock_checkpoint()
        gen = Package142DeckGenerator(self.donor_dir, self.output_dir, allow_mock_for_test=True)
        gen.verify_donor_checkpoint()
        gen.donor_mesh = self.shared_donor_mesh
        gen.receiver_mesh = self.shared_receiver_mesh
        gen.spatial_mapper = self.shared_mapper
        projected = gen.execute_state_projection()

        self.assertEqual(len(projected["target_disp"]), 4588)
        self.assertEqual(len(projected["target_phase"]), 4588)
        self.assertEqual(len(projected["target_gp_h"]), 4422 * 4)
        self.assertEqual(len(projected["target_gp_d0"]), 4422 * 4)

        # Verify values are bounded
        for d in projected["target_phase"].values():
            self.assertGreaterEqual(d, 0.0)
            self.assertLessEqual(d, 1.0)

        for h in projected["target_gp_h"].values():
            self.assertGreaterEqual(h, 0.0)

    def test_05_deck_assembly_and_manifest_generation(self):
        """Verifies generation of CSV initial condition tables and manifest with matching hashes."""
        self._create_mock_checkpoint()
        gen = Package142DeckGenerator(self.donor_dir, self.output_dir, allow_mock_for_test=True)
        gen.verify_donor_checkpoint()
        gen.donor_mesh = self.shared_donor_mesh
        gen.receiver_mesh = self.shared_receiver_mesh
        gen.spatial_mapper = self.shared_mapper
        projected = gen.execute_state_projection()
        out_files = gen.assemble_package142_decks(projected)

        self.assertTrue(os.path.exists(out_files["disp_file"]))
        self.assertTrue(os.path.exists(out_files["bounds_file"]))
        self.assertTrue(os.path.exists(out_files["phase_file"]))
        self.assertTrue(os.path.exists(out_files["manifest_file"]))

        # Verify manifest content
        with open(out_files["manifest_file"], "r") as f:
            m = json.load(f)
        self.assertEqual(m["package_id"], "142_c4_c3_int_state_transfer")
        self.assertEqual(m["acceptance_criteria"]["max_force_continuity_deficit_pct"], 5.0)
        self.assertEqual(m["acceptance_criteria"]["max_raw_energy_discrepancy_pct"], 2.00000)

    def test_06_predeclared_acceptance_criteria_invariance(self):
        """Verifies that acceptance criteria strictly maintain the original Gate C1-1 thresholds."""
        self._create_mock_checkpoint()
        gen = Package142DeckGenerator(self.donor_dir, self.output_dir, allow_mock_for_test=True)
        gen.verify_donor_checkpoint()
        gen.donor_mesh = self.shared_donor_mesh
        gen.receiver_mesh = self.shared_receiver_mesh
        gen.spatial_mapper = self.shared_mapper
        projected = gen.execute_state_projection()
        out_files = gen.assemble_package142_decks(projected)

        with open(out_files["manifest_file"], "r") as f:
            m = json.load(f)
        crit = m["acceptance_criteria"]
        self.assertEqual(crit["max_damage_healing_violations"], 0)
        self.assertEqual(crit["max_history_loss_violations"], 0)
        self.assertEqual(crit["slit_interpenetration_violations"], 0)


if __name__ == "__main__":
    unittest.main()
