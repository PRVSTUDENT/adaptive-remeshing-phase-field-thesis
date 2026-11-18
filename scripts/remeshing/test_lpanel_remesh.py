"""Test L-panel damage envelope remeshing under Abaqus CAE."""
from __future__ import print_function
import os, sys, json, time, hashlib, shutil

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.generalized_2d_adaptive_framework_driver_selection_f1852 import select_driver, remesh
from scripts.remeshing.generalized_2d_adaptive_framework_damage_envelope_f1849 import (
    AdaptiveConfig, AbaqusNativeRemeshingEngine, AdvancingDamageEnvelopeBuilder,
    MeshQualityAuditEngine, get_geometry_adapter
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
    print("Testing L-panel damage envelope remesh...")
    base_dir = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '285_f1856_lpanel_damage_envelope_remesh')
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # 1. Check signal
    snapshot_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '284_f1855_lpanel_fracture_job1', 'lpanel_coarse_final_snapshot.json')
    with open(snapshot_path, 'r') as f:
        snap = json.load(f)

    max_d = float(snap['max_damage'])
    d_core = 0.5
    fields = snap['mesh_fields']['fields']
    sdv1_max_list = fields['SDV1_MAX']
    elements_ge_core = sum([1 for el, d in sdv1_max_list if d >= d_core])
    fraction_ge_core = float(elements_ge_core) / float(len(sdv1_max_list))

    signal = {
        'source': snapshot_path,
        'source_odb_sha256': snap['source_odb_sha256'],
        'max_damage': max_d,
        'd_core': d_core,
        'elements_ge_core': elements_ge_core,
        'fraction_ge_core': fraction_ge_core,
        'total_elements': len(sdv1_max_list)
    }
    print("Signal measured:", signal)

    # 2. Build damage envelope ODB
    src_odb = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '284_f1855_lpanel_fracture_job1', 'PK_F1855_LPANEL_COARSE_JOB1.odb')
    env_odb = os.path.join(base_dir, 'PK_F1856_LPANEL_DAMAGE_ENVELOPE.odb')

    cfg_path = os.path.join(REPO_ROOT, 'configs', 'remeshing', 'f1846_unfamiliar_l_panel.json')
    cfg = AdaptiveConfig.from_json(cfg_path)
    cfg.step_name = 'Step-2'
    cfg.sizing_driver = 'CONSTRUCTED_DAMAGE_ENVELOPE'
    cfg.output_frequency = 'LAST_INCREMENT'

    print("Building damage envelope ODB...")
    t0 = time.time()
    AdvancingDamageEnvelopeBuilder.build_envelope_odb(
        src_odb, env_odb,
        l0=cfg.l0, h_bg=cfg.max_h, error_target=cfg.error_target / 100.0,
        step_name='Step-2', damage_variable='SDV1', frame_stride=5, s_base=100.0
    )
    print("Envelope ODB built in %.2f s: %s (%d bytes)" % (time.time() - t0, env_odb, os.path.getsize(env_odb)))

    # 3. Execute remesh
    out_dir = os.path.join(base_dir, 'fracture_remesh')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    print("Executing remesh via F1852 driver selection...")
    t1 = time.time()
    native_gate_dummy = {'accepted': False}
    inp_path, driver = remesh(cfg, signal, native_gate_dummy, env_odb, None, out_dir, 'F1856_LPANEL_FRACTURE')
    remesh_sec = time.time() - t1
    print("Remesh completed in %.2f s: driver=%s, inp=%s" % (remesh_sec, driver, inp_path))

    # 4. Audit mesh
    adapter = get_geometry_adapter(cfg)
    audit = MeshQualityAuditEngine.evaluate_mesh(inp_path, l0_mm=cfg.l0, adapter=adapter)
    b_sha = body_sha256(inp_path)
    audit.update(
        body_sha256=b_sha,
        mesh_sha256=sha256_file(inp_path),
        driver=driver,
        remesh_seconds=remesh_sec
    )
    print("Audit results:")
    print("  Total elements:", audit['total_elements'])
    print("  Quad percent:", audit['quad_percent'])
    print("  Min det(J):", audit['min_det_j'])
    print("  Max aspect ratio:", audit['max_aspect_ratio'])
    print("  Refinement ratio far-to-core (Gate 06):", audit['refinement_ratio_far_to_core'])
    print("  Body SHA-256:", b_sha)

if __name__ == '__main__':
    main()
