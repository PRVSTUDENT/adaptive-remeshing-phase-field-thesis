# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_and_solve_f1719_coarse_recovery.py
============================================================
Task F1719 Phase 5:
Continuous Constitutive Same-State Stress Recovery for Five-Hole Plate.

Extracts authentic coarse phase-field simulation fields from PK_F1719_COARSE_PFM.odb
(zero fine-mesh data leakage, zero predefined crack corridors) across 5 objective states:
  - State 0: Step 1, inc 30 (uy = 0.00300 mm, undamaged elastic, d_max = 0.0498)
  - State 1: Step 1, inc 35 (uy = 0.00350 mm, damage initiation, d_max = 0.0696)
  - State 2: Step 1, inc 55 (uy = 0.004965 mm, early localization, d_max = 0.1595)
  - State 3: Step 2, inc 240 (uy = 0.006200 mm, advanced softening, d_max = 0.3359)
  - State 4: Step 2, inc 356 (uy = 0.006451 mm, peak softening / crack bridging, d_max = 0.5252)

Constructs continuum recovery models (CPE4/CPE3) with 20 degraded elasticity bins:
  - Physical scale: E0 = 210,000 MPa (210 kN/mm^2), nu = 0.30
  - Companion dummy scale: E_dummy = 1.0e-11 kN/mm^2 (1.0e-8 MPa) for Fig 25(a) scale reproduction
Solves all jobs locally with Abaqus/Standard, extracts MISESERI and MISESAVG via SPR,
and saves results to results/validation/f1719_recovered_miseseri_multistate.json.
"""

from __future__ import print_function
import os
import sys
import json
import math
import subprocess

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
COARSE_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "PK_F1714_JOB1_COARSE.inp")
COARSE_ODB = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "210_f1719_five_hole_coarse_pfm", "PK_F1719_COARSE_PFM.odb")
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "211_f1719_coarse_recovery")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


def parse_coarse_inp(inp_path):
    nodes = {}
    quads = []
    tris = []
    in_node = False
    in_elem = False
    elem_type = ""

    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE"):
                    in_node = True
                    in_elem = False
                elif u.startswith("*ELEMENT"):
                    in_node = False
                    in_elem = True
                    elem_type = "CPE4" if "CPE4" in u else ("CPE3" if "CPE3" in u else "")
                else:
                    in_node = False
                    in_elem = False
                continue

            if in_node:
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 3 and p[0].isdigit():
                    nodes[int(p[0])] = (float(p[1]), float(p[2]))
            elif in_elem:
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 4 and p[0].isdigit():
                    eid = int(p[0])
                    conn = [int(x) for x in p[1:]]
                    if len(conn) == 4 or elem_type == "CPE4":
                        quads.append((eid, conn))
                    elif len(conn) == 3 or elem_type == "CPE3":
                        tris.append((eid, conn))

    return nodes, quads, tris


def compute_centroids(nodes, elements):
    centroids = {}
    for eid, conn in elements:
        pts = [nodes[n] for n in conn]
        cx = sum(pt[0] for pt in pts) / float(len(pts))
        cy = sum(pt[1] for pt in pts) / float(len(pts))
        centroids[eid] = (cx, cy)
    return centroids


def extract_coarse_states_from_odb():
    """
    Extracts nodal displacements and element damage (SDV14) from PK_F1719_COARSE_PFM.odb
    for each target state.
    """
    extract_script = os.path.join(OUT_DIR, "temp_extract_states.py")
    out_json = os.path.join(OUT_DIR, "temp_coarse_states.json")

    script_content = """
from __future__ import print_function
import sys
import json
from odbAccess import openOdb

odb_path = r"{odb_path}"
out_json = r"{out_json}"

odb = openOdb(odb_path, readOnly=True)
inst = odb.rootAssembly.instances['PART-1-1']

states_def = [
    {{"name": "STATE0", "step": "Step-1", "frame_idx": 6, "desc": "Undamaged Elastic (uy=0.00300 mm)"}},
    {{"name": "STATE1", "step": "Step-1", "frame_idx": 7, "desc": "Damage Initiation (uy=0.00350 mm)"}},
    {{"name": "STATE2", "step": "Step-1", "frame_idx": 11, "desc": "Early Localization (uy=0.004965 mm)"}},
    {{"name": "STATE3", "step": "Step-2", "frame_idx": 120, "desc": "Advanced Softening (uy=0.006200 mm)"}},
    {{"name": "STATE4", "step": "Step-2", "frame_idx": 178, "desc": "Peak Softening / Bridging (uy=0.006451 mm)"}}
]

results = {{}}

for s_info in states_def:
    sname = s_info["step"]
    f_idx = s_info["frame_idx"]
    state_name = s_info["name"]

    step = odb.steps[sname]
    frame = step.frames[f_idx]

    fkeys = frame.fieldOutputs.keys()
    u_field = frame.fieldOutputs['U'] if 'U' in fkeys else None
    sdv14_field = frame.fieldOutputs['SDV14'] if 'SDV14' in fkeys else None

    # Get RP displacement (node 2845)
    rp_uy = 0.0
    nodal_u = {{}}
    if u_field is not None:
        for val in u_field.values:
            nid = val.nodeLabel
            if nid <= 2844:
                nodal_u[nid] = (float(val.data[0]), float(val.data[1]))
            elif nid == 2845:
                rp_uy = float(val.data[1])

    # Get element damage (SDV14 on companion elements 5495..8241)
    # Physical element ID = companion element label - 5494
    elem_damage = {{}}
    if sdv14_field is not None:
        for val in sdv14_field.values:
            c_eid = val.elementLabel
            if 5495 <= c_eid <= 8241:
                p_eid = c_eid - 5494
                # If multiple integration points, take average
                d_val = float(val.data)
                if p_eid not in elem_damage:
                    elem_damage[p_eid] = []
                elem_damage[p_eid].append(d_val)

    elem_damage_avg = {{}}
    for p_eid, vals in elem_damage.items():
        elem_damage_avg[p_eid] = sum(vals) / float(len(vals))

    d_max = max(elem_damage_avg.values()) if elem_damage_avg else 0.0
    d_mean = sum(elem_damage_avg.values()) / float(len(elem_damage_avg)) if elem_damage_avg else 0.0

    results[state_name] = {{
        "name": state_name,
        "step": sname,
        "frame_idx": f_idx,
        "desc": s_info["desc"],
        "rp_uy": rp_uy,
        "d_max": d_max,
        "d_mean": d_mean,
        "nodal_u": nodal_u,
        "elem_damage": elem_damage_avg
    }}
    print("Extracted %s: uy=%.6f mm, d_max=%.4f, d_mean=%.4f" % (state_name, rp_uy, d_max, d_mean))

odb.close()

with open(out_json, "w") as f:
    json.dump(results, f)
print("Saved extracted states to %s" % out_json)
""".format(odb_path=COARSE_ODB.replace("\\", "\\\\"), out_json=out_json.replace("\\", "\\\\"))

    with open(extract_script, "w") as f:
        f.write(script_content)

    print("Running ODB state extraction via Abaqus Python...")
    cmd = 'abaqus python "%s"' % extract_script
    p = subprocess.run(cmd, cwd=OUT_DIR, shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        print("Error extracting states:\n", p.stderr)
        raise RuntimeError("Failed to extract states from ODB")
    print(p.stdout)

    with open(out_json, "r") as f:
        states_data = json.load(f)

    # Convert keys back to int
    for sname, sdata in states_data.items():
        sdata["nodal_u"] = {int(k): v for k, v in sdata["nodal_u"].items()}
        sdata["elem_damage"] = {int(k): v for k, v in sdata["elem_damage"].items()}

    return states_data


def build_recovery_deck(out_path, nodes, quads, tris, elem_damage, E0_val=210000.0, nu_val=0.30, k_res=1e-7, uy_val=0.0050, title="F1719 Recovery"):
    all_elements = quads + tris
    all_eids = [eid for eid, _ in all_elements]

    # Partition into 20 degradation bins: g_d = (1-d)^2 + k_res
    bins = {i: [] for i in range(20)}
    for eid in all_eids:
        d = elem_damage.get(eid, 0.0)
        g_d = (1.0 - d)**2 + k_res
        bin_idx = min(19, max(0, int(g_d * 20.0)))
        bins[bin_idx].append(eid)

    # Detect boundary nodes:
    bot_nodes = []
    top_nodes = []
    pin_node = None
    min_dist_pin = 1e9

    for nid, (x, y) in nodes.items():
        if abs(y - 0.0) <= 1e-4:
            bot_nodes.append(nid)
        if abs(y - 1.0) <= 1e-4:
            top_nodes.append(nid)
        d_pin = math.hypot(x - 0.0, y - 0.0)
        if d_pin < min_dist_pin:
            min_dist_pin = d_pin
            pin_node = nid

    with open(out_path, "w") as f:
        f.write("*HEADING\n")
        f.write(f"{title}\n")
        f.write(f"** E0 = {E0_val:.6e} MPa, nu = {nu_val:.2f}, uy = {uy_val:.6f} mm\n")

        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write(f"{nid}, {x:.9e}, {y:.9e}\n")

        # Elements
        if quads:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=QUADS\n")
            for eid, conn in quads:
                f.write(f"{eid}, " + ", ".join(str(c) for c in conn) + "\n")
        if tris:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=TRIS\n")
            for eid, conn in tris:
                f.write(f"{eid}, " + ", ".join(str(c) for c in conn) + "\n")

        # Facsimile set All_elem matching Section 4.3 architecture
        f.write("*ELSET, ELSET=All_elem\nQUADS\n")
        if tris:
            f.write("TRIS\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        def write_nset(name, nids):
            f.write(f"*NSET, NSET={name}\n")
            for i in range(0, len(nids), 16):
                f.write(", ".join(str(nid) for nid in nids[i:i+16]) + "\n")

        def write_elset(name, eids):
            f.write(f"*ELSET, ELSET={name}\n")
            for i in range(0, len(eids), 16):
                f.write(", ".join(str(eid) for eid in eids[i:i+16]) + "\n")

        write_nset("N_BOTTOM", bot_nodes)
        write_nset("N_TOP", top_nodes)
        write_nset("N_PIN", [pin_node])

        # Write material bins
        for b_idx in range(20):
            eids = bins[b_idx]
            if not eids:
                continue
            mat_name = f"MAT_BIN_{b_idx}"
            elset_name = f"ELSET_BIN_{b_idx}"
            write_elset(elset_name, eids)
            f.write(f"*SOLID SECTION, ELSET={elset_name}, MATERIAL={mat_name}\n1.0\n")
            f.write(f"*MATERIAL, NAME={mat_name}\n")
            g_mid = (b_idx + 0.5) / 20.0
            E_eff = E0_val * max(g_mid, k_res)
            f.write("*ELASTIC\n")
            f.write(f"{E_eff:.6e}, {nu_val:.4f}\n")

        # Recovery step
        f.write("*STEP, NAME=RECOVERY_STEP, NLGEOM=NO\n")
        f.write("*STATIC\n1.0, 1.0, 1.0, 1.0\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write(f"N_TOP, 2, 2, {uy_val:.6e}\n")

        # Field output requests on All_elem matching Section 4.3 Listing 3
        f.write("*OUTPUT, FIELD\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem, DIRECTION=YES\n")
        f.write("MISESERI, MISESAVG, S, EVOL\n")
        f.write("*NODE OUTPUT\nU, RF\n")
        f.write("*END STEP\n")


def solve_job(job_name, work_dir):
    print(f"Solving {job_name} locally with Abaqus in {work_dir}...")
    abaqus_cmd = r"C:\SIMULIA\Commands\abaqus.bat"
    cmd = f'"{abaqus_cmd}" job={job_name} interactive ask_delete=OFF'
    p = subprocess.run(cmd, cwd=work_dir, shell=True, capture_output=True, text=True)
    sta_path = os.path.join(work_dir, job_name + ".sta")
    if os.path.exists(sta_path):
        with open(sta_path, "r") as f:
            print("STA summary: " + f.read().strip())
    else:
        print(f"Warning: {sta_path} not found.")
    return p.returncode == 0


def extract_recovery_fields(odb_path):
    """
    Extracts elementwise MISESERI, MISESAVG, S, and EVOL from the solved recovery ODB.
    """
    extract_py = os.path.join(OUT_DIR, "temp_extract_fields.py")
    out_json = os.path.join(OUT_DIR, "temp_recovery_fields.json")

    script_content = """
from __future__ import print_function
import sys
import json
import odbAccess

odb_path = r"{odb_path}"
out_json = r"{out_json}"

odb = odbAccess.openOdb(odb_path, readOnly=True)
step = odb.steps['RECOVERY_STEP']
frame = step.frames[-1]

fkeys = frame.fieldOutputs.keys()
miseseri_field = frame.fieldOutputs['MISESERI'] if 'MISESERI' in fkeys else None
misesavg_field = frame.fieldOutputs['MISESAVG'] if 'MISESAVG' in fkeys else None
s_field = frame.fieldOutputs['S'] if 'S' in fkeys else None
evol_field = frame.fieldOutputs['EVOL'] if 'EVOL' in fkeys else None

data = {{}}

if miseseri_field is not None:
    for val in miseseri_field.values:
        eid = val.elementLabel
        if eid not in data:
            data[eid] = {{}}
        data[eid]['miseseri'] = float(val.data)

if misesavg_field is not None:
    for val in misesavg_field.values:
        eid = val.elementLabel
        if eid in data:
            data[eid]['misesavg'] = float(val.data)

if s_field is not None:
    for val in s_field.values:
        eid = val.elementLabel
        if eid in data and 's_mises' not in data[eid]:
            data[eid]['s_mises'] = float(val.mises)

if evol_field is not None:
    for val in evol_field.values:
        eid = val.elementLabel
        if eid in data:
            data[eid]['evol'] = float(val.data)

odb.close()

with open(out_json, "w") as f:
    json.dump(data, f)
""".format(odb_path=odb_path.replace("\\", "\\\\"), out_json=out_json.replace("\\", "\\\\"))

    with open(extract_py, "w") as f:
        f.write(script_content)

    cmd = 'abaqus python "%s"' % extract_py
    p = subprocess.run(cmd, cwd=OUT_DIR, shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        print("Field extraction error:", p.stderr)
        raise RuntimeError(f"Failed to extract fields from {odb_path}")

    with open(out_json, "r") as f:
        fields = json.load(f)

    return {int(k): v for k, v in fields.items()}


def main():
    print("=" * 80)
    print("TASK F1719 PHASE 5: CONTINUOUS CONSTITUTIVE SAME-STATE STRESS RECOVERY")
    print("=" * 80)

    # 1. Parse coarse mesh
    print(f"Loading coarse mesh from {COARSE_INP}...")
    nodes, quads, tris = parse_coarse_inp(COARSE_INP)
    all_elements = quads + tris
    all_eids = [eid for eid, _ in all_elements]
    centroids = compute_centroids(nodes, all_elements)
    print(f"Loaded: {len(nodes)} nodes, {len(quads)} quads, {len(tris)} tris ({len(all_elements)} total)")

    # 2. Extract authentic coarse states from PK_F1719_COARSE_PFM.odb
    states_data = extract_coarse_states_from_odb()

    # Define jobs to generate and solve:
    # We solve:
    # - STATE0: Physical (E0 = 210,000 MPa)
    # - STATE1: Physical (E0 = 210,000 MPa)
    # - STATE2: Physical (E0 = 210,000 MPa) AND Dummy (E_dummy = 1.0e-8 MPa)
    # - STATE3: Physical (E0 = 210,000 MPa) AND Dummy (E_dummy = 1.0e-8 MPa)
    # - STATE4: Physical (E0 = 210,000 MPa)
    job_specs = [
        {"job_name": "PK_F1719_REC_STATE0_PHYS", "state": "STATE0", "E0": 210000.0, "scale": "physical"},
        {"job_name": "PK_F1719_REC_STATE1_PHYS", "state": "STATE1", "E0": 210000.0, "scale": "physical"},
        {"job_name": "PK_F1719_REC_STATE2_PHYS", "state": "STATE2", "E0": 210000.0, "scale": "physical"},
        {"job_name": "PK_F1719_REC_STATE2_DUMMY", "state": "STATE2", "E0": 1.0e-8, "scale": "dummy"},
        {"job_name": "PK_F1719_REC_STATE3_PHYS", "state": "STATE3", "E0": 210000.0, "scale": "physical"},
        {"job_name": "PK_F1719_REC_STATE3_DUMMY", "state": "STATE3", "E0": 1.0e-8, "scale": "dummy"},
        {"job_name": "PK_F1719_REC_STATE4_PHYS", "state": "STATE4", "E0": 210000.0, "scale": "physical"}
    ]

    recovery_results = {
        "task_id": "F1719-COARSE-PHASE-FIELD-MISESERI-REMESH-FIVE-HOLE",
        "coarse_inp": COARSE_INP,
        "coarse_odb": COARSE_ODB,
        "mesh_summary": {
            "num_nodes": len(nodes),
            "num_elements": len(all_elements),
            "num_quads": len(quads),
            "num_tris": len(tris)
        },
        "states": {}
    }

    # Solve each job and extract fields
    for spec in job_specs:
        jname = spec["job_name"]
        skey = spec["state"]
        sdata = states_data[skey]
        E0_val = spec["E0"]
        scale = spec["scale"]
        uy_val = sdata["rp_uy"]
        elem_dmg = sdata["elem_damage"]

        inp_path = os.path.join(OUT_DIR, jname + ".inp")
        title = f"Task F1719 Recovery: {jname} ({sdata['desc']})"
        build_recovery_deck(inp_path, nodes, quads, tris, elem_dmg, E0_val=E0_val, nu_val=0.30, k_res=1e-7, uy_val=uy_val, title=title)
        print(f"\nGenerated deck: {inp_path} (uy = {uy_val:.6f} mm, E0 = {E0_val:.4e} MPa)")

        # Solve
        ok = solve_job(jname, OUT_DIR)
        if not ok:
            print(f"ERROR: Job {jname} failed!")
            continue

        odb_path = os.path.join(OUT_DIR, jname + ".odb")
        fields = extract_recovery_fields(odb_path)
        print(f"Extracted fields for {len(fields)} elements from {odb_path}")

        # Compute summary statistics
        miseseri_vals = [f["miseseri"] for f in fields.values() if "miseseri" in f]
        misesavg_vals = [f["misesavg"] for f in fields.values() if "misesavg" in f]
        eta_vals = [f["miseseri"] / f["misesavg"] * 100.0 for f in fields.values() if "miseseri" in f and "misesavg" in f and f["misesavg"] > 1e-15]

        # Top 5 error elements
        sorted_by_err = sorted(fields.items(), key=lambda kv: kv[1].get("miseseri", 0.0), reverse=True)
        top5_err = [
            {
                "eid": eid,
                "cx": centroids[eid][0],
                "cy": centroids[eid][1],
                "damage": elem_dmg.get(eid, 0.0),
                "miseseri": f.get("miseseri", 0.0),
                "misesavg": f.get("misesavg", 0.0),
                "eta_percent": (f.get("miseseri", 0.0) / f.get("misesavg", 1.0)) * 100.0 if f.get("misesavg", 0.0) > 1e-15 else 0.0
            }
            for eid, f in sorted_by_err[:5]
        ]

        # Critical ligament h3-h4 statistics (clearance between Hole 3 and Hole 4)
        # Hole 3 center (0.60, 0.55), R=0.05. Hole 4 center (0.75, 0.50), R=0.075.
        # Ligament box: x in [0.63, 0.70], y in [0.48, 0.56]
        h3_h4_eids = [
            eid for eid, (cx, cy) in centroids.items()
            if 0.63 <= cx <= 0.70 and 0.48 <= cy <= 0.56
        ]
        h3_h4_errors = [fields[eid]["miseseri"] for eid in h3_h4_eids if eid in fields]
        h3_h4_damages = [elem_dmg.get(eid, 0.0) for eid in h3_h4_eids]

        summary = {
            "job_name": jname,
            "state": skey,
            "desc": sdata["desc"],
            "scale": scale,
            "E0_MPa": E0_val,
            "uy_mm": uy_val,
            "d_max_coarse": sdata["d_max"],
            "d_mean_coarse": sdata["d_mean"],
            "miseseri_max": max(miseseri_vals) if miseseri_vals else 0.0,
            "miseseri_min": min(miseseri_vals) if miseseri_vals else 0.0,
            "miseseri_mean": sum(miseseri_vals) / float(len(miseseri_vals)) if miseseri_vals else 0.0,
            "misesavg_max": max(misesavg_vals) if misesavg_vals else 0.0,
            "misesavg_min": min(misesavg_vals) if misesavg_vals else 0.0,
            "misesavg_mean": sum(misesavg_vals) / float(len(misesavg_vals)) if misesavg_vals else 0.0,
            "eta_max_percent": max(eta_vals) if eta_vals else 0.0,
            "eta_mean_percent": sum(eta_vals) / float(len(eta_vals)) if eta_vals else 0.0,
            "top5_error_elements": top5_err,
            "ligament_h3_h4": {
                "num_elements": len(h3_h4_eids),
                "eids": h3_h4_eids,
                "d_max": max(h3_h4_damages) if h3_h4_damages else 0.0,
                "miseseri_max": max(h3_h4_errors) if h3_h4_errors else 0.0,
                "miseseri_mean": sum(h3_h4_errors) / float(len(h3_h4_errors)) if h3_h4_errors else 0.0
            }
        }

        print(f"Summary for {jname}:")
        print(f"  MISESERI: max = {summary['miseseri_max']:.6e}, mean = {summary['miseseri_mean']:.6e}")
        print(f"  eta_percent: max = {summary['eta_max_percent']:.2f}%, mean = {summary['eta_mean_percent']:.2f}%")
        print(f"  Ligament h3-h4: d_max = {summary['ligament_h3_h4']['d_max']:.4f}, err_max = {summary['ligament_h3_h4']['miseseri_max']:.6e}")
        print(f"  Peak element: ID={top5_err[0]['eid']}, coord=({top5_err[0]['cx']:.4f}, {top5_err[0]['cy']:.4f}), d={top5_err[0]['damage']:.4f}")

        # Store in master dictionary
        if skey not in recovery_results["states"]:
            recovery_results["states"][skey] = {
                "desc": sdata["desc"],
                "uy_mm": uy_val,
                "d_max": sdata["d_max"],
                "d_mean": sdata["d_mean"],
                "element_data": {
                    eid: {
                        "cx": centroids[eid][0],
                        "cy": centroids[eid][1],
                        "damage": elem_dmg.get(eid, 0.0)
                    }
                    for eid in sorted(all_eids)
                },
                "scales": {}
            }

        recovery_results["states"][skey]["scales"][scale] = {
            "summary": summary,
            "element_fields": {
                eid: {
                    "miseseri": fields[eid].get("miseseri", 0.0),
                    "misesavg": fields[eid].get("misesavg", 0.0),
                    "eta_percent": (fields[eid].get("miseseri", 0.0) / fields[eid].get("misesavg", 1.0)) * 100.0 if fields[eid].get("misesavg", 0.0) > 1e-15 else 0.0,
                    "s_mises": fields[eid].get("s_mises", 0.0)
                }
                for eid in sorted(fields.keys())
            }
        }

    # Save to JSON
    out_master_json = os.path.join(RESULTS_DIR, "f1719_recovered_miseseri_multistate.json")
    with open(out_master_json, "w") as f:
        json.dump(recovery_results, f, indent=2)
    print(f"\nSUCCESS: Master multi-state recovery dataset saved to {out_master_json} ({os.path.getsize(out_master_json)} bytes)")


if __name__ == "__main__":
    main()
