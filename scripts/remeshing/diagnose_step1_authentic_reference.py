# -*- coding: utf-8 -*-
"""
scripts/remeshing/diagnose_step1_authentic_reference.py
======================================================
Audit all potential authentic direct UEL+UMAT donors across the repository:
1. models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb
2. runs/probe_case1_remesh/PK_CASE1_NATIVE_DONOR.odb
3. models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb
4. models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PREANALYSIS.odb
5. models/pandey_kumar_mode1/198_pk_sec43_coupled_validation/SEC43_COARSE_JOB1.odb (if exists)
"""
from __future__ import print_function
import os
import sys
import hashlib
import json
import odbAccess

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"

def compute_sha256(filepath):
    if not os.path.exists(filepath):
        return "MISSING"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

candidates = [
    {
        "id": "F1720_COARSE_COUPLED",
        "path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "PK_F1720_COARSE_COUPLED.odb"),
        "inp_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "PK_F1720_COARSE_COUPLED.inp"),
        "for_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "f1720_direct_coupling_uel.for"),
        "case": "Case 4 (Five-Hole Plate)",
    },
    {
        "id": "CASE1_NATIVE_DONOR",
        "path": os.path.join(REPO_ROOT, "runs", "probe_case1_remesh", "PK_CASE1_NATIVE_DONOR.odb"),
        "inp_path": os.path.join(REPO_ROOT, "runs", "probe_case1_remesh", "PK_CASE1_NATIVE_DONOR.inp"),
        "for_path": None,
        "case": "Case 1 Probe",
    },
    {
        "id": "CASE2_COARSE_JOB1",
        "path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_COARSE_JOB1.odb"),
        "inp_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_COARSE_JOB1.inp"),
        "for_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "f42_mixed_uel.for"),
        "case": "Case 2 (Plate with Off-Axis Hole)",
    },
    {
        "id": "CASE2_METHOD_A_PREANALYSIS",
        "path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_METHOD_A_PREANALYSIS.odb"),
        "inp_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_METHOD_A_PREANALYSIS.inp"),
        "for_path": None,
        "case": "Case 2 (Preanalysis)",
    }
]

audit_results = {}

for cand in candidates:
    cid = cand["id"]
    p = cand["path"]
    print("="*80)
    print("INSPECTING CANDIDATE:", cid)
    print("Path:", p)
    if not os.path.exists(p):
        print("STATUS: MISSING")
        audit_results[cid] = {"status": "MISSING", "path": p}
        continue

    sz = os.path.getsize(p)
    sha = compute_sha256(p)
    inp_sha = compute_sha256(cand["inp_path"]) if cand["inp_path"] else "N/A"
    for_sha = compute_sha256(cand["for_path"]) if cand["for_path"] else "N/A"

    print("File size: %d bytes (%.2f MB)" % (sz, sz / 1048576.0))
    print("ODB SHA256:", sha)
    print("INP SHA256:", inp_sha)
    print("FOR SHA256:", for_sha)

    odb = odbAccess.openOdb(p, readOnly=True)
    steps_info = {}
    for sname, s in odb.steps.items():
        nframes = len(s.frames)
        f_first = s.frames[0] if nframes > 0 else None
        f_last = s.frames[-1] if nframes > 0 else None
        fo_names = list(f_last.fieldOutputs.keys()) if f_last else []
        has_miseseri = 'MISESERI' in fo_names
        has_misesavg = 'MISESAVG' in fo_names
        has_evol = 'EVOL' in fo_names
        has_sdv = 'SDV' in fo_names
        has_s = 'S' in fo_names

        eri_max = 0.0
        eri_min = 0.0
        avg_max = 0.0
        avg_mean = 0.0
        d_max = 0.0

        if has_miseseri and f_last:
            fo_eri = f_last.fieldOutputs['MISESERI']
            vals = [val.data for val in fo_eri.values]
            if vals:
                eri_max = max(vals)
                eri_min = min(vals)
        if has_misesavg and f_last:
            fo_avg = f_last.fieldOutputs['MISESAVG']
            vals = [val.data for val in fo_avg.values]
            if vals:
                avg_max = max(vals)
                avg_mean = sum(vals) / float(len(vals))
        if has_sdv and f_last:
            fo_sdv = f_last.fieldOutputs['SDV']
            vals = [val.data for val in fo_sdv.values]
            if vals:
                d_max = max(vals)

        steps_info[sname] = {
            "num_frames": nframes,
            "field_outputs": fo_names,
            "has_miseseri": has_miseseri,
            "has_misesavg": has_misesavg,
            "has_evol": has_evol,
            "has_sdv": has_sdv,
            "last_frame_eri_max": eri_max,
            "last_frame_eri_min": eri_min,
            "last_frame_avg_max": avg_max,
            "last_frame_avg_mean": avg_mean,
            "last_frame_d_max": d_max
        }

    insts = list(odb.rootAssembly.instances.keys())
    num_elems = len(odb.rootAssembly.instances[insts[0]].elements) if insts else 0
    odb.close()

    cand_audit = {
        "status": "EXISTS",
        "case": cand["case"],
        "path": p,
        "size_bytes": sz,
        "sha256": sha,
        "inp_path": cand["inp_path"],
        "inp_sha256": inp_sha,
        "for_path": cand["for_path"],
        "for_sha256": for_sha,
        "num_elements": num_elems,
        "steps": steps_info
    }
    audit_results[cid] = cand_audit

out_json = os.path.join(REPO_ROOT, "results", "validation", "step1_authentic_reference_inventory.json")
with open(out_json, "w") as f:
    json.dump(audit_results, f, indent=2)
print("\nSaved Step 1 Inventory to:", out_json)
