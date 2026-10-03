"""
Stage 6: Element / Output-Position & Stress Recovery Averaging Semantics Audit
Audits ODB output positions, element formulations (CPE4 vs CPE3),
stress recovery averaging, and visual colormap vs sizing mathematics.
"""
import sys
import os
import json
import math
from odbAccess import openOdb
from abaqusConstants import *


def serialize_helper(obj):
    if hasattr(obj, '__class__') and obj.__class__.__name__ in ('Boolean', 'SymbolicConstant'):
        if obj.__class__.__name__ == 'Boolean':
            return bool(obj)
        return str(obj)
    if isinstance(obj, (int, long)):
        return int(obj)
    if isinstance(obj, float):
        return float(obj)
    return str(obj)


def audit_odb_fields(odb_path, out_json_path):
    print("Starting Stage 6 Output-Position and Stress-Recovery Audit...")
    print("Opening ODB: " + str(odb_path))
    odb = openOdb(odb_path, readOnly=True)

    step_name = "Step-1"
    step = odb.steps[step_name]
    last_frame = step.frames[-1]

    print("Step: " + str(step_name) + ", Last Frame Index: " + str(last_frame.frameId))
    print("Available Field Outputs:")
    field_summary = {}
    for f_name in sorted(last_frame.fieldOutputs.keys()):
        f = last_frame.fieldOutputs[f_name]
        locs = [str(loc.position) for loc in f.locations]
        desc = str(f.description)
        print("  - " + str(f_name) + ": " + desc + " (locations: " + str(locs) + ")")
        field_summary[str(f_name)] = {
            "description": desc,
            "locations": locs
        }

    inst_name = "PART-1-1"
    if inst_name not in odb.rootAssembly.instances:
        inst_name = list(odb.rootAssembly.instances.keys())[0]
    inst = odb.rootAssembly.instances[inst_name]

    # Inspect MISESERI, MISESAVG, S, EVOL
    f_eri = last_frame.fieldOutputs['MISESERI'] if 'MISESERI' in last_frame.fieldOutputs else None
    f_avg = last_frame.fieldOutputs['MISESAVG'] if 'MISESAVG' in last_frame.fieldOutputs else None
    f_s = last_frame.fieldOutputs['S'] if 'S' in last_frame.fieldOutputs else None
    f_evol = last_frame.fieldOutputs['EVOL'] if 'EVOL' in last_frame.fieldOutputs else None

    # Element data extraction
    elem_data = {}
    node_coords = {}
    for n in inst.nodes:
        node_coords[n.label] = [float(n.coordinates[0]), float(n.coordinates[1])]

    for el in inst.elements:
        conn = [int(nid) for nid in el.connectivity]
        pts = [node_coords[nid] for nid in conn if nid in node_coords]
        cx = sum([p[0] for p in pts]) / float(len(pts)) if pts else 0.0
        cy = sum([p[1] for p in pts]) / float(len(pts)) if pts else 0.0
        elem_data[int(el.label)] = {
            "type": str(el.type),
            "connectivity": conn,
            "centroid": [float(cx), float(cy)],
            "num_nodes": int(len(conn))
        }

    # Extract MISESERI values
    eri_values = {}
    if f_eri is not None:
        for val in f_eri.values:
            if val.elementLabel is not None:
                eri_values[int(val.elementLabel)] = float(val.data)

    # Extract MISESAVG values (average Mises stress over element or at integration points)
    avg_values = {}
    if f_avg is not None:
        for val in f_avg.values:
            if val.elementLabel is not None:
                avg_values[int(val.elementLabel)] = float(val.data)

    # Extract EVOL values (element volumes)
    evol_values = {}
    if f_evol is not None:
        for val in f_evol.values:
            if val.elementLabel is not None:
                evol_values[int(val.elementLabel)] = float(val.data)

    # Extract Stress Components and compute Mises stress at integration points
    s_ip_data = {}
    if f_s is not None:
        for val in f_s.values:
            elabel = int(val.elementLabel)
            if elabel not in s_ip_data:
                s_ip_data[elabel] = []
            s11 = float(val.data[0])
            s22 = float(val.data[1])
            s33 = float(val.data[2]) if len(val.data) > 2 else 0.0
            s12 = float(val.data[3]) if len(val.data) > 3 else 0.0
            # Mises stress: sqrt( 0.5 * ( (s11-s22)^2 + (s22-s33)^2 + (s33-s11)^2 + 6*s12^2 ) )
            vm = math.sqrt(max(0.0, 0.5 * ((s11-s22)**2 + (s22-s33)**2 + (s33-s11)**2 + 6.0*s12**2)))
            s_ip_data[elabel].append({
                "ip": int(val.integrationPoint),
                "s11": s11,
                "s22": s22,
                "s33": s33,
                "s12": s12,
                "mises": vm
            })

    # Compute element-level stress metrics:
    cpe4_count = 0
    cpe3_count = 0
    cpe4_vm_spreads = []
    cpe4_eri_list = []
    cpe3_eri_list = []

    quad_farfield_eri = []
    quad_corridor_eri = []
    tri_eri = []

    regional_metrics = {
        "crack_corridor": {"count": 0, "eri_sum": 0.0, "evol_sum": 0.0, "mises_sum": 0.0, "eri_energy_sq": 0.0},
        "crack_wake": {"count": 0, "eri_sum": 0.0, "evol_sum": 0.0, "mises_sum": 0.0, "eri_energy_sq": 0.0},
        "right_ligament": {"count": 0, "eri_sum": 0.0, "evol_sum": 0.0, "mises_sum": 0.0, "eri_energy_sq": 0.0},
        "far_field": {"count": 0, "eri_sum": 0.0, "evol_sum": 0.0, "mises_sum": 0.0, "eri_energy_sq": 0.0},
        "boundary": {"count": 0, "eri_sum": 0.0, "evol_sum": 0.0, "mises_sum": 0.0, "eri_energy_sq": 0.0}
    }

    full_elem_records = []

    for elabel, edata in elem_data.items():
        cx, cy = edata["centroid"]
        etype = str(edata["type"])
        eri = float(eri_values.get(elabel, 0.0))
        avg_vm = float(avg_values.get(elabel, 0.0))
        evol = float(evol_values.get(elabel, 0.0004)) # default 0.02*0.02 = 0.0004 for 2D plane strain unit thickness

        # Integration point spread
        ip_list = s_ip_data.get(elabel, [])
        if len(ip_list) > 1:
            vm_vals = [ip["mises"] for ip in ip_list]
            vm_spread = max(vm_vals) - min(vm_vals)
            vm_mean = sum(vm_vals) / float(len(vm_vals))
            vm_rel_spread = vm_spread / max(1e-6, vm_mean)
        elif len(ip_list) == 1:
            vm_spread = 0.0
            vm_mean = ip_list[0]["mises"]
            vm_rel_spread = 0.0
        else:
            vm_spread = 0.0
            vm_mean = avg_vm
            vm_rel_spread = 0.0

        # Element energy norm error contribution: e_el^2 = (MISESERI)^2 * EVOL
        e_energy_sq = (eri ** 2) * evol

        # Classify region
        is_boundary = bool(cx <= 0.02 or cx >= 0.98 or cy <= 0.02 or cy >= 0.98)
        if 0.45 <= cx <= 0.55 and 0.45 <= cy <= 0.55:
            reg_name = "crack_corridor"
        elif cx < 0.45 and 0.45 <= cy <= 0.55:
            reg_name = "crack_wake"
        elif cx > 0.55 and 0.45 <= cy <= 0.55:
            reg_name = "right_ligament"
        else:
            reg_name = "far_field"

        reg = regional_metrics[reg_name]
        reg["count"] += 1
        reg["eri_sum"] += eri
        reg["evol_sum"] += evol
        reg["mises_sum"] += vm_mean
        reg["eri_energy_sq"] += e_energy_sq

        if is_boundary:
            reg_b = regional_metrics["boundary"]
            reg_b["count"] += 1
            reg_b["eri_sum"] += eri
            reg_b["evol_sum"] += evol
            reg_b["mises_sum"] += vm_mean
            reg_b["eri_energy_sq"] += e_energy_sq

        if edata["num_nodes"] == 4:
            cpe4_count += 1
            cpe4_vm_spreads.append(vm_spread)
            cpe4_eri_list.append(eri)
            if reg_name == "far_field":
                quad_farfield_eri.append(eri)
            elif reg_name == "crack_corridor":
                quad_corridor_eri.append(eri)
        else:
            cpe3_count += 1
            cpe3_eri_list.append(eri)
            tri_eri.append(eri)

        rel_error = eri / max(1e-6, vm_mean) * 100.0

        full_elem_records.append({
            "element_id": int(elabel),
            "type": etype,
            "num_nodes": int(edata["num_nodes"]),
            "centroid_x": round(cx, 6),
            "centroid_y": round(cy, 6),
            "region": reg_name,
            "is_boundary": is_boundary,
            "miseseri": round(eri, 6),
            "mises_mean": round(vm_mean, 6),
            "mises_ip_spread": round(vm_spread, 6),
            "mises_rel_spread_pct": round(vm_rel_spread * 100.0, 3),
            "misesavg": round(avg_vm, 6),
            "relative_error_pct": round(rel_error, 3),
            "evol": round(evol, 8),
            "energy_error_sq": round(e_energy_sq, 8)
        })

    # Summary statistics
    total_elements = len(elem_data)
    total_eri_sum = sum([r["miseseri"] for r in full_elem_records])
    total_energy_error_sq = sum([r["energy_error_sq"] for r in full_elem_records])
    total_energy_error_norm = math.sqrt(max(1e-12, total_energy_error_sq))

    max_eri = max([r["miseseri"] for r in full_elem_records])
    mean_eri = total_eri_sum / float(max(1, total_elements))

    # Compute regional energy norm error shares
    regional_summary = {}
    for rname, rdata in regional_metrics.items():
        r_energy_norm = math.sqrt(max(1e-12, rdata["eri_energy_sq"]))
        r_share_energy = (rdata["eri_energy_sq"] / total_energy_error_sq) * 100.0 if total_energy_error_sq > 0 else 0.0
        r_share_scalar = (rdata["eri_sum"] / total_eri_sum) * 100.0 if total_eri_sum > 0 else 0.0
        regional_summary[rname] = {
            "element_count": int(rdata["count"]),
            "element_count_pct": round(100.0 * rdata["count"] / float(max(1, total_elements)), 3),
            "scalar_eri_sum": round(rdata["eri_sum"], 6),
            "scalar_eri_share_pct": round(r_share_scalar, 3),
            "energy_norm_error_share_pct": round(r_share_energy, 3),
            "mean_miseseri": round(rdata["eri_sum"] / float(max(1, rdata["count"])), 6),
            "mean_stress_mises": round(rdata["mises_sum"] / float(max(1, rdata["count"])), 6),
            "mean_evol": round(rdata["evol_sum"] / float(max(1, rdata["count"])), 8)
        }

    # Analysis of Visual Contour Perception vs Literal Mathematical Sizing
    colormap_bins = {
        "top_50pct_of_colorbar": 0,
        "top_20pct_of_colorbar": 0,
        "top_10pct_of_colorbar": 0,
        "top_5pct_of_colorbar": 0,
        "bottom_95pct_colorbar_dark_blue": 0
    }
    for r in full_elem_records:
        norm_e = r["miseseri"] / max(1e-6, max_eri)
        if norm_e >= 0.50:
            colormap_bins["top_50pct_of_colorbar"] += 1
        elif norm_e >= 0.20:
            colormap_bins["top_20pct_of_colorbar"] += 1
        elif norm_e >= 0.10:
            colormap_bins["top_10pct_of_colorbar"] += 1
        elif norm_e >= 0.05:
            colormap_bins["top_5pct_of_colorbar"] += 1
        else:
            colormap_bins["bottom_95pct_colorbar_dark_blue"] += 1

    colormap_summary = {
        "max_eri_mpa": round(max_eri, 6),
        "mean_eri_mpa": round(mean_eri, 6),
        "peak_to_mean_ratio": round(max_eri / max(1e-6, mean_eri), 2),
        "visual_colormap_distribution": {
            "top_50pct_bracket_elements": int(colormap_bins["top_50pct_of_colorbar"]),
            "top_50pct_bracket_pct": round(100.0 * colormap_bins["top_50pct_of_colorbar"] / float(max(1, total_elements)), 3),
            "top_10pct_to_50pct_bracket_elements": int(colormap_bins["top_10pct_of_colorbar"] + colormap_bins["top_20pct_of_colorbar"]),
            "top_10pct_to_50pct_bracket_pct": round(100.0 * (colormap_bins["top_10pct_of_colorbar"] + colormap_bins["top_20pct_of_colorbar"]) / float(max(1, total_elements)), 3),
            "top_5pct_to_10pct_bracket_elements": int(colormap_bins["top_5pct_of_colorbar"]),
            "top_5pct_to_10pct_bracket_pct": round(100.0 * colormap_bins["top_5pct_of_colorbar"] / float(max(1, total_elements)), 3),
            "bottom_5pct_dark_blue_bracket_elements": int(colormap_bins["bottom_95pct_colorbar_dark_blue"]),
            "bottom_5pct_dark_blue_bracket_pct": round(100.0 * colormap_bins["bottom_95pct_colorbar_dark_blue"] / float(max(1, total_elements)), 3)
        }
    }

    # Element Formulation analysis (CPE4 vs CPE3)
    cpe4_mean_spread = sum(cpe4_vm_spreads) / float(len(cpe4_vm_spreads)) if cpe4_vm_spreads else 0.0
    cpe4_mean_eri = sum(cpe4_eri_list) / float(len(cpe4_eri_list)) if cpe4_eri_list else 0.0
    cpe3_mean_eri = sum(cpe3_eri_list) / float(len(cpe3_eri_list)) if cpe3_eri_list else 0.0

    formulation_summary = {
        "cpe4_quads": {
            "count": int(cpe4_count),
            "mean_miseseri_mpa": round(cpe4_mean_eri, 6),
            "mean_ip_mises_spread_mpa": round(cpe4_mean_spread, 6),
            "farfield_mean_miseseri_mpa": round(sum(quad_farfield_eri) / float(max(1, len(quad_farfield_eri))), 6),
            "corridor_mean_miseseri_mpa": round(sum(quad_corridor_eri) / float(max(1, len(quad_corridor_eri))), 6)
        },
        "cpe3_triangles": {
            "count": int(cpe3_count),
            "mean_miseseri_mpa": round(cpe3_mean_eri, 6),
            "note": "1-point integration: constant stress per element; SPR error driven purely by inter-element nodal jump"
        }
    }

    audit_results = {
        "audit_id": "GATE6B-STAGE6-OUTPUT-POSITION-AND-RECOVERY-AUDIT-20261003",
        "odb_path": str(odb_path),
        "step_name": str(step_name),
        "frame_index": int(last_frame.frameId),
        "total_elements": int(total_elements),
        "cpe4_elements": int(cpe4_count),
        "cpe3_elements": int(cpe3_count),
        "total_energy_error_norm": round(total_energy_error_norm, 6),
        "field_outputs": field_summary,
        "regional_summary": regional_summary,
        "colormap_visual_vs_sizing_analysis": colormap_summary,
        "element_formulation_summary": formulation_summary,
        "elements": full_elem_records
    }

    odb.close()

    with open(out_json_path, "w") as f:
        json.dump(audit_results, f, indent=2, default=serialize_helper)

    print("Stage 6 Audit Complete! Saved to: " + str(out_json_path))
    return audit_results


if __name__ == "__main__":
    odb_p = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906/PK_M1_JOB1_CONTINUUM_MATCHED_2906.odb"
    out_j = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906/STAGE6_OUTPUT_RECOVERY_AUDIT.json"
    audit_odb_fields(odb_p, out_j)
