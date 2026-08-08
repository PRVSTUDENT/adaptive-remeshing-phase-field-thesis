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

    manifest_path = os.environ.get(
        "F43REM4_CONFIG_PATH",
        os.environ.get(
            "F43REM3_MANIFEST_PATH",
            os.environ.get("F43REM2_MANIFEST_PATH", os.path.join(script_dir, "F43REM3_NATIVE_MANIFEST.json")),
        ),
    )

    if not os.path.exists(manifest_path):
        fail("Manifest/Config file missing: {}".format(manifest_path))

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    # Predecessor ODB check
    expected_odb_sha = "9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1"
    predecessor_odb_path = os.environ.get(
        "PREDECESSOR_ODB_PATH",
        os.path.join(script_dir, "evidence", "1385461.mmaster02", "F43PRE3_GEOM.odb")
    )
    if not os.path.exists(predecessor_odb_path):
        # Fallback to local file in cwd if available
        if os.path.exists("F43PRE3_GEOM.odb"):
            predecessor_odb_path = os.path.abspath("F43PRE3_GEOM.odb")
        else:
            fail("Predecessor ODB missing: {}".format(predecessor_odb_path))

    actual_odb_sha = sha256_file(predecessor_odb_path)
    if actual_odb_sha.lower() != expected_odb_sha.lower():
        fail("Predecessor ODB SHA mismatch! Expected {}, got {}".format(expected_odb_sha, actual_odb_sha))

    # Source CAE check
    expected_cae_sha = "0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa"
    source_cae_path = os.environ.get(
        "SOURCE_CAE_PATH",
        os.path.join(script_dir, "ModeII_Geometry_Source_Abaqus2023.cae")
    )
    if not os.path.exists(source_cae_path):
        ext_cae = "/home/pr21vyci/projects/adaptive-remeshing-artifacts/f43pre3/ModeII_Geometry_Source_Abaqus2023.cae"
        if os.path.exists(ext_cae):
            source_cae_path = ext_cae
        elif os.path.exists("ModeII_Geometry_Source.cae"):
            source_cae_path = os.path.abspath("ModeII_Geometry_Source.cae")
        else:
            fail("Source CAE missing: {}".format(source_cae_path))

    actual_cae_sha_before = sha256_file(source_cae_path)
    if actual_cae_sha_before.lower() != expected_cae_sha.lower():
        fail("Source CAE SHA mismatch! Expected {}, got {}".format(expected_cae_sha, actual_cae_sha_before))

    # Writable copy of CAE
    work_cae_path = "/tmp/f43_remesh_work_copy_{}.cae".format(os.getpid())
    if os.path.exists(work_cae_path):
        os.remove(work_cae_path)

    shutil.copyfile(source_cae_path, work_cae_path)
    work_cae_sha_before = sha256_file(work_cae_path)

    from abaqus import mdb, openMdb
    from abaqusConstants import MODEL, UNIFORM_ERROR, MINIMUM_MAXIMUM, NOT_ALLOWED, ON, OFF
    from odbAccess import openOdb

    print("[F43 Native Remesh] Opening writable copy of CAE: {}".format(work_cae_path))
    openMdb(pathName=work_cae_path)

    model_name = "ModeII_Geometry_Model"
    if model_name not in mdb.models.keys():
        fail("Model {} missing from CAE database!".format(model_name))
    m = mdb.models[model_name]

    cae_model_steps = list(m.steps.keys())
    step_name = "Step-1"
    if step_name not in cae_model_steps:
        fail("Step-1 missing from model steps: {}".format(cae_model_steps))

    odb = openOdb(predecessor_odb_path, readOnly=True)

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

    print("[F43 Native Remesh] Verified remeshing rule: {}".format(rule_name))

    # Pre-execution assertions
    if not hasattr(m, 'adaptiveRemesh'):
        fail("Model object has no adaptiveRemesh method in installed Abaqus CAE environment!")

    if hasattr(m.rootAssembly, 'remesh'):
        fail("Assembly.remesh is forbidden!")

    # Execute native adaptive remeshing via Model API
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

    out_inp_path = "{}.inp".format(job_name)
    if not os.path.exists(out_inp_path):
        fail("Refined input deck missing: {}".format(out_inp_path))

    odb.close()

    after_source_sha = sha256_file(source_cae_path)
    if after_source_sha.lower() != expected_cae_sha.lower():
        fail("Source CAE was modified in-place!")

    print("[F43 Native Remesh] Execution completed cleanly for {}!".format(job_name))

if __name__ == "__main__":
    execute_native_remeshing()
