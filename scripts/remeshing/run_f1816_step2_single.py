# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1816_step2_single.py
==========================================
Executes native adaptive remeshing in Abaqus CAE for a single case under either
Variant 2a (overlapping native rules) or Variant 2b (reduced 2-state envelope).

Invoked via:
  abaqus cae noGUI=scripts/remeshing/run_f1816_step2_single.py -- <case_id> <variant> <donor_path> <out_dir> <error_target> <job_name> [step_names_comma_separated]
"""
from __future__ import print_function
import os
import sys
import json

from abaqus import mdb, session
from abaqusConstants import *

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.path.join(REPO_ROOT, "scripts", "remeshing") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "remeshing"))

from reusable_2d_adaptive_framework import (
    AdaptiveConfig, get_geometry_adapter, AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine
)

def run_single():
    # Read parameters from JSON file passed as last argument or direct dict
    param_file = sys.argv[-1]
    if not os.path.exists(param_file) or not param_file.endswith(".json"):
        raise ValueError("FAIL_CLOSED: Expected parameter JSON file as last argument, got: %s" % param_file)
        
    with open(param_file, "r") as f:
        params = json.load(f)
        
    case_id = params["case_id"]
    variant = params["variant"] # '2a' or '2b'
    donor_path = params["donor_path"]
    out_dir = params["out_dir"]
    error_target = float(params["error_target"])
    job_name = params["job_name"]
    step_names = params.get("step_names", ["RECOVERY_STEP"])
    
    # Load base config
    cfg_map = {
        "case_1": "configs/remeshing/f1812_case1_native_miseseri.json",
        "case_2": "configs/remeshing/f1809_case2_native_miseseri.json",
        "case_3": "configs/remeshing/f1809_case3_native_miseseri.json",
        "case_5": "configs/remeshing/f1809_case5_native_miseseri.json"
    }
    cfg_file = os.path.join(REPO_ROOT, cfg_map[case_id])
    with open(cfg_file, "r") as f:
        cfg_data = json.load(f)
        
    cfg_data["error_target"] = error_target
    cfg_data["sizing_method"] = "UNIFORM_ERROR"
    cfg = AdaptiveConfig(cfg_data)
    adapter = get_geometry_adapter(cfg)
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    if variant == "2b":
        # Single envelope donor with 1 rule
        print("Executing Variant 2b (Reduced 2-State Envelope) for %s..." % case_id)
        out_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
            config=cfg,
            donor_odb_path=donor_path,
            output_dir=out_dir,
            model_name="Model_F1816_2B_" + case_id,
            adapter_override=adapter,
            output_job_name=job_name
        )
        print("Generated Variant 2b physical mesh: %s" % out_inp)
        
    elif variant == "2a":
        # Multi-step donor with 1 rule per step
        print("Executing Variant 2a (Overlapping Native Rules) for %s across steps: %s..." % (case_id, step_names))
        mname = "Model_F1816_2A_" + case_id
        if mname in mdb.models:
            del mdb.models[mname]
        m = mdb.Model(name=mname)
        if "Model-1" in mdb.models:
            del mdb.models["Model-1"]
            
        first_odb = session.openOdb(name=donor_path)
        target_part_name = list(first_odb.parts.keys())[0] if len(first_odb.parts) > 0 else "PART-1"
        target_inst_name = list(first_odb.rootAssembly.instances.keys())[0] if len(first_odb.rootAssembly.instances) > 0 else "PART-1-1"
        first_odb.close()
        
        seed_size = cfg.max_h
        p, a, inst = AbaqusNativeRemeshingEngine.build_cae_geometry(
            m, adapter, cfg, seed_size, part_name=target_part_name, instance_name=target_inst_name
        )
        
        # Ensure all steps exist in model sequentially
        prev_s = 'Initial'
        for sname in step_names:
            if sname in m.steps:
                prev_s = sname
                continue
            m.StaticStep(name=sname, previous=prev_s, timePeriod=1.0)
            prev_s = sname
            
        # Create one RemeshingRule per step
        coarsen_opt = NOT_ALLOWED if cfg.coarsening_factor == "NOT_ALLOWED" else DEFAULT_LIMIT
        for idx, sname in enumerate(step_names):
            rname = "Rule_2A_%s_s%d" % (case_id, idx + 1)
            m.RemeshingRule(
                name=rname,
                stepName=sname,
                region=inst.sets['ALL_ELEM'],
                variables=('MISESERI',),
                sizingMethod=UNIFORM_ERROR,
                errorTarget=cfg.error_target,
                refinementFactor=cfg.refinement_factor,
                coarseningFactor=coarsen_opt,
                specifyMinSize=True,
                minElementSize=cfg.min_h,
                specifyMaxSize=True,
                maxElementSize=cfg.max_h
            )
            
        # Call adaptiveRemesh once with all overlapping rules
        odb_donor = session.openOdb(name=donor_path)
        m.adaptiveRemesh(odb=odb_donor)
        odb_donor.close()
        
        # Write job input
        if job_name in mdb.jobs:
            del mdb.jobs[job_name]
        j = mdb.Job(name=job_name, model=mname, type=ANALYSIS)
        j.writeInput(consistencyChecking=OFF)
        
        # Move job_name.inp to phys_path
        raw_inp = job_name + ".inp"
        phys_name = job_name + "_PHYS.inp"
        phys_path = os.path.join(out_dir, phys_name)
        target_inp = os.path.join(out_dir, raw_inp)
        if os.path.exists(phys_path):
            os.remove(phys_path)
        if os.path.exists(raw_inp):
            import shutil
            shutil.move(raw_inp, phys_path)
        elif os.path.exists(target_inp):
            import shutil
            shutil.move(target_inp, phys_path)
        print("Generated Variant 2a physical mesh: %s" % phys_path)

if __name__ == "__main__":
    run_single()
