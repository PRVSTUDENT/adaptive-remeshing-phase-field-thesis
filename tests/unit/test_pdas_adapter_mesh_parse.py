#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import numpy as np
from pathlib import Path
import sys

class TestPDASAdapterMeshParse(unittest.TestCase):
    def test_mesh_parsing(self):
        mesh_path = Path("models/pandey_kumar_mode1/98_pdas_chatter_repair_pilot/candidate_crack_band_mesh_c5.inp")
        nodes = {}
        with open(mesh_path, "r", encoding="utf-8") as f:
            in_node = False
            for line in f:
                line = line.strip()
                u = line.upper()
                if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    in_node = True
                    continue
                elif line.startswith("*") and in_node:
                    in_node = False
                    continue
                if in_node and line:
                    parts = [p.strip() for p in line.split(",")]
                    nid = int(parts[0])
                    if nid != 999999:
                        nodes[nid] = (float(parts[1]), float(parts[2]))
        self.assertEqual(len(nodes), 4610)
        self.assertIn(1, nodes)
        self.assertIn(4610, nodes)

    def test_adapter_load_mesh_and_state(self):
        # Test full adapter class with the patched parsing
        adapter_path = Path("models/pandey_kumar_mode1/98_pdas_chatter_repair_pilot/pdas_cluster_execution_adapter.py")
        with open(adapter_path, "r", encoding="utf-8") as f:
            code = f.read()

        fixed_code = code.replace(
            'if line.startswith("*Node") or line.startswith("*NODE"):',
            'u = line.upper()\n                if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):'
        )

        mod = {}
        exec(fixed_code, mod)
        Adapter = mod["PDASClusterExecutionAdapter"]

        adapter = Adapter(
            seed_deck_path="models/pandey_kumar_mode1/98_pdas_chatter_repair_pilot/M1_C5_PACKAGE98_SEED_TRANSFER.inp",
            mesh_inp_path="models/pandey_kumar_mode1/98_pdas_chatter_repair_pilot/candidate_crack_band_mesh_c5.inp",
            state_table_path="models/pandey_kumar_mode1/98_pdas_chatter_repair_pilot/candidate_c5_frame7_mapped_state_table.csv",
            uel_path="models/pandey_kumar_mode1/98_pdas_chatter_repair_pilot/f42_mixed_uel.for",
            work_dir="models/pandey_kumar_mode1/98_pdas_chatter_repair_pilot",
            delta_u_nm=4.0,
            k_max=25,
            mode="local_mock"
        )
        self.assertEqual(adapter.n_nodes, 4610)
        self.assertEqual(len(adapter.elements), 4440)
        self.assertEqual(len(adapter.elem_h), 4440)
        self.assertAlmostEqual(adapter.d_ckpt.max(), 0.9971, places=3)
        self.assertAlmostEqual(adapter.d_ckpt.min(), 0.0, places=4)

if __name__ == "__main__":
    unittest.main()
