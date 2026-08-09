"""Extract and summarize technical dry test results for F43DRY_MM and F43DRY_PK5."""

from __future__ import print_function
import json
import os
import sys

def extract_dry_results():
    try:
        from odbAccess import openOdb
    except ImportError:
        print("odbAccess not available; must be run via abaqus python.")
        return

    results = {}

    cases = [
        ("MM", "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/dry_test_mm/F43DRY_MM.odb"),
        ("PK5", "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/dry_test_pk5/F43DRY_PK5.odb")
    ]

    for label, odb_path in cases:
        if not os.path.exists(odb_path):
            print("Warning: " + str(odb_path) + " not found.")
            continue

        odb = openOdb(path=odb_path, readOnly=True)
        step_name = list(odb.steps.keys())[0]
        step = odb.steps[step_name]

        frames_data = []
        rp_set_name = "SET_RP"

        # Locate RP node and boundary nodes
        rp_node_label = None
        rp_instance_name = None

        # Check rootAssembly nodeSets
        for nset_name, nset in odb.rootAssembly.nodeSets.items():
            if "RP" in nset_name.upper():
                rp_node_label = nset.nodes[0][0].label if nset.nodes and nset.nodes[0] else None
                rp_instance_name = None

        # Check instances nodeSets
        if rp_node_label is None:
            for inst_name, inst in odb.rootAssembly.instances.items():
                for nset_name, nset in inst.nodeSets.items():
                    if "RP" in nset_name.upper():
                        if nset.nodes:
                            rp_node_label = nset.nodes[0].label
                            rp_instance_name = inst_name
                            break

        for f_idx, frame in enumerate(step.frames):
            time = float(frame.frameValue)
            u_field = frame.fieldOutputs["U"] if "U" in frame.fieldOutputs else None
            rf_field = frame.fieldOutputs["RF"] if "RF" in frame.fieldOutputs else None

            rp_u_x = None
            rp_rf_x = 0.0
            found_rf = False

            if u_field:
                for val in u_field.values:
                    if rp_node_label is not None and val.nodeLabel == rp_node_label:
                        rp_u_x = float(val.data[0])
                        break
                    elif val.nodeLabel == 1000000 or val.nodeLabel == 999999 or val.nodeLabel == 10000:
                        rp_u_x = float(val.data[0])

            if rf_field:
                for val in rf_field.values:
                    # If this is the RP node:
                    if rp_node_label is not None and val.nodeLabel == rp_node_label:
                        rp_rf_x = float(val.data[0])
                        found_rf = True
                        break
                    # Otherwise sum reaction forces from bottom boundary (Y=0) or top boundary
                    elif val.nodeLabel == 1000000 or val.nodeLabel == 999999:
                        rp_rf_x = float(val.data[0])
                        found_rf = True

            frames_data.append({
                "frame_index": f_idx,
                "step_time": time,
                "rp_ux": rp_u_x,
                "rp_rfx": rp_rf_x if found_rf else None,
            })


        # Calculate initial elastic stiffness if available
        last_frame = frames_data[-1] if frames_data else None
        stiffness = None
        if last_frame and last_frame["rp_ux"] is not None and last_frame["rp_rfx"] is not None and abs(last_frame["rp_ux"]) > 1e-12:
            stiffness = last_frame["rp_rfx"] / last_frame["rp_ux"]

        results[label] = {
            "odb_path": odb_path,
            "step_name": step_name,
            "total_frames": len(step.frames),
            "final_time": float(step.frames[-1].frameValue) if step.frames else 0.0,
            "final_rp_ux": last_frame["rp_ux"] if last_frame else None,
            "final_rp_rfx": last_frame["rp_rfx"] if last_frame else None,
            "initial_elastic_stiffness_kN_per_mm": stiffness,
            "frames": frames_data
        }
        odb.close()

    out_path = "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43DUALDRY_EXECUTION_RESULTS.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print("Results written to " + str(out_path))
    for label, res in results.items():
        print("[%s] Frames=%d, Final_Time=%.4f, Final_Ux=%s, Final_RFx=%s, Stiffness=%.4f kN/mm" % (
            label, res["total_frames"], res["final_time"], str(res["final_rp_ux"]), str(res["final_rp_rfx"]),
            res["initial_elastic_stiffness_kN_per_mm"] if res["initial_elastic_stiffness_kN_per_mm"] is not None else 0.0
        ))

if __name__ == "__main__":
    extract_dry_results()

