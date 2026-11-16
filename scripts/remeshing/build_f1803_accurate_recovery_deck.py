# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_f1803_accurate_recovery_deck.py
======================================================
Task F1803: Build and solve high-fidelity damage-to-continuum recovery model for Case 3.

Uses authentic elementwise degraded moduli:
    E_i = E_0 * [(1 - d_i)^2 + k_res] kN/mm^2
where:
    E_0 = 210.0 kN/mm^2 (210 GPa)
    k_res = 1.0e-7
    nu = 0.30
    d_i from archived State 2 (Step-1 Frame 40, uy = 0.200 mm) of
    results/validation/f1694_sec43_five_state_damage_record.json.

Solves SEC43_STATE2_HIGH_FIDELITY_RECOVERY locally with Abaqus standard to produce
native recovered stress error fields MISESERI and MISESAVG.
"""

from __future__ import print_function
import os
import sys
import json
import math
import subprocess
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
PHYS_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1", "PK_SEC43_STAGGERED_PHYS.inp")
RECORD_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1694_sec43_five_state_damage_record.json")
WORK_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "253_f1803_case3_accurate_recovery")
JOB_NAME = "SEC43_STATE2_HIGH_FIDELITY_RECOVERY"
INP_PATH = os.path.join(WORK_DIR, JOB_NAME + ".inp")

if not os.path.exists(WORK_DIR):
    os.makedirs(WORK_DIR)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def parse_base_mesh():
    nodes = []
    quads = []
    tris = []
    in_node = False
    in_elem = False
    elem_type = ""
    
    with open(PHYS_INP, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue
            if line_str.startswith("*"):
                u = line_str.upper()
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
                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) >= 3:
                    nodes.append((int(parts[0]), float(parts[1]), float(parts[2])))
            elif in_elem:
                parts = [int(p.strip()) for p in line_str.split(",")]
                eid = parts[0]
                conn = parts[1:]
                if len(conn) == 4 or elem_type == "CPE4":
                    quads.append((eid, conn))
                elif len(conn) == 3 or elem_type == "CPE3":
                    tris.append((eid, conn))
                    
    print("Parsed %d nodes, %d quads, %d tris from base mesh." % (len(nodes), len(quads), len(tris)))
    return nodes, quads, tris

def identify_boundary_nodes(nodes):
    lower_nodes = []
    upper_nodes = []
    central_nodes = []
    
    for nid, x, y in nodes:
        d_lower = math.hypot(x - 20.0, y - 20.0)
        d_upper = math.hypot(x - 20.0, y - 100.0)
        d_central = math.hypot(x - 36.5, y - 51.0)
        
        if abs(d_lower - 5.0) <= 0.08:
            lower_nodes.append(nid)
        if abs(d_upper - 5.0) <= 0.08:
            upper_nodes.append(nid)
        if abs(d_central - 10.0) <= 0.08:
            central_nodes.append(nid)
            
    print("Boundary nodes: lower=%d, upper=%d, central=%d" % (
        len(lower_nodes), len(upper_nodes), len(central_nodes)
    ))
    return lower_nodes, upper_nodes, central_nodes

def build_accurate_deck(nodes, quads, tris, lower_nodes, upper_nodes, damage_dict):
    rp_nid = 999999
    E0 = 210.0  # kN/mm^2 (210 GPa)
    nu = 0.30
    k_res = 1.0e-7
    uy_val = 0.200  # mm (State 2 hole arrest)
    
    all_eids = [eid for eid, _ in quads] + [eid for eid, _ in tris]
    all_eids.sort()
    
    # Compute exact degraded modulus for each element
    moduli = {}
    for eid in all_eids:
        d_val = float(damage_dict.get(eid, damage_dict.get(str(eid), 0.0)))
        # clamp to [0.0, 1.0]
        d_clamped = max(0.0, min(1.0, d_val))
        g_d = (1.0 - d_clamped)**2 + k_res
        E_deg = E0 * g_d
        moduli[eid] = (d_clamped, g_d, E_deg)
        
    min_E = min(m[2] for m in moduli.values())
    max_E = max(m[2] for m in moduli.values())
    print("Moduli stats: min E = %.6e kN/mm^2 (d=%.6f), max E = %.6e kN/mm^2 (d=%.6f)" % (
        min_E, max(m[0] for m in moduli.values()),
        max_E, min(m[0] for m in moduli.values())
    ))
    
    with open(INP_PATH, "w") as f:
        f.write("*HEADING\n")
        f.write("Task F1803: Case 3 State 2 Accurate Constitutive Degraded-Modulus Recovery (uy=0.200mm)\n")
        
        f.write("*NODE\n")
        for nid, x, y in nodes:
            f.write("%d, %.7f, %.7f\n" % (nid, x, y))
        f.write("%d, 20.0000000, 100.0000000\n" % rp_nid)
        
        if quads:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=QUADS\n")
            for eid, conn in quads:
                f.write("%d, %s\n" % (eid, ", ".join(str(c) for c in conn)))
        if tris:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=TRIS\n")
            for eid, conn in tris:
                f.write("%d, %s\n" % (eid, ", ".join(str(c) for c in conn)))
                
        f.write("*ELSET, ELSET=All_elem\nQUADS\nTRIS\n")
        
        def write_nset(name, nids):
            f.write("*NSET, NSET=%s\n" % name)
            for i in range(0, len(nids), 16):
                f.write(", ".join(str(nid) for nid in nids[i:i+16]) + "\n")
                
        write_nset("N_LOWER_HOLE", lower_nodes)
        write_nset("N_UPPER_HOLE", upper_nodes)
        f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)
        
        # Write individual element set, solid section, and material for each element
        print("Writing elementwise materials and sections for %d elements..." % len(all_eids))
        for eid in all_eids:
            d_clamped, g_d, E_deg = moduli[eid]
            elset_name = "EL_%d" % eid
            mat_name = "MAT_%d" % eid
            
            f.write("*ELSET, ELSET=%s\n%d\n" % (elset_name, eid))
            f.write("*SOLID SECTION, ELSET=%s, MATERIAL=%s\n1.0\n" % (elset_name, mat_name))
            f.write("*MATERIAL, NAME=%s\n" % mat_name)
            f.write("*ELASTIC, TYPE=ISOTROPIC\n%.10e, %.4f\n" % (E_deg, nu))
            
        f.write("** Tie upper hole to RP\n")
        for nid in upper_nodes:
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))
            
        f.write("*STEP, NAME=RECOVERY_STEP, NLGEOM=NO\n")
        f.write("*STATIC\n1.0, 1.0, 1.0, 1.0\n")
        f.write("*BOUNDARY\n")
        f.write("N_LOWER_HOLE, 1, 2, 0.0\n")
        f.write("N_UPPER_HOLE, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, %.4f\n" % uy_val)
        
        f.write("*OUTPUT, FIELD\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\n")
        f.write("MISESERI, MISESAVG, EVOL, S, E\n")
        f.write("*NODE OUTPUT\nU, RF\n")
        f.write("*END STEP\n")
        
    print("Wrote input deck: %s (%d bytes)" % (INP_PATH, os.path.getsize(INP_PATH)))
    return moduli

def solve_deck():
    cmd = "abaqus job=" + JOB_NAME + " interactive ask_delete=OFF"
    print("Running Abaqus standard solve: %s in %s..." % (cmd, WORK_DIR))
    res = subprocess.run(cmd, shell=True, cwd=WORK_DIR, capture_output=True, text=True)
    print("Solve return code: %d" % res.returncode)
    if res.stdout:
        print("STDOUT:\n%s" % res.stdout[-1000:])
    if res.stderr:
        print("STDERR:\n%s" % res.stderr[-1000:])
        
    odb_path = os.path.join(WORK_DIR, JOB_NAME + ".odb")
    sta_path = os.path.join(WORK_DIR, JOB_NAME + ".sta")
    dat_path = os.path.join(WORK_DIR, JOB_NAME + ".dat")
    log_path = os.path.join(WORK_DIR, JOB_NAME + ".log")
    
    assert os.path.exists(odb_path), "ODB missing after solve: %s" % odb_path
    odb_size = os.path.getsize(odb_path)
    odb_sha = sha256_file(odb_path)
    print("ODB generated: %s (%d bytes, SHA-256 %s)" % (odb_path, odb_size, odb_sha))
    
    # Check .sta for successful completion
    with open(sta_path, "r") as f:
        sta_text = f.read()
    print("STA tail:\n%s" % "\n".join(sta_text.splitlines()[-10:]))
    assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta_text, "Abaqus solve did not complete successfully"
    print("Abaqus solve completed successfully (Exit 0).")
    return odb_path, odb_size, odb_sha

def main():
    nodes, quads, tris = parse_base_mesh()
    lower_nodes, upper_nodes, central_nodes = identify_boundary_nodes(nodes)
    
    print("Loading State 2 damage record from: %s" % RECORD_JSON)
    with open(RECORD_JSON, "r") as f:
        record_data = json.load(f)
    state2 = record_data["states"][1]
    print("State 2 metadata: uy = %s mm, elements in record = %d" % (
        state2.get("uy_mm"), len(state2["damage_by_element"])
    ))
    
    moduli = build_accurate_deck(nodes, quads, tris, lower_nodes, upper_nodes, state2["damage_by_element"])
    odb_path, odb_size, odb_sha = solve_deck()
    
    # Save metadata receipt for the recovery donor
    receipt = {
        "task_id": "F1803-CASE3-STATE2-DEGRADED-MODULUS-FIDELITY-NATIVE-REMESH",
        "job_name": JOB_NAME,
        "inp_path": INP_PATH,
        "inp_sha256": sha256_file(INP_PATH),
        "inp_size_bytes": os.path.getsize(INP_PATH),
        "odb_path": odb_path,
        "odb_size_bytes": odb_size,
        "odb_sha256": odb_sha,
        "constitutive_treatment": "ELEMENTWISE_EXACT_DEGRADED_ELASTIC",
        "E0_kn_per_mm2": 210.0,
        "nu": 0.30,
        "k_res": 1.0e-7,
        "num_elements": len(moduli),
        "min_degraded_E_kn_per_mm2": min(m[2] for m in moduli.values()),
        "max_degraded_E_kn_per_mm2": max(m[2] for m in moduli.values()),
        "elements_with_d_gt_09": sum(1 for m in moduli.values() if m[0] > 0.9),
        "min_degraded_E_in_severed_crack_kn_per_mm2": min(m[2] for m in moduli.values() if m[0] > 0.9),
        "uy_applied_mm": 0.200,
        "step_name": "RECOVERY_STEP",
        "frame_index": 1
    }
    
    receipt_path = os.path.join(WORK_DIR, "PK_F1803_CASE3_ACCURATE_DONOR_RECEIPT.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
    print("Donor receipt written to: %s" % receipt_path)

if __name__ == "__main__":
    main()
