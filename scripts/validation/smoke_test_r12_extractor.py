#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
smoke_test_r12_extractor.py
Tests the corrected repository-compatible extractor directly against
the authentic cluster ODB: M1_C3_ACTIVE_SET_R12_IT1.odb under Abaqus Python.
"""

import sys
import os
import json
from odbAccess import openOdb

def run_smoke_test(odb_path, bounds_path):
    print("--- Running Smoke Test on Authentic R12 IT1 ODB ---")
    print("ODB Path: " + odb_path)

    if not os.path.exists(odb_path):
        raise RuntimeError("ODB file not found: " + odb_path)

    # 1. Load bounds to know d0 for every node
    nodal_d0 = {}
    with open(bounds_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 4:
                    nid = int(parts[0])
                    d0 = float(parts[3])
                    nodal_d0[nid] = d0

    print("Loaded %d nodes with d0 lower bounds" % len(nodal_d0))

    # 2. Open ODB
    odb = openOdb(odb_path, readOnly=True)
    step_names = list(odb.steps.keys())
    print("ODB Steps found: " + str(step_names))

    if "Inc1-Coupled" not in odb.steps:
        odb.close()
        raise RuntimeError("Mandatory Step 'Inc1-Coupled' missing in ODB")

    step2 = odb.steps["Inc1-Coupled"]
    if len(step2.frames) == 0:
        odb.close()
        raise RuntimeError("No frames found in Step 'Inc1-Coupled'")

    last_frame = step2.frames[-1]
    print("Last frame value (Step 2): %.6f" % last_frame.frameValue)

    # 3. Check mandatory field outputs using Repository-compatible membership test
    if "U" not in last_frame.fieldOutputs:
        odb.close()
        raise RuntimeError("Mandatory field output 'U' missing in Step 2 frame")
    if "RF" not in last_frame.fieldOutputs:
        odb.close()
        raise RuntimeError("Mandatory field output 'RF' missing in Step 2 frame")

    u_field = last_frame.fieldOutputs["U"]
    rf_field = last_frame.fieldOutputs["RF"]

    # 4. Extract fields
    u_vals = {}
    rf_vals = {}
    rf2_rp = None
    u2_rp = None

    for val in u_field.values:
        nid = val.nodeLabel
        if nid == 999999:
            u2_rp = float(val.data[1])
        if len(val.data) >= 3:
            u_vals[nid] = (float(val.data[0]), float(val.data[1]), float(val.data[2]))

    for val in rf_field.values:
        nid = val.nodeLabel
        if nid == 999999:
            rf2_rp = float(val.data[1] * 1000.0) # to N
        if len(val.data) >= 3:
            rf_vals[nid] = (float(val.data[0]), float(val.data[1]), float(val.data[2]))

    # Extract energies
    energies = {}
    for key, reg in step2.historyRegions.items():
        for e_key, series in reg.historyOutputs.items():
            if len(series.data) > 0:
                energies[e_key] = series.data[-1][1]

    odb.close()

    print("Successfully extracted fields from ODB:")
    print("  RP Node 999999 U2: %.11f mm" % u2_rp)
    print("  RP Node 999999 RF2: %.6f N" % rf2_rp)
    print("  Total U nodes extracted: %d" % len(u_vals))
    print("  Total RF nodes extracted: %d" % len(rf_vals))
    print("  ALLSE: %.6f mJ" % (energies.get("ALLSE", 0.0) * 1000.0))

    # 5. Verify physical measurements
    target_u2 = 0.00196610735
    u2_err = abs(u2_rp - target_u2)
    print("  U2 Discrepancy vs Target: %.2e mm (tolerance <= 1e-7 mm)" % u2_err)
    if u2_err > 1.0e-7:
        raise RuntimeError("RP U2 discrepancy exceeds 1e-7 mm: %.2e" % u2_err)

    # In Iteration 1, all nodes were active
    tau_release = 5.0e-7 # kN/mm
    release_candidates = []
    min_lambda = 0.0
    max_lambda = 0.0

    for nid, d0 in nodal_d0.items():
        if nid in rf_vals:
            rf3 = rf_vals[nid][2]
            if rf3 < min_lambda:
                min_lambda = rf3
            if rf3 > max_lambda:
                max_lambda = rf3
            if rf3 < -tau_release:
                release_candidates.append((nid, rf3))

    print("  Active Multiplier Range (RF3): [%.3e, %.3e] kN/mm" % (min_lambda, max_lambda))
    print("  Nodes violating KKT dual feasibility (RF3 < -%.1e): %d" % (tau_release, len(release_candidates)))

    # 6. Verify writing valid revised active_set_boundary_cards.inc
    active_nodes = set(nodal_d0.keys())
    for nid, _ in release_candidates:
        active_nodes.discard(nid)

    test_inc_path = "test_revised_active_set_cards.inc"
    with open(test_inc_path, "w") as f:
        for nid in sorted(active_nodes):
            f.write("%d, 3, 3, %.8f\n" % (nid, nodal_d0[nid]))

    print("  Wrote revised active-set cards: %d active nodes (released %d nodes)" %
          (len(active_nodes), len(release_candidates)))

    # Clean up test inc file
    if os.path.exists(test_inc_path):
        os.remove(test_inc_path)

    result_summary = {
        "status": "SMOKE_TEST_PASS",
        "u2_rp_mm": u2_rp,
        "rf2_rp_N": rf2_rp,
        "allse_mJ": energies.get("ALLSE", 0.0) * 1000.0,
        "min_lambda": min_lambda,
        "max_lambda": max_lambda,
        "release_count": len(release_candidates),
        "total_nodes": len(nodal_d0)
    }

    print("\nSMOKE TEST COMPLETED SUCCESSFULLY!")
    print(json.dumps(result_summary, indent=2))
    return result_summary

if __name__ == "__main__":
    odb_p = sys.argv[1] if len(sys.argv) > 1 else "M1_C3_ACTIVE_SET_R12_IT1.odb"
    bounds_p = sys.argv[2] if len(sys.argv) > 2 else "stage_a_all_d0_boundary_cards.inc"
    run_smoke_test(odb_p, bounds_p)
