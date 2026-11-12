"""
F1720 Stage 2 Diagnostic Patch Analysis Script
Extracts and compares authentic UEL stresses, UMAT stresses, reaction forces,
mechanical neutrality, call sequence, and native MISESERI across:
  - Standalone UEL (Reference)
  - Config A (Zero-stress baseline)
  - Config B (Dummy-scaled direct coupling)
  - Config C (Unscaled physical stress)
  - Config B (4-element patch)
"""

import sys
import os
import json
import math
from odbAccess import openOdb

def analyze_model(odb_path, model_name, is_standalone=False):
    if not os.path.exists(odb_path):
        return {"error": "File not found: " + odb_path}

    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps['Step-1']
    last_frame = step.frames[-1]

    # Reaction force on top nodes
    total_rf_y = 0.0
    rf_field = last_frame.fieldOutputs['RF'] if 'RF' in last_frame.fieldOutputs.keys() else None
    u_field = last_frame.fieldOutputs['U'] if 'U' in last_frame.fieldOutputs.keys() else None

    # Top nodes
    top_nodes = [3, 4] if '4ELEM' not in model_name else [7, 8, 9]
    top_rf_y = {}
    top_u_y = {}

    if rf_field:
        for val in rf_field.values:
            if val.nodeLabel in top_nodes:
                top_rf_y[val.nodeLabel] = val.data[1]
                total_rf_y += val.data[1]

    if u_field:
        for val in u_field.values:
            if val.nodeLabel in top_nodes:
                top_u_y[val.nodeLabel] = val.data[1]

    # Stresses and SDVs
    s_field = last_frame.fieldOutputs['S'] if 'S' in last_frame.fieldOutputs.keys() else None
    sdv_field = last_frame.fieldOutputs['SDV'] if 'SDV' in last_frame.fieldOutputs.keys() else None
    miseseri_field = last_frame.fieldOutputs['MISESERI'] if 'MISESERI' in last_frame.fieldOutputs.keys() else None
    misesavg_field = last_frame.fieldOutputs['MISESAVG'] if 'MISESAVG' in last_frame.fieldOutputs.keys() else None

    elem_stresses = []
    if s_field:
        for val in s_field.values:
            # val.data: [S11, S22, S33, S12] for plane strain
            s11, s22, s33, s12 = val.data[0], val.data[1], val.data[2], val.data[3]
            mises = val.mises
            elem_stresses.append({
                "elem": val.elementLabel,
                "ip": val.integrationPoint,
                "s11": s11,
                "s22": s22,
                "s33": s33,
                "s12": s12,
                "mises": mises
            })

    elem_sdvs = []
    # In Abaqus ODB, SDVs are stored as individual field outputs SDV1, SDV2, ..., SDV20
    sdv_keys = [k for k in last_frame.fieldOutputs.keys() if k.startswith('SDV')]
    if sdv_keys:
        sdv_fields = {k: last_frame.fieldOutputs[k] for k in sdv_keys}
        # Get values from SDV1 to get element/IP structure
        base_field = sdv_fields.get('SDV1', None)
        if base_field:
            for i, val in enumerate(base_field.values):
                el_label = val.elementLabel
                ip_label = val.integrationPoint
                d_val   = sdv_fields['SDV1'].values[i].data if 'SDV1' in sdv_fields else 0.0
                h_val   = sdv_fields['SDV2'].values[i].data if 'SDV2' in sdv_fields else 0.0
                s11_u   = sdv_fields['SDV3'].values[i].data if 'SDV3' in sdv_fields else 0.0
                s22_u   = sdv_fields['SDV4'].values[i].data if 'SDV4' in sdv_fields else 0.0
                s33_u   = sdv_fields['SDV5'].values[i].data if 'SDV5' in sdv_fields else 0.0
                s12_u   = sdv_fields['SDV6'].values[i].data if 'SDV6' in sdv_fields else 0.0
                svm_u   = sdv_fields['SDV7'].values[i].data if 'SDV7' in sdv_fields else 0.0
                elem_sdvs.append({
                    "elem": el_label,
                    "ip": ip_label,
                    "d": d_val,
                    "h": h_val,
                    "s11_uel": s11_u,
                    "s22_uel": s22_u,
                    "s33_uel": s33_u,
                    "s12_uel": s12_u,
                    "svm_uel": svm_u
                })

    miseseri_vals = []
    if miseseri_field:
        for val in miseseri_field.values:
            miseseri_vals.append({
                "elem": val.elementLabel,
                "data": val.data
            })

    misesavg_vals = []
    if misesavg_field:
        for val in misesavg_field.values:
            misesavg_vals.append({
                "elem": val.elementLabel,
                "data": val.data
            })

    num_frames = len(step.frames)
    odb.close()

    return {
        "model_name": model_name,
        "num_frames": num_frames,
        "total_rf_y": total_rf_y,
        "top_rf_y": top_rf_y,
        "top_u_y": top_u_y,
        "elem_stresses": elem_stresses,
        "elem_sdvs": elem_sdvs,
        "has_miseseri": miseseri_field is not None,
        "miseseri_vals": miseseri_vals,
        "has_misesavg": misesavg_field is not None,
        "misesavg_vals": misesavg_vals
    }


def main():
    patch_dir = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\212_f1720_diagnostic_patch"

    models = [
        ("PK_F1720_DIAG_1ELEM_STANDALONE", "Standalone UEL (No Overlay)"),
        ("PK_F1720_DIAG_1ELEM_A", "Config A (Zero-Stress Baseline)"),
        ("PK_F1720_DIAG_1ELEM_B", "Config B (Dummy-Scaled Coupling)"),
        ("PK_F1720_DIAG_1ELEM_C", "Config C (Unscaled Stress, Dummy Stiffness)"),
        ("PK_F1720_DIAG_4ELEM_B", "Config B (4-Element Patch)")
    ]

    results = {}
    print("=" * 80)
    print("F1720 STAGE 2 DIAGNOSTIC PATCH RESULTS EXTRACTION")
    print("=" * 80)

    for job_name, desc in models:
        odb_path = os.path.join(patch_dir, job_name + ".odb")
        res = analyze_model(odb_path, desc, is_standalone=('STANDALONE' in job_name))
        results[job_name] = res
        print("\n--- %s (%s) ---" % (job_name, desc))
        if "error" in res:
            print("  ERROR: %s" % res["error"])
            continue

        print("  Frames: %d" % res["num_frames"])
        print("  Total Reaction Force RF_y: %.8e kN" % res["total_rf_y"])
        for n, rf in res["top_rf_y"].items():
            print("    Node %d: RF_y = %.8e kN, U_y = %.6f mm" % (n, rf, res["top_u_y"].get(n, 0.0)))

        if res["elem_stresses"]:
            print("  Element Stresses on Layer 3 (UMAT):")
            for s in res["elem_stresses"]:
                print("    Elem %d IP %d: S11=%.4e, S22=%.4e, S33=%.4e, S12=%.4e, Mises=%.4e" %
                      (s["elem"], s["ip"], s["s11"], s["s22"], s["s33"], s["s12"], s["mises"]))

        if res["elem_sdvs"]:
            print("  Retrieved UEL Stresses from SDV (STATEV 3..7):")
            for sdv in res["elem_sdvs"][:4]:
                print("    Elem %d IP %d: S11_UEL=%.4f, S22_UEL=%.4f, S33_UEL=%.4f, S12_UEL=%.4f, Mises=%.4f (MPa)" %
                      (sdv["elem"], sdv["ip"], sdv["s11_uel"]*1e3, sdv["s22_uel"]*1e3, sdv["s33_uel"]*1e3, sdv["s12_uel"]*1e3, sdv["svm_uel"]*1e3))

        print("  Native MISESERI present: %s (Count: %d)" % (res["has_miseseri"], len(res["miseseri_vals"])))
        if res["miseseri_vals"]:
            for m in res["miseseri_vals"]:
                print("    Elem %d MISESERI = %s" % (m["elem"], str(m["data"])))

        print("  Native MISESAVG present: %s (Count: %d)" % (res["has_misesavg"], len(res["misesavg_vals"])))
        if res["misesavg_vals"]:
            for m in res["misesavg_vals"]:
                print("    Elem %d MISESAVG = %s" % (m["elem"], str(m["data"])))

    # Mechanical Neutrality Comparison
    rf_standalone = results.get("PK_F1720_DIAG_1ELEM_STANDALONE", {}).get("total_rf_y", None)
    if rf_standalone:
        print("\n" + "=" * 80)
        print("MECHANICAL NEUTRALITY & PERTURBATION AUDIT (vs Standalone UEL)")
        print("=" * 80)
        print("Standalone Reference RF_y = %.10e kN" % rf_standalone)

        # Analytical solution
        # E0 = 210 kN/mm^2, nu = 0.3, eps_yy = 0.001
        # In plane strain (eps_zz = 0, sigma_xx = 0):
        # sigma_yy = E0 / (1 - nu^2) * eps_yy = 210 / (1 - 0.09) * 0.001 = 0.230769230769 kN/mm^2
        # Width = 1.0 mm, Thickness = 1.0 mm => Area = 1.0 mm^2
        # Analytical RF_y = sigma_yy * Area = 0.230769230769 kN
        rf_analytical = (210.0 / (1.0 - 0.3**2)) * 0.001 * 1.0 * 1.0
        print("Analytical Plane Strain RF_y = %.10e kN" % rf_analytical)
        diff_analytical = abs(rf_standalone - rf_analytical) / rf_analytical * 100.0
        print("Standalone vs Analytical: Delta = %.6e%%" % diff_analytical)

        for conf in ["PK_F1720_DIAG_1ELEM_A", "PK_F1720_DIAG_1ELEM_B", "PK_F1720_DIAG_1ELEM_C"]:
            rf_conf = results.get(conf, {}).get("total_rf_y", 0.0)
            delta_rf = rf_conf - rf_standalone
            rel_delta_pct = (delta_rf / rf_standalone) * 100.0
            print("\n  %s:" % conf)
            print("    RF_y = %.10e kN" % rf_conf)
            print("    Delta RF_y = %+.10e kN" % delta_rf)
            print("    Relative Perturbation = %+.8e%%" % rel_delta_pct)

    # Helper to convert float32 to float for json
    def convert_floats(obj):
        if isinstance(obj, bool):
            return obj
        elif isinstance(obj, dict):
            return {k: convert_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_floats(i) for i in obj]
        elif hasattr(obj, '__float__'):
            return float(obj)
        else:
            return obj

    # Dump results JSON
    out_json = os.path.join(r"D:\Master thesis\Adaptive remeshing\results\validation", "f1720_diagnostic_patch_results.json")
    with open(out_json, "w") as f:
        json.dump(convert_floats(results), f, indent=2)
    print("\nResults saved to: %s" % out_json)

if __name__ == "__main__":
    main()
