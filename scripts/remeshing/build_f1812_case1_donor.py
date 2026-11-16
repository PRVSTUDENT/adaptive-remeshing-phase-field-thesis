# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_f1812_case1_donor.py
Task F1812: Case 1 Multi-State Sequential Recovery Donor Construction.

Reads authentic crack propagation states from results/validation/f1812_case1_damage_record.json,
builds and solves authentic degraded-modulus continuum recovery models in Abaqus/Standard,
and synthesizes the multi-state maximum error envelope ODB:
models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_CASE1_MULTISTATE_RECOVERY.odb
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

F1812_BASE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement")
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

def build_case1_multistate_donor(output_dir=None):
    import odbAccess
    from abaqusConstants import SCALAR, WHOLE_ELEMENT

    print("\n" + "="*80)
    print("BUILDING CASE 1 MULTI-STATE RECOVERY DONOR (METHOD A.2)")
    print("="*80)

    c1_dir = output_dir or os.path.join(F1812_BASE, "case1")
    if not os.path.exists(c1_dir):
        os.makedirs(c1_dir)

    record_json_path = os.path.join(REPO_ROOT, "results", "validation", "f1812_case1_damage_record.json")
    with open(record_json_path, "r") as f:
        data = json.load(f)

    nodes = data["nodes"]
    quads = data["quads"]
    tris = data["tris"]
    n_bottom = data["n_bottom"]
    n_pin = data["n_pin"]
    n_top = data["n_top"]
    states = data["states"]

    print("Parsed Case 1 base mesh: %d nodes, %d elements (%d quads, %d tris)" % (
        len(nodes), len(quads) + len(tris), len(quads), len(tris)
    ))
    print("Available authentic states: %d" % len(states))

    E0 = 210000.0  # MPa
    nu = 0.30
    k_res = 1.0e-7

    solved_odbs = []
    for s_info in states:
        s_name = s_info["name"]
        uy_val = float(s_info["uy_mm"])
        damage_dict = {int(k): float(v) for k, v in s_info["damage"].items()}

        job_name = "PK_C1_" + s_name.upper()
        inp_path = os.path.join(c1_dir, job_name + ".inp")
        odb_path = os.path.join(c1_dir, job_name + ".odb")
        sta_path = os.path.join(c1_dir, job_name + ".sta")

        already_solved = False
        if os.path.exists(odb_path) and os.path.exists(sta_path):
            with open(sta_path, "r") as f_sta:
                if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in f_sta.read():
                    already_solved = True

        if not already_solved:
            print("  Writing recovery deck: %s (uy=%.6f mm)" % (inp_path, uy_val))
            with open(inp_path, "w") as f_out:
                f_out.write("*HEADING\nCase 1 Degraded-Modulus Continuum Recovery: %s\n" % s_info["label"])
                f_out.write("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO\n\n")

                # Nodes
                f_out.write("*NODE\n")
                for nid_str, (x, y) in sorted(nodes.items(), key=lambda item: int(item[0])):
                    f_out.write("%s, %.9e, %.9e\n" % (nid_str, x, y))

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

                f_out.write("*STEP, NAME=RECOVERY_STEP, NLGEOM=NO\n")
                f_out.write("*STATIC\n1.0, 1.0, 1.0, 1.0\n")
                f_out.write("*BOUNDARY\n")
                f_out.write("N_BOTTOM, 2, 2, 0.0\n")
                f_out.write("N_PIN, 1, 1, 0.0\n")
                f_out.write("N_TOP, 1, 1, 0.0\n")
                f_out.write("N_TOP, 2, 2, %.6f\n" % uy_val)

                f_out.write("*OUTPUT, FIELD\n")
                f_out.write("*ELEMENT OUTPUT, ELSET=All_elem\n")
                f_out.write("MISESERI, MISESAVG, EVOL, S, E\n")
                f_out.write("*NODE OUTPUT\nU, RF\n")
                f_out.write("*END STEP\n")

            print("  Solving %s via Abaqus standard..." % job_name)
            cmd = "%s job=%s interactive ask_delete=OFF" % (ABAQUS_BAT, job_name)
            subprocess.call(cmd, cwd=c1_dir, shell=True)

            with open(sta_path, "r") as f_sta:
                assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in f_sta.read(), "Abaqus solve failed for %s" % job_name

            # Ensure ALL_ELEM exists on instance in ODB
            odb_check = odbAccess.openOdb(odb_path, readOnly=False)
            inst_obj = list(odb_check.rootAssembly.instances.values())[0]
            if "ALL_ELEM" not in inst_obj.elementSets:
                inst_obj.ElementSetFromElementLabels(name="ALL_ELEM", elementLabels=[e.label for e in inst_obj.elements])
                odb_check.save()
            odb_check.close()
            print("  Solve complete: %s (%d bytes)" % (odb_path, os.path.getsize(odb_path)))

        solved_odbs.append(odb_path)

    # Build Envelope ODB
    print("\nSynthesizing Case 1 Multi-State Maximum Error Envelope across %d states..." % len(solved_odbs))
    multi_odb_path = os.path.join(c1_dir, "PK_CASE1_MULTISTATE_RECOVERY.odb")
    if os.path.exists(multi_odb_path):
        os.remove(multi_odb_path)

    shutil.copyfile(solved_odbs[0], multi_odb_path)

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

    env_frame = step_multi.Frame(frameId=2, frameValue=1.0, description="Multi-State Maximum Error Envelope (States 1-5)")
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
    print("Created Case 1 Multi-State Recovery Donor: %s" % multi_odb_path)
    print("  Size:   %d bytes" % odb_size)
    print("  SHA256: %s" % odb_sha)

    return multi_odb_path, odb_size, odb_sha

if __name__ == "__main__":
    build_case1_multistate_donor()
