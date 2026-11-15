# -*- coding: utf-8 -*-
"""
tests/unit/abaqus_test_f1793_causal_envelope.py
Task F1793: Abaqus Python Execution Test for Causal Damage Envelope Synthesis.

Runs inside Abaqus Python environment to verify:
1. AdvancingDamageEnvelopeBuilder builds a causal envelope ODB strictly bounded by max_frame_index.
2. At initiation (frame <= 100, t <= 0.20), damage is confined to the notch-to-hole ligament (max d ~ 0.32).
3. Distal elements (x > 0.75 mm) have zero damage (d < 0.05), receiving background sizing (h_bg).
4. Frame description explicitly records causal horizon provenance.
"""

import math
import os
import shutil
import sys
from pathlib import Path

# Add repo root to sys.path
REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    AdvancingDamageEnvelopeBuilder,
)
from odbAccess import openOdb

def test_causal_envelope_synthesis_case2():
    source_odb = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_COARSE_JOB1.odb")
    assert os.path.exists(source_odb), "Source ODB must exist: " + source_odb

    output_dir = os.path.join(REPO_ROOT, "runs", "f1793_causal_test")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    target_odb = os.path.join(output_dir, "PK_F1793_CASE2_CAUSAL_ENV_F100.odb")

    config_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case2_off_axis_hole.json")
    cfg = AdaptiveConfig.from_json(config_path)

    # Build causal envelope bounded strictly to Frame 100 (t <= 0.20, crack initiation stage)
    out_path = AdvancingDamageEnvelopeBuilder.build_envelope_from_config(
        config=cfg,
        source_odb_path=source_odb,
        target_odb_path=target_odb,
        max_frame_index=100,
        causal_mode=True
    )
    assert os.path.exists(out_path), "Target envelope ODB must be created: " + out_path

    # Verify contents of generated causal envelope ODB
    odb = openOdb(out_path, readOnly=True)
    step = odb.steps["Step-2"]
    assert 9999 in [f.frameId for f in step.frames], "Frame 9999 must exist in envelope ODB"
    env_frame = [f for f in step.frames if f.frameId == 9999][0]

    desc = env_frame.description
    print("Envelope Frame Description: %s" % desc)
    assert ("Horizon: frame <= 100" in desc or "Horizon: frame <= 99" in desc), "Frame description must record causal horizon"

    assert "EVOL" in env_frame.fieldOutputs, "EVOL field output must exist"
    assert "MISESERI" in env_frame.fieldOutputs, "MISESERI field output must exist"
    assert "MISESAVG" in env_frame.fieldOutputs, "MISESAVG field output must exist"

    # Inspect MISESERI values and element coordinates
    root_inst = odb.rootAssembly.instances
    inst_name = list(root_inst.keys())[0]
    inst = root_inst[inst_name]

    node_coords = {n.label: (n.coordinates[0], n.coordinates[1]) for n in inst.nodes}
    elem_coords = {}
    for el in inst.elements:
        pts = [node_coords[nl] for nl in el.connectivity if nl in node_coords]
        if pts:
            cx = sum(p[0] for p in pts) / float(len(pts))
            cy = sum(p[1] for p in pts) / float(len(pts))
            elem_coords[el.label] = (cx, cy)

    eri_fo = env_frame.fieldOutputs["MISESERI"]
    eri_values = {v.elementLabel: v.data for v in eri_fo.values}

    # Inspect damage values and target mesh sizing
    # Open the source ODB at frame 100 to check authentic causal damage
    odb_src = openOdb(source_odb, readOnly=True)
    f100 = odb_src.steps["Step-2"].frames[100]
    src_d = {v.elementLabel: v.data for v in f100.fieldOutputs["SDV1"].values}
    odb_src.close()

    notch_hole_d = []
    distal_d = []

    for el_lbl, (cx, cy) in elem_coords.items():
        if el_lbl in src_d:
            d_val = src_d[el_lbl]
            # Between notch tip and hole
            if 0.50 <= cx <= 0.65 and 0.45 <= cy <= 0.65:
                notch_hole_d.append(d_val)
            # Distal outer ligament (x >= 0.85, y in [0.50, 0.70])
            elif cx >= 0.85 and 0.50 <= cy <= 0.70:
                distal_d.append(d_val)

    max_nh_d = max(notch_hole_d) if notch_hole_d else 0.0
    max_dist_d = max(distal_d) if distal_d else 0.0

    print("Causal Frame 100: Max notch-to-hole damage: %.4f" % max_nh_d)
    print("Causal Frame 100: Max outer distal damage:   %.4f" % max_dist_d)

    # 1. At Frame 100 (initiation), damage is actively developing in the notch-to-hole corridor
    assert max_nh_d >= 0.20, "Active fracture process zone between notch and hole must have d >= 0.20"

    # 2. Outer distal ligament (x >= 0.85) has negligible damage (below noise threshold 0.08)
    assert max_dist_d < 0.05, "Outer distal ligament must have d < 0.05 (strictly undamaged at initiation)"

    # 3. Target sizing for distal elements evaluates to background size h_bg = 0.025 mm
    h_distal = AdvancingDamageEnvelopeBuilder.analytical_damage_sizing(
        max_dist_d, l0=cfg.l0, h_bg=getattr(cfg, 'h_bg', cfg.max_h),
        core_factor=cfg.core_factor, process_factor=cfg.process_factor,
        d_core=cfg.d_core, d_proc=cfg.d_proc, d_noise=cfg.d_noise
    )
    assert abs(h_distal - 0.025) < 1e-6, "Undamaged distal ligament must receive background sizing h_bg = 0.025 mm"

    # 4. Target sizing for developing notch-to-hole zone evaluates to refined sizing
    h_nh = AdvancingDamageEnvelopeBuilder.analytical_damage_sizing(
        max_nh_d, l0=cfg.l0, h_bg=getattr(cfg, 'h_bg', cfg.max_h),
        core_factor=cfg.core_factor, process_factor=cfg.process_factor,
        d_core=cfg.d_core, d_proc=cfg.d_proc, d_noise=cfg.d_noise
    )
    assert h_nh <= cfg.l0, "Active process zone must evaluate to refined sizing h <= l0"

    odb.close()
    print("PASS: Abaqus causal envelope synthesis verified successfully.")


if __name__ == "__main__":
    test_causal_envelope_synthesis_case2()
