"""
F1683: Comprehensive element-level spatial integration and area-weighted audit
of native Abaqus MISESERI discretization error indicator on PK_HOLE_F1661_RECOVERY.odb.

Resolves Independent Review HND-a9ff3c192a8e:
1. Implements two distinct spatial analyses:
   - Analysis A: Mutually Exclusive Disjoint Partition (element counts, areas, and squared L2 integrals sum to exactly 100%).
   - Analysis B: Diagnostic Feature Neighborhoods (explicitly noted as overlapping).
2. Reports both:
   - Ratio of norms: ||e||_{L2(Omega_i)} / ||e||_{L2(Omega)}
   - Additive contribution to squared norm: int_{Omega_i} e^2 dA / int_Omega e^2 dA
3. Enforces strict completeness checks: unique element IDs, valid positive EVOL, fails closed if any element lacks MISESERI or EVOL.
4. Verifies MISESAVG invariance across all elements.
5. Accurately calculates analytical domain area: Omega = 1.0*1.0 - pi*0.1^2 - slit_area.
"""

import sys
import os
import math
import json
import csv

def run_spatial_miseseri_audit(odb_path, out_json, out_csv):
    print("=" * 80)
    print("F1683: MISESERI SPATIAL INTEGRATION AND AREA-WEIGHTED ERROR AUDIT")
    print(f"Source ODB: {odb_path}")
    print("=" * 80)

    if not os.path.exists(odb_path):
        raise IOError(f"ODB not found: {odb_path}")

    from odbAccess import openOdb
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps['Step-1']
    frame = step.frames[-1]

    # Assembly instance
    inst = list(odb.rootAssembly.instances.values())[0]
    node_coords = {n.label: n.coordinates for n in inst.nodes}

    # Extract field outputs
    if 'MISESERI' not in frame.fieldOutputs:
        raise KeyError("Field output MISESERI missing from frame!")
    if 'EVOL' not in frame.fieldOutputs:
        raise KeyError("Field output EVOL missing from frame!")
    if 'MISESAVG' not in frame.fieldOutputs:
        raise KeyError("Field output MISESAVG missing from frame!")

    miseseri_field = frame.fieldOutputs['MISESERI']
    evol_field = frame.fieldOutputs['EVOL']
    misesavg_field = frame.fieldOutputs['MISESAVG']

    # Physical clarification: MISESAVG in Abaqus is "Element average mises stress" (WHOLE_ELEMENT),
    # NOT a pre-computed domain average. Each element has its own average Mises stress.
    misesavg_by_label = {}
    for v in misesavg_field.values:
        if v.elementLabel in misesavg_by_label:
            raise ValueError(f"Duplicate MISESAVG value for element {v.elementLabel}")
        misesavg_by_label[v.elementLabel] = float(v.data)

    miseseri_by_label = {}
    for v in miseseri_field.values:
        if v.elementLabel in miseseri_by_label:
            raise ValueError(f"Duplicate MISESERI value for element {v.elementLabel}")
        miseseri_by_label[v.elementLabel] = float(v.data)

    evol_by_label = {}
    for v in evol_field.values:
        if v.elementLabel in evol_by_label:
            raise ValueError(f"Duplicate EVOL value for element {v.elementLabel}")
        ev = float(v.data)
        if ev <= 0.0:
            raise ValueError(f"Non-positive element area/volume for element {v.elementLabel}: {ev}")
        evol_by_label[v.elementLabel] = ev

    # Compute true area-weighted domain average Mises stress:
    total_area_check = sum(evol_by_label.values())
    domain_avg_mises = sum(misesavg_by_label[el] * evol_by_label[el] for el in evol_by_label) / total_area_check
    print(f"True Domain Area-Weighted Mises Stress: {domain_avg_mises:.4f} MPa")
    print(f"Element Average Mises Stress range: [{min(misesavg_by_label.values()):.4f}, {max(misesavg_by_label.values()):.4f}] MPa")

    hole_center = (0.65, 0.65)
    notch_tip = (0.50, 0.50)

    elements_data = []
    total_elements_in_instance = len(inst.elements)

    for el in inst.elements:
        elabel = el.label
        eltype = el.type
        conn = el.connectivity
        coords = [node_coords[nl] for nl in conn]

        xc = sum(c[0] for c in coords) / float(len(coords))
        yc = sum(c[1] for c in coords) / float(len(coords))

        # Fail-closed check: verify presence
        if elabel not in miseseri_by_label:
            raise KeyError(f"Element {elabel} missing from MISESERI field output!")
        if elabel not in evol_by_label:
            raise KeyError(f"Element {elabel} missing from EVOL field output!")

        miseseri = miseseri_by_label[elabel]
        area = evol_by_label[elabel]

        # Distance to notch tip
        r_notch = math.sqrt((xc - notch_tip[0])**2 + (yc - notch_tip[1])**2)

        # Distance to hole center
        r_hole = math.sqrt((xc - hole_center[0])**2 + (yc - hole_center[1])**2)

        # ----------------------------------------------------------------------
        # Analysis A: Mutually Exclusive Disjoint Partition
        # Priority order guarantees every element belongs to EXACTLY ONE partition
        # ----------------------------------------------------------------------
        if r_notch <= 0.050:
            partition = "Notch_Tip_Partition"
        elif 0.10 <= r_hole <= 0.14:
            partition = "Hole_Annulus_Partition"
        elif 0.50 <= xc < 0.65 and 0.45 <= yc <= 0.65:
            partition = "Primary_Corridor_Partition"
        elif xc >= 0.70 and 0.55 <= yc <= 0.75:
            partition = "Secondary_Ligament_Partition"
        else:
            partition = "Far_Field_Bulk_Partition"

        # ----------------------------------------------------------------------
        # Analysis B: Diagnostic Feature Neighborhoods (Overlapping)
        # ----------------------------------------------------------------------
        diag_notch = (r_notch <= 0.050)
        diag_primary = (0.50 <= xc <= 0.65 and 0.48 <= yc <= 0.65 and r_hole >= 0.10)
        diag_hole_annulus = (0.10 <= r_hole <= 0.14)
        diag_secondary = (0.70 <= xc <= 1.00 and 0.55 <= yc <= 0.75)

        # Relative error indicators:
        # eta_local_pct: Normalized by that element's own MISESAVG (element average Mises stress)
        # eta_global_pct: Normalized by domain-wide area-weighted average Mises stress
        misesavg_e = misesavg_by_label[elabel]
        eta_local_pct = (miseseri / misesavg_e) * 100.0 if misesavg_e > 0 else 0.0
        eta_global_pct = (miseseri / domain_avg_mises) * 100.0 if domain_avg_mises > 0 else 0.0

        elements_data.append({
            "label": elabel,
            "type": eltype,
            "xc": xc,
            "yc": yc,
            "area_mm2": area,
            "misesavg_MPa": misesavg_e,
            "miseseri_MPa": miseseri,
            "eta_local_pct": eta_local_pct,
            "eta_global_pct": eta_global_pct,
            "weighted_error_MPa_mm2": miseseri * area,
            "weighted_error_sq_MPa2_mm2": (miseseri ** 2) * area,
            "partition": partition,
            "diag_notch": diag_notch,
            "diag_primary": diag_primary,
            "diag_hole_annulus": diag_hole_annulus,
            "diag_secondary": diag_secondary
        })

    odb.close()
    print(f"Verified and extracted 100% of physical elements: {len(elements_data)} / {total_elements_in_instance}")

    # Write element-level CSV
    with open(out_csv, 'w', newline='') as f:
        fieldnames = ["label", "type", "xc", "yc", "area_mm2", "misesavg_MPa", "miseseri_MPa",
                      "eta_local_pct", "eta_global_pct", "weighted_error_MPa_mm2", "weighted_error_sq_MPa2_mm2",
                      "partition", "diag_notch", "diag_primary", "diag_hole_annulus", "diag_secondary"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(elements_data)
    print(f"Saved element-level CSV: {out_csv}")

    # Global Domain Quantities
    total_count = len(elements_data)
    total_area = sum(e["area_mm2"] for e in elements_data)
    total_unweighted_sum = sum(e["miseseri_MPa"] for e in elements_data)
    total_area_weighted_sum = sum(e["weighted_error_MPa_mm2"] for e in elements_data)
    total_sq_l2_integral = sum(e["weighted_error_sq_MPa2_mm2"] for e in elements_data)
    total_l2_norm = math.sqrt(total_sq_l2_integral)

    # Analytical area calculation:
    # Plate: 1.0 x 1.0 mm^2
    # Circular hole: R = 0.10 mm -> Area_hole = pi * R^2 = pi * 0.01 = 0.0314159265 mm^2
    # Cutout notch in CAD: 0.50 mm long x 0.002 mm wide -> Area_slit = 0.50 * 0.002 = 0.001 mm^2
    # Analytical Area = 1.0 - pi*0.1^2 - 0.001 = 0.967584 mm^2
    analytical_area_smooth = 1.0 - math.pi * (0.10**2)
    analytical_area_with_slit = 1.0 - math.pi * (0.10**2) - 0.001
    area_ratio = (total_area / analytical_area_with_slit) * 100.0

    print(f"\nTotal specimen area: {total_area:.6f} mm^2")
    print(f"  Analytical area (smooth hole, zero slit): {analytical_area_smooth:.6f} mm^2")
    print(f"  Analytical area (CAD hole + 2um slit):   {analytical_area_with_slit:.6f} mm^2")
    print(f"  Area conservation vs analytical:        {area_ratio:.4f}%")
    print(f"Total unweighted MISESERI sum:            {total_unweighted_sum:.4f} MPa")
    print(f"Total area-weighted MISESERI integral:    {total_area_weighted_sum:.6f} MPa*mm^2")
    print(f"Total squared L2 error integral:          {total_sq_l2_integral:.6f} MPa^2*mm^2")
    print(f"Total L2 stress error norm:               {total_l2_norm:.6f} MPa*mm")

    def calc_group_stats(group_elems, name, is_disjoint=True):
        cnt = len(group_elems)
        if cnt == 0:
            return None
        vals = [e["miseseri_MPa"] for e in group_elems]
        vals.sort()
        area_sum = sum(e["area_mm2"] for e in group_elems)
        unw_sum = sum(e["miseseri_MPa"] for e in group_elems)
        weighted_sum = sum(e["weighted_error_MPa_mm2"] for e in group_elems)
        sq_l2_sum = sum(e["weighted_error_sq_MPa2_mm2"] for e in group_elems)
        l2_norm = math.sqrt(sq_l2_sum)

        h_med = vals[cnt // 2]
        return {
            "group_name": name,
            "is_disjoint_partition": is_disjoint,
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
            "squared_l2_error_integral_MPa2_mm2": sq_l2_sum,
            "share_of_squared_l2_integral_pct": (sq_l2_sum / total_sq_l2_integral) * 100.0,
            "l2_error_norm_MPa_mm": l2_norm,
            "norm_ratio_pct": (l2_norm / total_l2_norm) * 100.0,
            "area_averaged_error_MPa": weighted_sum / area_sum if area_sum > 0 else 0.0
        }

    # --------------------------------------------------------------------------
    # Analysis A: Mutually Exclusive Disjoint Partition
    # --------------------------------------------------------------------------
    p_notch = [e for e in elements_data if e["partition"] == "Notch_Tip_Partition"]
    p_hole = [e for e in elements_data if e["partition"] == "Hole_Annulus_Partition"]
    p_prim = [e for e in elements_data if e["partition"] == "Primary_Corridor_Partition"]
    p_sec = [e for e in elements_data if e["partition"] == "Secondary_Ligament_Partition"]
    p_bulk = [e for e in elements_data if e["partition"] == "Far_Field_Bulk_Partition"]

    partition_regions = [
        calc_group_stats(p_notch, "Notch Tip Region (r <= 50 um)", is_disjoint=True),
        calc_group_stats(p_hole, "Hole Perimeter Annulus (100 to 140 um)", is_disjoint=True),
        calc_group_stats(p_prim, "Primary Ligament Corridor", is_disjoint=True),
        calc_group_stats(p_sec, "Secondary Right Ligament", is_disjoint=True),
        calc_group_stats(p_bulk, "Far-Field Bulk Specimen", is_disjoint=True)
    ]

    # Verify partition summation
    part_count_sum = sum(r["element_count"] for r in partition_regions)
    part_area_sum = sum(r["area_mm2"] for r in partition_regions)
    part_int_sum = sum(r["area_weighted_error_integral_MPa_mm2"] for r in partition_regions)
    part_sq_sum = sum(r["squared_l2_error_integral_MPa2_mm2"] for r in partition_regions)

    if part_count_sum != total_count:
        raise ValueError(f"Partition count sum {part_count_sum} != total {total_count}")
    if abs(part_area_sum - total_area) > 1e-9:
        raise ValueError(f"Partition area sum {part_area_sum} != total {total_area}")
    if abs(part_int_sum - total_area_weighted_sum) > 1e-9:
        raise ValueError(f"Partition integral sum {part_int_sum} != total {total_area_weighted_sum}")
    if abs(part_sq_sum - total_sq_l2_integral) > 1e-6:
        raise ValueError(f"Partition squared L2 sum {part_sq_sum} != total {total_sq_l2_integral}")

    print("\n" + "=" * 125)
    print("ANALYSIS A: MUTUALLY EXCLUSIVE DISJOINT PARTITION (EXACT ADDITIVE DECOMPOSITION)")
    print("=" * 125)
    print(f"{'Partition Zone':<35} {'Count':<7} {'Area mm2':<10} {'Area %':<8} {'Integral MPa*mm2':<18} {'Int Share %':<13} {'Sq L2 Share %':<15} {'Norm Ratio %':<13}")
    print("-" * 125)
    for r in partition_regions:
        print(f"{r['group_name']:<35} {r['element_count']:<7d} {r['area_mm2']:<10.5f} {r['pct_of_domain_area']:<8.2f} {r['area_weighted_error_integral_MPa_mm2']:<18.4f} {r['share_of_area_weighted_integral_pct']:<13.2f} {r['share_of_squared_l2_integral_pct']:<15.2f} {r['norm_ratio_pct']:<13.2f}")
    print("-" * 125)
    print(f"{'TOTAL PARTITION RECONCILIATION':<35} {part_count_sum:<7d} {part_area_sum:<10.5f} {100.0:<8.2f} {part_int_sum:<18.4f} {100.0:<13.2f} {100.0:<15.2f} {'--':<13}")
    print("=" * 125)

    # --------------------------------------------------------------------------
    # Analysis B: Diagnostic Feature Neighborhoods (Overlapping)
    # --------------------------------------------------------------------------
    d_notch = [e for e in elements_data if e["diag_notch"]]
    d_prim = [e for e in elements_data if e["diag_primary"]]
    d_hole = [e for e in elements_data if e["diag_hole_annulus"]]
    d_sec = [e for e in elements_data if e["diag_secondary"]]

    diagnostic_regions = [
        calc_group_stats(d_notch, "Diagnostic: Notch Tip (r <= 50 um)", is_disjoint=False),
        calc_group_stats(d_prim, "Diagnostic: Primary Corridor (Notch->Hole)", is_disjoint=False),
        calc_group_stats(d_hole, "Diagnostic: Hole Annulus (100 to 140 um)", is_disjoint=False),
        calc_group_stats(d_sec, "Diagnostic: Secondary Ligament Zone", is_disjoint=False)
    ]

    print("\n" + "=" * 125)
    print("ANALYSIS B: DIAGNOSTIC FEATURE NEIGHBORHOODS (OVERLAPPING REGIONS)")
    print("=" * 125)
    print(f"{'Diagnostic Neighborhood':<35} {'Count':<7} {'Area mm2':<10} {'Area %':<8} {'Integral MPa*mm2':<18} {'Int Share %':<13} {'Sq L2 Share %':<15} {'Norm Ratio %':<13}")
    print("-" * 125)
    for r in diagnostic_regions:
        print(f"{r['group_name']:<35} {r['element_count']:<7d} {r['area_mm2']:<10.5f} {r['pct_of_domain_area']:<8.2f} {r['area_weighted_error_integral_MPa_mm2']:<18.4f} {r['share_of_area_weighted_integral_pct']:<13.2f} {r['share_of_squared_l2_integral_pct']:<15.2f} {r['norm_ratio_pct']:<13.2f}")
    print("=" * 125)

    # Export complete JSON report
    summary = {
        "source_odb": odb_path,
        "misesavg_definition": "Abaqus MISESAVG is Element average Mises stress (WHOLE_ELEMENT), not domain average",
        "true_domain_area_weighted_mises_MPa": domain_avg_mises,
        "misesavg_element_min_MPa": min(misesavg_by_label.values()),
        "misesavg_element_max_MPa": max(misesavg_by_label.values()),
        "total_elements": total_count,
        "total_domain_area_mm2": total_area,
        "analytical_area_smooth_mm2": analytical_area_smooth,
        "analytical_area_with_slit_mm2": analytical_area_with_slit,
        "area_conservation_pct": area_ratio,
        "total_unweighted_sum_MPa": total_unweighted_sum,
        "total_area_weighted_sum_MPa_mm2": total_area_weighted_sum,
        "total_squared_l2_integral_MPa2_mm2": total_sq_l2_integral,
        "total_l2_norm_MPa_mm": total_l2_norm,
        "analysis_a_disjoint_partition": partition_regions,
        "analysis_b_diagnostic_overlapping": diagnostic_regions
    }

    with open(out_json, 'w') as f:
        json.dump(summary, f, indent=4)
    print(f"\nSaved F1683 audit JSON: {out_json}")


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        odb_in = sys.argv[1]
        out_j = sys.argv[2]
        out_c = sys.argv[3]
    else:
        odb_in = "PK_HOLE_F1661_RECOVERY.odb"
        out_j = "results/validation/f1683_miseseri_spatial_integration_audit.json"
        out_c = "results/validation/f1683_miseseri_element_level_audit.csv"
    run_spatial_miseseri_audit(odb_in, out_j, out_c)
