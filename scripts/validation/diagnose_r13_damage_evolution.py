import os
import sys
import json
import math
from odbAccess import openOdb

def load_nodal_d0(inc_path):
    nodal_d0 = {}
    with open(inc_path, 'r') as f:
        for line in f:
            l = line.strip()
            if l and not l.startswith('**'):
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 4:
                    nid = int(parts[0])
                    d0 = float(parts[3])
                    nodal_d0[nid] = d0
    return nodal_d0

def get_released_nodes(stage_a_inc, active_inc):
    stage_a = set()
    with open(stage_a_inc, 'r') as f:
        for line in f:
            l = line.strip()
            if l and not l.startswith('**'):
                stage_a.add(int(l.split(',')[0]))
    active = set()
    with open(active_inc, 'r') as f:
        for line in f:
            l = line.strip()
            if l and not l.startswith('**'):
                active.add(int(l.split(',')[0]))
    released = sorted(list(stage_a - active))
    return released, stage_a, active

def inspect_odb(odb_path, nodal_d0):
    odb = openOdb(odb_path, readOnly=True)
    step_data = {}
    for step_name in ["Stage-A", "Inc1-Coupled"]:
        if step_name not in odb.steps:
            continue
        step = odb.steps[step_name]
        frame = step.frames[-1]
        u_field = frame.fieldOutputs["U"]
        rf_field = frame.fieldOutputs["RF"]

        u_map = {}
        rf_map = {}
        for val in u_field.values:
            nid = val.nodeLabel
            if len(val.data) >= 3:
                u_map[nid] = [float(val.data[0]), float(val.data[1]), float(val.data[2])]
            elif len(val.data) == 2:
                u_map[nid] = [float(val.data[0]), float(val.data[1]), 0.0]

        for val in rf_field.values:
            nid = val.nodeLabel
            if len(val.data) >= 3:
                rf_map[nid] = [float(val.data[0]), float(val.data[1]), float(val.data[2])]
            elif len(val.data) == 2:
                rf_map[nid] = [float(val.data[0]), float(val.data[1]), 0.0]

        energies = {}
        for reg_key, reg in step.historyRegions.items():
            for e_key, series in reg.historyOutputs.items():
                if len(series.data) > 0:
                    energies[e_key] = float(series.data[-1][1])

        step_data[step_name] = {
            "time": float(frame.frameValue),
            "rf2_rp": rf_map.get(999999, [0.0, 0.0, 0.0])[1] * 1000.0,
            "u2_rp": u_map.get(999999, [0.0, 0.0, 0.0])[1],
            "energies": energies,
            "u_map": u_map,
            "rf_map": rf_map
        }
    odb.close()
    return step_data

def main():
    run_dir = "/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r13"
    csv_path = os.path.join(run_dir, "d_lower_bounds.csv")
    stage_a_inc = os.path.join(run_dir, "stage_a_all_d0_boundary_cards.inc")
    active_inc = os.path.join(run_dir, "active_set_boundary_cards.inc")

    nodal_d0 = load_nodal_d0(stage_a_inc)
    released_nodes, all_nodes, active_nodes = get_released_nodes(stage_a_inc, active_inc)

    print("=== R13 ACTIVE-SET AUDIT ===")
    print("Total nodes: %d" % len(all_nodes))
    print("Active nodes: %d" % len(active_nodes))
    print("Released nodes count: %d" % len(released_nodes))
    print("Released node IDs: %s" % str(released_nodes))

    odb1_path = os.path.join(run_dir, "M1_C3_ACTIVE_SET_R13_IT1.odb")
    odb2_path = os.path.join(run_dir, "M1_C3_ACTIVE_SET_R13_IT2.odb")

    it1_data = inspect_odb(odb1_path, nodal_d0)
    it2_data = inspect_odb(odb2_path, nodal_d0)

    # Detailed inspection of released nodes
    released_node_details = []
    max_delta_d = -1e9
    min_delta_d = 1e9
    sum_sq_delta_d = 0.0

    it2_step2_u = it2_data["Inc1-Coupled"]["u_map"]
    it2_step2_rf = it2_data["Inc1-Coupled"]["rf_map"]
    it1_step2_u = it1_data["Inc1-Coupled"]["u_map"]
    it1_step2_rf = it1_data["Inc1-Coupled"]["rf_map"]

    for nid in released_nodes:
        d0 = nodal_d0.get(nid, 0.0)
        d_it1 = it1_step2_u.get(nid, [0.0, 0.0, d0])[2]
        rf3_it1 = it1_step2_rf.get(nid, [0.0, 0.0, 0.0])[2]
        d_it2 = it2_step2_u.get(nid, [0.0, 0.0, d0])[2]
        rf3_it2 = it2_step2_rf.get(nid, [0.0, 0.0, 0.0])[2]
        delta_d = d_it2 - d0

        if delta_d > max_delta_d: max_delta_d = delta_d
        if delta_d < min_delta_d: min_delta_d = delta_d
        sum_sq_delta_d += delta_d**2

        released_node_details.append({
            "node_id": nid,
            "d0": d0,
            "d_it1": d_it1,
            "rf3_it1_kN_mm": rf3_it1,
            "d_it2": d_it2,
            "rf3_it2_kN_mm": rf3_it2,
            "delta_d": delta_d
        })

    l2_norm_delta_d = math.sqrt(sum_sq_delta_d) if len(released_nodes) > 0 else 0.0

    print("\n--- Released Nodes Damage Details (12 nodes) ---")
    print("%-8s %-12s %-12s %-14s %-12s %-14s %-12s" % 
          ("Node", "d0", "d_it1", "rf3_it1", "d_it2", "rf3_it2", "delta_d"))
    for item in released_node_details:
        print("%-8d %-12.8f %-12.8f %-14.6e %-12.8f %-14.6e %-12.6e" %
              (item["node_id"], item["d0"], item["d_it1"], item["rf3_it1_kN_mm"],
               item["d_it2"], item["rf3_it2_kN_mm"], item["delta_d"]))

    print("\nDamage Evolution on Released Nodes:")
    print("  Max delta_d: %.10e" % max_delta_d)
    print("  Min delta_d: %.10e" % min_delta_d)
    print("  L2 norm delta_d: %.10e" % l2_norm_delta_d)

    # Whole mesh damage increments
    whole_mesh_max_delta = -1e9
    whole_mesh_min_delta = 1e9
    whole_mesh_sum_sq = 0.0
    healing_count = 0

    for nid in all_nodes:
        d0 = nodal_d0.get(nid, 0.0)
        d_val = it2_step2_u.get(nid, [0.0, 0.0, d0])[2]
        diff = d_val - d0
        if diff > whole_mesh_max_delta: whole_mesh_max_delta = diff
        if diff < whole_mesh_min_delta: whole_mesh_min_delta = diff
        whole_mesh_sum_sq += diff**2
        if diff < -1e-8:
            healing_count += 1

    whole_mesh_l2 = math.sqrt(whole_mesh_sum_sq)
    print("\nWhole Mesh Damage Statistics (2769 nodes):")
    print("  Max delta_d: %.10e" % whole_mesh_max_delta)
    print("  Min delta_d: %.10e" % whole_mesh_min_delta)
    print("  L2 norm delta_d: %.10e" % whole_mesh_l2)
    print("  Healing count: %d" % healing_count)

    # Telemetry comparison
    it1_rf2 = it1_data["Inc1-Coupled"]["rf2_rp"]
    it2_rf2 = it2_data["Inc1-Coupled"]["rf2_rp"]
    it1_allse = it1_data["Inc1-Coupled"]["energies"].get("ALLSE", 0.0) * 1000.0
    it2_allse = it2_data["Inc1-Coupled"]["energies"].get("ALLSE", 0.0) * 1000.0

    print("\nGlobal Telemetry Comparison:")
    print("  IT1 Step 2 RF2: %.6f N | ALLSE: %.6f mJ" % (it1_rf2, it1_allse))
    print("  IT2 Step 2 RF2: %.6f N | ALLSE: %.6f mJ" % (it2_rf2, it2_allse))
    print("  Delta RF2 (IT2 - IT1): %.10e N" % (it2_rf2 - it1_rf2))
    print("  Delta ALLSE (IT2 - IT1): %.10e mJ" % (it2_allse - it1_allse))

    # Save output to JSON
    output_report = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "released_node_count": len(released_nodes),
        "released_nodes": released_nodes,
        "released_node_details": released_node_details,
        "released_nodes_max_delta_d": max_delta_d,
        "released_nodes_min_delta_d": min_delta_d,
        "released_nodes_l2_norm_delta_d": l2_norm_delta_d,
        "whole_mesh_max_delta_d": whole_mesh_max_delta,
        "whole_mesh_min_delta_d": whole_mesh_min_delta,
        "whole_mesh_l2_norm_delta_d": whole_mesh_l2,
        "whole_mesh_healing_count": healing_count,
        "it1_rf2_rp_N": it1_rf2,
        "it2_rf2_rp_N": it2_rf2,
        "it1_allse_mJ": it1_allse,
        "it2_allse_mJ": it2_allse,
        "delta_rf2_N": it2_rf2 - it1_rf2,
        "delta_allse_mJ": it2_allse - it1_allse
    }

    out_json = os.path.join(run_dir, "r13_physical_verdict_audit.json")
    with open(out_json, "w") as f:
        json.dump(output_report, f, indent=2)
    print("\nSaved report to %s" % out_json)

if __name__ == "__main__":
    main()
