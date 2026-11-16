# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_f1809_multistate_donors.py
===================================================
Task F1809: Method A.2 Multi-State Sequential Recovery Donor Construction.

Builds and solves authentic degraded-modulus continuum recovery models for:
- Case 2: Multi-state recovery across 4 authentic states (Frame 10 pre-analysis,
  Frame 190 hole arrest, Frame 280 distal re-initiation, Frame 337 outer ligament propagation).
- Case 3: Multi-state recovery across 3 authentic states (State a initiation uy=0.100 mm,
  State b hole arrest uy=0.200 mm, State d secondary propagation uy=0.300 mm).

Combines the resulting native recovered stress error indicators into multi-state envelope
recovery ODBs:
- Case 2: models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_HOLE_MULTISTATE_RECOVERY.odb
- Case 3: models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/SEC43_MULTISTATE_RECOVERY.odb
"""

from __future__ import print_function
import os
import sys
import json
import math
import shutil
import hashlib
import subprocess

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

F1809_BASE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery")
ABAQUS_BAT = r"C:\SIMULIA\Commands\abaqus.bat"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

# ==============================================================================
# 1. CASE 2 MULTI-STATE RECOVERY SOLVER & ENVELOPE BUILDER
# ==============================================================================

def build_case2_multistate_donor():
    import odbAccess
    from abaqusConstants import SCALAR, WHOLE_ELEMENT

    print("\n" + "="*80)
    print("BUILDING CASE 2 MULTI-STATE RECOVERY DONOR (METHOD A.2)")
    print("="*80)

    c2_dir = os.path.join(F1809_BASE, "case2")
    if not os.path.exists(c2_dir):
        os.makedirs(c2_dir)

    source_odb_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_COARSE_JOB1.odb")
    phys_inp_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_COARSE_PHYS.inp")

    # Parse base physical mesh
    nodes = []
    quads = []
    tris = []
    n_bottom = []
    n_pin = []
    n_top = []

    in_node = in_quad = in_tri = in_bottom = in_pin = in_top = False
    with open(phys_inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                in_node = u.startswith("*NODE")
                in_quad = "*ELEMENT" in u and "QUAD" in u
                in_tri = "*ELEMENT" in u and "TRI" in u
                in_bottom = "*NSET" in u and "N_BOTTOM" in u
                in_pin = "*NSET" in u and "N_PIN" in u
                in_top = "*NSET" in u and "N_TOP" in u
                continue
            if in_node:
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 3:
                    nodes.append((int(p[0]), float(p[1]), float(p[2])))
            elif in_quad:
                p = [int(x.strip()) for x in l.split(",")]
                quads.append((p[0], p[1:]))
            elif in_tri:
                p = [int(x.strip()) for x in l.split(",")]
                tris.append((p[0], p[1:]))
            elif in_bottom:
                n_bottom.extend([int(x.strip()) for x in l.split(",") if x.strip()])
            elif in_pin:
                n_pin.extend([int(x.strip()) for x in l.split(",") if x.strip()])
            elif in_top:
                n_top.extend([int(x.strip()) for x in l.split(",") if x.strip()])

    print("Parsed Case 2 physical mesh: %d nodes, %d elements (2832 quads, 74 tris)" % (len(nodes), len(quads) + len(tris)))

    # Sample 4 authentic causal states from PK_HOLE_COARSE_JOB1.odb
    states_def = [
        {"name": "state1_preanalysis", "frame_idx": 10, "label": "State 1 (Frame 10, uy=0.005 mm pre-analysis)"},
        {"name": "state2_hole_arrest", "frame_idx": 190, "label": "State 2 (Frame 190, uy=0.0076 mm hole-arrest)"},
        {"name": "state3_distal_nucleation", "frame_idx": 280, "label": "State 3 (Frame 280, uy=0.0088 mm distal re-initiation)"},
        {"name": "state4_outer_propagation", "frame_idx": 337, "label": "State 4 (Frame 337, uy=0.010 mm outer propagation)"}
    ]

    print("Sampling authentic damage fields from source ODB...")
    src_odb = odbAccess.openOdb(source_odb_path, readOnly=True)
    step2 = src_odb.steps["Step-2"]

    solved_odbs = []
    for s_info in states_def:
        f_idx = s_info["frame_idx"]
        f = step2.frames[f_idx]
        t_val = float(f.frameValue)
        sdv1 = f.fieldOutputs["SDV1"]
        u_field = f.fieldOutputs["U"]
        top_uys = [v.data[1] for v in u_field.values if v.data[1] > 0.004]
        uy_val = max(top_uys) if top_uys else 0.007616

        elem_sdv = {}
        for v in sdv1.values:
            elem_sdv.setdefault(v.elementLabel, []).append(float(v.data))

        damage_dict = {}
        for vis_label, vals in elem_sdv.items():
            phys_eid = int(vis_label - 5812)
            damage_dict[phys_eid] = float(sum(vals) / float(len(vals)))

        max_d = max(damage_dict.values())
        min_d = min(damage_dict.values())
        print("  %s: t=%.4f s, uy=%.6f mm, max_d=%.4f, min_d=%.4f" % (s_info["label"], t_val, uy_val, max_d, min_d))

        job_name = "PK_C2_" + s_info["name"].upper()
        inp_path = os.path.join(c2_dir, job_name + ".inp")
        odb_path = os.path.join(c2_dir, job_name + ".odb")
        sta_path = os.path.join(c2_dir, job_name + ".sta")

        already_solved = False
        if os.path.exists(odb_path) and os.path.exists(sta_path):
            with open(sta_path, "r") as f_sta:
                if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in f_sta.read():
                    already_solved = True

        if not already_solved:
            print("  Writing recovery deck: %s" % inp_path)
            E0 = 210000.0  # MPa
            nu = 0.30
            k_res = 1.0e-7
            rp_nid = 999999

            with open(inp_path, "w") as f_out:
                f_out.write("*HEADING\nCase 2 Degraded-Modulus Continuum Recovery: %s\n" % s_info["label"])
                f_out.write("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO\n\n")

                # Nodes
                f_out.write("*NODE\n")
                for nid, x, y in nodes:
                    f_out.write("%d, %.9e, %.9e\n" % (nid, x, y))
                f_out.write("%d, 0.500000000e+00, 1.000000000e+00\n" % rp_nid)

                # Elements
                if quads:
                    f_out.write("*ELEMENT, TYPE=CPE4, ELSET=QUAD_ELEMS\n")
                    for eid, conn in quads:
                        f_out.write("%d, %s\n" % (eid, ", ".join(str(c) for c in conn)))
                if tris:
                    f_out.write("*ELEMENT, TYPE=CPE3, ELSET=TRI_ELEMS\n")
                    for eid, conn in tris:
                        f_out.write("%d, %s\n" % (eid, ", ".join(str(c) for c in conn)))

                f_out.write("*ELSET, ELSET=All_elem\nQUAD_ELEMS\nTRI_ELEMS\n")

                def write_nset(name, nids):
                    f_out.write("*NSET, NSET=%s\n" % name)
                    for i in range(0, len(nids), 16):
                        f_out.write(", ".join(str(nid) for nid in nids[i:i+16]) + "\n")

                write_nset("N_BOTTOM", n_bottom)
                write_nset("N_PIN", n_pin)
                write_nset("N_TOP", n_top)
                f_out.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

                all_eids = [eid for eid, _ in quads] + [eid for eid, _ in tris]
                all_eids.sort()
                for eid in all_eids:
                    d_val = damage_dict.get(eid, 0.0)
                    d_clamped = max(0.0, min(1.0, d_val))
                    g_d = (1.0 - d_clamped)**2 + k_res
                    E_deg = E0 * g_d
                    elset_name = "EL_%d" % eid
                    mat_name = "MAT_%d" % eid
                    f_out.write("*ELSET, ELSET=%s\n%d\n" % (elset_name, eid))
                    f_out.write("*SOLID SECTION, ELSET=%s, MATERIAL=%s\n1.0\n" % (elset_name, mat_name))
                    f_out.write("*MATERIAL, NAME=%s\n" % mat_name)
                    f_out.write("*ELASTIC, TYPE=ISOTROPIC\n%.10e, %.4f\n" % (E_deg, nu))

                # Tie rigid top displacement to RP
                f_out.write("** Tie rigid top displacement to RP\n")
                for nid in n_top:
                    f_out.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

                f_out.write("*STEP, NAME=RECOVERY_STEP, NLGEOM=NO\n")
                f_out.write("*STATIC\n1.0, 1.0, 1.0, 1.0\n")
                f_out.write("*BOUNDARY\n")
                f_out.write("N_BOTTOM, 2, 2, 0.0\n")
                f_out.write("N_PIN, 1, 1, 0.0\n")
                f_out.write("N_TOP, 1, 1, 0.0\n")
                f_out.write("N_RP, 2, 2, %.6f\n" % uy_val)

                f_out.write("*OUTPUT, FIELD\n")
                f_out.write("*ELEMENT OUTPUT, ELSET=All_elem\n")
                f_out.write("MISESERI, MISESAVG, EVOL, S, E\n")
                f_out.write("*NODE OUTPUT\nU, RF\n")
                f_out.write("*END STEP\n")

            print("  Solving %s via Abaqus standard..." % job_name)
            cmd = "%s job=%s interactive ask_delete=OFF" % (ABAQUS_BAT, job_name)
            subprocess.call(cmd, cwd=c2_dir, shell=True)

            with open(sta_path, "r") as f_sta:
                assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in f_sta.read(), "Abaqus solve failed for %s" % job_name

            # Ensure ALL_ELEM exists on instance in ODB
            odb_check = odbAccess.openOdb(odb_path, readOnly=False)
            inst = list(odb_check.rootAssembly.instances.values())[0]
            if "ALL_ELEM" not in inst.elementSets:
                inst.ElementSetFromElementLabels(name="ALL_ELEM", elementLabels=[e.label for e in inst.elements])
                odb_check.save()
            odb_check.close()
            print("  Solve complete: %s (%d bytes)" % (odb_path, os.path.getsize(odb_path)))

        solved_odbs.append(odb_path)

    src_odb.close()

    # Build Envelope ODB
    print("\nSynthesizing Case 2 Multi-State Maximum Error Envelope across %d states..." % len(solved_odbs))
    multi_odb_path = os.path.join(c2_dir, "PK_HOLE_MULTISTATE_RECOVERY.odb")
    if os.path.exists(multi_odb_path):
        os.remove(multi_odb_path)

    shutil.copyfile(solved_odbs[1], multi_odb_path)

    all_eri = {}
    all_avg = {}
    evol_dict = {}

    for path in solved_odbs:
        o = odbAccess.openOdb(path, readOnly=True)
        step = o.steps["RECOVERY_STEP"]
        f = step.frames[-1]
        eri = f.fieldOutputs["MISESERI"]
        avg = f.fieldOutputs["MISESAVG"]
        ev = f.fieldOutputs["EVOL"]
        for v in eri.values:
            all_eri.setdefault(v.elementLabel, []).append(float(v.data))
        for v in avg.values:
            all_avg.setdefault(v.elementLabel, []).append(float(v.data))
        for v in ev.values:
            evol_dict[v.elementLabel] = float(v.data)
        o.close()

    elem_labels = sorted(all_eri.keys())
    env_eri = tuple([[max(all_eri[el])] for el in elem_labels])
    env_avg = tuple([[sum(all_avg[el]) / float(len(all_avg[el]))] for el in elem_labels])
    env_evol = tuple([[evol_dict[el]] for el in elem_labels])

    odb_multi = odbAccess.openOdb(multi_odb_path, readOnly=False)
    step_multi = odb_multi.steps["RECOVERY_STEP"]
    inst_multi = list(odb_multi.rootAssembly.instances.values())[0]

    env_frame = step_multi.Frame(frameId=2, frameValue=1.0, description="Multi-State Maximum Error Envelope (States 1-4)")
    fo_evol = env_frame.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)
    fo_evol.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_evol)

    fo_eri = env_frame.FieldOutput(name='MISESERI', description='Multi-state maximum MISESERI', type=SCALAR)
    fo_eri.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_eri)

    fo_avg = env_frame.FieldOutput(name='MISESAVG', description='Mean domain MISESAVG', type=SCALAR)
    fo_avg.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_avg)

    odb_multi.save()
    odb_multi.close()

    odb_size = os.path.getsize(multi_odb_path)
    odb_sha = sha256_file(multi_odb_path)
    print("Created Case 2 Multi-State Recovery Donor: %s" % multi_odb_path)
    print("  Size:   %d bytes" % odb_size)
    print("  SHA256: %s" % odb_sha)

    return multi_odb_path, odb_size, odb_sha


# ==============================================================================
# 2. CASE 3 MULTI-STATE RECOVERY SOLVER & ENVELOPE BUILDER
# ==============================================================================

def build_case3_multistate_donor():
    import odbAccess
    from abaqusConstants import SCALAR, WHOLE_ELEMENT

    print("\n" + "="*80)
    print("BUILDING CASE 3 MULTI-STATE RECOVERY DONOR (METHOD A.2)")
    print("="*80)

    c3_dir = os.path.join(F1809_BASE, "case3")
    if not os.path.exists(c3_dir):
        os.makedirs(c3_dir)

    phys_inp_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1", "PK_SEC43_STAGGERED_PHYS.inp")
    record_json_path = os.path.join(REPO_ROOT, "results", "validation", "f1694_sec43_five_state_damage_record.json")

    with open(record_json_path, "r") as f:
        rec_data = json.load(f)

    # Parse base mesh
    nodes = []
    quads = []
    tris = []
    in_node = in_elem = False
    elem_type = ""
    with open(phys_inp_path, "r") as f:
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
                    in_node = in_elem = False
                continue
            if in_node:
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 3:
                    nodes.append((int(p[0]), float(p[1]), float(p[2])))
            elif in_elem:
                p = [int(x.strip()) for x in l.split(",")]
                eid = p[0]
                conn = p[1:]
                if len(conn) == 4 or elem_type == "CPE4":
                    quads.append((eid, conn))
                elif len(conn) == 3 or elem_type == "CPE3":
                    tris.append((eid, conn))

    lower_nodes = []
    upper_nodes = []
    for nid, x, y in nodes:
        if abs(math.hypot(x - 20.0, y - 20.0) - 5.0) <= 0.08:
            lower_nodes.append(nid)
        if abs(math.hypot(x - 20.0, y - 100.0) - 5.0) <= 0.08:
            upper_nodes.append(nid)

    print("Parsed Case 3 physical mesh: %d nodes, %d elements (3679 quads, 244 tris)" % (len(nodes), len(quads) + len(tris)))

    # Sample States:
    # State 1: state_a (Initiation, uy = 0.100 mm)
    # State 2: state_b (Hole Arrest, uy = 0.200 mm)
    # State 3: state_d (Secondary Propagation, uy = 0.300 mm)
    target_states = [
        {"name": "state1_initiation", "idx": 0, "uy": 0.100, "label": "State 1 Initiation (uy=0.100 mm)"},
        {"name": "state2_hole_arrest", "idx": 1, "uy": 0.200, "label": "State 2 Hole Arrest (uy=0.200 mm)"},
        {"name": "state3_propagation", "idx": 3, "uy": 0.300, "label": "State 3 Secondary Propagation (uy=0.300 mm)"}
    ]

    solved_odbs = []
    for s_info in target_states:
        s_data = rec_data["states"][s_info["idx"]]
        d_elem = {int(k): float(v) for k, v in s_data["damage_by_element"].items()}
        uy_val = float(s_info["uy"])

        job_name = "SEC43_C3_" + s_info["name"].upper()
        inp_path = os.path.join(c3_dir, job_name + ".inp")
        odb_path = os.path.join(c3_dir, job_name + ".odb")
        sta_path = os.path.join(c3_dir, job_name + ".sta")

        already_solved = False
        if os.path.exists(odb_path) and os.path.exists(sta_path):
            with open(sta_path, "r") as f_sta:
                if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in f_sta.read():
                    already_solved = True

        if not already_solved:
            print("  Writing recovery deck: %s (%s)" % (inp_path, s_info["label"]))
            E0 = 210.0  # kN/mm^2
            nu = 0.30
            k_res = 1.0e-7
            rp_nid = 999999

            with open(inp_path, "w") as f_out:
                f_out.write("*HEADING\nCase 3 High-Fidelity Recovery: %s\n" % s_info["label"])
                f_out.write("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO\n\n")

                f_out.write("*NODE\n")
                for nid, x, y in nodes:
                    f_out.write("%d, %.9e, %.9e\n" % (nid, x, y))
                f_out.write("%d, 2.000000000e+01, 1.000000000e+02\n" % rp_nid)

                if quads:
                    f_out.write("*ELEMENT, TYPE=CPE4, ELSET=QUAD_ELEMS\n")
                    for eid, conn in quads:
                        f_out.write("%d, %s\n" % (eid, ", ".join(str(c) for c in conn)))
                if tris:
                    f_out.write("*ELEMENT, TYPE=CPE3, ELSET=TRI_ELEMS\n")
                    for eid, conn in tris:
                        f_out.write("%d, %s\n" % (eid, ", ".join(str(c) for c in conn)))

                f_out.write("*ELSET, ELSET=All_elem\nQUAD_ELEMS\nTRI_ELEMS\n")

                def write_nset(name, nids):
                    f_out.write("*NSET, NSET=%s\n" % name)
                    for i in range(0, len(nids), 16):
                        f_out.write(", ".join(str(nid) for nid in nids[i:i+16]) + "\n")

                write_nset("N_LOWER_HOLE", lower_nodes)
                write_nset("N_UPPER_HOLE", upper_nodes)
                f_out.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

                all_eids = [eid for eid, _ in quads] + [eid for eid, _ in tris]
                all_eids.sort()
                for eid in all_eids:
                    d_val = d_elem.get(eid, 0.0)
                    d_clamped = max(0.0, min(1.0, d_val))
                    g_d = (1.0 - d_clamped)**2 + k_res
                    E_deg = E0 * g_d
                    elset_name = "EL_%d" % eid
                    mat_name = "MAT_%d" % eid
                    f_out.write("*ELSET, ELSET=%s\n%d\n" % (elset_name, eid))
                    f_out.write("*SOLID SECTION, ELSET=%s, MATERIAL=%s\n1.0\n" % (elset_name, mat_name))
                    f_out.write("*MATERIAL, NAME=%s\n" % mat_name)
                    f_out.write("*ELASTIC, TYPE=ISOTROPIC\n%.10e, %.4f\n" % (E_deg, nu))

                f_out.write("** Tie upper hole to RP\n")
                for nid in upper_nodes:
                    f_out.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

                f_out.write("*STEP, NAME=RECOVERY_STEP, NLGEOM=NO\n")
                f_out.write("*STATIC\n1.0, 1.0, 1.0, 1.0\n")
                f_out.write("*BOUNDARY\n")
                f_out.write("N_LOWER_HOLE, 1, 2, 0.0\n")
                f_out.write("N_UPPER_HOLE, 1, 1, 0.0\n")
                f_out.write("N_RP, 2, 2, %.4f\n" % uy_val)

                f_out.write("*OUTPUT, FIELD\n")
                f_out.write("*ELEMENT OUTPUT, ELSET=All_elem\n")
                f_out.write("MISESERI, MISESAVG, EVOL, S, E\n")
                f_out.write("*NODE OUTPUT\nU, RF\n")
                f_out.write("*END STEP\n")

            print("  Solving %s via Abaqus standard..." % job_name)
            cmd = "%s job=%s interactive ask_delete=OFF" % (ABAQUS_BAT, job_name)
            subprocess.call(cmd, cwd=c3_dir, shell=True)

            with open(sta_path, "r") as f_sta:
                assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in f_sta.read(), "Abaqus solve failed for %s" % job_name

            odb_check = odbAccess.openOdb(odb_path, readOnly=False)
            inst = list(odb_check.rootAssembly.instances.values())[0]
            if "ALL_ELEM" not in inst.elementSets:
                inst.ElementSetFromElementLabels(name="ALL_ELEM", elementLabels=[e.label for e in inst.elements])
                odb_check.save()
            odb_check.close()
            print("  Solve complete: %s (%d bytes)" % (odb_path, os.path.getsize(odb_path)))

        solved_odbs.append(odb_path)

    # Build Envelope ODB
    print("\nSynthesizing Case 3 Multi-State Maximum Error Envelope across %d states..." % len(solved_odbs))
    multi_odb_path = os.path.join(c3_dir, "SEC43_MULTISTATE_RECOVERY.odb")
    if os.path.exists(multi_odb_path):
        os.remove(multi_odb_path)

    shutil.copyfile(solved_odbs[1], multi_odb_path)

    all_eri = {}
    all_avg = {}
    evol_dict = {}

    for path in solved_odbs:
        o = odbAccess.openOdb(path, readOnly=True)
        step = o.steps["RECOVERY_STEP"]
        f = step.frames[-1]
        eri = f.fieldOutputs["MISESERI"]
        avg = f.fieldOutputs["MISESAVG"]
        ev = f.fieldOutputs["EVOL"]
        for v in eri.values:
            all_eri.setdefault(v.elementLabel, []).append(float(v.data))
        for v in avg.values:
            all_avg.setdefault(v.elementLabel, []).append(float(v.data))
        for v in ev.values:
            evol_dict[v.elementLabel] = float(v.data)
        o.close()

    elem_labels = sorted(all_eri.keys())
    env_eri = tuple([[max(all_eri[el])] for el in elem_labels])
    env_avg = tuple([[sum(all_avg[el]) / float(len(all_avg[el]))] for el in elem_labels])
    env_evol = tuple([[evol_dict[el]] for el in elem_labels])

    odb_multi = odbAccess.openOdb(multi_odb_path, readOnly=False)
    step_multi = odb_multi.steps["RECOVERY_STEP"]
    inst_multi = list(odb_multi.rootAssembly.instances.values())[0]

    env_frame = step_multi.Frame(frameId=2, frameValue=1.0, description="Multi-State Maximum Error Envelope (States 1-3)")
    fo_evol = env_frame.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)
    fo_evol.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_evol)

    fo_eri = env_frame.FieldOutput(name='MISESERI', description='Multi-state maximum MISESERI', type=SCALAR)
    fo_eri.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_eri)

    fo_avg = env_frame.FieldOutput(name='MISESAVG', description='Mean domain MISESAVG', type=SCALAR)
    fo_avg.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_avg)

    odb_multi.save()
    odb_multi.close()

    odb_size = os.path.getsize(multi_odb_path)
    odb_sha = sha256_file(multi_odb_path)
    print("Created Case 3 Multi-State Recovery Donor: %s" % multi_odb_path)
    print("  Size:   %d bytes" % odb_size)
    print("  SHA256: %s" % odb_sha)

    return multi_odb_path, odb_size, odb_sha


if __name__ == "__main__":
    c2_odb, c2_size, c2_sha = build_case2_multistate_donor()
    c3_odb, c3_size, c3_sha = build_case3_multistate_donor()
    print("\n" + "="*80)
    print("ALL MULTI-STATE RECOVERY DONORS BUILT SUCCESSFULLY!")
    print("  Case 2 Donor: %s (%d bytes, SHA-256 %s)" % (c2_odb, c2_size, c2_sha))
    print("  Case 3 Donor: %s (%d bytes, SHA-256 %s)" % (c3_odb, c3_size, c3_sha))
    print("="*80)
