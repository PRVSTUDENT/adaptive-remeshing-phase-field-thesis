# -*- coding: utf-8 -*-
import os, sys
from abaqus import mdb, backwardCompatibility
from abaqusConstants import UNIFORM_ERROR, ALL_ELEM, DEFAULT_LIMIT
backwardCompatibility.setValues(includeDeprecated=True, reportDeprecated=False)

repo_root = r"D:\Master thesis\Adaptive remeshing"
sys.path.append(os.path.join(repo_root, "scripts", "remeshing"))
from reusable_2d_adaptive_framework import AdaptiveConfig, get_geometry_adapter, AbaqusNativeRemeshingEngine

cfg_path = os.path.join(repo_root, "configs", "remeshing", "f1728_case1_mode1_edge_crack.json")
cfg = AdaptiveConfig.from_json(cfg_path)
adapter = get_geometry_adapter(cfg)

m = mdb.Model(name="Model-Remesh")
p, a, inst = AbaqusNativeRemeshingEngine.build_cae_geometry(
    m, adapter, cfg, seed_size=0.015, part_name="PART-1", instance_name="PART-1-1"
)
p.generateMesh()
m.rootAssembly.regenerate()

rr = m.RemeshingRule(
    name="RemeshRule-1",
    description="Test B Remeshing Rule",
    region=inst.sets["ALL_ELEM"],
    variables=("MISESERI",),
    sizingMethod=UNIFORM_ERROR,
    errorTarget=cfg.error_target,
    minElementSize=0.001,
    maxElementSize=0.020,
    coarseningFactor=DEFAULT_LIMIT,
    refinementFactor=10
)

donor_odb_path = r"D:\Master thesis\Adaptive remeshing\runs\test_b_indicator_perturbation\DONOR_HORIZ.odb"
from odbAccess import openOdb
odb_donor = openOdb(donor_odb_path)
m.adaptiveRemesh(odb=odb_donor)
odb_donor.close()

j = mdb.Job(name="Job-Remesh", model="Model-Remesh")
j.writeInput(consistencyChecking=False)
job_inp = "Job-Remesh.inp"
out_inp = r"D:\Master thesis\Adaptive remeshing\runs\test_b_indicator_perturbation\horiz\PK_ADAPT_CASE_1_PHYS.inp"
import shutil
if os.path.exists(job_inp):
    if os.path.exists(out_inp):
        try: os.remove(out_inp)
        except Exception: pass
    shutil.move(job_inp, out_inp)
print("REMESH_COMPLETED: " + out_inp)
