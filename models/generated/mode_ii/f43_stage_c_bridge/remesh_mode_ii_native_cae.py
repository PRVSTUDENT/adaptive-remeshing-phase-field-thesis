#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fail-Closed Abaqus Native Adaptive Remeshing Driver Script for F43REM2_NATIVE.
Requires Abaqus Python: abaqus python remesh_mode_ii_native_cae.py <manifest_json>
"""

import sys
import os
import shutil
import hashlib
import json

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def fail(msg):
    print("FATAL ERROR (F43REM2_NATIVE): " + msg)
    sys.exit(1)

def run_native_remeshing(manifest_path):
    if not os.path.exists(manifest_path):
        fail("Manifest file missing at: " + manifest_path)
        
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    pred_odb_path = manifest.get("predecessor_odb_path", "")
    expected_pred_sha = manifest["predecessor_odb_sha256"]
    source_cae_path = manifest.get("source_cae_path", "ModeII_Geometry_Source.cae")
    expected_cae_sha = manifest["source_cae_sha256"]
    
    # 1. Predecessor ODB SHA Verification
    if not os.path.exists(pred_odb_path):
        fail("Predecessor ODB missing at: " + pred_odb_path)
    actual_pred_sha = get_sha256(pred_odb_path)
    if actual_pred_sha.lower() != expected_pred_sha.lower():
        fail("Predecessor ODB SHA256 mismatch! Expected {}, got {}".format(expected_pred_sha, actual_pred_sha))
    print("[PASS] Predecessor ODB SHA256 verified: " + actual_pred_sha)
    
    # 2. Source CAE SHA Verification
    if not os.path.exists(source_cae_path):
        fail("Source CAE database missing at: " + source_cae_path)
    actual_cae_sha = get_sha256(source_cae_path)
    if actual_cae_sha.lower() != expected_cae_sha.lower():
        fail("Source CAE SHA256 mismatch! Expected {}, got {}".format(expected_cae_sha, actual_cae_sha))
    print("[PASS] Source CAE SHA256 verified: " + actual_cae_sha)
    
    # 3. Work-Copy CAE Creation (Source CAE open in place FORBIDDEN)
    work_cae_path = "ModeII_Geometry_WorkCopy.cae"
    if os.path.abspath(source_cae_path) == os.path.abspath(work_cae_path):
        fail("Opening source CAE in place is strictly forbidden!")
        
    shutil.copyfile(source_cae_path, work_cae_path)
    work_pre_sha = get_sha256(work_cae_path)
    if work_pre_sha.lower() != expected_cae_sha.lower():
        fail("Work-copy CAE pre-open hash mismatch!")
    print("[PASS] Work-copy CAE created and hash verified: " + work_cae_path)
    
    # 4. Open Work-Copy CAE in Abaqus CAE environment
    from abaqus import mdb, openMdb
    from odbAccess import openOdb
    
    openMdb(pathName=work_cae_path)
    
    model_name = manifest["identities"]["model_name"]
    rule_name = manifest["identities"]["remeshing_rule"]
    
    if model_name not in mdb.models:
        fail("Model '{}' missing from CAE database!".format(model_name))
    model = mdb.models[model_name]
    
    if rule_name not in model.remeshingRules:
        fail("Remeshing rule '{}' missing from model!".format(rule_name))
    rule = model.remeshingRules[rule_name]
    print("[PASS] Verified model and remeshing rule '{}'".format(rule_name))
    
    # 5. Open Predecessor ODB and Verify MISESERI Field
    odb = openOdb(pred_odb_path, readOnly=True)
    step_name = manifest["identities"]["step_name"]
    if step_name not in odb.steps:
        fail("Step '{}' missing from predecessor ODB!".format(step_name))
        
    step = odb.steps[step_name]
    last_frame = step.frames[-1]
    
    if 'MISESERI' not in last_frame.fieldOutputs:
        fail("Field Output 'MISESERI' missing from predecessor ODB last frame!")
        
    m_field = last_frame.fieldOutputs['MISESERI']
    m_vals = [v.data for v in m_field.values if v.elementLabel]
    odb.close()
    
    if not m_vals:
        fail("MISESERI field output is empty!")
    if max(m_vals) <= min(m_vals):
        fail("MISESERI field is constant/nontrivial check failed!")
    print("[PASS] Verified predecessor ODB MISESERI field: min={:.4f}, max={:.4f}".format(min(m_vals), max(m_vals)))
    
    # 6. Execute Native Adaptive Remeshing Process
    process_name = "F43_Native_Remesh_Process"
    if process_name in mdb.adaptivityProcesses:
        del mdb.adaptivityProcesses[process_name]
        
    process = mdb.AdaptivityProcess(
        name=process_name,
        jobName='F43PRE2_GEOM',
        model=model_name,
        description='F43REM2_NATIVE Adaptive Remeshing Process'
    )
    
    # Associate predecessor ODB
    process.setValues(jobName='F43PRE2_GEOM')
    
    print("Executing Abaqus Native AdaptivityProcess...")
    process.execute(remeshData=[(pred_odb_path, step_name, last_frame.frameValue)])
    
    # 7. Write Refined INP Deck
    job_name = "F43REM2_NATIVE"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
        
    job = mdb.Job(
        name=job_name,
        model=model_name,
        description='F43REM2_NATIVE Refined Standard Deck'
    )
    job.writeInput(consistencyChecking=OFF)
    
    inp_path = job_name + ".inp"
    if not os.path.exists(inp_path) or os.path.getsize(inp_path) == 0:
        fail("Refined input deck export failed or produced empty file!")
    print("[PASS] Refined input deck exported: " + inp_path)
    
    # 8. Save Work Copy CAE
    mdb.save()
    
    # 9. Emit Success Marker
    success_status = {
        "status": "F43REM2_NATIVE_PREPARATION_PASS",
        "predecessor_job": manifest["predecessor_job"],
        "predecessor_odb_sha256": actual_pred_sha,
        "work_copy_cae": work_cae_path,
        "refined_inp": inp_path,
        "inp_size_bytes": os.path.getsize(inp_path)
    }
    
    with open("F43REM2_NATIVE_SUCCESS.json", "w") as f:
        json.dump(success_status, f, indent=2)
        
    print("\nF43REM2_NATIVE Remeshing Driver Execution Completed Successfully.")

if __name__ == "__main__":
    m_path = sys.argv[1] if len(sys.argv) > 1 else "F43REM2_NATIVE_MANIFEST.json"
    run_native_remeshing(m_path)
