# -*- coding: utf-8 -*-
"""
extract_case3_step1_donor_fields.py
===================================
Extracts full nodal displacement (ux, uy), nodal damage (d), and 
Gauss-point strain energy history (H) from Step 1 (Increment 50, u2 = 0.05 mm)
of PK_METHOD_C_CASE3_COARSE_JOB1.odb on cluster scratch for Method C Case 3
Cycle-1 state transfer.
"""

from __future__ import print_function
import os
import sys
import json
import odbAccess
from abaqusConstants import *

def extract_case3_donor(run_dir):
    odb_path = os.path.join(run_dir, "PK_METHOD_C_CASE3_COARSE_JOB1.odb")
    if not os.path.exists(odb_path):
        raise IOError("ODB file not found: %s" % odb_path)

    print("Opening ODB: %s" % odb_path)
    odb = odbAccess.openOdb(odb_path, readOnly=True)

    try:
        step1 = None
        for sname in odb.steps.keys():
            if "Step-1" in sname:
                step1 = odb.steps[sname]
                break
        if step1 is None:
            raise KeyError("Step-1 not found in ODB steps: %s" % str(odb.steps.keys()))

        last_frame = step1.frames[-1]
        print("Frame description: %s" % last_frame.description)
        print("Frame stepTime: %f" % last_frame.frameValue)

        # 1. Nodal displacements U
        u_fo = last_frame.fieldOutputs["U"]
        print("U component labels: %s" % str(u_fo.componentLabels))
        has_u3 = "U3" in u_fo.componentLabels
        u_nodal = {}
        d_from_u = {}

        for val in u_fo.values:
            nid = val.nodeLabel
            u_data = val.data
            if has_u3 and len(u_data) >= 3:
                u_nodal[nid] = [float(u_data[0]), float(u_data[1])]
                d_from_u[nid] = float(u_data[2])
            elif len(u_data) >= 2:
                u_nodal[nid] = [float(u_data[0]), float(u_data[1])]
            else:
                u_nodal[nid] = [float(u_data[0]), 0.0]

        # 2. SDV1 (damage) and SDV2 (history H) from companion elements
        sdv1_fo = last_frame.fieldOutputs["SDV1"]
        sdv2_fo = last_frame.fieldOutputs["SDV2"]

        num_phys = 4671
        offset_layer3 = 2 * num_phys  # 9342

        # Map physical element and GP to history and damage
        d_gp = {}  # (phys_eid, gp_idx) -> d
        h_gp = {}  # (phys_eid, gp_idx) -> H

        for val in sdv1_fo.values:
            eid = val.elementLabel
            gp = val.integrationPoint
            phys_eid = eid - offset_layer3 if eid > offset_layer3 else eid
            if phys_eid <= num_phys:
                d_gp[(phys_eid, gp)] = float(val.data)

        for val in sdv2_fo.values:
            eid = val.elementLabel
            gp = val.integrationPoint
            phys_eid = eid - offset_layer3 if eid > offset_layer3 else eid
            if phys_eid <= num_phys:
                h_gp[(phys_eid, gp)] = float(val.data)

        # 3. Nodal damage
        d_nodal = {}
        if has_u3 and len(d_from_u) > 0 and max(d_from_u.values()) > 0.0:
            d_nodal = d_from_u
            print("Using nodal damage directly from U3 (max = %e)" % max(d_nodal.values()))
        else:
            print("Reconstructing nodal damage from SDV1 integration point values...")
            inst = odb.rootAssembly.instances["PART-1-1"] if "PART-1-1" in odb.rootAssembly.instances else None
            if inst is None:
                inst_name = list(odb.rootAssembly.instances.keys())[0]
                inst = odb.rootAssembly.instances[inst_name]

            node_elem_d = {}
            for elem in inst.elements:
                eid = elem.label
                phys_eid = eid - offset_layer3 if eid > offset_layer3 else eid
                if phys_eid <= num_phys:
                    gp_d_vals = [d_gp.get((phys_eid, g), 0.0) for g in range(1, 5) if (phys_eid, g) in d_gp]
                    if gp_d_vals:
                        elem_d_avg = sum(gp_d_vals) / float(len(gp_d_vals))
                        for n in elem.connectivity:
                            if n not in node_elem_d:
                                node_elem_d[n] = []
                            node_elem_d[n].append(elem_d_avg)

            for nid in u_nodal.keys():
                if nid in node_elem_d and len(node_elem_d[nid]) > 0:
                    d_nodal[nid] = max(0.0, min(1.0, sum(node_elem_d[nid]) / float(len(node_elem_d[nid]))))
                else:
                    d_nodal[nid] = 0.0
            print("Reconstructed nodal damage from SDV1 (max = %e, mean = %e)" % (
                max(d_nodal.values()), sum(d_nodal.values()) / float(len(d_nodal))
            ))

        h_gp_json = {"%d_%d" % (k[0], k[1]): v for k, v in h_gp.items()}
        d_gp_json = {"%d_%d" % (k[0], k[1]): v for k, v in d_gp.items()}

        out_data = {
            "source_odb": odb_path,
            "benchmark": "Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins",
            "case_id": "method_c_case3",
            "step_name": "Step-1",
            "frame_idx": len(step1.frames) - 1,
            "step_time": float(last_frame.frameValue),
            "num_nodes": len(u_nodal),
            "num_phys_elements": num_phys,
            "max_damage": float(max(d_nodal.values())),
            "mean_damage": float(sum(d_nodal.values()) / float(len(d_nodal))),
            "max_history_MPa": float(max(h_gp.values())) if h_gp else 0.0,
            "mean_history_MPa": float(sum(h_gp.values()) / float(len(h_gp))) if h_gp else 0.0,
            "u_nodal": u_nodal,
            "d_nodal": d_nodal,
            "h_gp": h_gp_json,
            "d_gp": d_gp_json
        }

        out_json_path = os.path.join(run_dir, "donor_case3_step1_state.json")
        with open(out_json_path, "w") as f:
            json.dump(out_data, f)

        print("Saved donor state to: %s (%d nodes, %d GP entries)" % (
            out_json_path, len(u_nodal), len(h_gp_json)
        ))
        print("  Max damage:  %e" % out_data["max_damage"])
        print("  Max history: %e MPa" % out_data["max_history_MPa"])
        return out_data

    finally:
        odb.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="/scratch9/pr21vyci/runs/mode1_290_method_c_case3")
    args = parser.parse_args()
    extract_case3_donor(args.run_dir)
