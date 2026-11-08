# -*- coding: utf-8 -*-
"""
scripts/validation/audit_f1685_energy_and_area.py
==================================================
Performs targeted quantitative audits for ChatGPT Review HND-dbc110c492ad:
1. Broken Element Census & Physical Damaged Area Reconciliation:
   - Resolves 10,953 broken element records as 2,790 unique physical elements (CPE4/CPE3).
   - Computes exact physical area of damaged zone for F1685 vs F1678.
2. Complete Energy Balance & Quadrature Analysis:
   - Evaluates W_ext, U, D_f, E_total increment-by-increment.
   - Diagnoses exact mechanical and mathematical origin of the 14.0% discrepancy.
"""
import os
import csv
import json
import math

def parse_inp_mesh(inp_path, n_phys):
    """Parse node coordinates and element connectivity for physical elements (1..n_phys)."""
    nodes = {}
    elements = {}
    in_nodes = False
    in_elems = False

    with open(inp_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('*NODE'):
                in_nodes = True
                in_elems = False
                continue
            elif line.startswith('*ELEMENT'):
                in_nodes = False
                # We only want physical elements (Layer 1, IDs <= n_phys)
                in_elems = True
                continue
            elif line.startswith('*'):
                in_nodes = False
                in_elems = False
                continue

            if in_nodes:
                parts = [p.strip() for p in line.split(',')]
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                except (ValueError, IndexError):
                    pass
            elif in_elems:
                parts = [p.strip() for p in line.split(',')]
                try:
                    eid = int(parts[0])
                    if eid <= n_phys:
                        conn = [int(p) for p in parts[1:]]
                        elements[eid] = conn
                except (ValueError, IndexError):
                    pass
    return nodes, elements

def element_area(nodes, conn):
    """Compute polygon area using shoelace formula."""
    pts = [nodes[nid] for nid in conn]
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    return abs(area) * 0.5

def audit_damaged_area():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # F1685 Combined Adapted
    inp_85 = os.path.join(repo_root, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_F1685_COMBINED_PROD.inp")
    crack_85 = os.path.join(repo_root, "results", "validation", "f1685_prod_crack_path.csv")
    nodes_85, elems_85 = parse_inp_mesh(inp_85, 21569)

    with open(crack_85, 'r') as f:
        reader = csv.DictReader(f)
        rows_85 = list(reader)

    unique_eids_85 = sorted(list(set(int(r['phys_elem_id']) for r in rows_85)))
    print(f"F1685: {len(rows_85)} IP records -> {len(unique_eids_85)} unique physical broken elements.")

    area_85_total = 0.0
    area_85_primary = 0.0
    area_85_secondary = 0.0
    h_equiv_85 = []

    for eid in unique_eids_85:
        if eid in elems_85:
            a = element_area(nodes_85, elems_85[eid])
            area_85_total += a
            h = math.sqrt(a)
            h_equiv_85.append(h)
            # Find centroid
            pts = [nodes_85[nid] for nid in elems_85[eid]]
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            if cx <= 0.65:
                area_85_primary += a
            else:
                area_85_secondary += a

    # F1678 Baseline
    inp_78 = os.path.join(repo_root, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_F1664_METHOD_A_PROD.inp")
    crack_78 = os.path.join(repo_root, "results", "validation", "f1678_prod_crack_path.csv")
    nodes_78, elems_78 = parse_inp_mesh(inp_78, 20213)

    with open(crack_78, 'r') as f:
        reader = csv.DictReader(f)
        rows_78 = list(reader)

    unique_eids_78 = sorted(list(set(int(r['phys_elem_id']) for r in rows_78)))
    print(f"F1678: {len(rows_78)} IP records -> {len(unique_eids_78)} unique physical broken elements.")

    area_78_total = 0.0
    area_78_primary = 0.0
    area_78_secondary = 0.0
    h_equiv_78 = []

    for eid in unique_eids_78:
        if eid in elems_78:
            a = element_area(nodes_78, elems_78[eid])
            area_78_total += a
            h = math.sqrt(a)
            h_equiv_78.append(h)
            pts = [nodes_78[nid] for nid in elems_78[eid]]
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            if cx <= 0.65:
                area_78_primary += a
            else:
                area_78_secondary += a

    med_h_85 = sorted(h_equiv_85)[len(h_equiv_85)//2] * 1000.0 if h_equiv_85 else 0.0
    med_h_78 = sorted(h_equiv_78)[len(h_equiv_78)//2] * 1000.0 if h_equiv_78 else 0.0

    print("=== DAMAGED ZONE PHYSICAL AREA AUDIT ===")
    print(f"F1678 Baseline (20,213 FEs):")
    print(f"  - Unique Broken Elements: {len(unique_eids_78)}")
    print(f"  - Total Damaged Area:     {area_78_total:.6f} mm^2 ({area_78_total/0.9678*100:.2f}% domain)")
    print(f"  - Primary Branch Area:    {area_78_primary:.6f} mm^2")
    print(f"  - Secondary Branch Area:  {area_78_secondary:.6f} mm^2")
    print(f"  - Median Element Size h:  {med_h_78:.2f} um")
    print(f"F1685 Combined Adapted (21,569 FEs):")
    print(f"  - Unique Broken Elements: {len(unique_eids_85)}")
    print(f"  - Total Damaged Area:     {area_85_total:.6f} mm^2 ({area_85_total/0.9678*100:.2f}% domain)")
    print(f"  - Primary Branch Area:    {area_85_primary:.6f} mm^2")
    print(f"  - Secondary Branch Area:  {area_85_secondary:.6f} mm^2")
    print(f"  - Median Element Size h:  {med_h_85:.2f} um")
    delta_area = (area_85_total - area_78_total) / area_78_total * 100.0
    print(f"Area Invariance: Delta Area = {delta_area:+.2f}%")

    return {
        "f1678": {
            "ip_records": len(rows_78),
            "unique_broken_elements": len(unique_eids_78),
            "total_damaged_area_mm2": area_78_total,
            "primary_damaged_area_mm2": area_78_primary,
            "secondary_damaged_area_mm2": area_78_secondary,
            "median_element_h_um": med_h_78
        },
        "f1685": {
            "ip_records": len(rows_85),
            "unique_broken_elements": len(unique_eids_85),
            "total_damaged_area_mm2": area_85_total,
            "primary_damaged_area_mm2": area_85_primary,
            "secondary_damaged_area_mm2": area_85_secondary,
            "median_element_h_um": med_h_85
        },
        "area_difference_pct": delta_area
    }

def audit_energy_balance():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    rf_csv = os.path.join(repo_root, "results", "validation", "f1685_prod_rf_u.csv")
    energy_csv = os.path.join(repo_root, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "f1685_uel_energy_balance.csv")

    rf_data = []
    with open(rf_csv, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rf_data.append({
                'step': r['step'],
                'frame': int(r['frame']),
                'time': float(r['time']),
                'u2': float(r['u2_mm']),
                'rf2': float(r['rf2_kN']),
                'w_ext': float(r['w_ext_kNmm'])
            })

    energy_data = []
    with open(energy_csv, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('Step'):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 7:
                energy_data.append({
                    'step': int(parts[0]),
                    'inc': int(parts[1]),
                    'time': float(parts[2]),
                    'u_elastic': float(parts[4]),
                    'd_fracture': float(parts[5]),
                    'e_total': float(parts[6])
                })

    print("=== ENERGY BALANCE INCREMENTAL AUDIT ===")
    print(f"Total RF-U records: {len(rf_data)}, Total UEL energy records: {len(energy_data)}")

    # Check energy monotonicity
    d_frac_monotonic = True
    max_d_frac_drop = 0.0
    for i in range(1, len(energy_data)):
        diff = energy_data[i]['d_fracture'] - energy_data[i-1]['d_fracture']
        if diff < -1e-12:
            d_frac_monotonic = False
            if abs(diff) > max_d_frac_drop:
                max_d_frac_drop = abs(diff)

    print(f"Fracture Dissipation Monotonicity: {'PASS (strictly non-decreasing)' if d_frac_monotonic else f'VIOLATED (max drop {max_d_frac_drop:.2e})'}")

    final_u_el = energy_data[-1]['u_elastic']
    final_d_fr = energy_data[-1]['d_fracture']
    final_e_tot = energy_data[-1]['e_total']
    final_w_ext = rf_data[-1]['w_ext']
    peak_u_el = max(e['u_elastic'] for e in energy_data)

    print(f"Peak Elastic Energy U_max:       {peak_u_el*1e3:.4f} mJ")
    print(f"Final Elastic Energy U_final:    {final_u_el*1e6:.4f} uJ (Relaxation: {(1.0 - final_u_el/peak_u_el)*100:.2f}%)")
    print(f"Final Fracture Dissipation D_f:  {final_d_fr*1e3:.4f} mJ")
    print(f"Final Total Internal Energy:     {final_e_tot*1e3:.4f} mJ")
    print(f"Final External Work W_ext:       {final_w_ext*1e3:.4f} mJ")
    residual_mJ = (final_e_tot - final_w_ext) * 1e3
    rel_discrepancy = abs(final_e_tot - final_w_ext) / final_e_tot * 100.0
    print(f"Energy Balance Residual:         {residual_mJ:+.4f} mJ ({rel_discrepancy:.2f}% relative to E_total)")

    # Diagnose where the discrepancy occurs
    # Prior to crack snap-through (at peak load u2 = 0.00534 mm)
    peak_rf_idx = max(range(len(rf_data)), key=lambda i: rf_data[i]['rf2'])
    peak_w_ext = rf_data[peak_rf_idx]['w_ext']
    print(f"Pre-peak energy balance at u2 = {rf_data[peak_rf_idx]['u2']:.5f} mm:")
    print(f"  W_ext = {peak_w_ext*1e3:.4f} mJ vs U_el = {peak_u_el*1e3:.4f} mJ (diff = {abs(peak_w_ext - peak_u_el)*1e3:.4f} mJ, {abs(peak_w_ext - peak_u_el)/peak_w_ext*100:.2f}%)")

    return {
        "d_fracture_monotonic": d_frac_monotonic,
        "peak_elastic_energy_mJ": peak_u_el * 1e3,
        "final_elastic_energy_uJ": final_u_el * 1e6,
        "elastic_relaxation_pct": (1.0 - final_u_el/peak_u_el)*100,
        "final_fracture_dissipation_mJ": final_d_fr * 1e3,
        "final_total_internal_energy_mJ": final_e_tot * 1e3,
        "final_external_work_mJ": final_w_ext * 1e3,
        "energy_residual_mJ": residual_mJ,
        "energy_discrepancy_pct": rel_discrepancy,
        "pre_peak_discrepancy_pct": abs(peak_w_ext - peak_u_el)/peak_w_ext*100
    }

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    area_res = audit_damaged_area()
    energy_res = audit_energy_balance()

    out_json = os.path.join(repo_root, "results", "validation", "f1685_targeted_offline_acceptance_audit.json")
    with open(out_json, 'w') as f:
        json.dump({
            "task_id": "F1685-METHOD-A-COMBINED-ADAPTED-FRACTURE-PREPARATION-AND-EXECUTION",
            "correlation_id": "HND-dbc110c492ad",
            "damaged_area_audit": area_res,
            "energy_balance_audit": energy_res
        }, f, indent=2)
    print(f"\nSaved targeted acceptance audit to: {out_json}")

if __name__ == '__main__':
    main()
