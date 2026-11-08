"""
F1682R: Comprehensive element-level spatial integration and area-weighted audit
of the native Abaqus MISESERI discretization error indicator on PK_HOLE_F1661_RECOVERY.odb.

Executes under Abaqus Python to extract:
- Node coordinates and element connectivity for exact element centroids (xc, yc)
- Exact element volume / area Ve from field output EVOL
- Recovered stress error indicator MISESERI_e from field output MISESERI
- Domain average Mises equivalent stress MISESAVG
- Computes unweighted sums, area-weighted integrals, and L2 error norms
  across defined spatial regions:
  1. Whole Specimen Domain
  2. Notch Tip Initiation Zone (r <= 50 um from (0.50, 0.50))
  3. Primary Ligament Corridor (0.50 <= x <= 0.65, 0.48 <= y <= 0.65, r_hole >= 0.10)
  4. Hole Perimeter Annulus (0.10 <= r_hole <= 0.14)
  5. Secondary Right Ligament Zone (0.70 <= x <= 1.00, 0.55 <= y <= 0.75)
  6. Quiescent Far-Field Remainder
"""

import sys
import os
import math
import json
import csv
from odbAccess import openOdb

def run_spatial_miseseri_audit(odb_path, out_json, out_csv):
    print("=" * 80)
    print("F1682R: MISESERI SPATIAL INTEGRATION AND AREA-WEIGHTED ERROR AUDIT")
    print(f"Source ODB: {odb_path}")
    print("=" * 80)

    if not os.path.exists(odb_path):
        raise IOError(f"ODB not found: {odb_path}")

    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps['Step-1']
    frame = step.frames[-1]

    # Assembly instance
    inst = list(odb.rootAssembly.instances.values())[0]
    node_coords = {n.label: n.coordinates for n in inst.nodes}

    # Extract field outputs
    miseseri_field = frame.fieldOutputs['MISESERI']
    evol_field = frame.fieldOutputs['EVOL']
    misesavg_field = frame.fieldOutputs['MISESAVG']

    misesavg_val = float(misesavg_field.values[0].data)
    print(f"Domain Average Mises Stress (MISESAVG): {misesavg_val:.4f} MPa")

    miseseri_by_label = {v.elementLabel: float(v.data) for v in miseseri_field.values}
    evol_by_label = {v.elementLabel: float(v.data) for v in evol_field.values}

    hole_center = (0.65, 0.65)
    notch_tip = (0.50, 0.50)

    elements_data = []
    for el in inst.elements:
        elabel = el.label
        eltype = el.type
        conn = el.connectivity
        coords = [node_coords[nl] for nl in conn]

        xc = sum(c[0] for c in coords) / len(coords)
        yc = sum(c[1] for c in coords) / len(coords)

        # Distance to notch tip
        r_notch = math.sqrt((xc - notch_tip[0])**2 + (yc - notch_tip[1])**2)

        # Distance to hole center
        r_hole = math.sqrt((xc - hole_center[0])**2 + (yc - hole_center[1])**2)

        miseseri = miseseri_by_label.get(elabel, 0.0)
        area = evol_by_label.get(elabel, 0.0)

        # Region classification
        is_notch = (r_notch <= 0.050)
        is_primary = (0.50 <= xc <= 0.65 and 0.48 <= yc <= 0.65 and r_hole >= 0.10)
        is_hole_annulus = (0.10 <= r_hole <= 0.14)
        is_secondary = (0.70 <= xc <= 1.00 and 0.55 <= yc <= 0.75)

        # Relative error indicator eta_e
        eta_e = (miseseri / misesavg_val) * 100.0 if misesavg_val > 0 else 0.0

        elements_data.append({
            "label": elabel,
            "type": eltype,
            "xc": xc,
            "yc": yc,
            "area_mm2": area,
            "miseseri_MPa": miseseri,
            "eta_pct": eta_e,
            "weighted_error_MPa_mm2": miseseri * area,
            "weighted_error_sq_MPa2_mm2": (miseseri ** 2) * area,
            "is_notch": is_notch,
            "is_primary": is_primary,
            "is_hole_annulus": is_hole_annulus,
            "is_secondary": is_secondary
        })

    odb.close()
    print(f"Extracted {len(elements_data)} elements.")

    # Write element-level CSV
    with open(out_csv, 'w', newline='') as f:
        fieldnames = ["label", "type", "xc", "yc", "area_mm2", "miseseri_MPa", "eta_pct",
                      "weighted_error_MPa_mm2", "weighted_error_sq_MPa2_mm2",
                      "is_notch", "is_primary", "is_hole_annulus", "is_secondary"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(elements_data)
    print(f"Saved element-level CSV: {out_csv}")

    # Compute integrals for regions
    total_count = len(elements_data)
    total_area = sum(e["area_mm2"] for e in elements_data)
    total_unweighted_sum = sum(e["miseseri_MPa"] for e in elements_data)
    total_area_weighted_sum = sum(e["weighted_error_MPa_mm2"] for e in elements_data)
    total_l2_norm = math.sqrt(sum(e["weighted_error_sq_MPa2_mm2"] for e in elements_data))

    print(f"\nTotal specimen area: {total_area:.6f} mm^2 (analytical plate-with-hole = 1.0 - pi*0.1^2 = {1.0 - math.pi*0.01:.6f})")
    print(f"Total unweighted MISESERI sum: {total_unweighted_sum:.2f} MPa")
    print(f"Total area-weighted MISESERI integral: {total_area_weighted_sum:.4f} MPa*mm^2")
    print(f"Total L2 stress error norm: {total_l2_norm:.4f} MPa*mm")

    def calc_group_stats(group_elems, name):
        cnt = len(group_elems)
        if cnt == 0:
            return None
        vals = [e["miseseri_MPa"] for e in group_elems]
        vals.sort()
        area_sum = sum(e["area_mm2"] for e in group_elems)
        unw_sum = sum(e["miseseri_MPa"] for e in group_elems)
        weighted_sum = sum(e["weighted_error_MPa_mm2"] for e in group_elems)
        l2_sum = math.sqrt(sum(e["weighted_error_sq_MPa2_mm2"] for e in group_elems))

        h_med = vals[cnt // 2]
        return {
            "group_name": name,
            "element_count": cnt,
            "pct_of_elements": (cnt / float(total_count)) * 100.0,
            "area_mm2": area_sum,
            "pct_of_domain_area": (area_sum / total_area) * 100.0,
            "miseseri_min_MPa": vals[0],
            "miseseri_median_MPa": h_med,
            "miseseri_mean_MPa": unw_sum / cnt,
            "miseseri_max_MPa": vals[-1],
            "unweighted_error_sum_MPa": unw_sum,
            "share_of_unweighted_sum_pct": (unw_sum / total_unweighted_sum) * 100.0,
            "area_weighted_error_integral_MPa_mm2": weighted_sum,
            "share_of_area_weighted_integral_pct": (weighted_sum / total_area_weighted_sum) * 100.0,
            "l2_error_norm_MPa_mm": l2_sum,
            "share_of_l2_norm_pct": (l2_sum / total_l2_norm) * 100.0,
            "area_averaged_error_MPa": weighted_sum / area_sum if area_sum > 0 else 0.0
        }

    notch_elems = [e for e in elements_data if e["is_notch"]]
    primary_elems = [e for e in elements_data if e["is_primary"]]
    hole_elems = [e for e in elements_data if e["is_hole_annulus"]]
    sec_elems = [e for e in elements_data if e["is_secondary"]]
    farfield_elems = [e for e in elements_data if not (e["is_notch"] or e["is_primary"] or e["is_secondary"])]

    regions = [
        calc_group_stats(elements_data, "Whole Specimen Domain"),
        calc_group_stats(notch_elems, "Notch Tip Initiation Zone (r <= 50 um)"),
        calc_group_stats(primary_elems, "Primary Ligament Corridor (Notch to Hole)"),
        calc_group_stats(hole_elems, "Hole Perimeter Annulus (100 to 140 um)"),
        calc_group_stats(sec_elems, "Secondary Right Ligament Zone"),
        calc_group_stats(farfield_elems, "Quiescent Far-Field Bulk")
    ]

    print("\n" + "=" * 110)
    print(f"{'Region':<40} {'Count':<7} {'Area mm2':<10} {'Unw Sum %':<12} {'Area Wtd %':<12} {'L2 Norm %':<12} {'Max MPa':<10}")
    print("=" * 110)
    for r in regions:
        print(f"{r['group_name']:<40} {r['element_count']:<7d} {r['area_mm2']:<10.5f} {r['share_of_unweighted_sum_pct']:<12.2f} {r['share_of_area_weighted_integral_pct']:<12.2f} {r['share_of_l2_norm_pct']:<12.2f} {r['miseseri_max_MPa']:<10.2f}")
    print("=" * 110)

    summary = {
        "source_odb": odb_path,
        "misesavg_MPa": misesavg_val,
        "total_elements": total_count,
        "total_domain_area_mm2": total_area,
        "total_unweighted_sum_MPa": total_unweighted_sum,
        "total_area_weighted_sum_MPa_mm2": total_area_weighted_sum,
        "total_l2_norm_MPa_mm": total_l2_norm,
        "regions": regions
    }

    with open(out_json, 'w') as f:
        json.dump(summary, f, indent=4)
    print(f"Saved audit JSON: {out_json}")


if __name__ == "__main__":
    odb_in = "PK_HOLE_F1661_RECOVERY.odb"
    out_j = "results/validation/f1682_miseseri_spatial_integration_audit.json"
    out_c = "results/validation/f1682_miseseri_element_level_audit.csv"
    run_spatial_miseseri_audit(odb_in, out_j, out_c)
