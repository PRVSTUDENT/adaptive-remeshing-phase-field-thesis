# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_seven_hole_coarse_odb.py
================================================
Audits the coarse Seven-Hole ODB:
1. Steps, frames, time history, reaction force RF2.
2. Extraction of MISESERI, MISESAVG, relative error eta_e.
3. Extraction of phase-field damage SDV1 across physical elements.
4. Regional breakdown: Upper fracture corridor (h1-h4-h2-h5-h3) vs Lower shielded holes (h6, h7).
"""

from odbAccess import openOdb
import os
import json
import math

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
STUDY_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study")
ODB_PATH = os.path.join(STUDY_DIR, "PK_F1726_SEVEN_HOLE_COARSE.odb")
OUT_JSON = os.path.join(STUDY_DIR, "f1726_coarse_odb_audit.json")

def audit_odb():
    print("Opening ODB: %s" % ODB_PATH)
    odb = openOdb(ODB_PATH, readOnly=True)

    print("Steps in ODB: %s" % list(odb.steps.keys()))
    step1 = odb.steps['Step-1']
    step2 = odb.steps['Step-2']

    print("Step 1 frames: %d" % len(step1.frames))
    print("Step 2 frames: %d" % len(step2.frames))

    # Examine terminal frame of Step 1 and Step 2
    f_step1_end = step1.frames[-1]
    f_step2_end = step2.frames[-1]

    print("Step 1 End: time = %f" % f_step1_end.frameValue)
    print("Step 2 End: time = %f" % f_step2_end.frameValue)

    # Physical element count
    # Elements in UMAT_QUADS + UMAT_TRIS have offset 2 * N_phys
    # In the ODB, check root assembly instances
    inst = odb.rootAssembly.instances.values()[0]
    total_elements = len(inst.elements)
    n_phys = total_elements // 3
    print("Total layered elements in ODB: %d -> N_phys = %d" % (total_elements, n_phys))

    # Calculate RF2 history from RP node
    rp_nid = 999999
    # Extract RF2 and U2 at RP
    history_rf2 = []
    for s_name, step in odb.steps.items():
        for idx, f in enumerate(step.frames):
            u_field = f.fieldOutputs['U'] if 'U' in f.fieldOutputs else None
            rf_field = f.fieldOutputs['RF'] if 'RF' in f.fieldOutputs else None
            u2_val = 0.0
            rf2_val = 0.0
            if u_field:
                for val in u_field.values:
                    if val.nodeLabel == rp_nid:
                        u2_val = val.data[1]
                        break
            if rf_field:
                for val in rf_field.values:
                    if val.nodeLabel == rp_nid:
                        rf2_val = val.data[1]
                        break
            history_rf2.append({
                "step": s_name,
                "frame": idx,
                "time": f.frameValue,
                "u2": u2_val,
                "rf2": rf2_val
            })

    print("Last 5 RF2 points:")
    for h in history_rf2[-5:]:
        print("  Step %s Fr %d: u2 = %.6f mm, RF2 = %.6f kN" % (
            h["step"], h["frame"], h["u2"], h["rf2"]
        ))

    # Inspect field outputs at terminal frame
    f_term = f_step2_end
    print("\nField outputs in terminal frame:")
    for k in f_term.fieldOutputs.keys():
        print("  %s" % k)

    # Element centroids and regional classification
    elem_centroids = {}
    for el in inst.elements:
        if el.label > 2 * n_phys:  # UMAT layer
            phys_id = el.label - 2 * n_phys
            conn_nodes = [inst.getNodeFromLabel(nid).coordinates for nid in el.connectivity]
            cx = sum(p[0] for p in conn_nodes) / len(conn_nodes)
            cy = sum(p[1] for p in conn_nodes) / len(conn_nodes)
            elem_centroids[phys_id] = (cx, cy)

    # Extract MISESERI, MISESAVG, SDV1 at terminal frame
    miseseri_field = f_term.fieldOutputs['MISESERI'] if 'MISESERI' in f_term.fieldOutputs else None
    misesavg_field = f_term.fieldOutputs['MISESAVG'] if 'MISESAVG' in f_term.fieldOutputs else None
    sdv_field = f_term.fieldOutputs['SDV1'] if 'SDV1' in f_term.fieldOutputs else (f_term.fieldOutputs['SDV'] if 'SDV' in f_term.fieldOutputs else None)

    miseseri_vals = {}
    if miseseri_field:
        for val in miseseri_field.values:
            if val.elementLabel > 2 * n_phys:
                phys_id = val.elementLabel - 2 * n_phys
                miseseri_vals[phys_id] = float(val.data)

    misesavg_vals = {}
    if misesavg_field:
        for val in misesavg_field.values:
            if val.elementLabel > 2 * n_phys:
                phys_id = val.elementLabel - 2 * n_phys
                misesavg_vals[phys_id] = float(val.data)

    damage_vals = {}
    if sdv_field:
        for val in sdv_field.values:
            if val.elementLabel > 2 * n_phys:
                phys_id = val.elementLabel - 2 * n_phys
                d_val = float(val.data[0]) if hasattr(val.data, '__len__') else float(val.data)
                damage_vals[phys_id] = d_val

    # Regional analysis
    # Upper fracture corridor: distance to segments h1-h4, h4-h2, h2-h5, h5-h3
    upper_segments = [
        ((0.15, 0.40), (0.30, 0.60)),
        ((0.30, 0.60), (0.50, 0.55)),
        ((0.50, 0.55), (0.70, 0.60)),
        ((0.70, 0.60), (0.85, 0.50))
    ]

    def dist_to_segments(px, py, segs):
        min_d = 1e9
        for (x1, y1), (x2, y2) in segs:
            dx, dy = x2 - x1, y2 - y1
            l2 = dx*dx + dy*dy
            t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2)) if l2 > 0 else 0.0
            d = math.hypot(px - (x1 + t*dx), py - (y1 + t*dy))
            if d < min_d:
                min_d = d
        return min_d

    upper_corridor_errors = []
    lower_h6_errors = []
    lower_h7_errors = []
    bulk_errors = []

    upper_corridor_damage = []
    lower_h6_damage = []
    lower_h7_damage = []
    bulk_damage = []

    for phys_id, (cx, cy) in elem_centroids.items():
        err = miseseri_vals.get(phys_id, 0.0)
        dam = damage_vals.get(phys_id, 0.0)

        d_upper = dist_to_segments(cx, cy, upper_segments)
        d_h6 = math.hypot(cx - 0.40, cy - 0.35) - 0.05
        d_h7 = math.hypot(cx - 0.65, cy - 0.35) - 0.05

        if d_upper <= 0.040:  # within 40 um of upper crack route
            upper_corridor_errors.append(err)
            upper_corridor_damage.append(dam)
        elif abs(d_h6) <= 0.040:
            lower_h6_errors.append(err)
            lower_h6_damage.append(dam)
        elif abs(d_h7) <= 0.040:
            lower_h7_errors.append(err)
            lower_h7_damage.append(dam)
        else:
            bulk_errors.append(err)
            bulk_damage.append(dam)

    print("\n=== REGIONAL AUDIT OF SEVEN-HOLE COARSE MODEL ===")
    print("Upper Fracture Corridor (h1-h4-h2-h5-h3):")
    print("  Elements: %d" % len(upper_corridor_errors))
    print("  Mean MISESERI: %.4e, Max MISESERI: %.4e" % (
        sum(upper_corridor_errors)/len(upper_corridor_errors) if upper_corridor_errors else 0.0,
        max(upper_corridor_errors) if upper_corridor_errors else 0.0
    ))
    print("  Mean Damage d: %.4f, Max Damage d: %.4f" % (
        sum(upper_corridor_damage)/len(upper_corridor_damage) if upper_corridor_damage else 0.0,
        max(upper_corridor_damage) if upper_corridor_damage else 0.0
    ))

    print("\nLower Hole h6 (x=0.40, y=0.35):")
    print("  Elements: %d" % len(lower_h6_errors))
    print("  Mean MISESERI: %.4e, Max MISESERI: %.4e" % (
        sum(lower_h6_errors)/len(lower_h6_errors) if lower_h6_errors else 0.0,
        max(lower_h6_errors) if lower_h6_errors else 0.0
    ))
    print("  Mean Damage d: %.4f, Max Damage d: %.4f" % (
        sum(lower_h6_damage)/len(lower_h6_damage) if lower_h6_damage else 0.0,
        max(lower_h6_damage) if lower_h6_damage else 0.0
    ))

    print("\nLower Hole h7 (x=0.65, y=0.35):")
    print("  Elements: %d" % len(lower_h7_errors))
    print("  Mean MISESERI: %.4e, Max MISESERI: %.4e" % (
        sum(lower_h7_errors)/len(lower_h7_errors) if lower_h7_errors else 0.0,
        max(lower_h7_errors) if lower_h7_errors else 0.0
    ))
    print("  Mean Damage d: %.4f, Max Damage d: %.4f" % (
        sum(lower_h7_damage)/len(lower_h7_damage) if lower_h7_damage else 0.0,
        max(lower_h7_damage) if lower_h7_damage else 0.0
    ))

    print("\nBulk / Far-field Domain:")
    print("  Elements: %d" % len(bulk_errors))
    print("  Mean MISESERI: %.4e, Max MISESERI: %.4e" % (
        sum(bulk_errors)/len(bulk_errors) if bulk_errors else 0.0,
        max(bulk_errors) if bulk_errors else 0.0
    ))
    print("  Mean Damage d: %.4f, Max Damage d: %.4f" % (
        sum(bulk_damage)/len(bulk_damage) if bulk_damage else 0.0,
        max(bulk_damage) if bulk_damage else 0.0
    ))

    # Save summary json
    summary = {
        "odb_path": str(ODB_PATH),
        "total_layered_elements": int(total_elements),
        "n_phys": int(n_phys),
        "step1_frames": int(len(step1.frames)),
        "step2_frames": int(len(step2.frames)),
        "terminal_displacement_mm": float(history_rf2[-1]["u2"]),
        "terminal_rf2_kn": float(history_rf2[-1]["rf2"]),
        "upper_corridor": {
            "element_count": len(upper_corridor_errors),
            "mean_miseseri": float(sum(upper_corridor_errors)/len(upper_corridor_errors)) if upper_corridor_errors else 0.0,
            "max_miseseri": float(max(upper_corridor_errors)) if upper_corridor_errors else 0.0,
            "mean_damage": float(sum(upper_corridor_damage)/len(upper_corridor_damage)) if upper_corridor_damage else 0.0,
            "max_damage": float(max(upper_corridor_damage)) if upper_corridor_damage else 0.0
        },
        "lower_hole_h6": {
            "element_count": len(lower_h6_errors),
            "mean_miseseri": float(sum(lower_h6_errors)/len(lower_h6_errors)) if lower_h6_errors else 0.0,
            "max_miseseri": float(max(lower_h6_errors)) if lower_h6_errors else 0.0,
            "mean_damage": float(sum(lower_h6_damage)/len(lower_h6_damage)) if lower_h6_damage else 0.0,
            "max_damage": float(max(lower_h6_damage)) if lower_h6_damage else 0.0
        },
        "lower_hole_h7": {
            "element_count": len(lower_h7_errors),
            "mean_miseseri": float(sum(lower_h7_errors)/len(lower_h7_errors)) if lower_h7_errors else 0.0,
            "max_miseseri": float(max(lower_h7_errors)) if lower_h7_errors else 0.0,
            "mean_damage": float(sum(lower_h7_damage)/len(lower_h7_damage)) if lower_h7_damage else 0.0,
            "max_damage": float(max(lower_h7_damage)) if lower_h7_damage else 0.0
        },
        "bulk_far_field": {
            "element_count": len(bulk_errors),
            "mean_miseseri": float(sum(bulk_errors)/len(bulk_errors)) if bulk_errors else 0.0,
            "max_miseseri": float(max(bulk_errors)) if bulk_errors else 0.0,
            "mean_damage": float(sum(bulk_damage)/len(bulk_damage)) if bulk_damage else 0.0,
            "max_damage": float(max(bulk_damage)) if bulk_damage else 0.0
        }
    }

    with open(OUT_JSON, "w") as jf:
        json.dump(summary, jf, indent=2)

    print("\nSaved ODB audit summary to: %s" % OUT_JSON)
    odb.close()

if __name__ == "__main__":
    audit_odb()
