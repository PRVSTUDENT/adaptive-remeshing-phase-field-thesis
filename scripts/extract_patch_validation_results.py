"""
scripts/extract_patch_validation_results.py

Runs under 'abaqus python' to extract exact field outputs from all 15 minimal patch ODBs:
- RF2 sum on top nodes (Node 3, 4)
- U2 on top nodes (Node 3, 4)
- S (S11, S22, S12, Mises) at integration points
- MISESERI (max, min, mean, availability)
- MISESAVG (max, min, mean, availability)

Outputs JSON to results/validation/f1698_minimal_patch_validation.json
"""

import os
import sys
import json
from odbAccess import openOdb

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
WORK_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "198_pk_sec43_coupled_validation")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")

if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

# Analytical reference values
E = 210000.0   # MPa
NU = 0.30
K_RES = 1.0e-7
C11 = E * (1.0 - NU) / ((1.0 + NU) * (1.0 - 2.0 * NU))   # 282692.3077 MPa
C12 = E * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))           # 121153.8462 MPa

STATES = {
    "intact": {"d": 0.0, "uy": 0.001},
    "partially_damaged": {"d": 0.50, "uy": 0.005},
    "strongly_damaged": {"d": 0.95, "uy": 0.010}
}

for name, s in STATES.items():
    d = s["d"]
    uy = s["uy"]
    g_d = (1.0 - d)**2 + K_RES
    s["g_d"] = g_d
    s["analytical_sigma_yy"] = g_d * C11 * uy
    s["analytical_sigma_xx"] = g_d * C12 * uy
    s["analytical_rf_y"] = g_d * C11 * uy * 1.0   # Area = 1.0 mm^2

test_cases = [
    ("PATCH_A_INTACT", "A", "intact", 0.0, 0.001, None),
    ("PATCH_A_PARTIAL", "A", "partially_damaged", 0.50, 0.005, None),
    ("PATCH_A_STRONG", "A", "strongly_damaged", 0.95, 0.010, None),

    ("PATCH_B1_INTACT", "B1", "intact", 0.0, 0.001, 1),
    ("PATCH_B1_PARTIAL", "B1", "partially_damaged", 0.50, 0.005, 1),
    ("PATCH_B1_STRONG", "B1", "strongly_damaged", 0.95, 0.010, 1),

    ("PATCH_B2_INTACT", "B2", "intact", 0.0, 0.001, 2),
    ("PATCH_B2_PARTIAL", "B2", "partially_damaged", 0.50, 0.005, 2),
    ("PATCH_B2_STRONG", "B2", "strongly_damaged", 0.95, 0.010, 2),

    ("PATCH_B3_INTACT", "B3", "intact", 0.0, 0.001, 3),
    ("PATCH_B3_PARTIAL", "B3", "partially_damaged", 0.50, 0.005, 3),
    ("PATCH_B3_STRONG", "B3", "strongly_damaged", 0.95, 0.010, 3),

    ("PATCH_C_INTACT", "C", "intact", 0.0, 0.001, None),
    ("PATCH_C_PARTIAL", "C", "partially_damaged", 0.50, 0.005, None),
    ("PATCH_C_STRONG", "C", "strongly_damaged", 0.95, 0.010, None),
]

results = {
    "analytical_references": STATES,
    "models": {}
}

for job_name, mtype, sname, d, uy, mode in test_cases:
    odb_path = os.path.join(WORK_DIR, job_name + ".odb")
    msg_path = os.path.join(WORK_DIR, job_name + ".msg")
    sta_path = os.path.join(WORK_DIR, job_name + ".sta")

    item_data = {
        "job_name": job_name,
        "model_type": mtype,
        "state": sname,
        "d_val": d,
        "uy_val": uy,
        "mode": mode,
        "exit_code": 1,
        "cutbacks": 0,
        "iterations": 0,
        "rf_y_total": 0.0,
        "rf_node3": 0.0,
        "rf_node4": 0.0,
        "u_node3": 0.0,
        "u_node4": 0.0,
        "sigma_yy": 0.0,
        "sigma_xx": 0.0,
        "sigma_mises": 0.0,
        "miseseri_available": False,
        "miseseri_max": 0.0,
        "misesavg_available": False,
        "misesavg_max": 0.0
    }

    # Inspect sta for exit status
    if os.path.exists(sta_path):
        f = open(sta_path, "r")
        content = f.read()
        f.close()
        if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in content:
            item_data["exit_code"] = 0

    # Inspect msg for cutbacks and iterations
    if os.path.exists(msg_path):
        f = open(msg_path, "r")
        lines = f.readlines()
        f.close()
        for line in lines:
            if "ITERATION SUMMARY" in line:
                item_data["iterations"] += 1
            if "CUTBACK" in line:
                item_data["cutbacks"] += 1

    if os.path.exists(odb_path):
        try:
            odb = openOdb(odb_path, readOnly=True)
            last_step = odb.steps[odb.steps.keys()[-1]]
            last_frame = last_step.frames[-1]

            # Extract RF on top nodes
            if "RF" in last_frame.fieldOutputs:
                rf_fo = last_frame.fieldOutputs["RF"]
                for val in rf_fo.values:
                    if val.nodeLabel == 3:
                        item_data["rf_node3"] = float(val.data[1])
                    elif val.nodeLabel == 4:
                        item_data["rf_node4"] = float(val.data[1])
                item_data["rf_y_total"] = item_data["rf_node3"] + item_data["rf_node4"]

            # Extract U on top nodes
            if "U" in last_frame.fieldOutputs:
                u_fo = last_frame.fieldOutputs["U"]
                for val in u_fo.values:
                    if val.nodeLabel == 3:
                        item_data["u_node3"] = float(val.data[1])
                    elif val.nodeLabel == 4:
                        item_data["u_node4"] = float(val.data[1])

            # Extract Stress S
            if "S" in last_frame.fieldOutputs:
                s_fo = last_frame.fieldOutputs["S"]
                s_yy_list = []
                s_xx_list = []
                s_mises_list = []
                for val in s_fo.values:
                    s_xx_list.append(float(val.data[0]))
                    s_yy_list.append(float(val.data[1]))
                    s_mises_list.append(float(val.mises))
                if len(s_yy_list) > 0:
                    item_data["sigma_xx"] = sum(s_xx_list) / len(s_xx_list)
                    item_data["sigma_yy"] = sum(s_yy_list) / len(s_yy_list)
                    item_data["sigma_mises"] = sum(s_mises_list) / len(s_mises_list)

            # Extract MISESERI
            if "MISESERI" in last_frame.fieldOutputs:
                eri_fo = last_frame.fieldOutputs["MISESERI"]
                eri_vals = [float(v.data) for v in eri_fo.values if v.data is not None]
                if len(eri_vals) > 0:
                    item_data["miseseri_available"] = True
                    item_data["miseseri_max"] = max(eri_vals)

            # Extract MISESAVG
            if "MISESAVG" in last_frame.fieldOutputs:
                avg_fo = last_frame.fieldOutputs["MISESAVG"]
                avg_vals = [float(v.data) for v in avg_fo.values if v.data is not None]
                if len(avg_vals) > 0:
                    item_data["misesavg_available"] = True
                    item_data["misesavg_max"] = max(avg_vals)

            odb.close()
        except Exception as e:
            item_data["extraction_error"] = str(e)

    results["models"][job_name] = item_data

out_json_path = os.path.join(RESULTS_DIR, "f1698_minimal_patch_validation.json")
f = open(out_json_path, "w")
json.dump(results, f, indent=2)
f.close()
print("Wrote results to " + out_json_path)
