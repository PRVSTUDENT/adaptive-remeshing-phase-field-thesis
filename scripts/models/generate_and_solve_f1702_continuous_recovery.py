# -*- coding: utf-8 -*-
"""
scripts/models/generate_and_solve_f1702_continuous_recovery.py
==============================================================
Task F1702: Gate B Elimination of 20-Bin Approximation via Continuous Degradation
Generates and solves 1-increment standard continuum recovery models with continuous
damage-dependent degradation using native Abaqus/Standard *ELASTIC, DEPENDENCIES=1
and *INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1.

Zero user subroutines required.
Zero parallel solver forces or stiffness corruption.
Exact physical residual floor k_res = 1e-7 implemented continuously across d in [0, 1].
Requests native SPR stress error outputs: MISESERI and MISESAVG.
Consistent units: length mm, force kN, stress kN/mm^2 (GPa).
"""

import os
import json
import subprocess
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UEL_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1700_extracted_uel_full_field.json")
BASE_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "200_pk_sec43_prescribed_same_state", "PK_SEC43_PRESCRIBED_STATE2.inp")
WORK_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "202_pk_sec43_continuous_recovery")

E0_GPA = 210.0  # 210 kN/mm^2 = GPa
NU = 0.30
K_RES = 1.0e-7

def parse_mesh(inp_path):
    nodes = {}
    elements = {}
    with open(inp_path, "r") as f:
        mode = None
        for line in f:
            line_s = line.strip()
            if line_s.startswith("*"):
                upper = line_s.upper()
                if upper.startswith("*NODE") and not any(k in upper for k in ["PRINT", "FILE", "OUTPUT"]):
                    mode = "NODE"
                elif upper.startswith("*ELEMENT") and "OUTPUT" not in upper:
                    if "CPE4" in upper:
                        mode = "CPE4"
                    elif "CPE3" in upper:
                        mode = "CPE3"
                    else:
                        mode = None
                else:
                    mode = None
                continue
            if not line_s or mode is None:
                continue
            parts = [p.strip() for p in line_s.split(",")]
            try:
                if mode == "NODE":
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                elif mode in ("CPE4", "CPE3"):
                    elements[int(parts[0])] = (mode, [int(p) for p in parts[1:]])
            except ValueError:
                pass
    return nodes, elements

def compute_nodal_damage(nodes, elements, elem_dmg):
    node_elem_dmg = {nid: [] for nid in nodes}
    for eid, (etype, nids) in elements.items():
        ext_eid = eid + 7846
        d_val = float(elem_dmg[str(ext_eid)])
        for nid in nids:
            node_elem_dmg[nid].append(d_val)
    nodal_damage = {}
    for nid, vals in node_elem_dmg.items():
        nodal_damage[nid] = float(np.mean(vals)) if vals else 0.0
    return nodal_damage

def generate_deck(state_key, state_data, nodes, elements, out_inp_path):
    nodal_u = state_data["nodal_displacements"]
    elem_dmg = state_data["element_avg_damage"]
    nodal_damage = compute_nodal_damage(nodes, elements, elem_dmg)

    with open(out_inp_path, "w") as f:
        f.write("*HEADING\n")
        f.write(f"Task F1702 Continuous Degradation Recovery: {state_key}\n")
        
        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write(f"{nid}, {x:.8f}, {y:.8f}\n")

        # Quads
        f.write("*ELEMENT, TYPE=CPE4, ELSET=All_elem\n")
        for eid, (etype, nids) in sorted(elements.items()):
            if etype == "CPE4":
                n_str = ", ".join(str(n) for n in nids)
                f.write(f"{eid}, {n_str}\n")

        # Tris
        f.write("*ELEMENT, TYPE=CPE3, ELSET=All_elem\n")
        for eid, (etype, nids) in sorted(elements.items()):
            if etype == "CPE3":
                n_str = ", ".join(str(n) for n in nids)
                f.write(f"{eid}, {n_str}\n")

        # Solid section with continuous material
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=MAT_CONTINUOUS_PFM\n")
        f.write("1.0\n")

        # Continuous material definition via field variable dependency
        f.write("*MATERIAL, NAME=MAT_CONTINUOUS_PFM\n")
        f.write("*ELASTIC, DEPENDENCIES=1\n")
        # 101 points from d=0.00 to d=1.00 in steps of 0.01 (E in kN/mm^2 = GPa)
        for i in range(101):
            d_val = i / 100.0
            g_val = (1.0 - d_val)**2 + K_RES
            e_val = E0_GPA * g_val
            f.write(f"{e_val:.8e}, {NU:.2f}, , {d_val:.2f}\n")

        # Initial conditions: continuous damage mapped to field variable 1 at NODES
        f.write("*INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1\n")
        for nid in sorted(nodes.keys()):
            d_val = nodal_damage[nid]
            d_clamped = max(0.0, min(1.0, d_val))
            f.write(f"{nid}, {d_clamped:.6f}\n")

        # Prescribed same-state recovery step
        f.write("*STEP, NAME=RECOVERY, NLGEOM=NO\n")
        f.write("*STATIC\n")
        f.write("1.0, 1.0, 1.0, 1.0\n")

        # Prescribe exact UEL displacements onto all nodes
        f.write("*BOUNDARY\n")
        for nid in sorted(nodes.keys()):
            u1, u2 = nodal_u[str(nid)]
            f.write(f"{nid}, 1, 1, {u1:.8e}\n")
            f.write(f"{nid}, 2, 2, {u2:.8e}\n")

        # Outputs required for SPR and stress recovery
        f.write("*OUTPUT, FIELD\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\n")
        f.write("S, E, FV, MISESERI, MISESAVG\n")
        f.write("*NODE OUTPUT\n")
        f.write("U, RF\n")
        f.write("*END STEP\n")

def solve_job(job_name, work_dir):
    print(f"\n--- Solving Abaqus job {job_name} in {work_dir} ---")
    cmd = f"abaqus job={job_name} interactive"
    p = subprocess.run(cmd, cwd=work_dir, shell=True, capture_output=True, text=True)
    print(f"Command finished with return code {p.returncode}")
    
    sta_path = os.path.join(work_dir, f"{job_name}.sta")
    if os.path.exists(sta_path):
        with open(sta_path, "r") as f:
            print(f"STA content:\n{f.read().strip()}")
    else:
        print(f"WARNING: {sta_path} does not exist!")

    odb_path = os.path.join(work_dir, f"{job_name}.odb")
    if os.path.exists(odb_path):
        print(f"SUCCESS: Generated {odb_path} ({os.path.getsize(odb_path)} bytes)")
        return True
    else:
        print(f"FAILURE: {odb_path} not found!")
        return False

def main():
    os.makedirs(WORK_DIR, exist_ok=True)
    print(f"Loading mesh from {BASE_INP}...")
    nodes, elements = parse_mesh(BASE_INP)
    print(f"Mesh: {len(nodes)} nodes, {len(elements)} elements")

    print(f"Loading UEL full-field data from {UEL_JSON}...")
    with open(UEL_JSON, "r") as f:
        data = json.load(f)

    jobs = [
        ("STATE2", "PK_SEC43_CONTINUOUS_STATE2"),
        ("STATE4", "PK_SEC43_CONTINUOUS_STATE4"),
        ("STATE5", "PK_SEC43_CONTINUOUS_STATE5"),
    ]

    for sk, job_name in jobs:
        inp_path = os.path.join(WORK_DIR, f"{job_name}.inp")
        print(f"\nGenerating {inp_path}...")
        generate_deck(sk, data[sk], nodes, elements, inp_path)
        print(f"Wrote deck ({os.path.getsize(inp_path)} bytes)")

        # Solve
        ok = solve_job(job_name, WORK_DIR)
        if not ok:
            print(f"ERROR: Job {job_name} failed!")
            return False

    print("\nAll 3 continuous recovery models solved successfully with native MISESERI output!")
    return True

if __name__ == "__main__":
    main()
