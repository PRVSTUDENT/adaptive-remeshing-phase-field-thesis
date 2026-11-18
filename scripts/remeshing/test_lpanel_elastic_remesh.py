"""Test L-panel native fallback remeshing under Abaqus CAE (F1854 completion)."""
from __future__ import print_function
import os, sys, json, time, hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.generalized_2d_adaptive_framework_driver_selection_f1852 import select_driver, remesh
from scripts.remeshing.generalized_2d_adaptive_framework_damage_envelope_f1849 import (
    AdaptiveConfig, MeshQualityAuditEngine, get_geometry_adapter
)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1048576), b''):
            h.update(c)
    return h.hexdigest()

def body_sha256(p):
    h = hashlib.sha256()
    with open(p, 'r') as f:
        for line in f:
            stripped = line.strip()
            if not stripped.startswith('**'):
                h.update((stripped + '\n').encode('utf-8'))
    return h.hexdigest()

def main():
    print("Testing L-panel native fallback remesh...")
    base_dir = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '285_f1856_lpanel_damage_envelope_remesh')
    out_dir = os.path.join(base_dir, 'elastic_fallback_remesh')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    native_donor = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '276_f1846_generalized_framework', 'l_panel', 'PK_F1846_LPANEL_COARSE.odb')
    assert os.path.exists(native_donor), "Native donor ODB missing!"

    cfg_path = os.path.join(REPO_ROOT, 'configs', 'remeshing', 'f1846_unfamiliar_l_panel.json')
    cfg = AdaptiveConfig.from_json(cfg_path)
    cfg.step_name = 'Step-1'

    signal = {
        'source': native_donor,
        'max_damage': 0.0,
        'd_core': 0.5,
        'elements_ge_core': 0,
        'fraction_ge_core': 0.0,
        'total_elements': 340
    }

    native_gate = {
        'accepted': True,
        'step': 'Step-1',
        'source': native_donor,
        'source_sha256': sha256_file(native_donor),
        'source_bytes': os.path.getsize(native_donor)
    }

    driver = select_driver(signal, native_gate)
    print("Selected driver for elastic donor:", driver)
    assert driver == 'NATIVE_ABAQUS_STRESS_RECOVERY_ERROR', "Driver selection mismatch!"

    t0 = time.time()
    inp_path, driver_used = remesh(cfg, signal, native_gate, None, native_donor, out_dir, 'F1856_LPANEL_ELASTIC_FALLBACK')
    remesh_sec = time.time() - t0
    print("Native fallback remesh completed in %.2f s: inp=%s" % (remesh_sec, inp_path))

    adapter = get_geometry_adapter(cfg)
    audit = MeshQualityAuditEngine.evaluate_mesh(inp_path, l0_mm=cfg.l0, adapter=adapter)
    b_sha = body_sha256(inp_path)

    f1846_baseline_inp = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '276_f1846_generalized_framework', 'l_panel', 'PK_F1846_UNFAMILIAR_L_PANEL_ADAPT_PHYS.inp')
    f1846_b_sha = body_sha256(f1846_baseline_inp)

    print("Native fallback audit results:")
    print("  Total elements:", audit['total_elements'])
    print("  F1846 baseline elements: 567")
    print("  Quad percent:", audit['quad_percent'])
    print("  Min det(J):", audit['min_det_j'])
    print("  Max aspect ratio:", audit['max_aspect_ratio'])
    print("  Refinement ratio far-to-core (Gate 06):", audit['refinement_ratio_far_to_core'])
    print("  Generated Body SHA-256:", b_sha)
    print("  F1846 baseline Body SHA-256:", f1846_b_sha)
    print("  Body identical to F1846:", b_sha == f1846_b_sha)

if __name__ == '__main__':
    main()
