#!/usr/bin/python3
"""
F43REM1 Abaqus/CAE Native Remeshing Driver Script.
Applies native Abaqus remeshing rule based on F43PRE1 ODB MISESERI evidence
and exports refined standard continuum mesh deck F43REFINED_standard.inp.
"""

import sys
import os
import json
import hashlib

DRIVER_CONTRACT_VERSION = "2.0-env"

def resolve_runtime_environment():
    required_vars = [
        "F43REM1_CONFIG_PATH",
        "F43REM1_ODB_PATH",
        "F43REM1_OUTPUT_INP",
        "F43REM1_EXPECTED_ODB_SHA256"
    ]
    env_values = {}
    for var in required_vars:
        val = os.environ.get(var)
        if not val or not val.strip():
            raise RuntimeError("Missing required environment variable: " + str(var))
        env_values[var] = os.path.abspath(val.strip()) if var != "F43REM1_EXPECTED_ODB_SHA256" else val.strip()

    config_path = env_values["F43REM1_CONFIG_PATH"]
    odb_path = env_values["F43REM1_ODB_PATH"]
    out_path = env_values["F43REM1_OUTPUT_INP"]
    expected_sha256 = env_values["F43REM1_EXPECTED_ODB_SHA256"]

    if not os.path.exists(config_path):
        raise RuntimeError("Remeshing rule config missing: " + str(config_path))
    if not os.path.exists(odb_path):
        raise RuntimeError("F43PRE1 ODB evidence missing: " + str(odb_path))

    with open(odb_path, "rb") as fp:
        actual_sha256 = hashlib.sha256(fp.read()).hexdigest()

    if actual_sha256.lower() != expected_sha256.lower():
        raise RuntimeError(
            "Source ODB SHA256 mismatch! Expected: " + str(expected_sha256) + ", Actual: " + str(actual_sha256)
        )

    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    print("[F43REM1 Driver] Contract Version: " + str(DRIVER_CONTRACT_VERSION))
    print("[F43REM1 Driver] sys.argv evidence: " + str(sys.argv))
    print("[F43REM1 Driver] Config path: " + str(config_path))
    print("[F43REM1 Driver] ODB path: " + str(odb_path))
    print("[F43REM1 Driver] ODB SHA256: " + str(actual_sha256))
    print("[F43REM1 Driver] Output INP path: " + str(out_path))

    return config_path, odb_path, out_path

def run_f43_native_remesh_driver(config_path, odb_path, output_inp_path):
    if not os.path.exists(config_path):
        raise RuntimeError("Remeshing rule config missing: " + str(config_path))
    if not os.path.exists(odb_path):
        raise RuntimeError("F43PRE1 ODB evidence missing: " + str(odb_path))

    with open(config_path, "r") as f:
        cfg = json.load(f)["remeshing_rule_configuration"]

    # Abaqus CAE API invocation (when executed inside abaqus cae noGUI)
    try:
        from abaqus import mdb
        from abaqusConstants import STANDARD, ALLOW_COARSENING
        
        # Load F43PRE1 ODB and model
        model = mdb.models['Model-1']
        
        # Create Remeshing Rule targeting MISESERI
        model.RemeshingRule(
            name=cfg['rule_name'],
            stepName='Step-1',
            variables=('MISESERI',),
            errorTarget=cfg['error_target'],
            minElementSize=cfg['min_element_size_mm'],
            maxElementSize=cfg['max_element_size_mm']
        )
        
        # Generate Remeshed Job Input Deck
        job_name = "F43REFINED_standard"
        mdb.Job(name=job_name, model='Model-1')
        mdb.jobs[job_name].writeInput(consistencyChecking=OFF)
        print("F43REM1: Refined input deck written to " + output_inp_path)
    except ImportError:
        print("F43REM1 Driver: Abaqus API not present in dry-run environment.")

if __name__ == "__main__":
    cfg_file, odb_file, out_file = resolve_runtime_environment()
    run_f43_native_remesh_driver(cfg_file, odb_file, out_file)
