"""Unit tests for Turn 257: Persistent state checkpointing and reconstruction qualification.

Validates:
1. Complete round-trip serialization/deserialization for 4,588 nodes and 17,688 Gauss points.
2. Exact export of UEL-compatible files (d_lower_bounds.csv, nodal_displacements.csv, active_set_boundary_cards.inc).
3. Rejection of partial or corrupted checkpoints (missing nodes, non-finite values, out-of-bounds damage).
4. Irreversibility enforcement (detection of healing violations).
5. Restoration function for same-mesh continuation.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scripts.driver.mode1_am_state_checkpoint import (
    serialize_checkpoint,
    load_and_validate_checkpoint,
    restore_coupled_state_for_continuation,
    EXPECTED_NODE_COUNT,
    EXPECTED_ELEMENT_COUNT,
    TOTAL_GP_COUNT
)


class TestMode1F1597Turn257StateCheckpointSerialization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix="am_checkpoint_test_")
        # Build synthetic 4,588 nodes and 4,422 quads matching C4 topology
        cls.nodes = {i: (float(i) * 0.001, float(i) * 0.002) for i in range(1, EXPECTED_NODE_COUNT + 1)}
        cls.elements = {}
        for eid in range(1, EXPECTED_ELEMENT_COUNT + 1):
            n1 = (eid % EXPECTED_NODE_COUNT) + 1
            n2 = ((eid + 1) % EXPECTED_NODE_COUNT) + 1
            n3 = ((eid + 2) % EXPECTED_NODE_COUNT) + 1
            n4 = ((eid + 3) % EXPECTED_NODE_COUNT) + 1
            cls.elements[eid] = [n1, n2, n3, n4]

        cls.u_nodal = {i: (1e-4 * (i % 10), 2e-4 * (i % 10)) for i in cls.nodes}
        cls.d_nodal = {i: 0.1 + 0.0001 * (i % 100) for i in cls.nodes}
        cls.h_committed = {eid: [0.005 + 0.001 * k for k in range(4)] for eid in cls.elements}

        cls.metrics = {
            "rf2_rp_N": 183.807775,
            "d_max": 0.624108,
            "e_elas_mJ": 0.177283,
            "e_frac_mJ": 0.055780,
            "e_tot_mJ": 0.233063,
            "cycles_completed": 12,
            "stationarity_converged": True
        }
        cls.parameters = {
            "E_GPa": 210.0,
            "nu": 0.3,
            "Gc_N_mm": 2.7,
            "l0_mm": 0.0075
        }
        cls.provenance = {
            "source_package": "PACKAGE_123_C4_INC86_HOLDOUT_DIAGNOSTIC",
            "donor_increment": 86,
            "uel_sha256": "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"
        }

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_01_round_trip_serialization_and_deserialization(self):
        ckpt_dir = os.path.join(self.test_dir, "roundtrip")
        receipt = serialize_checkpoint(
            output_dir=ckpt_dir,
            mesh_info={"name": "Candidate C4"},
            nodes=self.nodes,
            elements=self.elements,
            u_nodal=self.u_nodal,
            d_nodal=self.d_nodal,
            h_committed=self.h_committed,
            cycle=12,
            metrics=self.metrics,
            parameters=self.parameters,
            source_provenance=self.provenance,
            checkpoint_basename="test_c4_checkpoint"
        )

        self.assertEqual(receipt["node_count"], EXPECTED_NODE_COUNT)
        self.assertEqual(receipt["element_count"], EXPECTED_ELEMENT_COUNT)
        self.assertEqual(receipt["gp_count"], TOTAL_GP_COUNT)

        # Validate deserialization
        loaded = load_and_validate_checkpoint(receipt["checkpoint_json_path"])
        self.assertEqual(len(loaded["u_nodal"]), EXPECTED_NODE_COUNT)
        self.assertEqual(len(loaded["d_nodal"]), EXPECTED_NODE_COUNT)
        self.assertEqual(len(loaded["h_committed"]), EXPECTED_ELEMENT_COUNT)

        # Check values match exactly
        self.assertAlmostEqual(loaded["u_nodal"][1][0], self.u_nodal[1][0], places=9)
        self.assertAlmostEqual(loaded["d_nodal"][1], self.d_nodal[1], places=9)
        self.assertAlmostEqual(loaded["h_committed"][1][0], self.h_committed[1][0], places=9)

    def test_02_exported_files_integrity(self):
        ckpt_dir = os.path.join(self.test_dir, "files_check")
        receipt = serialize_checkpoint(
            output_dir=ckpt_dir,
            mesh_info={"name": "Candidate C4"},
            nodes=self.nodes,
            elements=self.elements,
            u_nodal=self.u_nodal,
            d_nodal=self.d_nodal,
            h_committed=self.h_committed,
            cycle=12,
            metrics=self.metrics,
            parameters=self.parameters,
            source_provenance=self.provenance,
            checkpoint_basename="exported_check"
        )

        self.assertTrue(os.path.isfile(receipt["bounds_csv_path"]))
        self.assertTrue(os.path.isfile(receipt["disp_csv_path"]))
        self.assertTrue(os.path.isfile(receipt["cards_inc_path"]))

        # Count lines in d_lower_bounds.csv: 1 header + 4422 data lines
        with open(receipt["bounds_csv_path"], "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), EXPECTED_ELEMENT_COUNT + 1)

        # Count lines in nodal_displacements.csv: 1 header + 4588 data lines
        with open(receipt["disp_csv_path"], "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), EXPECTED_NODE_COUNT + 1)

        # Count lines in active_set_cards.inc: 4588 data lines
        with open(receipt["cards_inc_path"], "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), EXPECTED_NODE_COUNT)

    def test_03_rejection_of_corrupt_data(self):
        corrupt_dir = os.path.join(self.test_dir, "corrupt")

        # 1. Missing node
        incomplete_u = {k: v for k, v in list(self.u_nodal.items())[:-1]}
        with self.assertRaises(ValueError):
            serialize_checkpoint(
                output_dir=corrupt_dir,
                mesh_info={"name": "Candidate C4"},
                nodes=self.nodes,
                elements=self.elements,
                u_nodal=incomplete_u,
                d_nodal=self.d_nodal,
                h_committed=self.h_committed,
                cycle=12,
                metrics=self.metrics,
                parameters=self.parameters,
                source_provenance=self.provenance
            )

        # 2. Non-finite damage (NaN)
        nan_d = self.d_nodal.copy()
        nan_d[1] = float("nan")
        with self.assertRaises(ValueError):
            serialize_checkpoint(
                output_dir=corrupt_dir,
                mesh_info={"name": "Candidate C4"},
                nodes=self.nodes,
                elements=self.elements,
                u_nodal=self.u_nodal,
                d_nodal=nan_d,
                h_committed=self.h_committed,
                cycle=12,
                metrics=self.metrics,
                parameters=self.parameters,
                source_provenance=self.provenance
            )

        # 3. Negative driving energy
        neg_h = {eid: [-0.01, 0.0, 0.0, 0.0] if eid == 1 else h for eid, h in self.h_committed.items()}
        with self.assertRaises(ValueError):
            serialize_checkpoint(
                output_dir=corrupt_dir,
                mesh_info={"name": "Candidate C4"},
                nodes=self.nodes,
                elements=self.elements,
                u_nodal=self.u_nodal,
                d_nodal=self.d_nodal,
                h_committed=neg_h,
                cycle=12,
                metrics=self.metrics,
                parameters=self.parameters,
                source_provenance=self.provenance
            )

    def test_04_irreversibility_enforcement(self):
        ckpt_dir = os.path.join(self.test_dir, "irreversibility")
        receipt = serialize_checkpoint(
            output_dir=ckpt_dir,
            mesh_info={"name": "Candidate C4"},
            nodes=self.nodes,
            elements=self.elements,
            u_nodal=self.u_nodal,
            d_nodal=self.d_nodal,
            h_committed=self.h_committed,
            cycle=12,
            metrics=self.metrics,
            parameters=self.parameters,
            source_provenance=self.provenance,
            checkpoint_basename="irrev_test"
        )

        # Normal load with lower prior bounds (no healing) -> pass
        prior_bounds_ok = {i: 0.05 for i in self.nodes}
        loaded = load_and_validate_checkpoint(receipt["checkpoint_json_path"], prior_d_lower=prior_bounds_ok)
        self.assertIsNotNone(loaded)

        # Healing violation: prior bounds higher than checkpoint damage -> fail
        prior_bounds_violating = {i: 0.90 for i in self.nodes}
        with self.assertRaises(ValueError):
            load_and_validate_checkpoint(receipt["checkpoint_json_path"], prior_d_lower=prior_bounds_violating)

    def test_05_continuation_restoration_procedure(self):
        ckpt_dir = os.path.join(self.test_dir, "restore_src")
        receipt = serialize_checkpoint(
            output_dir=ckpt_dir,
            mesh_info={"name": "Candidate C4"},
            nodes=self.nodes,
            elements=self.elements,
            u_nodal=self.u_nodal,
            d_nodal=self.d_nodal,
            h_committed=self.h_committed,
            cycle=12,
            metrics=self.metrics,
            parameters=self.parameters,
            source_provenance=self.provenance,
            checkpoint_basename="restore_source"
        )

        target_dir = os.path.join(self.test_dir, "continuation_target")
        restored = restore_coupled_state_for_continuation(
            checkpoint_json_path=receipt["checkpoint_json_path"],
            target_dir=target_dir
        )

        self.assertTrue(os.path.isfile(restored["d_lower_bounds_csv"]))
        self.assertTrue(os.path.isfile(restored["nodal_displacements_csv"]))
        self.assertTrue(os.path.isfile(restored["active_set_boundary_cards_inc"]))


if __name__ == "__main__":
    unittest.main()
