# -*- coding: utf-8 -*-
import os, sys, json
from abaqus import mdb, backwardCompatibility
from abaqusConstants import FREE, QUAD, TRI, STANDARD, DEFAULT
backwardCompatibility.setValues(includeDeprecated=True, reportDeprecated=False)

repo_root = r"D:\Master thesis\Adaptive remeshing"
sys.path.append(os.path.join(repo_root, "scripts", "remeshing"))
from reusable_2d_adaptive_framework import AdaptiveConfig, get_geometry_adapter, AbaqusNativeRemeshingEngine

cfg_path = r"D:\Master thesis\Adaptive remeshing\configs\remeshing\f1783_test_a_perturbed_case3.json"
cfg = AdaptiveConfig.from_json(cfg_path)
adapter = get_geometry_adapter(cfg)

m = mdb.Model(name="Model-TestA")
p, a, inst = AbaqusNativeRemeshingEngine.build_cae_geometry(
    m, adapter, cfg, seed_size=1.5, part_name="PART-TESTA", instance_name="PART-TESTA-1"
)

# Query actual CAD face area
face_area = p.faces[0].getSize()

# Mesh part
p.generateMesh()
m.rootAssembly.regenerate()

# Write physical mesh
out_inp = r"D:\Master thesis\Adaptive remeshing\runs\test_a_geometry_perturbation\PK_TEST_A_PERT_PHYS.inp"
j = mdb.Job(name="Job-TestA", model="Model-TestA")
j.writeInput(consistencyChecking=False)
job_inp = "Job-TestA.inp"
import shutil
if os.path.exists(job_inp):
    if os.path.exists(out_inp):
        try: os.remove(out_inp)
        except Exception: pass
    shutil.move(job_inp, out_inp)

result = {
    "cad_face_area_mm2": float(face_area),
    "mesh_elements": len(p.elements),
    "mesh_nodes": len(p.nodes)
}
with open(r"D:\Master thesis\Adaptive remeshing\runs\test_a_geometry_perturbation\test_a_cae_output.json", "w") as f:
    json.dump(result, f, indent=2)

print("TEST_A_CAD_FACE_AREA: " + str(face_area))
