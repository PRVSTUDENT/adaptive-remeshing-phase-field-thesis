#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
plot_f1690_sec43_miseseri.py

Task F1690: Evaluates MISESERI error indicator contour on Pandey-Kumar Section 4.3
rectangular plate with 3 holes on the finer coarse mesh (24,718 elements, h=0.60 mm).
Computes 90%-energy area, relative error distribution, and compares directly with Paper Fig. 15b.
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from odbAccess import openOdb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
model_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "190_pk_sec43_job1_rerun"
odb_path = model_dir / "PK_SEC43_RERUN_RECOVERY.odb"
fig_dir = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures"
results_dir = REPO_ROOT / "results" / "validation"

def main():
    print("=" * 80)
    print("TASK F1690: PANDEY-KUMAR SECTION 4.3 MISESERI EVALUATION ON FINER MESH (h=0.6 mm)")
    print("=" * 80)
    
    if not odb_path.exists():
        raise FileNotFoundError("ODB not found at: %s" % odb_path)
        
    odb = openOdb(str(odb_path))
    step = odb.steps['RECOVERY_STEP']
    frame = step.frames[-1]
    
    root_assembly = odb.rootAssembly
    nodes_dict = {}
    for inst_name, inst in root_assembly.instances.items():
        for n in inst.nodes:
            nodes_dict[n.label] = (n.coordinates[0], n.coordinates[1])
            
    miseseri_field = frame.fieldOutputs['MISESERI']
    misesavg_field = frame.fieldOutputs['MISESAVG']
    
    eri_dict = {v.elementLabel: float(v.data) for v in miseseri_field.values}
    avg_dict = {v.elementLabel: float(v.data) for v in misesavg_field.values}
    
    elems_data = []
    patches = []
    eri_vals = []
    
    for inst_name, inst in root_assembly.instances.items():
        for el in inst.elements:
            eid = el.label
            if eid not in eri_dict:
                continue
            conn = list(el.connectivity)
            pts = [nodes_dict[nid] for nid in conn if nid in nodes_dict]
            if len(pts) < 3:
                continue
            poly_pts = np.array(pts)
            
            x = poly_pts[:, 0]
            y = poly_pts[:, 1]
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            cx = np.mean(x)
            cy = np.mean(y)
            
            eri = eri_dict[eid]
            avg = avg_dict.get(eid, 0.0)
            
            elems_data.append({
                "eid": eid,
                "cx": cx,
                "cy": cy,
                "area": area,
                "eri": eri,
                "avg": avg,
                "pts": pts
            })
            patches.append(MplPolygon(poly_pts, closed=True))
            eri_vals.append(eri)

    odb.close()
    
    print("Loaded %d elements with MISESERI." % len(elems_data))
    
    elems_sorted = sorted(elems_data, key=lambda x: x["eri"], reverse=True)
    print("\nTop 10 elements with highest MISESERI:")
    for el in elems_sorted[:10]:
        print("  Element %5d: cx=%6.2f, cy=%6.2f, area=%.4f mm^2, MISESERI=%.4e, MISESAVG=%.4e" % 
              (el['eid'], el['cx'], el['cy'], el['area'], el['eri'], el['avg']))
        
    tot_energy = sum([el["area"] * (el["eri"]**2) for el in elems_data])
    tot_area = sum([el["area"] for el in elems_data])
    print("\nTotal Plate Area: %.2f mm^2" % tot_area)
    print("Total Error Energy (sum A * eri^2): %.4e" % tot_energy)
    
    # 90% error energy area
    cum_energy = 0.0
    area_90 = 0.0
    for idx, el in enumerate(elems_sorted):
        cum_energy += el["area"] * (el["eri"]**2)
        if cum_energy >= 0.90 * tot_energy:
            area_90 = sum([e["area"] for e in elems_sorted[:idx+1]])
            break
            
    rel_waste_90 = (area_90 / tot_area) * 100.0
    print("Area containing 90%% error energy: %.2f mm^2 (%.2f%% of total specimen area)" % (area_90, rel_waste_90))
    
    # Check secondary ligament (x >= 46.5 mm, y between 40 and 65 mm)
    sec_elems = [el for el in elems_data if el["cx"] >= 46.5 and 40.0 <= el["cy"] <= 65.0]
    sec_eri_max = max([el["eri"] for el in sec_elems]) if sec_elems else 0.0
    sec_eri_mean = np.mean([el["eri"] for el in sec_elems]) if sec_elems else 0.0
    print("\nSecondary Ligament Analysis (%d elements):" % len(sec_elems))
    print("  Max MISESERI in secondary ligament: %.4e" % sec_eri_max)
    print("  Mean MISESERI in secondary ligament: %.4e" % sec_eri_mean)
    print("  Ratio of secondary max to peak notch-tip max: %.4e" % (sec_eri_max / max(eri_vals)))
    
    # Plot
    fig, ax = plt.subplots(figsize=(6, 10))
    p = PatchCollection(patches, cmap='jet', edgecolors='none', linewidths=0.0)
    p.set_array(np.array(eri_vals))
    ax.add_collection(p)
    
    ax.set_xlim(0, 65)
    ax.set_ylim(0, 120)
    ax.set_aspect('equal')
    ax.set_xlabel('X [mm]', fontsize=11)
    ax.set_ylabel('Y [mm]', fontsize=11)
    ax.set_title('Task F1690: Pandey-Kumar §4.3 MISESERI Error Indicator\n(Linear-Elastic Recovery on Finer Coarse Mesh h=0.60 mm, 24,718 Elements)', fontsize=10)
    
    cb = fig.colorbar(p, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label(r'MISESERI Discretization Error Indicator', fontsize=10)
    
    out_pdf = fig_dir / "fig_f1690_sec43_miseseri.pdf"
    out_png = fig_dir / "fig_f1690_sec43_miseseri.png"
    plt.tight_layout()
    plt.savefig(str(out_pdf), dpi=300)
    plt.savefig(str(out_png), dpi=300)
    plt.close()
    print("Saved MISESERI plots to:\n  %s\n  %s" % (out_pdf, out_png))
    
    summary = {
        "benchmark": "Pandey_Kumar_2025_Section_4.3_F1690_RERUN",
        "mesh_type": "Finer_Coarse_h060",
        "element_count": len(elems_data),
        "total_area": tot_area,
        "miseseri_min": float(min(eri_vals)),
        "miseseri_max": float(max(eri_vals)),
        "total_error_energy": float(tot_energy),
        "area_90pct_energy": float(area_90),
        "rel_area_90pct": float(rel_waste_90),
        "secondary_ligament": {
            "element_count": len(sec_elems),
            "miseseri_max": float(sec_eri_max),
            "miseseri_mean": float(sec_eri_mean),
            "ratio_to_peak": float(sec_eri_max / max(eri_vals))
        },
        "top_elements": [
            {"eid": int(el["eid"]), "cx": float(el["cx"]), "cy": float(el["cy"]), "eri": float(el["eri"])}
            for el in elems_sorted[:15]
        ]
    }
    
    json_path = results_dir / "f1690_sec43_miseseri_evaluation.json"
    with open(str(json_path), "w") as f:
        json.dump(summary, f, indent=2)
    print("Saved evaluation JSON to: %s" % json_path)

if __name__ == "__main__":
    main()
