#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_release_crack_tip_nodes.py
Tests releasing the crack-tip nodes (1366, 1367, 1420, 1421) in Step 2
to see how Abaqus/Standard solves the free phase field.
"""

import os
import subprocess
from odbAccess import openOdb

# Read stage_a_all_d0_boundary_cards.inc
nodal_d0 = {}
with open("stage_a_all_d0_boundary_cards.inc", "r") as f:
    for line in f:
        line = line.strip()
        if line:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 4:
                nodal_d0[int(parts[0])] = float(parts[3])

# Release the crack tip nodes: 1366, 1367, 1420, 1421
released_nodes = {1366, 1367, 1420, 1421}
active_nodes = set(nodal_d0.keys()) - released_nodes

# Write active_set_boundary_cards.inc
with open("active_set_boundary_cards.inc", "w") as f:
    for nid in sorted(active_nodes):
        f.write("%d, 3, 3, %.8f\n" % (nid, nodal_d0[nid]))

print("Wrote active_set_boundary_cards.inc with %d active nodes (released %d crack-tip nodes)" %
      (len(active_nodes), len(released_nodes)))

# Run Abaqus
job_name = "TEST_RELEASE_CRACK_TIP"
cmd = ["abaqus", "job=" + job_name, "input=M1_C3_ACTIVE_SET_R12_CONTINUATION.inp",
       "user=f42_unified_12dof_active_set_uel.for", "cpus=1", "interactive"]
print("Running Abaqus test job: " + job_name)
subprocess.call(cmd)

# Inspect ODB
odb_path = job_name + ".odb"
if os.path.exists(odb_path):
    odb = openOdb(odb_path, readOnly=True)
    step2 = odb.steps["Inc1-Coupled"]
    last_frame = step2.frames[-1]

    u_field = last_frame.fieldOutputs["U"]
    rf_field = last_frame.fieldOutputs["RF"]

    rf2_rp = None
    d_vals = {}
    rf3_vals = {}

    for val in u_field.values:
        if val.nodeLabel == 999999:
            pass
        if val.nodeLabel in released_nodes:
            d_vals[val.nodeLabel] = val.data[2]

    for val in rf_field.values:
        if val.nodeLabel == 999999:
            rf2_rp = val.data[1] * 1000.0
        if val.nodeLabel in released_nodes:
            rf3_vals[val.nodeLabel] = val.data[2]

    odb.close()

    print("\n--- TEST JOB COMPLETED ---")
    print("RP RF2: %.6f N" % rf2_rp)
    for nid in sorted(released_nodes):
        d0 = nodal_d0[nid]
        d_new = d_vals.get(nid, 0.0)
        rf3_new = rf3_vals.get(nid, 0.0)
        print("  Node %d: d0=%.6f -> d_new=%.6f (Delta_d=%+.6f), RF3=%.3e" %
              (nid, d0, d_new, d_new - d0, rf3_new))
