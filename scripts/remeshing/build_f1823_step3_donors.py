# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_f1823_step3_donors.py
============================================
Synthesizes the 6 targeted donor ODBs for Step 3 using abaqus python:
  - Case 2:
      c2_omit_s1: States 2, 3, 4
      c2_omit_s3: States 1, 2, 4
      c2_omit_s4: States 1, 2, 3
  - Case 3:
      c3_omit_s1: States 2, 3
      c3_omit_s2: States 1, 3
      c3_omit_s3: States 1, 2
"""
from __future__ import print_function
import os
import sys
import shutil
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.path.join(REPO_ROOT, "scripts", "remeshing") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "remeshing"))

import odbAccess
from abaqusConstants import SCALAR, WHOLE_ELEMENT

STEP3_BASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "267_f1823_investigation", "step3_donors")
DONOR_DIR = os.path.join(STEP3_BASE_DIR, "donors")

C2_SRC_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2")
C3_SRC_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3")

def py_sum(iterable, start=0.0):
    total = start
    for item in iterable:
        total += item
    return total

def synthesize_custom_envelope_odb(solved_odbs, target_odb_path, step_name='RECOVERY_STEP', frame_desc="Multi-State Maximum Error Envelope"):
    target_dir = os.path.dirname(target_odb_path)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if os.path.exists(target_odb_path):
        os.remove(target_odb_path)

    shutil.copyfile(solved_odbs[0], target_odb_path)

    all_eri = {}
    all_avg = {}
    evol_dict = {}

    for path in solved_odbs:
        o = odbAccess.openOdb(path, readOnly=True)
        if step_name not in o.steps:
            avail = list(o.steps.keys())
            o.close()
            raise KeyError("FAIL_CLOSED: Step '%s' not found in '%s' (available: %s)" % (step_name, path, avail))
        step = o.steps[step_name]
        f = step.frames[-1]
        if "MISESERI" not in f.fieldOutputs or "MISESAVG" not in f.fieldOutputs:
            avail_f = list(f.fieldOutputs.keys())
            o.close()
            raise KeyError("FAIL_CLOSED: Required error fields missing in '%s' (available: %s)" % (path, avail_f))
        eri = f.fieldOutputs["MISESERI"]
        avg = f.fieldOutputs["MISESAVG"]
        if "EVOL" in f.fieldOutputs:
            ev = f.fieldOutputs["EVOL"]
        else:
            ev = None
        for v in eri.values:
            all_eri.setdefault(v.elementLabel, []).append(float(v.data))
        for v in avg.values:
            all_avg.setdefault(v.elementLabel, []).append(float(v.data))
        if ev is not None:
            for v in ev.values:
                evol_dict[v.elementLabel] = float(v.data)
        o.close()

    elem_labels = sorted(all_eri.keys())
    env_eri = tuple([[max(all_eri[el])] for el in elem_labels])
    env_avg = tuple([[py_sum(all_avg[el]) / float(len(all_avg[el]))] for el in elem_labels])

    odb_multi = odbAccess.openOdb(target_odb_path, readOnly=False)
    step_multi = odb_multi.steps[step_name]
    inst_multi = list(odb_multi.rootAssembly.instances.values())[0]

    env_frame_id = len(step_multi.frames)
    env_frame = step_multi.Frame(frameId=env_frame_id, frameValue=1.0, description=frame_desc)

    if evol_dict:
        env_evol = tuple([[evol_dict.get(el, 1.0)] for el in elem_labels])
        fo_evol = env_frame.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)
        fo_evol.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_evol)

    fo_eri = env_frame.FieldOutput(name='MISESERI', description='Multi-state maximum MISESERI', type=SCALAR)
    fo_eri.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_eri)

    fo_avg = env_frame.FieldOutput(name='MISESAVG', description='Mean domain MISESAVG', type=SCALAR)
    fo_avg.addData(position=WHOLE_ELEMENT, instance=inst_multi, labels=elem_labels, data=env_avg)

    odb_multi.save()
    odb_multi.close()

    print("  -> Successfully synthesized: %s (%d bytes)" % (os.path.basename(target_odb_path), os.path.getsize(target_odb_path)))
    return target_odb_path

def main():
    if not os.path.exists(DONOR_DIR):
        os.makedirs(DONOR_DIR)

    c2_s1 = os.path.join(C2_SRC_DIR, "PK_C2_STATE1_PREANALYSIS.odb")
    c2_s2 = os.path.join(C2_SRC_DIR, "PK_C2_STATE2_HOLE_ARREST.odb")
    c2_s3 = os.path.join(C2_SRC_DIR, "PK_C2_STATE3_DISTAL_NUCLEATION.odb")
    c2_s4 = os.path.join(C2_SRC_DIR, "PK_C2_STATE4_OUTER_PROPAGATION.odb")
    
    c3_s1 = os.path.join(C3_SRC_DIR, "SEC43_C3_STATE1_INITIATION.odb")
    c3_s2 = os.path.join(C3_SRC_DIR, "SEC43_C3_STATE2_HOLE_ARREST.odb")
    c3_s3 = os.path.join(C3_SRC_DIR, "SEC43_C3_STATE3_PROPAGATION.odb")

    print("Synthesizing Case 2 donors...")
    p_c2_omit_s1 = os.path.join(DONOR_DIR, "PK_C2_DONOR_OMIT_S1.odb")
    synthesize_custom_envelope_odb([c2_s2, c2_s3, c2_s4], p_c2_omit_s1, frame_desc="Case 2 Envelope Omit State 1 (States 2, 3, 4)")

    p_c2_omit_s3 = os.path.join(DONOR_DIR, "PK_C2_DONOR_OMIT_S3.odb")
    synthesize_custom_envelope_odb([c2_s1, c2_s2, c2_s4], p_c2_omit_s3, frame_desc="Case 2 Envelope Omit State 3 (States 1, 2, 4)")

    p_c2_omit_s4 = os.path.join(DONOR_DIR, "PK_C2_DONOR_OMIT_S4.odb")
    synthesize_custom_envelope_odb([c2_s1, c2_s2, c2_s3], p_c2_omit_s4, frame_desc="Case 2 Envelope Omit State 4 (States 1, 2, 3)")

    print("Synthesizing Case 3 donors...")
    p_c3_omit_s1 = os.path.join(DONOR_DIR, "SEC43_C3_DONOR_OMIT_S1.odb")
    synthesize_custom_envelope_odb([c3_s2, c3_s3], p_c3_omit_s1, frame_desc="Case 3 Envelope Omit State 1 (States 2, 3)")

    p_c3_omit_s2 = os.path.join(DONOR_DIR, "SEC43_C3_DONOR_OMIT_S2.odb")
    synthesize_custom_envelope_odb([c3_s1, c3_s3], p_c3_omit_s2, frame_desc="Case 3 Envelope Omit State 2 (States 1, 3)")

    p_c3_omit_s3 = os.path.join(DONOR_DIR, "SEC43_C3_DONOR_OMIT_S3.odb")
    synthesize_custom_envelope_odb([c3_s1, c3_s2], p_c3_omit_s3, frame_desc="Case 3 Envelope Omit State 3 (States 1, 2)")

    print("\nAll 6 donors successfully synthesized!")

if __name__ == "__main__":
    main()
