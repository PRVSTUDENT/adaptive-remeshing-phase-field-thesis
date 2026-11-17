# -*- coding: utf-8 -*-
"""
scripts/remeshing/create_case2_pilot_single_frame_donor.py
==========================================================
Extracts the untouched native fields from an explicitly identified evolved frame
(e.g. Frame 300, Increment 300, Step-2, Step Time 0.5937 s) of PK_HOLE_COARSE_F1838_PILOT.odb
into a compact 7 MB standalone donor ODB for single-pass native remeshing.
"""
from __future__ import print_function
import os
import sys
import shutil
import odbAccess
from abaqusConstants import SCALAR, WHOLE_ELEMENT

def main():
    src_path = "PK_HOLE_COARSE_F1838_PILOT.odb"
    tpl_path = "template.odb"
    tgt_path = "PK_F1838_CASE2_FRAME300_DONOR.odb"
    fidx = 300
    
    if len(sys.argv) > 1:
        fidx = int(sys.argv[1])
    if len(sys.argv) > 2:
        tgt_path = sys.argv[2]
        
    print("="*80)
    print("CREATING NATIVE UNTOUCHED SINGLE-FRAME DONOR ODB")
    print("Source: %s, Step: Step-2, Frame: %d" % (src_path, fidx))
    print("Target: %s (using template %s)" % (tgt_path, tpl_path))
    print("="*80)
    
    # 1. Read fields from source ODB
    src_odb = odbAccess.openOdb(src_path, readOnly=True)
    step = src_odb.steps["Step-2"]
    fr = step.frames[fidx]
    frame_val = float(fr.frameValue)
    desc = fr.description
    print("Source frame description: '%s', time: %.4f" % (desc, frame_val))
    
    eri_fo = fr.fieldOutputs["MISESERI"]
    avg_fo = fr.fieldOutputs["MISESAVG"]
    evol_fo = fr.fieldOutputs["EVOL"] if "EVOL" in fr.fieldOutputs else None
    sdv_fo  = fr.fieldOutputs["SDV1"] if "SDV1" in fr.fieldOutputs else None
    
    # In 3-layer deck, UMAT companion elements are 5813 to 8718 (offset = 5812)
    # Physical element p (1..2906) corresponds to UMAT companion element 5812 + p
    n_phys = 2906
    offset = 5812
    
    eri_raw = {v.elementLabel: float(v.data) for v in eri_fo.values}
    avg_raw = {v.elementLabel: float(v.data) for v in avg_fo.values}
    evol_raw = {v.elementLabel: float(v.data) for v in evol_fo.values} if evol_fo else {}
    sdv_raw  = {v.elementLabel: float(v.data) for v in sdv_fo.values} if sdv_fo else {}
    
    src_odb.close()
    
    elem_labels = list(range(1, n_phys + 1))
    eri_data = []
    avg_data = []
    evol_data = []
    sdv_data  = []
    
    # Audit mapping
    missing_count = 0
    for p in elem_labels:
        umat_el = offset + p
        if umat_el in eri_raw:
            eri_data.append([eri_raw[umat_el]])
            avg_data.append([avg_raw[umat_el]])
            if evol_raw:
                evol_data.append([evol_raw.get(umat_el, 1.0)])
            if sdv_raw:
                sdv_data.append([sdv_raw.get(umat_el, 0.0)])
        else:
            missing_count += 1
            eri_data.append([0.0])
            avg_data.append([1.0])
            if evol_raw: evol_data.append([1.0])
            if sdv_raw: sdv_data.append([0.0])
            
    print("Mapped %d physical elements from companion elements (missing: %d)" % (n_phys, missing_count))
    assert missing_count == 0, "Mapping error: companion elements missing!"
    
    # 2. Replicate template ODB
    if os.path.exists(tgt_path):
        os.remove(tgt_path)
    shutil.copyfile(tpl_path, tgt_path)
    
    tgt_odb = odbAccess.openOdb(tgt_path, readOnly=False)
    tgt_step = tgt_odb.steps[list(tgt_odb.steps.keys())[0]]
    tgt_inst = list(tgt_odb.rootAssembly.instances.values())[0]
    
    # Check existing frames
    frame_id = len(tgt_step.frames)
    new_frame = tgt_step.Frame(
        frameId=frame_id, 
        frameValue=frame_val, 
        description="Case 2 Evolved Native Donor Frame %d (Step-2, t=%.4f s, untouched native fields)" % (fidx, frame_val)
    )
    
    fo_eri = new_frame.FieldOutput(name='MISESERI', description='Untouched native MISESERI stress recovery error', type=SCALAR)
    fo_eri.addData(position=WHOLE_ELEMENT, instance=tgt_inst, labels=elem_labels, data=tuple(eri_data))
    
    fo_avg = new_frame.FieldOutput(name='MISESAVG', description='Untouched native MISESAVG mean stress', type=SCALAR)
    fo_avg.addData(position=WHOLE_ELEMENT, instance=tgt_inst, labels=elem_labels, data=tuple(avg_data))
    
    if evol_data:
        fo_ev = new_frame.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)
        fo_ev.addData(position=WHOLE_ELEMENT, instance=tgt_inst, labels=elem_labels, data=tuple(evol_data))
        
    if sdv_data:
        fo_sdv = new_frame.FieldOutput(name='SDV1', description='Phase field damage d', type=SCALAR)
        fo_sdv.addData(position=WHOLE_ELEMENT, instance=tgt_inst, labels=elem_labels, data=tuple(sdv_data))
        
    tgt_odb.save()
    tgt_odb.close()
    
    sz = os.path.getsize(tgt_path)
    print("Successfully created standalone native donor ODB: %s (%d bytes)" % (tgt_path, sz))

if __name__ == "__main__":
    main()
