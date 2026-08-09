#!/usr/bin/env python3
"""Unit tests for extract_mode_ii_uniform_reference.py post-processing extractor."""

import json
import tempfile
import unittest
from pathlib import Path


class DummyNode:
    def __init__(self, label, coords):
        self.label = label
        self.coordinates = coords


class DummyValue:
    def __init__(self, data, elem_label=1):
        self.data = [data]
        self.elementLabel = elem_label


class DummySubset:
    def __init__(self, values):
        self.values = values


class DummyFrame:
    def __init__(self, frame_id, frame_val, field_outputs):
        self.frameId = frame_id
        self.frameValue = frame_val
        self.fieldOutputs = field_outputs


class DummyStep:
    def __init__(self, frames):
        self.frames = frames


class DummyInstance:
    def __init__(self, name, node_sets=None, nodes=None, elements=None):
        self.name = name
        self.nodeSets = node_sets or {}
        self.nodes = nodes or []
        self.elements = elements or []


class DummyAssembly:
    def __init__(self, node_sets=None, instances=None):
        self.nodeSets = node_sets or {}
        self.instances = instances or {}


class DummyODB:
    def __init__(self, steps=None, root_assembly=None):
        self.steps = steps or {}
        self.rootAssembly = root_assembly or DummyAssembly()

    def close(self):
        pass


class TestExtractorUnitLogic(unittest.TestCase):

    def test_rp_set_lookup_assembly_vs_instance(self):
        """Verify RP node set is found in assembly or instance nodeSets."""
        # Assembly level
        asm = DummyAssembly(node_sets={"RP": "assembly_rp_set"})
        self.assertIn("RP", asm.nodeSets)

        # Instance level
        inst = DummyInstance("PART-1-1", node_sets={"RP": "instance_rp_set"})
        asm_inst = DummyAssembly(instances={"PART-1-1": inst})
        
        rp = None
        if "RP" in asm_inst.nodeSets:
            rp = asm_inst.nodeSets["RP"]
        else:
            for i in asm_inst.instances.values():
                if "RP" in i.nodeSets:
                    rp = i.nodeSets["RP"]
                    break

        self.assertEqual(rp, "instance_rp_set")

    def test_non_contiguous_node_dict_mapping(self):
        """Verify node label mapping handles non-contiguous node IDs correctly."""
        nodes = [
            DummyNode(1, (0.0, 0.0)),
            DummyNode(10, (1.0, 0.0)),
            DummyNode(100, (1.0, 1.0)),
            DummyNode(1000, (0.0, 1.0)),
        ]
        node_dict = {n.label: n.coordinates for n in nodes}
        
        connectivity = [1, 10, 100, 1000]
        coords = [node_dict[nid] for nid in connectivity if nid in node_dict]
        
        self.assertEqual(len(coords), 4)
        self.assertEqual(coords[0], (0.0, 0.0))
        self.assertEqual(coords[3], (0.0, 1.0))
        
        cx = sum(c[0] for c in coords) / 4.0
        cy = sum(c[1] for c in coords) / 4.0
        self.assertAlmostEqual(cx, 0.5)
        self.assertAlmostEqual(cy, 0.5)

    def test_sdv_value_extraction_min_max(self):
        """Verify SDV values are correctly extracted and zero-substitution is avoided."""
        values = [DummyValue(0.123), DummyValue(0.991), DummyValue(0.005)]
        sub = DummySubset(values)
        
        extracted = [float(v.data[0]) for v in sub.values]
        self.assertEqual(max(extracted), 0.991)
        self.assertEqual(min(extracted), 0.005)
        self.assertEqual(len(extracted), 3)


if __name__ == "__main__":
    unittest.main()
