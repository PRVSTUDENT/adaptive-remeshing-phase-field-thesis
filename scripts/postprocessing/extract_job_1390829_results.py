#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extraction and Post-Processing for Job 1390829.mmaster02
Package: M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL
"""

import os
import sys
import json
from odbAccess import openOdb

def extract():
    pkg_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL"
    odb_path = os.path.join(pkg_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL.odb")
    json_path = os.path.join(pkg_dir, "postprocessing_summary.json")
    
    odb = openOdb(odb_path, readOnly=True)
    num_steps = len(odb.steps)
    print("ODB Path: %s" % odb_path)
    print("Steps in ODB: %d" % num_steps)
    
    total_frames = 0
    if num_steps > 0:
        step = odb.steps.values()[0]
        total_frames = len(step.frames)
        print("Frames in Step 1: %d" % total_frames)
    odb.close()
    
    summary = {
        "job_id": "1390829.mmaster02",
        "job_name": "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL",
        "scheduler_status": "FAILED_LAUNCHER_INTERPRETER_DEFECT (Exit_status = 126)",
        "solver_executed": False,
        "total_frames": total_frames,
        "note": "Abaqus solver was not invoked due to PBS shebang CRLF defect (/bin/bash\\r). ODB contains only pre-submission datacheck Frame 0."
    }
    
    with open(json_path, "w") as fp:
        json.dump(summary, fp, indent=2)
        
    print("Summary written to: %s" % json_path)

if __name__ == "__main__":
    extract()
