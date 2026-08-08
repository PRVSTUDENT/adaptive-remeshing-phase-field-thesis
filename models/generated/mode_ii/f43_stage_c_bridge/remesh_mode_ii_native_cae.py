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

def execute_native_remeshing():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    manifest_path = os.path.join(script_dir, "F43REM3_NATIVE_MANIFEST.json")

    if not os.path.exists(manifest_path):
        print("FATAL ERROR: Manifest file missing: {}".format(manifest_path))
        sys.exit(1)

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    source_cae_path = manifest["source_cae_path"]
    expected_cae_sha = manifest["source_cae_sha256"]
    predecessor_odb_path = os.path.join(script_dir, manifest["predecessor_odb_path"])
    expected_odb_sha = manifest["predecessor_odb_sha256"]

    print("[F43REM3 Native] Verifying pre-execution file integrity...")
    if not os.path.exists(source_cae_path):
        print("FATAL ERROR: Source CAE missing: {}".format(source_cae_path))
        sys.exit(1)

    actual_cae_sha = sha256_file(source_cae_path)
    if actual_cae_sha != expected_cae_sha:
        print("FATAL ERROR: Source CAE SHA mismatch! Expected {}, got {}".format(expected_cae_sha, actual_cae_sha))
        sys.exit(1)

    if not os.path.exists(predecessor_odb_path):
        print("FATAL ERROR: Predecessor ODB missing: {}".format(predecessor_odb_path))
        sys.exit(1)

    actual_odb_sha = sha256_file(predecessor_odb_path)
    if actual_odb_sha != expected_odb_sha:
        print("FATAL ERROR: Predecessor ODB SHA mismatch! Expected {}, got {}".format(expected_odb_sha, actual_odb_sha))
        sys.exit(1)

    # Create runtime writable COPY of source CAE
    work_cae_path = os.path.join(script_dir, "_runtime_work_copy.cae")
    if os.path.exists(work_cae_path):
        os.remove(work_cae_path)
    shutil.copy2(source_cae_path, work_cae_path)
    print("[F43REM3 Native] Created writable work copy CAE: {}".format(work_cae_path))

    from abaqus import mdb, openMdb
    from odbAccess import openOdb
    import job

    print("[F43REM3 Native] Opening work copy MDB read-write...")
    openMdb(pathName=work_cae_path)

    model_name = mdb.models.keys()[0]
    m = mdb.models[model_name]
    print("[F43REM3 Native] Loaded model: {}".format(model_name))

    print("[F43REM3 Native] Opening predecessor ODB read-only...")
    odb = openOdb(pathName=predecessor_odb_path, readOnly=True)

    # Configure remeshing rule
    remesh_params = manifest["remesh_parameters"]
    rule_name = "StageC_MISESERI_RemeshingRule"

    if rule_name in m.remeshingRules.keys():
        del m.remeshingRules[rule_name]

    inst_name = m.rootAssembly.instances.keys()[0]
    inst = m.rootAssembly.instances[inst_name]

    m.RemeshingRule(
        name=rule_name,
        description="Stage C MISESERI Native Adaptive Remeshing Rule",
        region=(inst,),
        errorIndicator="MISESERI",
        errorTarget=remesh_params["error_target"],
        refinementFactor=remesh_params["refinement_factor"],
        minElementSize=remesh_params["min_element_size_mm"],
        maxElementSize=remesh_params["max_element_size_mm"]
    )
    print("[F43REM3 Native] Created remeshing rule: {}".format(rule_name))

    # Execute native adaptive remeshing
    print("[F43REM3 Native] Executing native adaptive remeshing operation...")
    m.rootAssembly.remesh(remeshingRule=rule_name, odb=odb)
    print("[F43REM3 Native] Native remeshing completed.")

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
    print("[F43REM3 Native] Refined input deck written: {}.inp".format(job_name))

    odb.close()

    # Confirm source CAE was never modified in-place
    after_source_sha = sha256_file(source_cae_path)
    if after_source_sha != expected_cae_sha:
        print("FATAL ERROR: Source CAE was modified in-place!")
        sys.exit(1)

    print("[F43REM3 Native] Execution completed cleanly.")

if __name__ == "__main__":
    execute_native_remeshing()
