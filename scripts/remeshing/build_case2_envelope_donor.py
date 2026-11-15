# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_case2_envelope_donor.py
===============================================
Synthesizes an authentic advancing damage envelope from the 338-frame
coupled fracture donor PK_HOLE_COARSE_JOB1.odb into an inverted sizing
donor ODB PK_F1779_CASE2_ENVELOPE.odb for Case 2 (Plate with an Off-Axis Hole).

Eliminates linear-elastic pre-analysis stress decay across the secondary ligament
by using genuine physical phase-field damage indicator information from the
advancing crack trajectory.
"""
from __future__ import print_function
import os
import sys
import math
import shutil
from odbAccess import openOdb
from abaqusConstants import SCALAR, WHOLE_ELEMENT

def analytical_damage_sizing(d, l0=0.0075, h_bg=0.020):
    # Core crack path (d >= 0.5): refine densely to h <= l0/2.5 = 0.0030 mm
    # Process zone (0.1 <= d < 0.5): transition to l0 = 0.0075 mm
    # Far-field bulk: transition to background h_bg = 0.020 mm
    h_core = l0 / 2.5   # 0.0030 mm = 3.0 um
    h_proc = l0 / 1.2   # 0.00625 mm = 6.25 um
    if d >= 0.5:
        return h_core
    elif d >= 0.1:
        frac = (d - 0.1) / (0.5 - 0.1)
        return h_proc - frac * (h_proc - h_core)
    elif d >= 0.01:
        frac = (d - 0.01) / (0.1 - 0.01)
        return h_bg - frac * (h_bg - h_proc)
    else:
        return h_bg

def build_case2_envelope(source_odb, target_odb, error_target=0.023):
    print("=== BUILDING CASE 2 ADVANCING CRACK ENVELOPE DONOR ===")
    print("Source ODB: %s" % source_odb)
    print("Target ODB: %s" % target_odb)
    print("Error Target: %.4f" % error_target)

    odb_src = openOdb(source_odb, readOnly=True)
    inst_src = odb_src.rootAssembly.instances['PART-1-1']
    umatelem_set = inst_src.elementSets['UMATELEM']
    target_elements = list(umatelem_set.elements)
    elem_labels = [e.label for e in target_elements]
    print("Target visualizer elements: %d (labels %d to %d)" % (len(elem_labels), min(elem_labels), max(elem_labels)))

    node_coords = {}
    for node in inst_src.nodes:
        node_coords[node.label] = (node.coordinates[0], node.coordinates[1])

    elem_h_old = {}
    evol_data = []
    for elem in target_elements:
        conn = elem.connectivity
        pts = [node_coords[nl] for nl in conn]
        if len(pts) == 4:
            x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]; x4, y4 = pts[3]
            area = 0.5 * abs((x1*y2 - x2*y1) + (x2*y3 - x3*y2) + (x3*y4 - x4*y3) + (x4*y1 - x1*y4))
        elif len(pts) == 3:
            x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]
            area = 0.5 * abs(x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))
        else:
            area = 0.0004
        elem_h_old[elem.label] = math.sqrt(max(1e-12, area))
        evol_data.append((area,))

    step2 = odb_src.steps['Step-2']
    n_frames = len(step2.frames)
    print("Scanning max damage d across %d frames of Step-2..." % n_frames)

    d_max_env = {el: 0.0 for el in elem_labels}
    # Sample every 5 frames to capture advancing front envelope
    frame_indices = list(range(0, n_frames, 5))
    if (n_frames - 1) not in frame_indices:
        frame_indices.append(n_frames - 1)

    for f_idx in frame_indices:
        f = step2.frames[f_idx]
        sdv1_fo = f.fieldOutputs['SDV1']
        for v in sdv1_fo.values:
            el = v.elementLabel
            if el in d_max_env:
                if v.data > d_max_env[el]:
                    d_max_env[el] = v.data

    core_elems = sum(1 for el, d in d_max_env.items() if d >= 0.5)
    proc_elems = sum(1 for el, d in d_max_env.items() if 0.1 <= d < 0.5)
    print("Damage envelope extracted:")
    print("  Core crack elements (d >= 0.5): %d" % core_elems)
    print("  Process zone elements (0.1 <= d < 0.5): %d" % proc_elems)
    print("  Max damage in envelope: %.4f" % max(d_max_env.values()))
    odb_src.close()

    s_base = 100.0
    eri_vals = []
    avg_vals = []
    for el in elem_labels:
        d = max(0.0, min(1.0, d_max_env[el]))
        h_tgt = analytical_damage_sizing(d)
        h_old = elem_h_old[el]
        eta_hat = error_target * (h_old / h_tgt)
        eri = s_base * eta_hat
        eri_vals.append((eri,))
        avg_vals.append((s_base,))

    # Create target ODB with the envelope frame
    target_dir = os.path.dirname(target_odb)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir)
    if os.path.exists(target_odb):
        os.remove(target_odb)
    print("Copying template to %s..." % target_odb)
    shutil.copyfile(source_odb, target_odb)

    print("Opening target ODB read-write...")
    odb_dst = openOdb(target_odb, readOnly=False)
    inst_dst = odb_dst.rootAssembly.instances['PART-1-1']
    step2_dst = odb_dst.steps['Step-2']

    print("Adding single envelope frame (frameId=9999)...")
    env_frame = step2_dst.Frame(frameId=9999, frameValue=999.0, description="Advancing Crack Temporal Damage Envelope")

    fo_evol = env_frame.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)
    fo_evol.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=elem_labels, data=evol_data)

    fo_eri = env_frame.FieldOutput(name='MISESERI', description='Temporal Error Envelope from Advancing Crack Front', type=SCALAR)
    fo_eri.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=elem_labels, data=eri_vals)

    fo_avg = env_frame.FieldOutput(name='MISESAVG', description='Uniform Reference Average Stress', type=SCALAR)
    fo_avg.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=elem_labels, data=avg_vals)

    print("Saving target ODB...")
    odb_dst.save()
    odb_dst.close()
    print("SUCCESS: Target envelope ODB created in %s" % target_odb)
    return target_odb

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\176_method_a_plate_with_hole\PK_HOLE_COARSE_JOB1.odb"
    dst = sys.argv[2] if len(sys.argv) > 2 else r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\224_f1734_case2_distal_refinement\PK_F1779_CASE2_ENVELOPE.odb"
    build_case2_envelope(src, dst)
