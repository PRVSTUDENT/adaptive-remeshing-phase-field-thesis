"""
Abaqus Python script to generate the canonical, unscaled reference dataset
across all Mode-II benchmark runs: H1, H2, PK10R1, PK10R2, R7 restart, and PK10R3.
"""

import sys
import os
import csv
import json
import hashlib
from odbAccess import openOdb

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

MODELS = [
    {
        "id": "H1_UNIFORM_FINE",
        "job_name": "M2CORR_H1_FREEU2_FULL_U050",
        "pbs_job_id": "1389686.mmaster02",
        "odb_path": os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"),
        "rp_node": 12383,
        "n_physical_quads": 12064,
        "h_min_mm": 0.0020
    },
    {
        "id": "H2_UNIFORM_ULTRAFINE",
        "job_name": "M2CORR_H2_FREEU2_FULL_U050",
        "pbs_job_id": "1389687.mmaster02",
        "odb_path": os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.odb"),
        "rp_node": 34509,
        "n_physical_quads": 33852,
        "h_min_mm": 0.0010
    },
    {
        "id": "PK10R1_DEFECTIVE_BASELINE",
        "job_name": "M2CORR_PK10R1_CONTINUOUS_U050",
        "pbs_job_id": "1389684.mmaster02",
        "odb_path": os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.odb"),
        "rp_node": 99999,
        "n_physical_quads": 9612,
        "h_min_mm": 0.0050
    },
    {
        "id": "PK10R2_TOPOLOGY_CORRECTED",
        "job_name": "M2CORR_PK10R2_TOPOLOGY_CORRECTED",
        "pbs_job_id": "1390056.mmaster02",
        "odb_path": os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.odb"),
        "rp_node": 99999,
        "n_physical_quads": 6048,
        "h_min_mm": 0.0050
    },
    {
        "id": "R7_SAMEMESH_RESTART_VALIDATED",
        "job_name": "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7",
        "pbs_job_id": "1390042.mmaster02",
        "odb_path": os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.odb"),
        "rp_node": 99999,
        "n_physical_quads": 9612,
        "h_min_mm": 0.0050
    },
    {
        "id": "PK10R3_REFINED_TIP",
        "job_name": "M2CORR_PK10R3_REFINED_TIP",
        "pbs_job_id": "1390098.mmaster02",
        "odb_path": os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.odb"),
        "rp_node": 99999,
        "n_physical_quads": 17732,
        "h_min_mm": 0.0020
    }
]

def extract_canonical_model(m_info):
    odb_path = m_info["odb_path"]
    if not os.path.exists(odb_path):
        print("MISSING ODB: " + odb_path)
        return None

    print("Extracting Canonical Dataset for: " + m_info["id"] + " (" + odb_path + ")")
    odb = openOdb(odb_path, readOnly=True)

    steps_data = {}
    cumulative_records = []
    
    total_work_done = 0.0
    prev_u1 = 0.0
    prev_rf1 = 0.0

    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        step_records = []
        for f_idx, f in enumerate(step.frames):
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

            sum_pos_rf1 = 0.0
            sum_neg_rf1 = 0.0
            sum_all_rf1 = 0.0
            sum_all_rf2 = 0.0
            for n, rf in rf_dict.items():
                r1 = float(rf[0])
                r2 = float(rf[1]) if len(rf) > 1 else 0.0
                sum_all_rf1 += r1
                sum_all_rf2 += r2
                if r1 > 0.0:
                    sum_pos_rf1 += r1
                elif r1 < 0.0:
                    sum_neg_rf1 += r1

            rp_node = m_info["rp_node"]
            rp_u1 = float(u_dict[rp_node][0]) if (rp_node in u_dict) else 0.0
            rp_u2 = float(u_dict[rp_node][1]) if (rp_node in u_dict and len(u_dict[rp_node]) > 1) else 0.0
            rp_rf1 = float(rf_dict[rp_node][0]) if (rp_node in rf_dict) else 0.0
            rp_rf2 = float(rf_dict[rp_node][1]) if (rp_node in rf_dict and len(rf_dict[rp_node]) > 1) else 0.0

            # If rp_rf1 is zero (like in H2 where RP was uncoupled in output), use sum_pos_rf1
            effective_rf1 = rp_rf1 if abs(rp_rf1) > 1e-12 else sum_pos_rf1
            effective_u1 = rp_u1 if abs(rp_u1) > 1e-12 else t

            # Integrate trapezoidal work
            if len(cumulative_records) > 0:
                du = effective_u1 - prev_u1
                if du > 0:
                    total_work_done += 0.5 * (effective_rf1 + prev_rf1) * du
            prev_u1 = effective_u1
            prev_rf1 = effective_rf1

            rec = {
                "step": step_name,
                "frame": f_idx,
                "time": t,
                "u1_mm": effective_u1,
                "u2_mm": rp_u2,
                "rf1_kN": effective_rf1,
                "rf2_kN": rp_rf2,
                "sum_pos_rf1_kN": sum_pos_rf1,
                "sum_neg_rf1_kN": sum_neg_rf1,
                "sum_all_rf1_kN": sum_all_rf1,
                "sum_all_rf2_kN": sum_all_rf2,
                "work_done_kN_mm": total_work_done
            }
            step_records.append(rec)
            cumulative_records.append(rec)

        steps_data[step_name] = step_records

    odb.close()

    # Compute key canonical summary metrics
    k0 = 0.0
    for r in cumulative_records[1:]:
        if r["u1_mm"] > 1e-8:
            k0 = r["rf1_kN"] / r["u1_mm"]
            break

    peak_r = max(cumulative_records, key=lambda x: x["rf1_kN"])
    term_r = cumulative_records[-1]

    summary = {
        "model_id": m_info["id"],
        "job_name": m_info["job_name"],
        "pbs_job_id": m_info["pbs_job_id"],
        "odb_path": m_info["odb_path"],
        "rp_node": m_info["rp_node"],
        "mesh_stats": {
            "physical_quads": m_info["n_physical_quads"],
            "h_min_mm": m_info["h_min_mm"]
        },
        "canonical_metrics": {
            "k0_kN_mm": k0,
            "peak_rf1_kN": peak_r["rf1_kN"],
            "peak_u1_mm": peak_r["u1_mm"],
            "peak_frame": peak_r["frame"],
            "peak_step": peak_r["step"],
            "terminal_rf1_kN": term_r["rf1_kN"],
            "terminal_u1_mm": term_r["u1_mm"],
            "total_energy_dissipated_kN_mm": total_work_done,
            "total_steps": len(steps_data),
            "total_frames": len(cumulative_records)
        },
        "trajectory": cumulative_records
    }
    return summary

def main():
    print("================================================================================")
    print("BUILDING CANONICAL MODE-II UNIFIED REFERENCE DATASET (INCLUDING PK10R3)")
    print("================================================================================")
    
    dataset = {}
    summary_only = {}
    csv_dir = os.path.join(ROOT, "models/generated/mode_ii")
    
    for m in MODELS:
        res = extract_canonical_model(m)
        if res:
            dataset[m["id"]] = res
            csv_path = os.path.join(csv_dir, "canonical_" + m["id"].lower() + "_trajectory.csv")
            with open(csv_path, "w") as fp:
                writer = csv.writer(fp)
                writer.writerow(["step", "frame", "time", "u1_mm", "u2_mm", "rf1_kN", "rf2_kN", "sum_pos_rf1_kN", "sum_neg_rf1_kN", "sum_all_rf1_kN", "work_done_kN_mm"])
                for r in res["trajectory"]:
                    writer.writerow([r["step"], r["frame"], r["time"], r["u1_mm"], r["u2_mm"], r["rf1_kN"], r["rf2_kN"], r["sum_pos_rf1_kN"], r["sum_neg_rf1_kN"], r["sum_all_rf1_kN"], r["work_done_kN_mm"]])
            
            # Compute hash
            with open(csv_path, "rb") as fp:
                h = hashlib.sha256(fp.read()).hexdigest()
            print("Wrote CSV: " + csv_path + " (SHA-256: " + h + ")")
            
            summary_only[m["id"]] = {
                "model_id": res["model_id"],
                "job_name": res["job_name"],
                "pbs_job_id": res["pbs_job_id"],
                "mesh_stats": res["mesh_stats"],
                "canonical_metrics": res["canonical_metrics"],
                "trajectory_csv_sha256": h
            }

    out_json = os.path.join(ROOT, "docs/studies/canonical_mode_ii_summary.json")
    with open(out_json, "w") as fp:
        json.dump(summary_only, fp, indent=2)
    print("Wrote summary JSON: " + out_json)

if __name__ == "__main__":
    main()
