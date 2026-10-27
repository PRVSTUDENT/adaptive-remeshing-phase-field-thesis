"""
Unit regression test for Package 116 forensic diagnosis and mesh reconciliation.
Verifies:
1. Package 116 *UEL PROPERTY card permutation defect.
2. Expected PROPS order in f42_unified_12dof_active_set_uel.for.
3. C4 node count reconciliation (4588 physical nodes + 1 RP = 4589 total, 4556 unique coords, 32 slit duplicates).
4. C3-Int node count verification (2610 physical nodes + 1 RP = 2611 total, 2585 unique coords, 25 slit duplicates).
"""

import os
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

class TestPackage116ForensicAudit(unittest.TestCase):

    def test_c4_node_counts(self):
        c4_inp = os.path.join(REPO_ROOT, "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/M1_C4_INC79_DIRECT_TRANSFER.inp")
        self.assertTrue(os.path.exists(c4_inp), "C4 inp deck must exist")

        nodes = {}
        in_node = False
        with open(c4_inp, "r") as f:
            for line in f:
                l = line.strip()
                if l.upper().startswith("*NODE") and not any(l.upper().startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    in_node = True
                    continue
                elif in_node and l.startswith("*"):
                    in_node = False
                if in_node and l and not l.startswith("**"):
                    p = l.split(",")
                    nid = int(p[0].strip())
                    nodes[nid] = (float(p[1]), float(p[2]))

        # Physical nodes without RP 999999
        self.assertIn(999999, nodes)
        del nodes[999999]
        self.assertEqual(len(nodes), 4588, "C4 physical nodes must equal 4588")

        unique_coords = set((round(x, 7), round(y, 7)) for x, y in nodes.values())
        self.assertEqual(len(unique_coords), 4556, "C4 unique coords must equal 4556")
        self.assertEqual(len(nodes) - len(unique_coords), 32, "C4 slit flank duplicates must equal 32")

    def test_c3_int_node_counts(self):
        c3_int_inp = os.path.join(REPO_ROOT, "models/pandey_kumar_mode1/116_c3_int_inc79_direct_transfer/M1_C3_INT_INC79_DIRECT_TRANSFER.inp")
        self.assertTrue(os.path.exists(c3_int_inp), "C3-Int inp deck must exist")

        nodes = {}
        in_node = False
        with open(c3_int_inp, "r") as f:
            for line in f:
                l = line.strip()
                if l.upper().startswith("*NODE") and not any(l.upper().startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    in_node = True
                    continue
                elif in_node and l.startswith("*"):
                    in_node = False
                if in_node and l and not l.startswith("**"):
                    p = l.split(",")
                    nid = int(p[0].strip())
                    nodes[nid] = (float(p[1]), float(p[2]))

        self.assertIn(999999, nodes)
        del nodes[999999]
        self.assertEqual(len(nodes), 2610, "C3-Int physical nodes must equal 2610")

        unique_coords = set((round(x, 7), round(y, 7)) for x, y in nodes.values())
        self.assertEqual(len(unique_coords), 2585, "C3-Int unique coords must equal 2585")
        self.assertEqual(len(nodes) - len(unique_coords), 25, "C3-Int slit flank duplicates must equal 25")

    def test_uel_property_order(self):
        uel_src = os.path.join(REPO_ROOT, "models/pandey_kumar_mode1/116_c3_int_inc79_direct_transfer/f42_unified_12dof_active_set_uel.for")
        self.assertTrue(os.path.exists(uel_src))

        # Check expected PROPS indices
        with open(uel_src, "r") as f:
            content = f.read()
        self.assertIn("E_L0  = PROPS(1)", content)
        self.assertIn("E_GC  = PROPS(2)", content)
        self.assertIn("E_MOD = PROPS(3)", content)
        self.assertIn("E_NU  = PROPS(4)", content)
        self.assertIn("E_K   = PROPS(5)", content)

    def test_forensic_audit_artifact(self):
        audit_path = os.path.join(REPO_ROOT, "results/validation/c3_int_package116_terminal_failure_forensic_audit.json")
        self.assertTrue(os.path.exists(audit_path))
        with open(audit_path, "r") as f:
            data = json.load(f)
        self.assertEqual(data["scientific_classification"], "INTERMEDIATE_MESH_NUMERICAL_FAILURE")
        self.assertEqual(data["root_cause_diagnosis"]["defect_type"], "UEL_PROPERTY_CARD_PARAMETER_PERMUTATION")
        self.assertEqual(data["c4_node_count_reconciliation"]["reconciled_physical_abaqus_nodes"], 4588)

if __name__ == "__main__":
    unittest.main()
