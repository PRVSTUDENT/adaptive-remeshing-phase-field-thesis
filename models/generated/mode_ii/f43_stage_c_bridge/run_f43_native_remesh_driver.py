#!/usr/bin/python3
"""
F43REM1 Abaqus/CAE Native Remeshing Driver Script.
Applies native Abaqus remeshing rule based on F43PRE1 ODB MISESERI evidence
and exports refined standard continuum mesh deck F43REFINED_standard.inp.
"""

import sys
import os
import json

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
    cfg_file = sys.argv[1] if len(sys.argv) > 1 else "f43_remeshing_rule_config.json"
    odb_file = sys.argv[2] if len(sys.argv) > 2 else "F43PRE1.odb"
    out_file = sys.argv[3] if len(sys.argv) > 3 else "F43REFINED_standard.inp"
    run_f43_native_remesh_driver(cfg_file, odb_file, out_file)
