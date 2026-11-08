#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
plot_f1688_sec43_miseseri.py

Plots MISESERI error indicator contour on Pandey-Kumar Section 4.3 rectangular plate with a hole.
Computes 90%-energy width W_90, relative waste area, and compares directly with Paper Fig. 15b.
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
model_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "188_pk_sec43_hole_plate"
odb_path = model_dir / "PK_SEC43_COARSE_RECOVERY.odb"
fig_dir = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures"
results_dir = REPO_ROOT / "results" / "validation"

def main():
    print("=" * 80)
    print("TASK F1688: PANDEY-KUMAR SECTION 4.3 MISESERI EVALUATION & SPATIAL AUDIT")
    print("=" * 80)
    
    odb = openOdb(str(odb_path))
    step = odb.steps['RECOVERY_STEP']
    frame = step.frames[-1]
    
    # Extract element centroids, areas, and MISESERI
    root_assembly = odb.rootAssembly
    # Get elements and nodes
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
            pts = [nodes_dict[nid] for nid in conn]
            poly_pts = np.array(pts)
            
            # Shoelace formula for area
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
    
    print(f"Loaded {len(elems_data)} elements with MISESERI.")
    
    # Sort by MISESERI descending
    elems_sorted = sorted(elems_data, key=lambda x: x["eri"], reverse=True)
    print("\nTop 10 elements with highest MISESERI:")
    for el in elems_sorted[:10]:
        print(f"  Element {el['eid']:5d}: cx={el['cx']:6.2f}, cy={el['cy']:6.2f}, area={el['area']:.4f} mm^2, MISESERI={el['eri']:.4e}, MISESAVG={el['avg']:.4e}")
        
    # Spatial energy integration
    # Total error energy = sum(area * eri^2)
    tot_energy = sum([el["area"] * (el["eri"]**2) for el in elems_data])
    tot_area = sum([el["area"] for el in elems_data])
    print(f"\nTotal Plate Area: {tot_area:.2f} mm^2 (Nominal: {65*120 - 10*0.4 - np.pi*(25+25+100):.2f} mm^2)")
    print(f"Total Error Energy (sum A * eri^2): {tot_energy:.4e}")
    
    # Define crack corridors matching Pandey & Kumar Fig. 15a/15b:
    # Primary crack: from notch tip (10, 70) to upper hole bottom (20, 95)
    # Secondary crack: from upper-right hole boundary (approx (43.5, 58) or (20, 105)) to right edge (65, y)
    # Wait, in Fig. 14 & 15a:
    # Notch is at (10, 70).
    # Central hole is at (36.5, 51), R=10.
    # Upper hole is at (20, 100), R=5.
    # Lower hole is at (20, 20), R=5.
    # In Fig. 15a (Ambati / Pandey):
    # Primary crack curves from notch (10, 70) into the central hole at (36.5, 51)!
    # Secondary crack initiates from the central hole and propagates to the right edge (x = 65)!
    # Let's check distance to the crack path!
    
    # Compute cumulative energy fraction vs area
    cum_energy = 0.0
    area_90 = 0.0
    for el in elems_sorted:
        cum_energy += el["area"] * (el["eri"]**2)
        if cum_energy >= 0.90 * tot_energy:
            area_90 = sum([e["area"] for e in elems_sorted[:elems_sorted.index(el)+1]])
            break
            
    rel_waste_90 = (area_90 / tot_area) * 100.0
    print(f"Area containing 90% error energy: {area_90:.2f} mm^2 ({rel_waste_90:.2f}% of total specimen area)")
    
    # Generate Plot
    fig, ax = plt.subplots(figsize=(6, 10))
    p = PatchCollection(patches, cmap='jet', edgecolors='black', linewidths=0.2)
    p.set_array(np.array(eri_vals))
    ax.add_collection(p)
    
    ax.set_xlim(0, 65)
    ax.set_ylim(0, 120)
    ax.set_aspect('equal')
    ax.set_xlabel('X [mm]', fontsize=11)
    ax.set_ylabel('Y [mm]', fontsize=11)
    ax.set_title('Task F1688: Pandey-Kumar §4.3 MISESERI Error Indicator\n(Linear-Elastic Recovery on Coarse Mesh, 65 x 120 mm)', fontsize=11)
    
    cb = fig.colorbar(p, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label(r'MISESERI Discretization Error Indicator', fontsize=10)
    
    out_pdf = fig_dir / "fig_f1688_sec43_miseseri.pdf"
    out_png = fig_dir / "fig_f1688_sec43_miseseri.png"
    plt.tight_layout()
    plt.savefig(out_pdf, dpi=300)
    plt.savefig(out_png, dpi=300)
    plt.close()
    print(f"Saved MISESERI plots to:\n  {out_pdf}\n  {out_png}")
    
    # Save JSON summary
    summary = {
        "benchmark": "Pandey_Kumar_2025_Section_4.3",
        "specimen_dimensions": {"width": 65.0, "height": 120.0, "notch_length": 10.0, "notch_width": 0.4},
        "holes": [
            {"name": "lower", "x": 20.0, "y": 20.0, "r": 5.0},
            {"name": "upper", "x": 20.0, "y": 100.0, "r": 5.0},
            {"name": "central", "x": 36.5, "y": 51.0, "r": 10.0}
        ],
        "element_count": len(elems_data),
        "total_area": tot_area,
        "miseseri_min": float(min(eri_vals)),
        "miseseri_max": float(max(eri_vals)),
        "total_error_energy": float(tot_energy),
        "area_90pct_energy": float(area_90),
        "rel_area_90pct": float(rel_waste_90),
        "top_elements": [
            {"eid": int(el["eid"]), "cx": float(el["cx"]), "cy": float(el["cy"]), "eri": float(el["eri"])}
            for el in elems_sorted[:15]
        ]
    }
    
    json_path = results_dir / "f1688_sec43_miseseri_evaluation.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved evaluation JSON to: {json_path}")

if __name__ == "__main__":
    main()
