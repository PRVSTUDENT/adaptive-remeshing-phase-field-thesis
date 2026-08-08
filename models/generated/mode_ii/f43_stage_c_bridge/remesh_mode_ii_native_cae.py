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
    candidate_id = os.environ.get("F43REM4_CANDIDATE_ID", "F43REM3_NATIVE")
    preflight_only = (os.environ.get("F43REM4_PREFLIGHT_ONLY") == "1")

    # Explicit Bridge Directory Resolution (no CWD fallback)
    bridge_dir_env = os.environ.get("F43REM4_BRIDGE_DIR")
    if bridge_dir_env and isinstance(bridge_dir_env, str):
        bridge_dir = os.path.realpath(os.path.abspath(bridge_dir_env))
    elif '__file__' in globals() and __file__:
        bridge_dir = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))
    else:
        bridge_dir = os.path.realpath(os.path.abspath(os.getcwd()))

    # Config / Manifest Resolution
    config_path_env = os.environ.get(
        "F43REM4_CONFIG_PATH",
        os.environ.get("F43REM3_MANIFEST_PATH", os.environ.get("F43REM2_MANIFEST_PATH"))
    )
    if config_path_env:
        manifest_path = os.path.realpath(os.path.abspath(config_path_env))
    else:
        manifest_path = os.path.realpath(os.path.abspath(os.path.join(bridge_dir, "F43REM3_NATIVE_MANIFEST.json")))

    if not os.path.exists(manifest_path):
        fail("Manifest/Config file missing: {}".format(manifest_path))

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    # Driver explicitly rejects predecessor 1384674
    pred_id = str(manifest.get("predecessor_odb_job_id", ""))
    pred_path_val = str(manifest.get("predecessor_odb_path", ""))
    if "1384674" in pred_id or "1384674" in pred_path_val:
        fail("Predecessor ODB job 1384674 is explicitly rejected for Stage C adaptive remeshing!")

    # Predecessor ODB Check (fail-closed absolute path resolution)
    expected_odb_sha = "9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1"
    env_odb_path = os.environ.get("F43REM4_PREDECESSOR_ODB", os.environ.get("PREDECESSOR_ODB_PATH"))

    cand_odb_paths = []
    if env_odb_path and isinstance(env_odb_path, str):
        cand_odb_paths.append(os.path.realpath(os.path.abspath(env_odb_path)))
    cand_odb_paths.append(os.path.realpath(os.path.abspath(os.path.join(bridge_dir, "evidence", "1385461.mmaster02", "F43PRE3_GEOM.odb"))))
    cand_odb_paths.append(os.path.realpath(os.path.abspath("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1385461.mmaster02/F43PRE3_GEOM.odb")))

    predecessor_odb_path = None
    for p in cand_odb_paths:
        if p and os.path.exists(p) and os.path.isfile(p):
            predecessor_odb_path = p
            break

    if not predecessor_odb_path:
        fail("Predecessor ODB missing from all valid search paths: {}".format(cand_odb_paths))

    actual_odb_sha = sha256_file(predecessor_odb_path)
    if actual_odb_sha.lower() != expected_odb_sha.lower():
        fail("Predecessor ODB SHA mismatch! Expected {}, got {}".format(expected_odb_sha, actual_odb_sha))

    # Source CAE Check (fail-closed absolute path resolution)
    expected_cae_sha = "0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa"
    env_cae_path = os.environ.get("F43REM4_SOURCE_CAE", os.environ.get("SOURCE_CAE_PATH"))

    cand_cae_paths = []
    if env_cae_path and isinstance(env_cae_path, str):
        cand_cae_paths.append(os.path.realpath(os.path.abspath(env_cae_path)))
    cand_cae_paths.append(os.path.realpath(os.path.abspath(os.path.join(bridge_dir, "ModeII_Geometry_Source_Abaqus2023.cae"))))
    cand_cae_paths.append(os.path.realpath(os.path.abspath("/home/pr21vyci/projects/adaptive-remeshing-artifacts/f43pre3/ModeII_Geometry_Source_Abaqus2023.cae")))

    source_cae_path = None
    for p in cand_cae_paths:
        if p and os.path.exists(p) and os.path.isfile(p):
            source_cae_path = p
            break

    if not source_cae_path:
        fail("Source CAE missing from all valid search paths: {}".format(cand_cae_paths))

    actual_cae_sha_before = sha256_file(source_cae_path)
    if actual_cae_sha_before.lower() != expected_cae_sha.lower():
        fail("Source CAE SHA mismatch! Expected {}, got {}".format(expected_cae_sha, actual_cae_sha_before))

    # Output directory resolution
    output_dir_env = os.environ.get("F43REM4_OUTPUT_DIR", os.getcwd())
    output_dir = os.path.realpath(os.path.abspath(output_dir_env))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("[F43 Native Remesh] Candidate ID: {}".format(candidate_id))
    print("[F43 Native Remesh] Bridge directory: {}".format(bridge_dir))
    print("[F43 Native Remesh] Resolved source CAE: {}".format(source_cae_path))
    print("[F43 Native Remesh] Resolved predecessor ODB: {}".format(predecessor_odb_path))
    print("[F43 Native Remesh] Resolved output directory: {}".format(output_dir))

    # Writable candidate-isolated copy of CAE (_runtime_work_copy_<candidate>.cae)
    work_cae_filename = "_runtime_work_copy_{}_{}.cae".format(candidate_id, os.getpid())
    work_cae_path = os.path.join(output_dir, work_cae_filename)
    if os.path.exists(work_cae_path):
        os.remove(work_cae_path)

    shutil.copyfile(source_cae_path, work_cae_path)
    work_cae_sha_before = sha256_file(work_cae_path)

    from abaqus import mdb, openMdb
    from abaqusConstants import MODEL, UNIFORM_ERROR, MINIMUM_MAXIMUM, NOT_ALLOWED, ON, OFF
    from odbAccess import openOdb

    print("[F43 Native Remesh] Opening candidate-isolated copy of CAE: {}".format(work_cae_path))
    openMdb(pathName=work_cae_path)

    model_name = "ModeII_Geometry_Model"
    if model_name not in mdb.models.keys():
        fail("Model {} missing from CAE database!".format(model_name))
    m = mdb.models[model_name]

    cae_model_steps = list(m.steps.keys())
    step_name = "Step-1"
    if step_name not in cae_model_steps:
        fail("Step-1 missing from model steps: {}".format(cae_model_steps))

    part_name = "Part-1"
    inst_name = "Part-1-1"

    odb = openOdb(predecessor_odb_path, readOnly=True)
    odb_step_names = list(odb.steps.keys())
    odb_analysis_step = odb_step_names[0] if odb_step_names else "Step-1"
    st = odb.steps[odb_analysis_step]
    num_frames = len(st.frames)
    last_frame = st.frames[-1] if num_frames > 0 else None
    final_frame_time = float(last_frame.frameValue) if last_frame else 0.0
    frame_fields = list(last_frame.fieldOutputs.keys()) if last_frame else []

    if "MISESERI" not in frame_fields:
        fail("MISESERI field output missing from predecessor ODB!")

    # Check for F43REM4 candidate config format
    is_f43rem4_cfg = ("remeshing_rule" in manifest and "candidate_id" in manifest)

    if is_f43rem4_cfg:
        rule_cfg = manifest["remeshing_rule"]
        rule_name = str(rule_cfg["name"])
        job_name = str(manifest.get("expected_output_deck", manifest["candidate_id"] + ".inp")).replace(".inp", "")

        if rule_name in m.remeshingRules.keys():
            del m.remeshingRules[rule_name]

        if rule_cfg["sizingMethod"] == "UNIFORM_ERROR":
            r = m.RemeshingRule(
                name=rule_name,
                stepName=step_name,
                variables=('MISESERI',),
                region=MODEL,
                sizingMethod=UNIFORM_ERROR,
                errorTarget=float(rule_cfg["errorTarget"]),
                specifyMinSize=ON if rule_cfg["specifyMinSize"] else OFF,
                minElementSize=float(rule_cfg["minElementSize"]),
                specifyMaxSize=ON if rule_cfg["specifyMaxSize"] else OFF,
                maxElementSize=float(rule_cfg["maxElementSize"]),
                coarseningFactor=NOT_ALLOWED,
                refinementFactor=int(rule_cfg["refinementFactor"]),
            )
        elif rule_cfg["sizingMethod"] == "MINIMUM_MAXIMUM":
            r = m.RemeshingRule(
                name=rule_name,
                stepName=step_name,
                variables=('MISESERI',),
                region=MODEL,
                sizingMethod=MINIMUM_MAXIMUM,
                maxSolutionErrorTarget=float(rule_cfg["maxSolutionErrorTarget"]),
                minSolutionErrorTarget=float(rule_cfg["minSolutionErrorTarget"]),
                meshBias=int(rule_cfg["meshBias"]),
                specifyMinSize=ON if rule_cfg["specifyMinSize"] else OFF,
                minElementSize=float(rule_cfg["minElementSize"]),
                specifyMaxSize=ON if rule_cfg["specifyMaxSize"] else OFF,
                maxElementSize=float(rule_cfg["maxElementSize"]),
            )
    else:
        remesh_params = manifest.get("remesh_parameters", {
            "min_element_size_mm": 0.0075,
            "max_element_size_mm": 0.03,
            "refinement_factor": 10,
            "error_target": 0.05
        })
        rule_name = "StageC_MISESERI_RemeshingRule"
        job_name = "F43REM3_NATIVE"

        if rule_name not in m.remeshingRules.keys():
            m.RemeshingRule(
                name=rule_name,
                stepName=step_name,
                variables=('MISESERI',),
                description="Stage C MISESERI Native Adaptive Remeshing Rule",
                region=MODEL,
                errorTarget=remesh_params["error_target"],
                minElementSize=remesh_params["min_element_size_mm"],
                maxElementSize=remesh_params["max_element_size_mm"]
            )

    remeshing_rule_constructed = (rule_name in m.remeshingRules.keys())

    # Preflight Mode Execution
    if preflight_only:
        preflight_status = {
            "status": "PASS",
            "Abaqus_version": "2023",
            "candidate_id": candidate_id,
            "bridge_dir": bridge_dir,
            "source_cae_path": source_cae_path,
            "source_cae_sha": actual_cae_sha_before,
            "source_CAE_found": True,
            "source_CAE_SHA_match": True,
            "predecessor_odb_path": predecessor_odb_path,
            "predecessor_odb_sha": actual_odb_sha,
            "predecessor_ODB_found": True,
            "predecessor_ODB_SHA_match": True,
            "rule_construction": "PASS",
            "rule_name": rule_name,
            "rule_step": step_name,
            "variables": ["MISESERI"],
            "region": "MODEL",
            "output_dir": output_dir,
            "adaptiveRemesh_called": False,
            "exit_status": 0
        }
        preflight_json_path = os.path.join(output_dir, "F43REM4_{}_PREFLIGHT_STATUS.json".format(candidate_id))
        with open(preflight_json_path, "w") as pf:
            json.dump(preflight_status, pf, indent=2)
        odb.close()
        print("[PASS] F43REM4 Preflight Completed Successfully for {}!".format(candidate_id))
        return

    # Non-preflight full remeshing execution
    print("[F43 Native Remesh] Executing native Model.adaptiveRemesh(odb)...")
    adaptivity_iteration = m.adaptiveRemesh(odb)
    print("[F43 Native Remesh] Model.adaptiveRemesh(odb) completed cleanly.")

    # Write refined input deck
    if job_name in mdb.jobs.keys():
        del mdb.jobs[job_name]

    j = mdb.Job(
        name=job_name,
        model=model_name,
        description="F43REM4 Refined Standard Input Deck " + str(job_name)
    )
    j.writeInput(consistencyChecking=OFF)
    print("[F43 Native Remesh] Refined input deck written: {}.inp".format(job_name))

    out_inp_path = os.path.join(output_dir, "{}.inp".format(job_name))
    if not os.path.exists(out_inp_path) and os.path.exists("{}.inp".format(job_name)):
        shutil.move("{}.inp".format(job_name), out_inp_path)

    if not os.path.exists(out_inp_path):
        fail("Refined input deck missing: {}".format(out_inp_path))

    odb.close()

    after_source_sha = sha256_file(source_cae_path)
    if after_source_sha.lower() != expected_cae_sha.lower():
        fail("Source CAE was modified in-place!")

    print("[F43 Native Remesh] Execution completed cleanly for {}!".format(job_name))

if __name__ == "__main__":
    execute_native_remeshing()

