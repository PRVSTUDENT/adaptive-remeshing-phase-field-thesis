"""Extract and summarize technical dry test results for F43DRY_MM and F43DRY_PK5."""

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
            print(f"Warning: {odb_path} not found.")
            continue

        odb = openOdb(path=odb_path, readOnly=True)
        step_name = odb.steps.keys()[0]
        step = odb.steps[step_name]

        frames_data = []
        rp_set_name = "SET_RP"

        for f_idx, frame in enumerate(step.frames):
            time = frame.frameValue
            u_field = frame.fieldOutputs.get("U")
            rf_field = frame.fieldOutputs.get("RF")

            # Check RP node
            rp_u_x = None
            rp_rf_x = None

            if u_field and rf_field:
                # Find RP
                try:
                    root_assembly = odb.rootAssembly
                    if rp_set_name in root_assembly.nodeSets:
                        rp_set = root_assembly.nodeSets[rp_set_name]
                        u_sub = u_field.getSubset(region=rp_set)
                        rf_sub = rf_field.getSubset(region=rp_set)
                        if u_sub.values:
                            rp_u_x = float(u_sub.values[0].data[0])
                        if rf_sub.values:
                            rp_rf_x = float(rf_sub.values[0].data[0])
                except Exception as e:
                    pass

            frames_data.append({
                "frame_index": f_idx,
                "step_time": time,
                "rp_ux": rp_u_x,
                "rp_rfx": rp_rf_x,
            })

        # Calculate initial elastic stiffness if available
        last_frame = frames_data[-1] if frames_data else None
        stiffness = None
        if last_frame and last_frame["rp_ux"] and last_frame["rp_rfx"] and abs(last_frame["rp_ux"]) > 1e-12:
            stiffness = last_frame["rp_rfx"] / last_frame["rp_ux"]

        results[label] = {
            "odb_path": odb_path,
            "step_name": step_name,
            "total_frames": len(step.frames),
            "final_time": step.frames[-1].frameValue if step.frames else 0.0,
            "final_rp_ux": last_frame["rp_ux"] if last_frame else None,
            "final_rp_rfx": last_frame["rp_rfx"] if last_frame else None,
            "initial_elastic_stiffness_kN_per_mm": stiffness,
            "frames": frames_data
        }
        odb.close()

    out_path = "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43DUALDRY_EXECUTION_RESULTS.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results written to {out_path}")
    for label, res in results.items():
        print(f"[{label}] Frames={res['total_frames']}, Final_Time={res['final_time']:.4f}, Final_Ux={res['final_rp_ux']}, Final_RFx={res['final_rp_rfx']}, Stiffness={res['initial_elastic_stiffness_kN_per_mm']:.4f} kN/mm")

if __name__ == "__main__":
    extract_dry_results()
