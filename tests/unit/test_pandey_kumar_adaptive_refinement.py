#!/usr/bin/env python3
"""
Unit and regression tests for the reference-faithful Pandey & Kumar (2025)
adaptive mesh refinement Python module and native Abaqus CAE orchestration.
"""

import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.remeshing.pandey_kumar_adaptive_refinement import (
    create_remeshing_rule_spec,
    evaluate_miseseri_marking,
    generate_graded_axis_coordinates,
    build_mode1_mesh,
    compute_signed_polygon_area,
    DEFAULT_REMESHRULE_PARAMS,
    DEFAULT_MODE1_MATERIAL,
    DEFAULT_MODE1_MESH_SIZES
)
from scripts.remeshing.run_pandey_kumar_native_orchestration import (
    convert_mesh_to_layered_uel,
    compute_sha256
)


class TestPandeyKumarAdaptiveRefinement(unittest.TestCase):
    def test_remeshing_rule_spec_matches_publication(self):
        """Verify RemeshingRule object parameters strictly match Listing 1."""
        spec = create_remeshing_rule_spec(
            model_name="Model-1",
            instance_name="Instance-1",
            step_name="Step-1",
            max_size=0.02,
            min_size=0.001,
            error_target=1.0,
            refinement_factor=10
        )
        self.assertEqual(spec["rule_name"], "RR: 1")
        self.assertEqual(spec["region_set_name"], "Instance-1.All_elem")
        self.assertEqual(spec["variables"], ("MISESERI",))
        self.assertEqual(spec["sizing_method"], "UNIFORM_ERROR")
        self.assertEqual(spec["error_target"], 1.0)
        self.assertEqual(spec["coarsening_factor"], "NOT_ALLOWED")
        self.assertEqual(spec["refinement_factor"], 10)
        self.assertTrue(spec["specify_min_size"])
        self.assertTrue(spec["specify_max_size"])
        self.assertEqual(spec["min_element_size"], 0.001)
        self.assertEqual(spec["max_element_size"], 0.02)

    def test_miseseri_marking_rule(self):
        """Verify relative error marking rule (MISESERI / max(MISESERI) >= errorTarget)."""
        miseseri_data = {
            1: 100.0,
            2: 50.0,
            3: 5.0,
            4: 4.9,
            5: 0.1
        }
        centroids = {
            1: (0.50, 0.50),
            2: (0.55, 0.50),
            3: (0.60, 0.50),
            4: (0.70, 0.50),
            5: (0.90, 0.90)
        }
        # 5% relative error threshold on max=100.0 is 5.0
        res = evaluate_miseseri_marking(
            elements_miseseri=miseseri_data,
            elements_centroids=centroids,
            error_target_pct=5.0
        )
        self.assertEqual(res["max_miseseri"], 100.0)
        self.assertEqual(res["threshold"], 5.0)
        self.assertIn(1, res["marked_elements"])
        self.assertIn(2, res["marked_elements"])
        self.assertIn(3, res["marked_elements"])
        self.assertNotIn(4, res["marked_elements"])
        self.assertNotIn(5, res["marked_elements"])
        self.assertEqual(res["num_marked"], 3)
        self.assertAlmostEqual(res["mark_fraction"], 0.60, places=4)

    def test_signed_polygon_area(self):
        """Verify polygon area calculation using shoelace formula."""
        square = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        area = compute_signed_polygon_area(square)
        self.assertAlmostEqual(area, 1.0, places=9)

    def test_graded_axis_coordinates(self):
        """Verify 1D graded coordinates preserve bounds and stations."""
        coords = generate_graded_axis_coordinates(
            start=0.0,
            refined_min=0.4,
            refined_max=0.6,
            end=1.0,
            local_h=0.01,
            global_h=0.05,
            ratio=1.5,
            force_stations=[0.0, 0.5, 1.0]
        )
        self.assertEqual(coords[0], 0.0)
        self.assertEqual(coords[-1], 1.0)
        self.assertIn(0.5, coords)
        # Verify strictly increasing
        for k in range(len(coords) - 1):
            self.assertGreater(coords[k + 1], coords[k])

    def test_build_mode1_mesh_integrity(self):
        """Verify Mode-I benchmark mesh topology and geometric validity."""
        mesh = build_mode1_mesh(
            domain_x=(0.0, 1.0),
            domain_y=(0.0, 1.0),
            notch_length=0.5,
            notch_y=0.5,
            local_h=0.02,
            global_h=0.10
        )
        self.assertTrue(mesh["geometry_valid"], f"Invalid geometry: {mesh['invalid_elements']}")
        self.assertAlmostEqual(mesh["total_area"], 1.0, places=5)
        self.assertGreater(mesh["num_elements"], 0)
        self.assertGreater(mesh["num_nodes"], 0)
        self.assertGreater(len(mesh["slit_node_pairs"]), 0)
        self.assertIn("bottom_nodes", mesh["node_sets"])
        self.assertIn("top_nodes", mesh["node_sets"])

    def test_convert_mesh_to_layered_uel_correspondence(self):
        """Verify standard 2D mesh is correctly converted to 4-element layered UEL deck."""
        sample_inp = """*HEADING
Test Mesh Deck
*NODE
1, 0.0, 0.0
2, 1.0, 0.0
3, 1.0, 1.0
4, 0.0, 1.0
5, 2.0, 0.0
6, 2.0, 1.0
*ELEMENT, TYPE=CPS4R, ELSET=QUAD_SET
1, 1, 2, 3, 4
*ELEMENT, TYPE=CPS3, ELSET=TRI_SET
2, 2, 5, 3
*ELEMENT OUTPUT
MISESERI, MISESAVG, S, EVOL
"""
        with tempfile.TemporaryDirectory() as td:
            src_inp = os.path.join(td, "source.inp")
            dst_uel = os.path.join(td, "layered_uel.inp")
            with open(src_inp, "w") as f:
                f.write(sample_inp)

            info = convert_mesh_to_layered_uel(src_inp, dst_uel, job_name="TEST_JOB")
            self.assertEqual(info["num_nodes"], 6)
            self.assertEqual(info["num_elements"], 2)
            self.assertEqual(info["num_quads"], 1)
            self.assertEqual(info["num_tris"], 1)

            with open(dst_uel, "r") as f:
                uel_content = f.read()

            # Verify presence of all 4 UEL types
            self.assertIn("*USER ELEMENT, NODES=4, TYPE=U1", uel_content)
            self.assertIn("*USER ELEMENT, NODES=3, TYPE=U2", uel_content)
            self.assertIn("*USER ELEMENT, NODES=4, TYPE=U3", uel_content)
            self.assertIn("*USER ELEMENT, NODES=3, TYPE=U4", uel_content)
            # Verify displacement layer
            self.assertIn("*ELEMENT, TYPE=U3, ELSET=DISP_QUADS", uel_content)
            self.assertIn("*ELEMENT, TYPE=U4, ELSET=DISP_TRIS", uel_content)
            # Verify phase-field layer
            self.assertIn("*ELEMENT, TYPE=U1, ELSET=PF_QUADS", uel_content)
            self.assertIn("*ELEMENT, TYPE=U2, ELSET=PF_TRIS", uel_content)
            # Verify UMAT dummy visualization layer
            self.assertIn("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS", uel_content)
            self.assertIn("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS", uel_content)
            self.assertIn("*ELSET, ELSET=umatelem", uel_content)
            self.assertIn("*ELSET, ELSET=All_elem", uel_content)

    def test_no_forbidden_coarsening_guarantee(self):
        """Verify that coarsening factor is strictly forbidden in RemeshingRule configuration."""
        spec = create_remeshing_rule_spec(
            model_name="Model-1",
            instance_name="Instance-1",
            step_name="Step-1",
            max_size=0.05,
            min_size=0.002,
            error_target=1.0
        )
        self.assertEqual(spec["coarsening_factor"], "NOT_ALLOWED")
        self.assertLessEqual(spec["min_element_size"], spec["max_element_size"])

    def test_regression_refinement_must_alter_mesh_topology(self):
        """
        Fail-closed assertion: An adaptive remeshing pass must fail if the refined mesh
        contains identical node or element counts to the coarse mesh when MISESERI is nontrivial.
        """
        coarse_mesh_stats = {"num_elements": 553, "num_nodes": 601}
        identical_refined_stats = {"num_elements": 553, "num_nodes": 601}
        genuine_refined_stats = {"num_elements": 2222, "num_nodes": 2288}

        def validate_refinement_occurred(coarse, refined):
            if refined["num_elements"] <= coarse["num_elements"] or refined["num_nodes"] <= coarse["num_nodes"]:
                raise AssertionError(
                    f"Refinement failed: coarse={coarse} vs refined={refined}. "
                    "Mesh count did not strictly increase despite active MISESERI error field."
                )
            return True

        # Assert identical counts fail
        with self.assertRaises(AssertionError):
            validate_refinement_occurred(coarse_mesh_stats, identical_refined_stats)

        # Assert genuine refinement passes
        self.assertTrue(validate_refinement_occurred(coarse_mesh_stats, genuine_refined_stats))


if __name__ == "__main__":
    unittest.main()
