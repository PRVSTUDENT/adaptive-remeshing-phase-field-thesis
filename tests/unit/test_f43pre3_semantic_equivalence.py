#!/usr/bin/env python3
"""
test_f43pre3_semantic_equivalence.py

Unit tests for PRE2 vs PRE3 semantic equivalence validator script.
Tests canonical PRE2 vs PRE3 semantic equivalence PASS, and verifies fail-closed
detection of material mismatches, nu mismatches, endpoint mismatches, BC errors,
domain errors, missing output requests, and invalid element geometries.
"""

import os
import sys
import unittest
import tempfile
import json
import re

from scripts.validation.validate_f43pre3_semantic_equivalence import compare_decks

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRE2_PATH = os.path.join(REPO_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge", "F43PRE2_GEOM.inp")
PRE3_PATH = os.path.join(REPO_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge", "F43PRE3_GEOM.inp")

class TestPRE3SemanticEquivalence(unittest.TestCase):

    def test_canonical_pre2_vs_pre3_passes(self):
        res = compare_decks(PRE2_PATH, PRE3_PATH)
        self.assertTrue(res['overall_passed'], f"Canonical PRE2 vs PRE3 audit failed: {res.get('failures')}")
        self.assertEqual(res['continuum_model_semantic_identity'], "PASS")
        self.assertFalse(res['mesh_topology_identity'])
        self.assertEqual(res['mesh_difference_classification'], "accepted_discretization_difference_between_Abaqus2024_and_Abaqus2023_lineages")

    def test_material_mismatch_fails(self):
        with open(PRE3_PATH, 'r') as f:
            content = f.read()
        bad_content = content.replace("210000.", "200000.")
        with tempfile.NamedTemporaryFile('w', suffix='.inp', delete=False) as tf:
            tf.write(bad_content)
            tf_path = tf.name
        try:
            res = compare_decks(PRE2_PATH, tf_path)
            self.assertFalse(res['overall_passed'])
            self.assertIn("material_E", res['checks'])
            self.assertFalse(res['checks']['material_E'])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_nu_mismatch_fails(self):
        with open(PRE3_PATH, 'r') as f:
            content = f.read()
        bad_content = content.replace("210000., 0.3", "210000., 0.25")
        with tempfile.NamedTemporaryFile('w', suffix='.inp', delete=False) as tf:
            tf.write(bad_content)
            tf_path = tf.name
        try:
            res = compare_decks(PRE2_PATH, tf_path)
            self.assertFalse(res['overall_passed'])
            self.assertFalse(res['checks']['material_nu'])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_wrong_u1_endpoint_fails(self):
        with open(PRE3_PATH, 'r') as f:
            content = f.read()
        bad_content = content.replace("RP, 1, 1, 0.001", "RP, 1, 1, 0.002")
        with tempfile.NamedTemporaryFile('w', suffix='.inp', delete=False) as tf:
            tf.write(bad_content)
            tf_path = tf.name
        try:
            res = compare_decks(PRE2_PATH, tf_path)
            self.assertFalse(res['overall_passed'])
            self.assertFalse(res['checks']['load_endpoint_equivalence'])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_wrong_constrained_dof_fails(self):
        with open(PRE3_PATH, 'r') as f:
            content = f.read()
        bad_content = content.replace("bottom_nodes, 2, 2", "bottom_nodes, 3, 3")
        with tempfile.NamedTemporaryFile('w', suffix='.inp', delete=False) as tf:
            tf.write(bad_content)
            tf_path = tf.name
        try:
            res = compare_decks(PRE2_PATH, tf_path)
            self.assertFalse(res['overall_passed'])
            self.assertFalse(res['checks']['bc_dof_equivalence'])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_wrong_boundary_region_geometry_fails(self):
        with open(PRE3_PATH, 'r') as f:
            lines = f.readlines()
        new_lines = []
        in_part_node = False
        for l in lines:
            if l.strip().upper().startswith('*NODE'):
                in_part_node = True
                new_lines.append(l)
            elif l.strip().startswith('*'):
                in_part_node = False
                new_lines.append(l)
            elif in_part_node:
                p = [x.strip() for x in l.split(',')]
                if len(p) >= 3 and float(p[2]) == -0.5: # bottom nodes y = -0.5
                    p[2] = '0.0'
                    new_lines.append(f" {p[0]}, {p[1]}, {p[2]}\n")
                else:
                    new_lines.append(l)
            else:
                new_lines.append(l)
        bad_content = "".join(new_lines)
        with tempfile.NamedTemporaryFile('w', suffix='.inp', delete=False) as tf:
            tf.write(bad_content)
            tf_path = tf.name
        try:
            res = compare_decks(PRE2_PATH, tf_path)
            self.assertFalse(res['overall_passed'])
            self.assertFalse(res['checks']['bc_region_equivalence'])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_wrong_domain_bounds_fails(self):
        with open(PRE3_PATH, 'r') as f:
            lines = f.readlines()
        new_lines = []
        for l in lines:
            if '-0.5' in l:
                l = l.replace('-0.5', '-0.6')
            new_lines.append(l)
        bad_content = "".join(new_lines)
        with tempfile.NamedTemporaryFile('w', suffix='.inp', delete=False) as tf:
            tf.write(bad_content)
            tf_path = tf.name
        try:
            res = compare_decks(PRE2_PATH, tf_path)
            self.assertFalse(res['overall_passed'])
            self.assertFalse(res['checks']['domain_geometry'])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_wrong_notch_geometry_fails(self):
        with open(PRE3_PATH, 'r') as f:
            lines = f.readlines()
        new_lines = []
        in_part_node = False
        for l in lines:
            if l.strip().upper().startswith('*NODE'):
                in_part_node = True
                new_lines.append(l)
            elif l.strip().startswith('*'):
                in_part_node = False
                new_lines.append(l)
            elif in_part_node:
                p = [x.strip() for x in l.split(',')]
                if len(p) >= 3 and float(p[2]) == 0.0 and float(p[1]) <= 0.0:
                    p[2] = '0.1' # move notch nodes from y=0 to y=0.1
                    new_lines.append(f" {p[0]}, {p[1]}, {p[2]}\n")
                else:
                    new_lines.append(l)
            else:
                new_lines.append(l)
        bad_content = "".join(new_lines)
        with tempfile.NamedTemporaryFile('w', suffix='.inp', delete=False) as tf:
            tf.write(bad_content)
            tf_path = tf.name
        try:
            res = compare_decks(PRE2_PATH, tf_path)
            self.assertFalse(res['overall_passed'])
            self.assertFalse(res['checks']['notch_seam_equivalence'])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_missing_miseseri_fails(self):
        with open(PRE3_PATH, 'r') as f:
            content = f.read()
        bad_content = content.replace("MISESERI,", "")
        with tempfile.NamedTemporaryFile('w', suffix='.inp', delete=False) as tf:
            tf.write(bad_content)
            tf_path = tf.name
        try:
            res = compare_decks(PRE2_PATH, tf_path)
            self.assertFalse(res['overall_passed'])
            self.assertFalse(res['checks']['output_request_equivalence'])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_missing_misesavg_fails(self):
        with open(PRE3_PATH, 'r') as f:
            content = f.read()
        bad_content = content.replace("MISESAVG,", "")
        with tempfile.NamedTemporaryFile('w', suffix='.inp', delete=False) as tf:
            tf.write(bad_content)
            tf_path = tf.name
        try:
            res = compare_decks(PRE2_PATH, tf_path)
            self.assertFalse(res['overall_passed'])
            self.assertFalse(res['checks']['output_request_equivalence'])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_negative_element_area_fails(self):
        with open(PRE3_PATH, 'r') as f:
            lines = f.readlines()
        new_lines = []
        in_part_node = False
        modified = False
        for l in lines:
            if l.strip().upper().startswith('*NODE'):
                in_part_node = True
                new_lines.append(l)
            elif l.strip().startswith('*'):
                in_part_node = False
                new_lines.append(l)
            elif in_part_node and not modified:
                p = [x.strip() for x in l.split(',')]
                # set first node coordinates to NaN/huge or move to collapse quad
                p[1] = '10.0'
                p[2] = '10.0'
                new_lines.append(f" {p[0]}, {p[1]}, {p[2]}\n")
                modified = True
            else:
                new_lines.append(l)
        bad_content = "".join(new_lines)
        with tempfile.NamedTemporaryFile('w', suffix='.inp', delete=False) as tf:
            tf.write(bad_content)
            tf_path = tf.name
        try:
            res = compare_decks(PRE2_PATH, tf_path)
            self.assertFalse(res['overall_passed'])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

if __name__ == '__main__':
    unittest.main()
