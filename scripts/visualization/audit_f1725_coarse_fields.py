# -*- coding: utf-8 -*-
"""
scripts/visualization/audit_f1725_coarse_fields.py
================================================
Extracts spatial fields (damage, stress, MISESERI, MISESAVG, eta_e) from
PK_F1720_COARSE_COUPLED.odb across key checkpoints and compares them with
published Figure 25(a).
"""

import sys
import os
import json
import math
from odbAccess import openOdb

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
ODB_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "PK_F1720_COARSE_COUPLED.odb")
OUT_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "f1725_coarse_spatial_audit.json")

def extract():
    print("Opening ODB: %s" % ODB_PATH)
    odb = openOdb(ODB_PATH, readOnly=True)
    root = odb.rootAssembly
    inst = root.instances['PART-1-1'] if 'PART-1-1' in root.instances else root.instances.values()[0]

    node_coords = {n.label: (n.coordinates[0], n.coordinates[1]) for n in inst.nodes}
    elems = {}
    for el in inst.elements:
        pts = [node_coords[nl] for nl in el.connectivity]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        elems[el.label] = {
            "conn": [nl for nl in el.connectivity],
            "cx": cx,
            "cy": cy
        }

    # Identify checkpoints:
    # 1. Step-1 last frame (pure elastic, uy = 0.0050 mm)
    # 2. Step-2 Frame 60 (intermediate damage, uy ~ 0.0057 mm)
    # 3. Step-2 Frame 120 (progressive damage, uy ~ 0.0062 mm)
    # 4. Step-2 Last Frame (terminal state, frame 178, uy = 0.00645141 mm)

    checkpoints = [
        ("Step-1", len(odb.steps["Step-1"].frames) - 1, "Step1_End_Elastic_0p0050mm"),
        ("Step-2", 60, "Step2_Mid1_0p0057mm"),
        ("Step-2", 120, "Step2_Mid2_0p0062mm"),
        ("Step-2", len(odb.steps["Step-2"].frames) - 1, "Step2_Terminal_0p00645mm")
    ]

    out_data = {
        "checkpoints": {},
        "elements": {el_id: {"cx": round(v["cx"], 5), "cy": round(v["cy"], 5)} for el_id, v in elems.items()}
    }

    for step_name, f_idx, label in checkpoints:
        step = odb.steps[step_name]
        frame = step.frames[f_idx]
        print("Extracting checkpoint: %s (Step %s, frame %d, time %.4f)" % (label, step_name, f_idx, frame.frameValue))

        d_map = {}
        if 'SDV1' in frame.fieldOutputs:
            for val in frame.fieldOutputs['SDV1'].values:
                d_map[val.elementLabel] = float(val.data)

        miseseri_map = {}
        if 'MISESERI' in frame.fieldOutputs:
            for val in frame.fieldOutputs['MISESERI'].values:
                miseseri_map[val.elementLabel] = float(val.data)

        misesavg_map = {}
        if 'MISESAVG' in frame.fieldOutputs:
            for val in frame.fieldOutputs['MISESAVG'].values:
                misesavg_map[val.elementLabel] = float(val.data)

        s_mises_map = {}
        if 'S' in frame.fieldOutputs:
            s_field = frame.fieldOutputs['S']
            for val in s_field.values:
                if val.mises is not None:
                    s_mises_map[val.elementLabel] = float(val.mises)

        # Regional ligament metrics
        lig1_d = []
        lig2_d = []
        lig3_d = []
        lig4_d = []

        lig1_err = []
        lig2_err = []
        lig3_err = []
        lig4_err = []
        bulk_err = []

        for el_id, el_info in elems.items():
            cx = el_info["cx"]
            cy = el_info["cy"]
            d_val = d_map.get(el_id, 0.0)
            err_val = miseseri_map.get(el_id, 0.0)

            if 0.08 <= cx <= 0.27 and 0.40 <= cy <= 0.56:
                lig1_d.append(d_val)
                lig1_err.append(err_val)
            elif 0.42 <= cx <= 0.57 and 0.42 <= cy <= 0.58:
                lig2_d.append(d_val)
                lig2_err.append(err_val)
            elif 0.63 <= cx <= 0.70 and 0.48 <= cy <= 0.56:
                lig3_d.append(d_val)
                lig3_err.append(err_val)
            elif 0.80 <= cx <= 0.95 and 0.40 <= cy <= 0.55:
                lig4_d.append(d_val)
                lig4_err.append(err_val)
            elif cy > 0.70 or cy < 0.30:
                bulk_err.append(err_val)

        def arr_stats(arr):
            if not arr: return {"min": 0, "max": 0, "mean": 0}
            return {
                "min": float("%.4e" % min(arr)),
                "max": float("%.4e" % max(arr)),
                "mean": float("%.4e" % (sum(arr) / float(len(arr))))
            }

        out_data["checkpoints"][label] = {
            "step": step_name,
            "frame_idx": f_idx,
            "step_time": float(frame.frameValue),
            "max_damage": float("%.4f" % max(d_map.values())) if d_map else 0.0,
            "max_miseseri": float("%.4e" % max(miseseri_map.values())) if miseseri_map else 0.0,
            "min_miseseri": float("%.4e" % min(miseseri_map.values())) if miseseri_map else 0.0,
            "lig1_damage": arr_stats(lig1_d),
            "lig2_damage": arr_stats(lig2_d),
            "lig3_damage": arr_stats(lig3_d),
            "lig4_damage": arr_stats(lig4_d),
            "lig1_miseseri": arr_stats(lig1_err),
            "lig2_miseseri": arr_stats(lig2_err),
            "lig3_miseseri": arr_stats(lig3_err),
            "lig4_miseseri": arr_stats(lig4_err),
            "bulk_miseseri": arr_stats(bulk_err),
            "element_data": {
                el_id: {
                    "d": round(d_map.get(el_id, 0.0), 5),
                    "miseseri": float("%.4e" % miseseri_map.get(el_id, 0.0)) if el_id in miseseri_map else 0.0,
                    "misesavg": float("%.4e" % misesavg_map.get(el_id, 0.0)) if el_id in misesavg_map else 0.0,
                    "eta_pct": round(100.0 * miseseri_map.get(el_id, 0.0) / max(1e-25, misesavg_map.get(el_id, 1.0)), 3) if el_id in miseseri_map and el_id in misesavg_map else 0.0
                }
                for el_id in elems.keys()
            }
        }

    with open(OUT_JSON, "w") as f:
        json.dump(out_data, f, indent=2)

    print("Audit written to: %s" % OUT_JSON)
    odb.close()

if __name__ == "__main__":
    extract()
