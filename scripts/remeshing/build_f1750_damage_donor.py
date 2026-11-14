# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_f1750_damage_donor.py

Task F1750: Local Native Abaqus Damage-Derived Sizing Probe on Case 3 Coarse Mesh.
Constructs the synthetic damage-aware donor ODB:
PK_SEC43_STATE_B_DAMAGE_DONOR.odb

Addresses Independent Review Directive HND-F1749-TIME-CAUSAL-002:
1. Time-causal donor selection:
   - State b (u_y = 0.20 mm, Frame 40, Step-1, RF_2 = 1.9658 kN).
   - Selection rule: Earliest post-initiation state exhibiting macroscopic primary crack
     growth (d_max > 0.99) prior to secondary crack initiation.
2. Inverted native UNIFORM_ERROR sizing interface mapping:
   - Target size: h_target(d_e) from analytical damage sizing heuristic.
   - Old element size: h_old(e) = sqrt(EVOL_e).
   - Error indicator: eta_hat_e = errorTarget * (h_old(e) / h_target(d_e)).
   - MISESERI_e = S_base * eta_hat_e (S_base = 100.0 MPa).
   - MISESAVG_e = S_base = 100.0 MPa.
   - EVOL_e = element area * unit thickness.
3. Explicit reporting of primary target-size weakness:
   - Only 3 of 35 sampled primary-corridor elements request h <= l0/2.
"""
from __future__ import print_function
import os
import sys
import shutil
import math
import json
import odbAccess
from abaqusConstants import *

def analytical_damage_sizing(d, l0=0.285, h_bg=1.3670):
    """
    Computes analytical target element size h(d) from scalar damage d in [0, 1].
    h_core = l0 / 3 = 0.0950 mm
    h_proc = l0 / 2 = 0.1425 mm
    """
    d_core = 0.60653066  # exp(-0.5)
    d_proc = 0.36787944  # exp(-1.0)
    d_diff = 0.05000000

    h_core = l0 / 3.0  # 0.0950 mm
    h_proc = l0 / 2.0  # 0.1425 mm

    if d >= d_core:
        return h_core
    elif d >= d_proc:
        # Linear transition between core and process zone limit
        frac = (d - d_proc) / (d_core - d_proc)
        return h_proc - frac * (h_proc - h_core)
    elif d >= d_diff:
        # Quadratic expansion to background size
        frac = (d - d_diff) / (d_proc - d_diff)
        return h_bg - (h_bg - h_proc) * (frac ** 2)
    else:
        return h_bg

def build_f1750_donor(
    template_odb_path,
    damage_json_path,
    out_odb_path,
    error_target=0.30,
    l0=0.285,
    h_bg=1.3670,
    s_base=100.0
):
    print("=== TASK F1750: BUILDING STATE B DAMAGE-DRIVEN DONOR ODB ===")
    print("  Template ODB: %s" % template_odb_path)
    print("  Damage JSON: %s" % damage_json_path)
    print("  Output ODB:   %s" % out_odb_path)
    print("  Error target: %.4f, l0 = %.4f mm, S_base = %.1f MPa" % (error_target, l0, s_base))

    if not os.path.isfile(template_odb_path):
        raise RuntimeError("Template ODB missing: %s" % template_odb_path)
    if not os.path.isfile(damage_json_path):
        raise RuntimeError("Damage JSON missing: %s" % damage_json_path)

    # 1. Load authentic damage record for State b
    with open(damage_json_path, 'r') as f:
        rec = json.load(f)

    state_b = None
    for s in rec.get('states', []):
        if s.get('state_id') == 'state_b':
            state_b = s
            break
    if state_b is None:
        raise RuntimeError("State b not found in %s" % damage_json_path)

    damage_by_element = state_b['damage_by_element']
    print("  Loaded State b: uy = %.4f mm, rf2 = %.4f kN, frame = %d, elements = %d" % (
        state_b.get('uy_mm', 0.20),
        state_b.get('rf2_kN', 1.9658),
        state_b.get('frame_idx', 40),
        len(damage_by_element)
    ))

    # 2. Open template ODB to read element volumes and labels
    template_odb = odbAccess.openOdb(template_odb_path, readOnly=True)
    root_inst = template_odb.rootAssembly.instances.values()[0]
    n_elems = len(root_inst.elements)
    element_labels = [el.label for el in root_inst.elements]

    step0 = template_odb.steps.values()[0]
    frame0 = step0.frames[-1]
    f_evol_orig = frame0.fieldOutputs['EVOL']

    evol_by_element = {}
    for v in f_evol_orig.values:
        evol_by_element[v.elementLabel] = float(v.data)
    template_odb.close()

    if len(evol_by_element) != n_elems:
        raise RuntimeError("EVOL count mismatch: %d vs %d" % (len(evol_by_element), n_elems))

    # 3. Compute target sizes and inverted error indicator
    target_sizes = {}
    eta_hat = {}
    miseseri_vals = {}
    h_old_vals = {}

    n_active = 0
    n_strict_proc = 0
    n_core = 0

    for lbl in element_labels:
        # Damage from record (convert lbl to string key if needed)
        d_val = float(damage_by_element.get(str(lbl), damage_by_element.get(lbl, 0.0)))
        evol_val = evol_by_element[lbl]
        h_old = math.sqrt(evol_val)
        h_old_vals[lbl] = h_old

        h_target = analytical_damage_sizing(d_val, l0=l0, h_bg=h_bg)
        target_sizes[lbl] = h_target

        if d_val >= 0.05:
            n_active += 1
        if h_target <= (l0 / 2.0):
            n_strict_proc += 1
        if d_val >= 0.6065:
            n_core += 1

        # Inverted relative error indicator:
        # eta_hat_e = errorTarget * (h_old / h_target)
        eta_e = error_target * (h_old / h_target)
        eta_hat[lbl] = eta_e
        miseseri_vals[lbl] = s_base * eta_e

    print("  Computed sizing across %d elements:" % n_elems)
    print("    Active elements (d >= 0.05): %d (%.2f%%)" % (n_active, 100.0 * n_active / n_elems))
    print("    Strict process-zone target (h <= l0/2 = 0.1425 mm): %d (%.2f%%)" % (
        n_strict_proc, 100.0 * n_strict_proc / n_elems
    ))
    print("    Crack-core target (d >= 0.6065, h = 0.0950 mm): %d (%.2f%%)" % (
        n_core, 100.0 * n_core / n_elems
    ))
    all_etas = [eta_hat[lbl] for lbl in element_labels]
    all_targets = [target_sizes[lbl] for lbl in element_labels]
    all_old = [h_old_vals[lbl] for lbl in element_labels]
    print("    Target size [mm]: min = %.4f, mean = %.4f, max = %.4f" % (
        min(all_targets), sum(all_targets) / len(all_targets), max(all_targets)
    ))
    print("    Old size [mm]:    min = %.4f, mean = %.4f, max = %.4f" % (
        min(all_old), sum(all_old) / len(all_old), max(all_old)
    ))
    print("    eta_hat indicator: min = %.4f, mean = %.4f, max = %.4f" % (
        min(all_etas), sum(all_etas) / len(all_etas), max(all_etas)
    ))

    # 4. Create output ODB by copying template
    if os.path.exists(out_odb_path):
        os.remove(out_odb_path)
    shutil.copyfile(template_odb_path, out_odb_path)

    # 5. Open output ODB for writing
    odb = odbAccess.openOdb(out_odb_path, readOnly=False)
    step = odb.steps.values()[0]
    frame = step.frames[-1]

    # Create new Frame
    new_frame = step.Frame(
        incrementNumber=9999,
        frameValue=1.0,
        description="State B Damage-Derived Target Sizing Frame"
    )

    # Copy EVOL
    f_evol_new = new_frame.FieldOutput(name='EVOL', description='Element Volume', type=SCALAR)
    f_evol_new.addData(field=frame.fieldOutputs['EVOL'])

    # Create synthetic MISESERI = S_base * eta_hat [MPa]
    f_eri_new = new_frame.FieldOutput(
        name='MISESERI',
        description='State B Inverted Damage Sizing Error Indicator [MPa]',
        type=SCALAR
    )
    # Create uniform MISESAVG = S_base [MPa]
    f_avg_new = new_frame.FieldOutput(
        name='MISESAVG',
        description='Reference Uniform Stress Base [MPa]',
        type=SCALAR
    )

    root_inst = odb.rootAssembly.instances.values()[0]
    labels_to_set = [el.label for el in root_inst.elements]

    eri_data = tuple((lbl, float(miseseri_vals[lbl])) for lbl in labels_to_set)
    avg_data = tuple((lbl, float(s_base)) for lbl in labels_to_set)

    f_eri_new.addData(position=WHOLE_ELEMENT, instance=root_inst, labels=labels_to_set, data=[(d[1],) for d in eri_data])
    f_avg_new.addData(position=WHOLE_ELEMENT, instance=root_inst, labels=labels_to_set, data=[(d[1],) for d in avg_data])

    odb.save()
    odb.close()
    print("SUCCESS: Donor ODB saved to: %s" % out_odb_path)

    # Return summary dict for JSON recording
    summary = {
        "donor_odb_path": os.path.abspath(out_odb_path),
        "donor_state": "state_b",
        "time_causal_rule": "Earliest post-initiation state exhibiting macroscopic primary crack growth (d_max > 0.99) prior to secondary crack initiation.",
        "displacement_mm": state_b.get('uy_mm', 0.20),
        "rf2_kN": state_b.get('rf2_kN', 1.9658),
        "frame_idx": state_b.get('frame_idx', 40),
        "total_donor_elements": n_elems,
        "active_elements_d_ge_005": n_active,
        "active_elements_fraction": n_active / float(n_elems),
        "strict_process_zone_target_count": n_strict_proc,
        "strict_process_zone_target_fraction": n_strict_proc / float(n_elems),
        "crack_core_target_count": n_core,
        "crack_core_target_fraction": n_core / float(n_elems),
        "s_base_MPa": s_base,
        "error_target": error_target,
        "min_target_size_mm": min(all_targets),
        "mean_target_size_mm": sum(all_targets) / len(all_targets),
        "max_target_size_mm": max(all_targets),
        "min_eta_hat": min(all_etas),
        "mean_eta_hat": sum(all_etas) / len(all_etas),
        "max_eta_hat": max(all_etas),
        "primary_sampled_weakness_retained": {
            "total_sampled": 35,
            "damage_active": 35,
            "target_h_le_l0_over_2": 3,
            "compliance_percent": 8.5714,
            "diffuse_tail_h_range_mm": [0.44, 1.09]
        }
    }
    return summary

if __name__ == '__main__':
    work_dir = sys.argv[1] if len(sys.argv) > 1 else 'models/pandey_kumar_mode1/233_f1750_local_sizing_probe'
    template_odb = sys.argv[2] if len(sys.argv) > 2 else 'models/pandey_kumar_mode1/200_pk_sec43_prescribed_same_state/PK_SEC43_PRESCRIBED_STATE2.odb'
    damage_json = sys.argv[3] if len(sys.argv) > 3 else 'results/validation/f1694_sec43_five_state_damage_record.json'
    out_odb = os.path.join(work_dir, 'PK_SEC43_STATE_B_DAMAGE_DONOR.odb')
    s = build_f1750_donor(template_odb, damage_json, out_odb)
    with open(os.path.join(work_dir, 'donor_summary.json'), 'w') as f:
        json.dump(s, f, indent=2)
