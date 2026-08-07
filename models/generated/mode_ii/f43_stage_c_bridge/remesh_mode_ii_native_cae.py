#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fail-Closed Abaqus Native Adaptive Remeshing Driver Script for F43REM2_NATIVE.
Requires Abaqus/CAE Kernel noGUI execution: abaqus cae noGUI=remesh_mode_ii_native_cae.py
Manifest Path provided via environment variable F43REM2_MANIFEST_PATH.
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

def to_str_tree(val):
    if isinstance(val, dict):
        return dict((str(k), to_str_tree(v)) for k, v in val.items())
    elif isinstance(val, list):
        return [to_str_tree(x) for x in val]
    elif sys.version_info[0] == 2 and isinstance(val, unicode):
        return val.encode('utf-8')
    else:
        return str(val) if isinstance(val, (str, bytes)) else val

def run_native_remeshing():
    # 1. Environment-driven Manifest Transport
    manifest_path = os.environ.get("F43REM2_MANIFEST_PATH")
    if not manifest_path:
        # Fallback to searching sys.argv for a valid non-option json file
        for arg in sys.argv[1:]:
            if not arg.startswith("-") and arg.endswith(".json") and os.path.exists(arg):
                manifest_path = arg
                break
    if not manifest_path and os.path.exists("F43REM2_NATIVE_MANIFEST.json"):
        manifest_path = "F43REM2_NATIVE_MANIFEST.json"

    if not manifest_path or not os.path.exists(manifest_path):
        fail("F43REM2_MANIFEST_PATH environment variable missing or manifest file not found: " + str(manifest_path))

    with open(manifest_path, 'r') as f:
        manifest = to_str_tree(json.load(f))

    pred_odb_path = os.environ.get("F43REM2_PREDECESSOR_ODB", manifest.get("predecessor_odb_path", ""))
    expected_pred_sha = manifest["predecessor_odb_sha256"]
    source_cae_path = os.environ.get("F43REM2_SOURCE_CAE", manifest.get("source_cae_path", "ModeII_Geometry_Source.cae"))
    expected_cae_sha = manifest["source_cae_sha256"]

    # 2. Predecessor ODB Rejection & SHA Verification
    if "1384674" in pred_odb_path or expected_pred_sha.lower() == "3a201a6d405b92f4588e3d7e68177797706fd80ca9fa541e36ed0b10fdfb0534":
        fail("Predecessor ODB 1384674 is strictly prohibited for F43REM2_NATIVE! Must use 1385392.mmaster02.")

    if not os.path.exists(pred_odb_path):
        fail("Predecessor ODB missing at: " + pred_odb_path)
    actual_pred_sha = get_sha256(pred_odb_path)
    if actual_pred_sha.lower() != expected_pred_sha.lower():
        fail("Predecessor ODB SHA256 mismatch! Expected {}, got {}".format(expected_pred_sha, actual_pred_sha))
    print("[PASS] Predecessor ODB SHA256 verified: " + actual_pred_sha)

    # 3. Source CAE SHA Verification
    if not os.path.exists(source_cae_path):
        fail("Source CAE database missing at: " + source_cae_path)
    actual_cae_sha = get_sha256(source_cae_path)
    if actual_cae_sha.lower() != expected_cae_sha.lower():
        fail("Source CAE SHA256 mismatch! Expected {}, got {}".format(expected_cae_sha, actual_cae_sha))
    print("[PASS] Source CAE SHA256 verified: " + actual_cae_sha)

    # 4. Work-Copy CAE Creation (Source CAE open in place FORBIDDEN)
    work_cae_path = "ModeII_Geometry_WorkCopy.cae"
    if os.path.abspath(source_cae_path) == os.path.abspath(work_cae_path):
        fail("Opening source CAE in place is strictly forbidden!")

    shutil.copyfile(source_cae_path, work_cae_path)
    work_pre_sha = get_sha256(work_cae_path)
    if work_pre_sha.lower() != expected_cae_sha.lower():
        fail("Work-copy CAE pre-open hash mismatch!")
    print("[PASS] Work-copy CAE created and hash verified: " + work_cae_path)

    # 5. Import Abaqus CAE Kernel Objects
    try:
        from abaqus import mdb
    except ImportError as e:
        fail("Non-CAE-kernel invocation! abaqus module may only be imported in the Abaqus kernel process: " + str(e))

    # Resolve openMdb from abaqus module or kernel global namespace
    open_mdb_fn = None
    try:
        from abaqus import openMdb
        open_mdb_fn = openMdb
    except ImportError:
        open_mdb_fn = globals().get('openMdb', getattr(sys.modules.get('__main__'), 'openMdb', None))
        if open_mdb_fn is None:
            import abaqus
            open_mdb_fn = getattr(abaqus, 'openMdb', None)

    if open_mdb_fn is None:
        fail("openMdb function unavailable in Abaqus CAE kernel environment!")

    # 6. Open Work-Copy CAE in Abaqus CAE Kernel
    open_mdb_fn(pathName=work_cae_path)

    model_name = str(manifest.get("model_name", manifest.get("identities", {}).get("model_name", "ModeII_Geometry_Model")))
    rule_name = str(manifest.get("remeshing_rule_name", manifest.get("identities", {}).get("remeshing_rule", "MISESERI_Adaptive_Rule")))

    if model_name not in mdb.models:
        fail("Model '{}' missing from CAE database!".format(model_name))
    model = mdb.models[model_name]

    part_name = str(manifest.get("part_name", manifest.get("identities", {}).get("part_name", "PlatePart")))
    if part_name not in model.parts:
        fail("Part '{}' missing from model!".format(part_name))

    inst_name = str(manifest.get("instance_name", manifest.get("identities", {}).get("instance_name", "PlateInstance")))
    if inst_name not in model.rootAssembly.instances:
        fail("Instance '{}' missing from assembly!".format(inst_name))

    step_name = str(manifest.get("step_name", manifest.get("identities", {}).get("step_name", "Step-1")))
    if step_name not in model.steps:
        fail("Step '{}' missing from model!".format(step_name))

    if rule_name not in model.remeshingRules:
        fail("Remeshing rule '{}' missing from model!".format(rule_name))
    rule = model.remeshingRules[rule_name]
    print("[PASS] Verified model '{}' and remeshing rule '{}'".format(model_name, rule_name))

    # 7. Lightweight Kernel Probe Mode Check
    if os.environ.get("F43REM2_KERNEL_PROBE_ONLY") == "1":
        probe_status = {
            "status": "PASS",
            "cae_kernel_probe": "PASS",
            "openMdb_probe": "PASS",
            "native_remesh_called": False,
            "work_copy_cae": work_cae_path,
            "model_name": model_name,
            "part_name": part_name,
            "instance_name": inst_name,
            "step_name": step_name,
            "rule_name": rule_name
        }
        with open("F43REM2_KERNEL_PROBE_STATUS.json", "w") as f:
            json.dump(probe_status, f, indent=2)
        print("[PASS] Abaqus CAE Kernel Probe Completed Successfully.")
        return

    # 8. Open Predecessor ODB and Verify MISESERI Field
    from odbAccess import openOdb
    odb = openOdb(pred_odb_path, readOnly=True)
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

    # 9. Execute Native Adaptive Remeshing Process
    process_name = "F43_Native_Remesh_Process"
    if process_name in mdb.adaptivityProcesses:
        del mdb.adaptivityProcesses[process_name]

    process = mdb.AdaptivityProcess(
        name=process_name,
        jobName='F43PRE2_GEOM',
        model=model_name,
        description='F43REM2_NATIVE Adaptive Remeshing Process'
    )

    process.setValues(jobName='F43PRE2_GEOM')

    print("Executing Abaqus Native AdaptivityProcess...")
    process.execute(remeshData=[(pred_odb_path, step_name, last_frame.frameValue)])

    # 10. Write Refined INP Deck
    job_name = "F43REM2_NATIVE"
    output_inp = os.environ.get("F43REM2_OUTPUT_INP", job_name + ".inp")
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

    # 11. Save Work Copy CAE
    mdb.save()

    # 12. Emit Success Marker
    success_status = {
        "status": "F43REM2_NATIVE_PREPARATION_PASS",
        "predecessor_job": manifest.get("predecessor_job_id", "1385392.mmaster02"),
        "predecessor_odb_sha256": actual_pred_sha,
        "work_copy_cae": work_cae_path,
        "refined_inp": inp_path,
        "inp_size_bytes": os.path.getsize(inp_path)
    }

    with open("F43REM2_NATIVE_SUCCESS.json", "w") as f:
        json.dump(success_status, f, indent=2)

    print("\nF43REM2_NATIVE Remeshing Driver Execution Completed Successfully.")

if __name__ == "__main__":
    run_native_remeshing()

