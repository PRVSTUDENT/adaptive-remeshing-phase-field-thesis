# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_f1816_step2_donors.py
============================================
Builds authentic donors for Step 2 of Task F1816:
  - Variant 2b (Reduced 2-State Envelope):
      Case 1: State 1 (initiation) + State 5 (terminal severance)
      Case 2: State 2 (hole arrest) + State 4 (outer propagation)
      Case 3: State 2 (hole arrest) + State 3 (secondary propagation)
  - Variant 2a (Per-State Overlapping Native Rules):
      Case 1: 5 distinct steps (STATE_1 to STATE_5)
      Case 2: 4 distinct steps (STATE_1 to STATE_4)
      Case 3: 3 distinct steps (STATE_1 to STATE_3)

Must be executed via: abaqus python scripts/remeshing/build_f1816_step2_donors.py
"""
from __future__ import print_function
import os
import sys
import shutil
import hashlib
import subprocess

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.path.join(REPO_ROOT, "scripts", "remeshing") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "remeshing"))

import odbAccess
from abaqusConstants import SCALAR, WHOLE_ELEMENT, TIME

from reusable_2d_adaptive_framework import MultiStateRecoveryDonorBuilder, py_sum

DONOR_BASE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step2_envelope", "donors")
C1_SRC_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1")
C2_SRC_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2")
C3_SRC_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3")

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

def ensure_c1_state_odbs():
    state_names = [
        "PK_C1_STATE1_INITIATION",
        "PK_C1_STATE2_EARLY_PROPAGATION",
        "PK_C1_STATE3_MID_PROPAGATION",
        "PK_C1_STATE4_OUTER_PROPAGATION",
        "PK_C1_STATE5_TERMINAL_SEVERANCE"
    ]
    solved_odbs = []
    for sname in state_names:
        odb_path = os.path.join(C1_SRC_DIR, sname + ".odb")
        inp_path = os.path.join(C1_SRC_DIR, sname + ".inp")
        sta_path = os.path.join(C1_SRC_DIR, sname + ".sta")
        
        if not os.path.exists(odb_path):
            print("Solving Case 1 state: %s..." % sname)
            cmd = [ABAQUS_BAT, "job=" + sname, "input=" + sname + ".inp", "interactive"]
            subprocess.call(cmd, cwd=C1_SRC_DIR, shell=True)
            
            with open(sta_path, "r") as f_sta:
                assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in f_sta.read(), "Solve failed for %s" % sname
                
            # Ensure ALL_ELEM exists
            o = odbAccess.openOdb(odb_path, readOnly=False)
            inst = list(o.rootAssembly.instances.values())[0]
            if "ALL_ELEM" not in inst.elementSets:
                inst.ElementSetFromElementLabels(name="ALL_ELEM", elementLabels=[e.label for e in inst.elements])
                o.save()
            o.close()
            print("  Solved: %s (%d bytes)" % (odb_path, os.path.getsize(odb_path)))
        else:
            # Check ALL_ELEM
            o = odbAccess.openOdb(odb_path, readOnly=False)
            inst = list(o.rootAssembly.instances.values())[0]
            if "ALL_ELEM" not in inst.elementSets:
                inst.ElementSetFromElementLabels(name="ALL_ELEM", elementLabels=[e.label for e in inst.elements])
                o.save()
            o.close()
        solved_odbs.append(odb_path)
    return solved_odbs

def build_multistep_rules_odb(solved_odbs, target_odb_path, step_prefix="STATE_"):
    """
    Builds an ODB where each authentic state lives in a separate step:
    STATE_1, STATE_2, ... with EVOL, MISESAVG, MISESERI.
    """
    if os.path.exists(target_odb_path):
        os.remove(target_odb_path)
        
    shutil.copyfile(solved_odbs[0], target_odb_path)
    o = odbAccess.openOdb(target_odb_path, readOnly=False)
    
    # Rename existing step to STATE_1
    first_step_name = list(o.steps.keys())[0]
    # In odbAccess, we cannot directly rename steps easily in all versions,
    # so we add new steps or copy frames.
    # Let's inspect step creation:
    inst = list(o.rootAssembly.instances.values())[0]
    
    # Read field values from all source ODBs
    all_step_data = []
    for idx, path in enumerate(solved_odbs):
        src_o = odbAccess.openOdb(path, readOnly=True)
        src_step = list(src_o.steps.values())[-1]
        src_frame = src_step.frames[-1]
        
        step_name = "%s%d" % (step_prefix, idx + 1)
        step_dict = {"name": step_name, "fields": {}}
        for fname in ["MISESERI", "MISESAVG", "EVOL"]:
            if fname in src_frame.fieldOutputs:
                fo = src_frame.fieldOutputs[fname]
                labels = [v.elementLabel for v in fo.values]
                data = tuple([[float(v.data)] for v in fo.values])
                desc = fo.description
                step_dict["fields"][fname] = (labels, data, desc)
        src_o.close()
        all_step_data.append(step_dict)
        
    # In target ODB, first step already exists (RECOVERY_STEP or Step-1).
    # We add new steps for idx >= 1, or recreate.
    # To be totally clean, let's keep the existing step as STATE_1 if possible,
    # or create STATE_1..STATE_K.
    # Note: Abaqus CAE RemeshingRule needs the stepName to match what's in the model!
    step_names = []
    for idx, sdata in enumerate(all_step_data):
        if idx == 0:
            s_name = first_step_name
            step_names.append(s_name)
            st = o.steps[first_step_name]
            f = st.frames[-1]
            for fname, (labels, data, desc) in sdata["fields"].items():
                if fname not in f.fieldOutputs:
                    new_fo = f.FieldOutput(name=fname, description=desc, type=SCALAR)
                    new_fo.addData(position=WHOLE_ELEMENT, instance=inst, labels=labels, data=data)
        else:
            s_name = sdata["name"]
            step_names.append(s_name)
            new_step = o.Step(name=s_name, description="Recovery state %d" % (idx+1), domain=TIME, timePeriod=1.0)
            f = new_step.Frame(frameId=0, frameValue=1.0, description="Frame 1")
            for fname, (labels, data, desc) in sdata["fields"].items():
                new_fo = f.FieldOutput(name=fname, description=desc, type=SCALAR)
                new_fo.addData(position=WHOLE_ELEMENT, instance=inst, labels=labels, data=data)
                
    o.save()
    o.close()
    print("Created multi-step ODB: %s (%d bytes, steps=%s)" % (target_odb_path, os.path.getsize(target_odb_path), step_names))
    return target_odb_path, step_names

def main():
    if not os.path.exists(DONOR_BASE):
        os.makedirs(DONOR_BASE)
        
    print("="*80)
    print("BUILDING STEP 2 DONORS (VARIANTS 2a AND 2b)")
    print("="*80)
    
    # 1. Case 1 state ODBs
    c1_odbs = ensure_c1_state_odbs()
    
    # 2. Case 2 state ODBs
    c2_odbs = [
        os.path.join(C2_SRC_DIR, "PK_C2_STATE1_PREANALYSIS.odb"),
        os.path.join(C2_SRC_DIR, "PK_C2_STATE2_HOLE_ARREST.odb"),
        os.path.join(C2_SRC_DIR, "PK_C2_STATE3_DISTAL_NUCLEATION.odb"),
        os.path.join(C2_SRC_DIR, "PK_C2_STATE4_OUTER_PROPAGATION.odb")
    ]
    for p in c2_odbs:
        assert os.path.exists(p), "Missing Case 2 donor: %s" % p
        
    # 3. Case 3 state ODBs
    c3_odbs = [
        os.path.join(C3_SRC_DIR, "SEC43_C3_STATE1_INITIATION.odb"),
        os.path.join(C3_SRC_DIR, "SEC43_C3_STATE2_HOLE_ARREST.odb"),
        os.path.join(C3_SRC_DIR, "SEC43_C3_STATE3_PROPAGATION.odb")
    ]
    for p in c3_odbs:
        assert os.path.exists(p), "Missing Case 3 donor: %s" % p
        
    # --- VARIANT 2b: REDUCED 2-STATE ENVELOPES ---
    print("\n--- Constructing Variant 2b: Reduced 2-State Envelopes ---")
    
    # Case 1: State 1 (initiation) + State 5 (terminal)
    c1_2b_path = os.path.join(DONOR_BASE, "PK_CASE1_2STATE_ENVELOPE.odb")
    MultiStateRecoveryDonorBuilder.synthesize_envelope_odb(
        solved_odbs=[c1_odbs[0], c1_odbs[4]],
        target_odb_path=c1_2b_path,
        step_name="RECOVERY_STEP",
        frame_desc="Case 1 Reduced 2-State Error Envelope (States 1 and 5)"
    )
    print("  Case 1 2-State Envelope: %s (%s)" % (c1_2b_path, sha256_file(c1_2b_path)))
    
    # Case 2: State 2 (hole arrest) + State 4 (outer propagation)
    c2_2b_path = os.path.join(DONOR_BASE, "PK_CASE2_2STATE_ENVELOPE.odb")
    MultiStateRecoveryDonorBuilder.synthesize_envelope_odb(
        solved_odbs=[c2_odbs[1], c2_odbs[3]],
        target_odb_path=c2_2b_path,
        step_name="RECOVERY_STEP",
        frame_desc="Case 2 Reduced 2-State Error Envelope (States 2 and 4)"
    )
    print("  Case 2 2-State Envelope: %s (%s)" % (c2_2b_path, sha256_file(c2_2b_path)))
    
    # Case 3: State 2 (hole arrest) + State 3 (secondary propagation)
    c3_2b_path = os.path.join(DONOR_BASE, "PK_CASE3_2STATE_ENVELOPE.odb")
    MultiStateRecoveryDonorBuilder.synthesize_envelope_odb(
        solved_odbs=[c3_odbs[1], c3_odbs[2]],
        target_odb_path=c3_2b_path,
        step_name="RECOVERY_STEP",
        frame_desc="Case 3 Reduced 2-State Error Envelope (States 2 and 3)"
    )
    print("  Case 3 2-State Envelope: %s (%s)" % (c3_2b_path, sha256_file(c3_2b_path)))
    
    # --- VARIANT 2a: MULTI-STEP RULES ODBS ---
    print("\n--- Constructing Variant 2a: Multi-Step Overlapping Rules ODBs ---")
    c1_2a_path = os.path.join(DONOR_BASE, "PK_CASE1_MULTISTEP_RULES.odb")
    build_multistep_rules_odb(c1_odbs, c1_2a_path, step_prefix="STATE_")
    print("  Case 1 Multi-Step Rules ODB: %s (%s)" % (c1_2a_path, sha256_file(c1_2a_path)))
    
    c2_2a_path = os.path.join(DONOR_BASE, "PK_CASE2_MULTISTEP_RULES.odb")
    build_multistep_rules_odb(c2_odbs, c2_2a_path, step_prefix="STATE_")
    print("  Case 2 Multi-Step Rules ODB: %s (%s)" % (c2_2a_path, sha256_file(c2_2a_path)))
    
    c3_2a_path = os.path.join(DONOR_BASE, "PK_CASE3_MULTISTEP_RULES.odb")
    build_multistep_rules_odb(c3_odbs, c3_2a_path, step_prefix="STATE_")
    print("  Case 3 Multi-Step Rules ODB: %s (%s)" % (c3_2a_path, sha256_file(c3_2a_path)))
    
    print("\nStep 2 donors successfully constructed!")

if __name__ == "__main__":
    main()
