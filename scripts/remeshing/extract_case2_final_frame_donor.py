# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_case2_final_frame_donor.py
===================================================
Task F1840: Extracts the untouched native fields from the FINAL converged frame
(Step-2 Frame 337, Increment 338, Step Time 0.655825 s, d_max=0.9976) of
PK_HOLE_COARSE_F1838_PILOT.odb into a compact standalone donor ODB
PK_F1840_CASE2_FINAL_FRAME_DONOR.odb for single-pass native remeshing.

Performs and records field-by-field fidelity checks between source companion
elements and extracted physical elements.
"""
from __future__ import print_function
import os
import sys
import json
import shutil
import hashlib
import odbAccess
from abaqusConstants import SCALAR, WHOLE_ELEMENT

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    src_path = "PK_HOLE_COARSE_F1838_PILOT.odb"
    tpl_path = "template.odb"
    tgt_path = "PK_F1840_CASE2_FINAL_FRAME_DONOR.odb"
    fidx = 337

    if len(sys.argv) > 1:
        fidx = int(sys.argv[1])
    if len(sys.argv) > 2:
        tgt_path = sys.argv[2]
    if len(sys.argv) > 3:
        src_path = sys.argv[3]
    if len(sys.argv) > 4:
        tpl_path = sys.argv[4]

    print("=" * 80)
    print("TASK F1840: EXTRACTING FINAL CONVERGED FRAME NATIVE DONOR ODB")
    print("Source ODB:   %s" % src_path)
    print("Template ODB: %s" % tpl_path)
    print("Target ODB:   %s" % tgt_path)
    print("Step: Step-2, Target Frame Index: %d" % fidx)
    print("=" * 80)

    assert os.path.exists(src_path), "Missing source ODB: %s" % src_path
    assert os.path.exists(tpl_path), "Missing template ODB: %s" % tpl_path

    # 1. Read source fields from Step-2 Frame fidx
    src_odb = odbAccess.openOdb(src_path, readOnly=True)
    step = src_odb.steps["Step-2"]
    total_frames = len(step.frames)
    print("Step-2 total frames: %d" % total_frames)
    assert fidx < total_frames, "Requested frame %d exceeds total frames %d" % (fidx, total_frames)

    fr = step.frames[fidx]
    frame_val = float(fr.frameValue)
    desc = fr.description
    print("Source frame description: '%s', time: %.6f" % (desc, frame_val))

    eri_fo = fr.fieldOutputs["MISESERI"]
    avg_fo = fr.fieldOutputs["MISESAVG"]
    sdv_fo = fr.fieldOutputs.get("SDV1", None) if hasattr(fr.fieldOutputs, "get") else (fr.fieldOutputs["SDV1"] if "SDV1" in fr.fieldOutputs else None)

    eri_raw = {v.elementLabel: float(v.data) for v in eri_fo.values}
    avg_raw = {v.elementLabel: float(v.data) for v in avg_fo.values}
    sdv_raw = {v.elementLabel: float(v.data) for v in sdv_fo.values} if sdv_fo else {}

    src_odb.close()

    # 2. In 3-layer deck, companion UMAT elements are 5813 to 8718 (offset = 5812)
    # Physical element p (1..2906) corresponds to UMAT companion element 5812 + p
    n_phys = 2906
    offset = 5812
    elem_labels = list(range(1, n_phys + 1))

    # Read EVOL from template Frame 0
    tpl_odb = odbAccess.openOdb(tpl_path, readOnly=True)
    tpl_step = tpl_odb.steps[list(tpl_odb.steps.keys())[0]]
    evol_fo = tpl_step.frames[0].fieldOutputs["EVOL"]
    evol_dict = {v.elementLabel: float(v.data) for v in evol_fo.values}
    tpl_odb.close()

    eri_data = []
    avg_data = []
    evol_data = []
    sdv_data = []

    missing_count = 0
    for p in elem_labels:
        umat_el = offset + p
        if umat_el in eri_raw:
            eri_data.append([eri_raw[umat_el]])
            avg_data.append([avg_raw[umat_el]])
            evol_data.append([evol_dict.get(p, 1.0)])
            if sdv_raw:
                sdv_data.append([sdv_raw.get(umat_el, 0.0)])
        else:
            missing_count += 1
            eri_data.append([0.0])
            avg_data.append([1.0])
            evol_data.append([1.0])
            if sdv_raw:
                sdv_data.append([0.0])

    print("Mapped %d physical elements from companion elements (missing: %d)" % (n_phys, missing_count))
    assert missing_count == 0, "Mapping error: companion elements missing!"

    # 3. Replicate template ODB and write Frame 2
    if os.path.exists(tgt_path):
        os.remove(tgt_path)
    shutil.copyfile(tpl_path, tgt_path)

    tgt_odb = odbAccess.openOdb(tgt_path, readOnly=False)
    tgt_step = tgt_odb.steps[list(tgt_odb.steps.keys())[0]]
    tgt_inst = list(tgt_odb.rootAssembly.instances.values())[0]

    # Frame index in donor ODB: Frame 2 (matching Frame 300 pilot donor structure)
    frame_id = len(tgt_step.frames)
    new_frame = tgt_step.Frame(
        frameId=frame_id,
        frameValue=frame_val,
        description="Case 2 Final Evolved Native Donor Frame %d (Step-2, t=%.6f s, untouched native fields)" % (fidx, frame_val)
    )

    fo_eri = new_frame.FieldOutput(name='MISESERI', description='Untouched native MISESERI stress recovery error', type=SCALAR)
    fo_eri.addData(position=WHOLE_ELEMENT, instance=tgt_inst, labels=elem_labels, data=tuple(eri_data))

    fo_avg = new_frame.FieldOutput(name='MISESAVG', description='Untouched native MISESAVG mean stress', type=SCALAR)
    fo_avg.addData(position=WHOLE_ELEMENT, instance=tgt_inst, labels=elem_labels, data=tuple(avg_data))

    fo_ev = new_frame.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)
    fo_ev.addData(position=WHOLE_ELEMENT, instance=tgt_inst, labels=elem_labels, data=tuple(evol_data))

    if sdv_data:
        fo_sdv = new_frame.FieldOutput(name='SDV1', description='Phase field damage d', type=SCALAR)
        fo_sdv.addData(position=WHOLE_ELEMENT, instance=tgt_inst, labels=elem_labels, data=tuple(sdv_data))

    tgt_odb.save()
    tgt_odb.close()

    sz = os.path.getsize(tgt_path)
    tgt_sha = sha256_file(tgt_path)
    print("Successfully created standalone native donor ODB: %s" % tgt_path)
    print("  Size:    %d bytes" % sz)
    print("  SHA-256: %s" % tgt_sha)

    # 4. Field-by-field fidelity audit
    print("\nExecuting field-by-field fidelity audit...")
    verify_odb = odbAccess.openOdb(tgt_path, readOnly=True)
    v_step = verify_odb.steps[list(verify_odb.steps.keys())[0]]
    v_fr = v_step.frames[-1]

    v_eri = {v.elementLabel: float(v.data) for v in v_fr.fieldOutputs["MISESERI"].values}
    v_avg = {v.elementLabel: float(v.data) for v in v_fr.fieldOutputs["MISESAVG"].values}
    v_ev = {v.elementLabel: float(v.data) for v in v_fr.fieldOutputs["EVOL"].values}
    v_sdv = {v.elementLabel: float(v.data) for v in v_fr.fieldOutputs["SDV1"].values} if "SDV1" in v_fr.fieldOutputs else {}
    verify_odb.close()

    max_diff_eri = 0.0
    max_diff_avg = 0.0
    max_diff_sdv = 0.0

    for p in elem_labels:
        umat_el = offset + p
        d_eri = abs(v_eri[p] - eri_raw[umat_el])
        d_avg = abs(v_avg[p] - avg_raw[umat_el])
        if d_eri > max_diff_eri: max_diff_eri = d_eri
        if d_avg > max_diff_avg: max_diff_avg = d_avg
        if sdv_raw:
            d_sdv = abs(v_sdv[p] - sdv_raw[umat_el])
            if d_sdv > max_diff_sdv: max_diff_sdv = d_sdv

    # Scale-invariant eta
    s_dummy = 4.7619047619e-14
    eri_max = max(v_eri.values())
    eri_min = min(v_eri.values())
    avg_max = max(v_avg.values())
    avg_min = min(v_avg.values())
    d_max = max(v_sdv.values()) if v_sdv else 0.0

    eta_values = {p: (v_eri[p] / v_avg[p]) if v_avg[p] > 0 else 0.0 for p in elem_labels}
    eta_max = max(eta_values.values())
    eta_mean = sum(eta_values.values()) / len(eta_values)

    # Physical stress values (1 kN/mm^2 = 1000 MPa)
    phys_eri_max = (eri_max / s_dummy) * 1e3  # MPa
    phys_avg_max = (avg_max / s_dummy) * 1e3  # MPa

    # Distal elements over target
    # Load nodal coordinates to evaluate distal region
    distal_over = 0
    total_over = 0
    for p, eta in eta_values.items():
        if eta >= 0.040:
            total_over += 1

    print("Field Fidelity Check Results:")
    print("  Max |diff(MISESERI)|: %.4e (Exact Match: %s)" % (max_diff_eri, max_diff_eri == 0.0))
    print("  Max |diff(MISESAVG)|: %.4e (Exact Match: %s)" % (max_diff_avg, max_diff_avg == 0.0))
    print("  Max |diff(SDV1)|:     %.4e (Exact Match: %s)" % (max_diff_sdv, max_diff_sdv == 0.0))
    print("  Physical eri_max:     %.2f MPa (dummy: %.4e)" % (phys_eri_max, eri_max))
    print("  Physical avg_max:     %.2f MPa (dummy: %.4e)" % (phys_avg_max, avg_max))
    print("  Max eta:              %.2f%%" % (eta_max * 100))
    print("  Mean eta:             %.2f%%" % (eta_mean * 100))
    print("  Elements with eta>=4%%: %d / %d" % (total_over, n_phys))
    print("  Peak damage d_max:    %.4f" % d_max)

    audit_data = {
        "task_id": "F1840-CASE2-FINAL-FRAME-REMESH-COMPARISON",
        "source_odb": src_path,
        "target_donor_odb": tgt_path,
        "target_donor_sha256": tgt_sha,
        "target_donor_size_bytes": sz,
        "source_step": "Step-2",
        "source_frame_idx": fidx,
        "source_frame_time": frame_val,
        "source_frame_description": desc,
        "total_elements": n_phys,
        "companion_offset": offset,
        "field_fidelity": {
            "max_abs_diff_miseseri": max_diff_eri,
            "max_abs_diff_misesavg": max_diff_avg,
            "max_abs_diff_sdv1": max_diff_sdv,
            "exact_match": (max_diff_eri == 0.0 and max_diff_avg == 0.0 and max_diff_sdv == 0.0)
        },
        "field_metrics": {
            "d_max": d_max,
            "dummy_eri_max": eri_max,
            "dummy_eri_min": eri_min,
            "dummy_avg_max": avg_max,
            "dummy_avg_min": avg_min,
            "scaling_factor_s": s_dummy,
            "physical_eri_max_mpa": phys_eri_max,
            "physical_avg_max_mpa": phys_avg_max,
            "eta_max_pct": eta_max * 100.0,
            "eta_mean_pct": eta_mean * 100.0,
            "elements_over_4pct_target": total_over
        }
    }

    with open("f1840_extraction_fidelity_audit.json", "w") as f:
        json.dump(audit_data, f, indent=2)
    print("Fidelity audit saved to f1840_extraction_fidelity_audit.json")

if __name__ == "__main__":
    main()
