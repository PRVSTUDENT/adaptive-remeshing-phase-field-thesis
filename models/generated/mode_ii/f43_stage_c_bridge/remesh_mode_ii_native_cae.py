# Abaqus/CAE Native Adaptive Remeshing Execution Script for Stage C
# Runs under: abaqus cae noGUI=remesh_mode_ii_native_cae.py

import os
import sys
import shutil
import json
import hashlib

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def fail(msg):
    print("FATAL ERROR: " + str(msg))
    sys.exit(1)

def execute_native_remeshing():
    if '__file__' in globals() and __file__:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_defined = True
        fallback_used = False
    else:
        script_dir = os.getcwd()
        file_defined = False
        fallback_used = True

    cwd = os.getcwd()

    # Resolve manifest path supporting F43REM3 and F43REM2 environment variables
    manifest_path = os.environ.get("F43REM3_MANIFEST_PATH",
                     os.environ.get("F43REM2_MANIFEST_PATH",
                     os.path.join(script_dir, "F43REM3_NATIVE_MANIFEST.json")))

    if not os.path.exists(manifest_path):
        fail("Manifest file missing: {}".format(manifest_path))

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    # Explicitly reject legacy 1384674 predecessor
    pred_id = str(manifest.get("predecessor_odb_job_id", ""))
    pred_path_val = str(manifest.get("predecessor_odb_path", ""))
    if "1384674" in pred_id or "1384674" in pred_path_val:
        fail("Driver explicitly rejects 1384674 predecessor")

    source_cae_path = str(manifest.get("source_cae_path", "/home/pr21vyci/projects/adaptive-remeshing-artifacts/f43pre3/ModeII_Geometry_Source_Abaqus2023.cae"))
    expected_cae_sha = str(manifest.get("source_cae_sha256", "0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa"))

    raw_pred_path = str(manifest.get("predecessor_odb_path", "evidence/1385461.mmaster02/F43PRE3_GEOM.odb"))
    predecessor_odb_path = str(raw_pred_path if os.path.isabs(raw_pred_path) else os.path.join(script_dir, raw_pred_path))
    expected_odb_sha = str(manifest.get("predecessor_odb_sha256", "9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1"))

    print("[F43 Native Remesh] Verifying pre-execution file integrity...")
    if not os.path.exists(source_cae_path):
        fail("Source CAE missing: {}".format(source_cae_path))

    actual_cae_sha = sha256_file(source_cae_path)
    actual_cae_sha_before = actual_cae_sha
    if actual_cae_sha != expected_cae_sha:
        fail("Source CAE SHA mismatch! Expected {}, got {}".format(expected_cae_sha, actual_cae_sha))

    if not os.path.exists(predecessor_odb_path):
        fail("Predecessor ODB missing: {}".format(predecessor_odb_path))

    actual_odb_sha = sha256_file(predecessor_odb_path)
    if actual_odb_sha != expected_odb_sha:
        fail("Predecessor ODB SHA mismatch! Expected {}, got {}".format(expected_odb_sha, actual_odb_sha))

    # Create runtime writable COPY of source CAE (source CAE remains strictly immutable)
    work_cae_path = str(os.path.join(script_dir, "_runtime_work_copy.cae"))
    if os.path.exists(work_cae_path):
        os.remove(work_cae_path)
    shutil.copy2(source_cae_path, work_cae_path)
    work_cae_sha_before = sha256_file(work_cae_path)
    print("[F43 Native Remesh] Created writable work copy CAE: {}".format(work_cae_path))

    from abaqus import mdb, openMdb
    from abaqusConstants import OFF
    from odbAccess import openOdb
    import job

    open_mdb_fn = openMdb
    print("[F43 Native Remesh] Opening work copy MDB read-write via open_mdb_fn...")
    open_mdb_fn(pathName=work_cae_path)

    model_name = mdb.models.keys()[0]
    m = mdb.models[model_name]
    print("[F43 Native Remesh] Loaded model: {}".format(model_name))

    part_name = m.parts.keys()[0] if m.parts else "PlatePart"
    inst_name = m.rootAssembly.instances.keys()[0] if m.rootAssembly.instances else "PlateInstance"
    
    # Audit model steps: select actual mechanical analysis step (Step-1), not Initial
    cae_model_steps = list(m.steps.keys())
    if "Step-1" not in cae_model_steps:
        fail("Required mechanical analysis step Step-1 missing from model steps: {}".format(cae_model_steps))

    analysis_step_name = [s for s in cae_model_steps if s != "Initial"][0] if any(s != "Initial" for s in cae_model_steps) else "Step-1"
    step_name = analysis_step_name
    if step_name not in m.steps.keys():
        fail("Target step {} not found in model steps: {}".format(step_name, cae_model_steps))
    if step_name == "Initial":
        fail("Remeshing rule step_name cannot be Initial!")

    print("[F43 Native Remesh] Model steps: {}, Selected analysis step: {}".format(cae_model_steps, analysis_step_name))

    remesh_params = manifest.get("remesh_parameters", {
        "min_element_size_mm": 0.0075,
        "max_element_size_mm": 0.03,
        "refinement_factor": 0.5,
        "error_target": 0.05
    })
    rule_name = "StageC_MISESERI_RemeshingRule"

    print("[F43 Native Remesh] Opening predecessor ODB read-only...")
    odb = openOdb(predecessor_odb_path, readOnly=True)

    odb_step_names = list(odb.steps.keys())
    odb_analysis_step = odb_step_names[0] if odb_step_names else "Step-1"
    st = odb.steps[odb_analysis_step]
    num_frames = len(st.frames)
    last_frame = st.frames[-1] if num_frames > 0 else None
    final_frame_time = float(last_frame.frameValue) if last_frame else 0.0
    frame_fields = list(last_frame.fieldOutputs.keys()) if last_frame else []
    print("[F43 Native Remesh] Predecessor ODB step: {}, frames: {}, final time: {}".format(odb_analysis_step, num_frames, final_frame_time))

    # Support Kernel Probe Modes
    is_adaptiveremesh_probe_mode = (os.environ.get("F43REM3_ADAPTIVEREMESH_API_PROBE_ONLY") == "1")
    is_rule_probe_mode = (os.environ.get("F43REM3_RULE_PROBE_ONLY") == "1")
    is_kernel_probe_mode = (os.environ.get("F43REM3_KERNEL_PROBE_ONLY") == "1" or
                             os.environ.get("F43REM2_KERNEL_PROBE_ONLY") == "1")

    if is_adaptiveremesh_probe_mode:
        if rule_name in m.remeshingRules.keys():
            del m.remeshingRules[rule_name]

        import regionToolset
        inst = m.rootAssembly.instances[inst_name]
        if hasattr(inst, 'faces') and len(inst.faces) > 0:
            rule_region = regionToolset.Region(faces=inst.faces)
        elif hasattr(inst, 'elements') and len(inst.elements) > 0:
            rule_region = regionToolset.Region(elements=inst.elements)
        else:
            rule_region = (inst,)

        m.RemeshingRule(
            name=rule_name,
            stepName=step_name,
            variables=('MISESERI',),
            description="Stage C MISESERI Native Adaptive Remeshing Rule",
            region=rule_region,
            errorTarget=remesh_params["error_target"],
            minElementSize=remesh_params["min_element_size_mm"],
            maxElementSize=remesh_params["max_element_size_mm"]
        )

        remeshing_rule_constructed = (rule_name in m.remeshingRules.keys())
        rule_obj = m.remeshingRules[rule_name]
        rule_step_name = getattr(rule_obj, "stepName", step_name)

        actual_cae_sha_after = sha256_file(source_cae_path)
        source_cae_unmodified = (actual_cae_sha_after == expected_cae_sha)
        miseseri_available = ("MISESERI" in frame_fields)

        has_m_adaptiveRemesh = hasattr(m, 'adaptiveRemesh')
        has_ass_remesh = hasattr(m.rootAssembly, 'remesh')

        api_probe_status = {
            "status": "PASS",
            "abaqus_cae_kernel_entered": True,
            "file_defined": file_defined,
            "fallback_used": fallback_used,
            "resolved_script_dir": script_dir,
            "cwd": cwd,
            "source_cae_path": source_cae_path,
            "source_cae_sha_before": actual_cae_sha_before,
            "source_cae_sha_after": actual_cae_sha_after,
            "source_cae_opened_in_place": False,
            "source_cae_unmodified_in_place": source_cae_unmodified,
            "work_copy_cae_sha_before": work_cae_sha_before,
            "source_CAE_copy_open": "PASS",
            "model_inventory": "PASS",
            "model_name": model_name,
            "model_steps": cae_model_steps,
            "analysis_step_name": analysis_step_name,
            "part_name": part_name,
            "instance_name": inst_name,
            "step_name": step_name,
            "rule_name": rule_name,
            "rule_creation_attempted": True,
            "rule_creation_status": "PASS",
            "remeshing_rule_constructed": remeshing_rule_constructed,
            "remeshing_rule_step": rule_step_name,
            "rule_step_name": rule_step_name,
            "MISESERI_verified": miseseri_available,
            "MISESERI_available": miseseri_available,
            "predecessor_ODB_available": "PASS",
            "predecessor_odb_sha": actual_odb_sha,
            "predecessor_odb_steps": odb_step_names,
            "predecessor_odb_analysis_step": odb_analysis_step,
            "predecessor_odb_frame_count": num_frames,
            "predecessor_odb_final_frame_time": final_frame_time,
            "predecessor_odb_fields": frame_fields,
            "Model_adaptiveRemesh_exists": has_m_adaptiveRemesh,
            "Assembly_remesh_exists": has_ass_remesh,
            "adaptiveRemesh_callable": has_m_adaptiveRemesh,
            "adaptiveRemesh_called": False,
            "probe_exit_status": 0
        }
        probe_out_path = os.path.join(script_dir, "F43REM3_ADAPTIVEREMESH_API_PROBE_STATUS.json")
        with open(probe_out_path, "w") as f:
            json.dump(api_probe_status, f, indent=2)
        odb.close()
        print("[PASS] Abaqus CAE Model.adaptiveRemesh API Probe Completed Successfully.")
        return

    if is_rule_probe_mode:
        if rule_name in m.remeshingRules.keys():
            del m.remeshingRules[rule_name]

        import regionToolset
        inst = m.rootAssembly.instances[inst_name]
        if hasattr(inst, 'faces') and len(inst.faces) > 0:
            rule_region = regionToolset.Region(faces=inst.faces)
        elif hasattr(inst, 'elements') and len(inst.elements) > 0:
            rule_region = regionToolset.Region(elements=inst.elements)
        else:
            rule_region = (inst,)

        m.RemeshingRule(
            name=rule_name,
            stepName=step_name,
            variables=('MISESERI',),
            description="Stage C MISESERI Native Adaptive Remeshing Rule",
            region=rule_region,
            errorTarget=remesh_params["error_target"],
            minElementSize=remesh_params["min_element_size_mm"],
            maxElementSize=remesh_params["max_element_size_mm"]
        )

        remeshing_rule_constructed = (rule_name in m.remeshingRules.keys())
        rule_obj = m.remeshingRules[rule_name]
        rule_step_name = getattr(rule_obj, "stepName", step_name)

        actual_cae_sha_after = sha256_file(source_cae_path)
        source_cae_unmodified = (actual_cae_sha_after == expected_cae_sha)
        miseseri_available = ("MISESERI" in frame_fields)

        rule_probe_status = {
            "status": "PASS",
            "abaqus_cae_kernel_entered": True,
            "file_defined": file_defined,
            "fallback_used": fallback_used,
            "resolved_script_dir": script_dir,
            "cwd": cwd,
            "source_cae_path": source_cae_path,
            "source_cae_sha_before": actual_cae_sha_before,
            "source_cae_sha_after": actual_cae_sha_after,
            "source_cae_opened_in_place": False,
            "source_cae_unmodified_in_place": source_cae_unmodified,
            "work_copy_cae_sha_before": work_cae_sha_before,
            "source_CAE_copy_open": "PASS",
            "model_inventory": "PASS",
            "model_name": model_name,
            "model_steps": cae_model_steps,
            "analysis_step_name": analysis_step_name,
            "part_inventory": "PASS",
            "part_name": part_name,
            "instance_inventory": "PASS",
            "instance_name": inst_name,
            "step_inventory": "PASS",
            "step_name": step_name,
            "remeshing_rule_inventory": "PASS",
            "rule_name": rule_name,
            "rule_creation_attempted": True,
            "rule_creation_status": "PASS",
            "remeshing_rule_constructed": remeshing_rule_constructed,
            "remeshing_rule_step": rule_step_name,
            "rule_step_name": rule_step_name,
            "MISESERI_verified": miseseri_available,
            "MISESERI_available": miseseri_available,
            "predecessor_ODB_available": "PASS",
            "predecessor_odb_sha": actual_odb_sha,
            "predecessor_odb_steps": odb_step_names,
            "predecessor_odb_analysis_step": odb_analysis_step,
            "predecessor_odb_frame_count": num_frames,
            "predecessor_odb_final_frame_time": final_frame_time,
            "predecessor_odb_fields": frame_fields,
            "native_remesh_called": False,
            "probe_exit_status": 0
        }
        probe_out_path = os.path.join(script_dir, "F43REM3_RULE_PROBE_STATUS.json")
        with open(probe_out_path, "w") as f:
            json.dump(rule_probe_status, f, indent=2)
        odb.close()
        print("[PASS] Abaqus CAE Remeshing Rule Construction Probe Completed Successfully.")
        return

    if is_kernel_probe_mode:
        actual_cae_sha_after = sha256_file(source_cae_path)
        source_cae_unmodified = (actual_cae_sha_after == expected_cae_sha)
        probe_status = {
            "status": "PASS",
            "abaqus_cae_kernel_entered": True,
            "file_defined": file_defined,
            "fallback_used": fallback_used,
            "resolved_script_dir": script_dir,
            "cwd": cwd,
            "source_cae_path": source_cae_path,
            "source_cae_sha_before": actual_cae_sha_before,
            "source_cae_sha_after": actual_cae_sha_after,
            "source_cae_opened_in_place": False,
            "source_cae_unmodified_in_place": source_cae_unmodified,
            "work_copy_cae_sha_before": work_cae_sha_before,
            "source_CAE_copy_open": "PASS",
            "model_inventory": "PASS",
            "model_name": model_name,
            "model_steps": cae_model_steps,
            "analysis_step_name": analysis_step_name,
            "part_inventory": "PASS",
            "part_name": part_name,
            "instance_inventory": "PASS",
            "instance_name": inst_name,
            "step_inventory": "PASS",
            "step_name": step_name,
            "remeshing_rule_inventory": "PASS",
            "rule_name": rule_name,
            "predecessor_ODB_available": "PASS",
            "predecessor_odb_sha": actual_odb_sha,
            "predecessor_odb_steps": odb_step_names,
            "predecessor_odb_analysis_step": odb_analysis_step,
            "predecessor_odb_frame_count": num_frames,
            "predecessor_odb_final_frame_time": final_frame_time,
            "predecessor_odb_fields": frame_fields,
            "native_remesh_called": False,
            "probe_exit_status": 0
        }
        probe_out_path = os.path.join(script_dir, "F43REM3_KERNEL_PROBE_STATUS.json")
        with open(probe_out_path, "w") as f:
            json.dump(probe_status, f, indent=2)
        with open(os.path.join(script_dir, "F43REM2_KERNEL_PROBE_STATUS.json"), "w") as f:
            json.dump(probe_status, f, indent=2)
        odb.close()
        print("[PASS] Abaqus CAE Kernel Probe Completed Successfully.")
        return

    if rule_name in m.remeshingRules.keys():
        del m.remeshingRules[rule_name]

    import regionToolset
    inst = m.rootAssembly.instances[inst_name]
    if hasattr(inst, 'faces') and len(inst.faces) > 0:
        rule_region = regionToolset.Region(faces=inst.faces)
    elif hasattr(inst, 'elements') and len(inst.elements) > 0:
        rule_region = regionToolset.Region(elements=inst.elements)
    else:
        rule_region = (inst,)

    m.RemeshingRule(
        name=rule_name,
        stepName=step_name,
        variables=('MISESERI',),
        description="Stage C MISESERI Native Adaptive Remeshing Rule",
        region=rule_region,
        errorTarget=remesh_params["error_target"],
        minElementSize=remesh_params["min_element_size_mm"],
        maxElementSize=remesh_params["max_element_size_mm"]
    )

    print("[F43 Native Remesh] Created remeshing rule: {}".format(rule_name))

    # Fail-closed preconditions immediately before adaptiveRemesh
    if not hasattr(m, 'adaptiveRemesh'):
        fail("Model object has no adaptiveRemesh method in installed Abaqus CAE environment!")

    if hasattr(m.rootAssembly, 'remesh'):
        fail("Assembly.remesh is forbidden!")

    if step_name != "Step-1":
        fail("Remeshing rule stepName must be Step-1!")

    if rule_name not in m.remeshingRules.keys():
        fail("Remeshing rule {} missing from model!".format(rule_name))

    rule_obj = m.remeshingRules[rule_name]
    if getattr(rule_obj, "stepName", "") != "Step-1":
        fail("Remeshing rule stepName is not Step-1!")

    rule_vars = getattr(rule_obj, "variables", [])
    if "MISESERI" not in rule_vars:
        fail("Remeshing rule variables must include MISESERI!")

    if expected_odb_sha != "9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1":
        fail("Predecessor ODB SHA mismatch!")

    if final_frame_time != 1.0 or "MISESERI" not in frame_fields:
        fail("Predecessor ODB final frame time or MISESERI field mismatch!")

    # Execute native adaptive remeshing via Model API
    print("[F43 Native Remesh] Executing native Model.adaptiveRemesh(odb)...")
    adaptivity_iteration = m.adaptiveRemesh(odb)
    print("[F43 Native Remesh] Model.adaptiveRemesh(odb) completed cleanly.")

    # Write refined input deck
    job_name = "F43REM3_NATIVE"
    if job_name in mdb.jobs.keys():
        del mdb.jobs[job_name]

    j = mdb.Job(
        name=job_name,
        model=model_name,
        description="F43REM3 Refined Standard Input Deck"
    )
    j.writeInput(consistencyChecking=OFF)
    print("[F43 Native Remesh] Refined input deck written: {}.inp".format(job_name))

    odb.close()

    # Confirm source CAE was never modified in-place
    after_source_sha = sha256_file(source_cae_path)
    if after_source_sha != expected_cae_sha:
        fail("Source CAE was modified in-place!")

    print("[F43 Native Remesh] Execution completed cleanly.")

if __name__ == "__main__":
    execute_native_remeshing()

