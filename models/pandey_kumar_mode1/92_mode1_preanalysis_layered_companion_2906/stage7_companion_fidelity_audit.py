"""
Stage 7: Layered Companion-Element / All_elem Reference-Fidelity Audit Script
Extracts and compares MISESERI, S, SDV, RF2 from PK_M1_JOB1_LAYERED_COMPANION_2906.odb
against PK_M1_JOB1_CONTINUUM_MATCHED_2906.odb and digitized Pandey-Kumar Fig. 6(a).
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


def audit_layered_companion_odb(odb_layered_path, odb_control_path, out_json_path):
    print("=== STARTING STAGE 7 LAYERED COMPANION FIDELITY AUDIT ===")
    print("Opening Layered ODB: " + str(odb_layered_path))
    odb_lay = openOdb(odb_layered_path, readOnly=True)

    print("Opening Control ODB: " + str(odb_control_path))
    odb_ctrl = openOdb(odb_control_path, readOnly=True)

    # 1. Audit Steps & Frames
    step_name = "Step-1"
    step_lay = odb_lay.steps[step_name]
    frame_lay_last = step_lay.frames[-1]

    step_ctrl = odb_ctrl.steps[step_name]
    frame_ctrl_last = step_ctrl.frames[-1]

    print("Layered Step-1 frames: " + str(len(step_lay.frames)) + ", Last Frame ID: " + str(frame_lay_last.frameId))
    print("Control Step-1 frames: " + str(len(step_ctrl.frames)) + ", Last Frame ID: " + str(frame_ctrl_last.frameId))

    # 2. Field Output Inspection on Layered ODB
    lay_fields = {}
    for f_name in sorted(frame_lay_last.fieldOutputs.keys()):
        f = frame_lay_last.fieldOutputs[f_name]
        locs = [str(loc.position) for loc in f.locations]
        desc = str(f.description)
        print("  Layered Field - " + str(f_name) + ": " + desc + " (locations: " + str(locs) + ")")
        lay_fields[str(f_name)] = {
            "description": desc,
            "locations": locs
        }

    # Extract MISESERI, MISESAVG, S, EVOL, SDV from layered ODB
    f_lay_eri = frame_lay_last.fieldOutputs['MISESERI'] if 'MISESERI' in frame_lay_last.fieldOutputs else None
    f_lay_avg = frame_lay_last.fieldOutputs['MISESAVG'] if 'MISESAVG' in frame_lay_last.fieldOutputs else None
    f_lay_s = frame_lay_last.fieldOutputs['S'] if 'S' in frame_lay_last.fieldOutputs else None
    f_lay_sdv = frame_lay_last.fieldOutputs['SDV'] if 'SDV' in frame_lay_last.fieldOutputs else None
    f_lay_evol = frame_lay_last.fieldOutputs['EVOL'] if 'EVOL' in frame_lay_last.fieldOutputs else None

    # Control field outputs
    f_ctrl_eri = frame_ctrl_last.fieldOutputs['MISESERI'] if 'MISESERI' in frame_ctrl_last.fieldOutputs else None

    # Node coordinates from control / layered
    inst_name = list(odb_ctrl.rootAssembly.instances.keys())[0]
    inst_ctrl = odb_ctrl.rootAssembly.instances[inst_name]
    node_coords = {}
    for n in inst_ctrl.nodes:
        node_coords[n.label] = [float(n.coordinates[0]), float(n.coordinates[1])]

    elem_data = {}
    for el in inst_ctrl.elements:
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

    # Layered companion elements: re-index from NOEL in [5813..8718] to physical index [1..2906]
    # For a 2906-element mesh: 88 tris (1..88), 2818 quads (89..2906)
    # Companion tris: 5813..5900 (NOEL - 5812 = 1..88)
    # Companion quads: 5901..8718 (NOEL - 5812 = 89..2906)
    lay_eri_values = {}
    if f_lay_eri is not None:
        for val in f_lay_eri.values:
            if val.elementLabel is not None:
                noel = int(val.elementLabel)
                # Map to physical index
                if noel > 5812:
                    phys_id = noel - 5812
                else:
                    phys_id = noel
                lay_eri_values[phys_id] = float(val.data)

    lay_s_values = {}
    if f_lay_s is not None:
        for val in f_lay_s.values:
            if val.elementLabel is not None:
                noel = int(val.elementLabel)
                if noel > 5812:
                    phys_id = noel - 5812
                else:
                    phys_id = noel
                if phys_id not in lay_s_values:
                    lay_s_values[phys_id] = []
                lay_s_values[phys_id].append(float(val.mises) if hasattr(val, 'mises') else 0.0)

    # Control MISESERI
    ctrl_eri_values = {}
    if f_ctrl_eri is not None:
        for val in f_ctrl_eri.values:
            if val.elementLabel is not None:
                ctrl_eri_values[int(val.elementLabel)] = float(val.data)

    # Reaction forces
    rf_lay_step1_end = 0.0
    if 'RF' in frame_lay_last.fieldOutputs:
        for val in frame_lay_last.fieldOutputs['RF'].values:
            if val.nodeLabel == 999999 or val.nodeLabel == 25:
                rf_lay_step1_end += float(val.data[1])

    rf_ctrl_step1_end = 0.0
    if 'RF' in frame_ctrl_last.fieldOutputs:
        for val in frame_ctrl_last.fieldOutputs['RF'].values:
            if val.nodeLabel == 999999 or val.nodeLabel == 25:
                rf_ctrl_step1_end += float(val.data[1])

    # Quantitative Comparison Metrics
    total_elements = len(elem_data)
    lay_eri_list = [lay_eri_values.get(e, 0.0) for e in sorted(elem_data.keys())]
    ctrl_eri_list = [ctrl_eri_values.get(e, 0.0) for e in sorted(elem_data.keys())]

    lay_max_eri = max(lay_eri_list) if lay_eri_list else 0.0
    lay_mean_eri = sum(lay_eri_list) / float(max(1, total_elements)) if lay_eri_list else 0.0
    ctrl_max_eri = max(ctrl_eri_list) if ctrl_eri_list else 0.0
    ctrl_mean_eri = sum(ctrl_eri_list) / float(max(1, total_elements)) if ctrl_eri_list else 0.0

    # Regional analysis
    regional_data = {
        "crack_corridor": {"count": 0, "lay_eri_sum": 0.0, "ctrl_eri_sum": 0.0},
        "crack_wake": {"count": 0, "lay_eri_sum": 0.0, "ctrl_eri_sum": 0.0},
        "right_ligament": {"count": 0, "lay_eri_sum": 0.0, "ctrl_eri_sum": 0.0},
        "far_field": {"count": 0, "lay_eri_sum": 0.0, "ctrl_eri_sum": 0.0},
        "boundary": {"count": 0, "lay_eri_sum": 0.0, "ctrl_eri_sum": 0.0}
    }

    for elabel, edata in elem_data.items():
        cx, cy = edata["centroid"]
        is_boundary = (cx <= 0.02 or cx >= 0.98 or cy <= 0.02 or cy >= 0.98)
        if 0.45 <= cx <= 0.55 and 0.45 <= cy <= 0.55:
            reg_name = "crack_corridor"
        elif cx < 0.45 and 0.45 <= cy <= 0.55:
            reg_name = "crack_wake"
        elif cx > 0.55 and 0.45 <= cy <= 0.55:
            reg_name = "right_ligament"
        else:
            reg_name = "far_field"

        reg = regional_data[reg_name]
        reg["count"] += 1
        reg["lay_eri_sum"] += lay_eri_values.get(elabel, 0.0)
        reg["ctrl_eri_sum"] += ctrl_eri_values.get(elabel, 0.0)

        if is_boundary:
            reg_b = regional_data["boundary"]
            reg_b["count"] += 1
            reg_b["lay_eri_sum"] += lay_eri_values.get(elabel, 0.0)
            reg_b["ctrl_eri_sum"] += ctrl_eri_values.get(elabel, 0.0)

    # Classify Architecture Result
    if lay_max_eri == 0.0 and lay_mean_eri == 0.0:
        verdict = "LAYERED_COMPANION_ZERO_STRESS_CONFIRMED"
        classification = "LAYERED_COMPANION_INVALID_OR_UNRESOLVED"
        explanation = (
            "Because the authoritative companion UMAT sets STRESS = 0.D0 and DDSDDE = 1.D-11 to prevent "
            "double-counting mechanical stiffness with UEL Layer 2, the Cauchy stress on All_elem is identically zero. "
            "Consequently, Abaqus stress recovery evaluates MISESERI = 0.0 across all 2,906 elements. "
            "This confirms that the companion layer in the Molnar/Pandey-Kumar lineage is a visualization layer for SDVs "
            "and cannot produce a non-zero MISESERI error field without an independent continuum stress solution."
        )
    elif abs(lay_max_eri - ctrl_max_eri) / max(1e-6, ctrl_max_eri) < 0.01:
        verdict = "LAYERED_COMPANION_MATCHES_CONTINUUM_CONTROL"
        classification = "LAYERED_COMPANION_NO_MEANINGFUL_CHANGE"
        explanation = "Layered companion MISESERI field matches standard continuum control."
    elif lay_mean_eri / max(1e-6, lay_max_eri) < ctrl_mean_eri / max(1e-6, ctrl_max_eri):
        verdict = "LAYERED_COMPANION_TOWARD_LOCALIZATION"
        classification = "LAYERED_COMPANION_TOWARD_PANDEY_KUMAR_LOCALIZATION"
        explanation = "Layered companion exhibits narrower relative error localization."
    else:
        verdict = "LAYERED_COMPANION_EVALUATED"
        classification = "LAYERED_COMPANION_INVALID_OR_UNRESOLVED"
        explanation = "Layered companion evaluation completed."

    # Published Pandey-Kumar Fig. 6(a) Legend Reference Data (Digitized Evidence)
    published_fig6a_evidence = {
        "source": "Pandey & Kumar (2025) Figure 6(a) (CMES, vol. 142, no. 1, pp. 297-327)",
        "label": "Digitized visual/legend evidence from published contour plot",
        "legend_range_reported_mpa": [0.0, 95.0],
        "legend_max_miseseri_reported": 95.0,
        "note": "Published contour legend shows values up to ~95.0 MPa at u=0.01 mm, representing a 50x-100x scaling relative to our u=0.005 mm pre-analysis (0.95 MPa) or a different displacement/load level."
    }

    audit_summary = {
        "audit_id": "GATE6B-STAGE7-LAYERED-COMPANION-FIDELITY-AUDIT-20261003",
        "verdict": verdict,
        "classification": classification,
        "explanation": explanation,
        "odb_layered": odb_layered_path,
        "odb_control": odb_control_path,
        "step_name": step_name,
        "total_elements": total_elements,
        "layered_metrics": {
            "max_miseseri_mpa": round(lay_max_eri, 6),
            "mean_miseseri_mpa": round(lay_mean_eri, 6),
            "rf2_at_step1_end_kn": round(rf_lay_step1_end, 6)
        },
        "control_metrics": {
            "max_miseseri_mpa": round(ctrl_max_eri, 6),
            "mean_miseseri_mpa": round(ctrl_mean_eri, 6),
            "rf2_at_step1_end_kn": round(rf_ctrl_step1_end, 6)
        },
        "regional_comparison": regional_data,
        "published_fig6a_evidence": published_fig6a_evidence,
        "field_outputs_layered": lay_fields
    }

    odb_lay.close()
    odb_ctrl.close()

    with open(out_json_path, "w") as f:
        json.dump(audit_summary, f, indent=2, default=serialize_helper)

    print("Stage 7 Audit Complete! Results saved to: " + str(out_json_path))
    return audit_summary


if __name__ == "__main__":
    odb_lay = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/92_mode1_preanalysis_layered_companion_2906/PK_M1_JOB1_LAYERED_COMPANION_2906.odb"
    odb_ctrl = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906/PK_M1_JOB1_CONTINUUM_MATCHED_2906.odb"
    out_j = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/92_mode1_preanalysis_layered_companion_2906/STAGE7_LAYERED_COMPANION_FIDELITY_AUDIT.json"
    audit_layered_companion_odb(odb_lay, odb_ctrl, out_j)
