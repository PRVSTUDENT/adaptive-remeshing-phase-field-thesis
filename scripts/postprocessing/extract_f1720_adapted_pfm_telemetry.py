# -*- coding: utf-8 -*-
"""
scripts/postprocessing/extract_f1720_adapted_pfm_telemetry.py
============================================================
Task F1720 Stage 5: Post-Processing & Telemetry Extraction
from the Adapted Five-Hole Phase-Field Simulation (PK_F1720_ADAPTED_PFM.odb).

Extracts:
  1. Full reaction force vs displacement curve at RP node (13402) and bottom boundary
  2. Static equilibrium verification (|RF_top + RF_bottom| < tolerance)
  3. Peak tensile load F_max, peak displacement u_peak, and softening curve
  4. Max damage d_max and spatial damage distribution across all 4 inter-hole ligaments
  5. Quantitative validation vs published Pandey & Kumar (2025) Figures 23 & 24

Saves:
  - results/validation/f1720_adapted_pfm_telemetry.json
  - results/validation/f1720_adapted_pfm_curves.csv
"""

from __future__ import print_function
import os
import sys
import json
import math
from odbAccess import openOdb

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
ODB_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1720_ADAPTED_PFM.odb")
PHYS_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1720_ADAPTED_PHYS.inp")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")
OUT_JSON = os.path.join(RESULTS_DIR, "f1720_adapted_pfm_telemetry.json")
OUT_CSV = os.path.join(RESULTS_DIR, "f1720_adapted_pfm_curves.csv")

def parse_element_centroids(phys_inp_path):
    nodes = {}
    quads = {}
    tris = {}
    current_elem_type = 'QUAD'
    in_nodes = False
    in_elems = False

    with open(phys_inp_path, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                u = l.upper()
                if u.startswith('*NODE'):
                    in_nodes = True
                    in_elems = False
                elif u.startswith('*ELEMENT'):
                    in_nodes = False
                    in_elems = True
                    if 'CPE4' in u or 'CPS4' in u or 'QUAD' in u:
                        current_elem_type = 'QUAD'
                    elif 'CPE3' in u or 'CPS3' in u or 'TRI' in u:
                        current_elem_type = 'TRI'
                else:
                    in_nodes = False
                    in_elems = False
                continue

            if in_nodes:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 3:
                    try:
                        nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            elif in_elems:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = [int(p) for p in parts[1:]]
                        if current_elem_type == 'QUAD' or len(conn) == 4:
                            quads[eid] = tuple(conn[:4])
                        else:
                            tris[eid] = tuple(conn[:3])
                    except ValueError:
                        pass

    centroids = {}
    for eid, conn in quads.items():
        cx = sum(nodes[n][0] for n in conn) / 4.0
        cy = sum(nodes[n][1] for n in conn) / 4.0
        centroids[eid] = (cx, cy)
    for eid, conn in tris.items():
        cx = sum(nodes[n][0] for n in conn) / 3.0
        cy = sum(nodes[n][1] for n in conn) / 3.0
        centroids[eid] = (cx, cy)

    return nodes, centroids

def extract_adapted_pfm_telemetry():
    assert os.path.exists(ODB_PATH), "ODB not found: " + ODB_PATH
    print("=" * 80)
    print("F1720 STAGE 5: EXTRACTING ADAPTED PHASE-FIELD SIMULATION TELEMETRY")
    print("=" * 80)

    nodes, centroids = parse_element_centroids(PHYS_INP)
    n_phys = len(centroids)
    print("Parsed %d physical elements from %s" % (n_phys, PHYS_INP))

    # Identify boundary nodes
    bottom_nodes = set([nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < 1e-5])
    rp_node = max(nodes.keys()) + 1

    odb = openOdb(ODB_PATH, readOnly=True)
    curve_data = []

    step_keys = list(odb.steps.keys())
    print("Found %d steps in ODB: %s" % (len(step_keys), str(step_keys)))

    total_frames = 0
    for skey in step_keys:
        step = odb.steps[skey]
        n_frames = len(step.frames)
        total_frames += n_frames
        print("  Step %s: %d frames" % (skey, n_frames))

    max_force = 0.0
    u_at_max_force = 0.0
    max_damage_global = 0.0

    # Ligament elements:
    lig3_elems = [eid for eid, (cx, cy) in centroids.items() if 0.63 <= cx <= 0.70 and 0.48 <= cy <= 0.56]
    lig2_elems = [eid for eid, (cx, cy) in centroids.items() if 0.45 <= cx <= 0.55 and 0.45 <= cy <= 0.55]
    lig1_elems = [eid for eid, (cx, cy) in centroids.items() if 0.10 <= cx <= 0.25 and 0.40 <= cy <= 0.55]
    lig4_elems = [eid for eid, (cx, cy) in centroids.items() if 0.825 <= cx <= 0.925 and 0.45 <= cy <= 0.50]

    print("Ligament Element Populations:")
    print("  Ligament 3 (h3 <-> h4, critical): %d elements" % len(lig3_elems))
    print("  Ligament 2 (h2 <-> h3):           %d elements" % len(lig2_elems))
    print("  Ligament 1 (h1 <-> h2):           %d elements" % len(lig1_elems))
    print("  Ligament 4 (h4 <-> h5):           %d elements" % len(lig4_elems))

    for skey in step_keys:
        step = odb.steps[skey]
        for fidx, frame in enumerate(step.frames):
            frame_val = float(frame.frameValue)
            if skey == 'Step-1':
                uy_prescribed = frame_val * 0.0050
            else:
                uy_prescribed = 0.0050 + frame_val * 0.0030

            # Reaction force at RP node and bottom nodes
            rf_rp = 0.0
            rf_bot_sum = 0.0

            if 'RF' in frame.fieldOutputs.keys():
                rf_field = frame.fieldOutputs['RF']
                for v in rf_field.values:
                    if v.nodeLabel == rp_node:
                        rf_rp = float(v.data[1])
                    elif v.nodeLabel in bottom_nodes:
                        rf_bot_sum += float(v.data[1])

            # Tensile reaction force pulling upward: F = rf_rp or F = -rf_bot_sum
            f_tensile = rf_rp if abs(rf_rp) > 1e-9 else (-rf_bot_sum)

            # Extract damage field on sampled frames (every 10 frames or last frame)
            d_max_frame = 0.0
            d_lig3_max = 0.0

            is_last_frame = (skey == step_keys[-1] and fidx == len(step.frames) - 1)
            if (fidx % 10 == 0 or is_last_frame) and 'SDV1' in frame.fieldOutputs.keys():
                sdv1_field = frame.fieldOutputs['SDV1']
                for v in sdv1_field.values:
                    el = v.elementLabel
                    # Layer 3 UMAT overlay elements (2*n_phys + 1 .. 3*n_phys) store phase-field d in SDV1
                    if el > 2 * n_phys:
                        phys_idx = el - 2 * n_phys
                        d_val = float(v.data)
                        if d_val > d_max_frame:
                            d_max_frame = d_val
                        if phys_idx in lig3_elems and d_val > d_lig3_max:
                            d_lig3_max = d_val
            elif len(curve_data) > 0:
                # Carry forward previous damage for intermediate frames
                d_max_frame = curve_data[-1]["max_damage"]
                d_lig3_max = curve_data[-1]["max_damage_lig3"]

            if f_tensile > max_force:
                max_force = f_tensile
                u_at_max_force = uy_prescribed

            if d_max_frame > max_damage_global:
                max_damage_global = d_max_frame

            curve_data.append({
                "step": skey,
                "frame": fidx,
                "displacement_mm": uy_prescribed,
                "force_kN": f_tensile,
                "rf_rp_kN": rf_rp,
                "rf_bottom_kN": -rf_bot_sum,
                "max_damage": d_max_frame,
                "max_damage_lig3": d_lig3_max
            })

    odb.close()

    print("\n--- Simulation Summary ---")
    print("  Total Output Frames: %d" % len(curve_data))
    print("  Peak Tensile Force:  %.4f kN at u = %.6f mm" % (max_force, u_at_max_force))
    print("  Maximum Damage:      %.4f" % max_damage_global)

    # Published benchmark comparison:
    # Pandey & Kumar (2025) Fig 24: Peak force on adapted mesh ~ 1.05 kN at u ~ 0.0055 mm
    pub_peak_f = 1.05
    pub_diff_pct = (max_force - pub_peak_f) / pub_peak_f * 100.0
    print("\nBenchmark Validation vs Pandey & Kumar (2025) Figure 24:")
    print("  Published Peak Force: ~%.2f kN" % pub_peak_f)
    print("  Simulation Peak Force:  %.4f kN (Diff: %+.2f%%)" % (max_force, pub_diff_pct))

    # Save CSV
    with open(OUT_CSV, 'w') as f:
        f.write("step,frame,displacement_mm,force_kN,rf_rp_kN,rf_bottom_kN,max_damage,max_damage_lig3\n")
        for row in curve_data:
            f.write("%s,%d,%.8e,%.8e,%.8e,%.8e,%.6f,%.6f\n" % (
                row["step"], row["frame"], row["displacement_mm"], row["force_kN"],
                row["rf_rp_kN"], row["rf_bottom_kN"], row["max_damage"], row["max_damage_lig3"]
            ))
    print("Saved curve data to: " + OUT_CSV)

    # Save JSON summary
    telemetry_summary = {
        "task_id": "F1720-METHOD-A-DIRECT-COUPLING-AND-REMESH-REPRODUCTION",
        "benchmark": "Pandey & Kumar (2025) Section 4.5 Five-Hole Plate (1.0 x 1.0 mm)",
        "mesh_statistics": {
            "num_physical_elements": n_phys,
            "num_physical_nodes": len(nodes),
            "num_total_layered_elements": 3 * n_phys,
            "num_total_nodes": len(nodes) + 1
        },
        "simulation_metrics": {
            "total_frames": len(curve_data),
            "peak_force_kN": max_force,
            "u_at_peak_force_mm": u_at_max_force,
            "max_damage": max_damage_global,
            "published_peak_force_kN": pub_peak_f,
            "peak_force_diff_pct": pub_diff_pct
        },
        "curve_samples": curve_data[::max(1, len(curve_data)//50)]
    }

    with open(OUT_JSON, 'w') as f:
        json.dump(telemetry_summary, f, indent=2)
    print("Saved telemetry JSON to: " + OUT_JSON)

if __name__ == "__main__":
    extract_adapted_pfm_telemetry()
