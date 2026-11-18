# -*- coding: utf-8 -*-
"""
scripts/remeshing/test_generate_f1861_uniform_meshes.py
Test generation of uniform highly refined reference meshes for Cases 1, 2, 3, 5.
"""
from __future__ import print_function
import os
import sys
import math

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from abaqus import mdb, session
from abaqusConstants import *

from reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    StraightNotchMode1Adapter,
    OffAxisHoleMode1Adapter,
    NotchedPlateWithPinHolesAdapter,
    SevenHolePlateAdapter,
    AbaqusNativeRemeshingEngine
)

configs = [
    ("case1", r"models\pandey_kumar_mode1\279_f1849_damage_envelope\case1_config.json", 0.00375),
    ("case2", r"models\pandey_kumar_mode1\279_f1849_damage_envelope\case2_config.json", 0.00375),
    ("case3_86k", r"models\pandey_kumar_mode1\279_f1849_damage_envelope\case3_config.json", 0.29),
    ("case3_half_l0", r"models\pandey_kumar_mode1\279_f1849_damage_envelope\case3_config.json", 0.1425),
    ("case5_81k", r"models\pandey_kumar_mode1\279_f1849_damage_envelope\case5_config.json", 0.0033),
    ("case5_half_l0", r"models\pandey_kumar_mode1\279_f1849_damage_envelope\case5_config.json", 0.0040),
]

for name, cfg_path, seed_size in configs:
    cfg = AdaptiveConfig.from_json(cfg_path)
    model_name = "Model_" + name
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    
    if "case1" in name:
        adapter = StraightNotchMode1Adapter(cfg)
    elif "case2" in name:
        adapter = OffAxisHoleMode1Adapter(cfg)
    elif "case3" in name:
        adapter = NotchedPlateWithPinHolesAdapter(cfg)
    elif "case5" in name:
        adapter = SevenHolePlateAdapter(cfg)
    else:
        raise ValueError("Unknown case: " + name)
        
    p, a, inst = AbaqusNativeRemeshingEngine.build_cae_geometry(
        m=m, adapter=adapter, config=cfg, seed_size=seed_size
    )
    
    total_elems = len(p.elements)
    quads = sum([1 for el in p.elements if len(el.connectivity) == 4])
    tris = sum([1 for el in p.elements if len(el.connectivity) == 3])
    quad_pct = float(quads) / total_elems * 100.0 if total_elems > 0 else 0.0
    nodes = len(p.nodes)
    
    print("MESH [%s] (seed=%.5f): %d elements (%d quads [%.2f%%], %d tris), %d nodes" % (
        name, seed_size, total_elems, quads, quad_pct, tris, nodes
    ))
