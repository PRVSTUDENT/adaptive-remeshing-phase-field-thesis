"""
Abaqus Python script to extract exact trajectory, stiffness, peak, and terminal data
for all Mode-II reference and control ODBs to a clean JSON file.
"""

import sys
import os
import json
from odbAccess import openOdb

def process_odb(odb_path):
    if not os.path.exists(odb_path):
        return {"error": "file_not_found", "path": odb_path}

    try:
        odb = openOdb(odb_path, readOnly=True)
    except Exception as e:
        return {"error": str(e), "path": odb_path}

    step_data = {}
    for step_name, step in odb.steps.items():
        frames = step.frames
        traj = []
        for f_idx, f in enumerate(frames):
            t = float(f.frameValue)
            u_field = f.fieldOutputs['U'] if 'U' in f.fieldOutputs.keys() else None
            rf_field = f.fieldOutputs['RF'] if 'RF' in f.fieldOutputs.keys() else None

            u_dict = {}
            rf_dict = {}
            if u_field:
                for v in u_field.values:
                    u_dict[v.nodeLabel] = v.data
            if rf_field:
                for v in rf_field.values:
                    rf_dict[v.nodeLabel] = v.data

            sum_pos = 0.0
            sum_neg = 0.0
            for n, rf in rf_dict.items():
                if rf[0] > 0.0:
                    sum_pos += float(rf[0])
                elif rf[0] < 0.0:
                    sum_neg += float(rf[0])

            # Check RP node
            rp_node = None
            rp_rf1 = 0.0
            rp_u1 = 0.0
            for cand in [99999, 12383, 34261, 6250, 12065]:
                if cand in rf_dict:
                    rp_node = cand
                    rp_rf1 = float(rf_dict[cand][0])
                    if cand in u_dict:
                        rp_u1 = float(u_dict[cand][0])
                    break

            traj.append({
                "frame": f_idx,
                "time": t,
                "rp_node": rp_node,
                "rp_rf1": rp_rf1,
                "rp_u1": rp_u1,
                "sum_pos_rf1": sum_pos,
                "sum_neg_rf1": sum_neg
            })

        # Calculate metrics
        k0_rp = traj[1]["rp_rf1"] / traj[1]["rp_u1"] if len(traj) > 1 and traj[1]["rp_u1"] != 0 else 0.0
        k0_sum = traj[1]["sum_pos_rf1"] / traj[1]["rp_u1"] if len(traj) > 1 and traj[1]["rp_u1"] != 0 else 0.0
        peak_rp = max(traj, key=lambda x: abs(x["rp_rf1"]))
        peak_sum = max(traj, key=lambda x: abs(x["sum_pos_rf1"]))
        last = traj[-1]

        step_data[step_name] = {
            "total_frames": len(frames),
            "k0_rp_kN_mm": k0_rp,
            "k0_sum_kN_mm": k0_sum,
            "peak_rp": {
                "frame": peak_rp["frame"],
                "time": peak_rp["time"],
                "rp_node": peak_rp["rp_node"],
                "rp_rf1_kN": peak_rp["rp_rf1"],
                "rp_u1_mm": peak_rp["rp_u1"]
            },
            "peak_sum": {
                "frame": peak_sum["frame"],
                "time": peak_sum["time"],
                "sum_pos_rf1_kN": peak_sum["sum_pos_rf1"]
            },
            "terminal": {
                "frame": last["frame"],
                "time": last["time"],
                "rp_node": last["rp_node"],
                "rp_rf1_kN": last["rp_rf1"],
                "rp_u1_mm": last["rp_u1"],
                "sum_pos_rf1_kN": last["sum_pos_rf1"]
            },
            "sample_trajectory": [traj[i] for i in range(0, len(traj), max(1, len(traj)//10))]
        }

    odb.close()
    return {
        "path": odb_path,
        "steps": step_data
    }

def main():
    targets = [
        "models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050/M2REF_H1_FULL_U050.odb",
        "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb",
        "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.odb",
        "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050/M2CORR_H2_FULL_U050.odb",
        "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.odb",
        "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.odb"
    ]
    results = {}
    for t in targets:
        print("Processing: " + t)
        res = process_odb(t)
        results[t] = res

    out_file = "forensic_m2_odbs_summary.json"
    with open(out_file, "w") as fp:
        json.dump(results, fp, indent=2)
    print("Wrote summary to: " + out_file)

if __name__ == "__main__":
    main()
