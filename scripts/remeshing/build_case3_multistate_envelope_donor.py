# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_case3_multistate_envelope_donor.py

Authoritative offline builder for Case 3 (Pandey & Kumar Sec 4.3)
Multi-State Error-Indicator Envelope Donor ODB.

Implements the dimensionless relative-error envelope norm:
    eta_e^(env) = max( eta_e^(2), eta_e^(4) )
where:
    eta_e^(k) = MISESERI_e^(k) / MISESAVG_e^(k)
and writes:
    MISESERI_e^(env) = eta_e^(env) * S_ref
    MISESAVG_e^(env) = S_ref
into a dedicated envelope frame in PK_SEC43_MULTISTATE_ENVELOPE_DONOR.odb.

This guarantees:
    h_(e, new)^(env) = min( h_(e, new)^(2), h_(e, new)^(4) )
under native Abaqus UNIFORM_ERROR sizing without ad-hoc MPa scalar mixing.
"""
from __future__ import print_function
import os
import sys
import shutil
import json

def build_envelope_odb(repo_root=None):
    if repo_root is None:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    from odbAccess import openOdb
    from abaqusConstants import SCALAR, WHOLE_ELEMENT, INTEGRATION_POINT

    donor_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "200_pk_sec43_prescribed_same_state")
    odb2_path = os.path.join(donor_dir, "PK_SEC43_PRESCRIBED_STATE2.odb")
    odb4_path = os.path.join(donor_dir, "PK_SEC43_PRESCRIBED_STATE4.odb")
    out_odb_path = os.path.join(donor_dir, "PK_SEC43_MULTISTATE_ENVELOPE_DONOR.odb")
    out_json_path = os.path.join(repo_root, "results", "validation", "f1740_case3_envelope_donor_summary.json")

    print("Building Multi-State Envelope Donor ODB...")
    print("  Primary Donor (State 2):  %s" % odb2_path)
    print("  Secondary Donor (State 4): %s" % odb4_path)
    print("  Output Envelope ODB:      %s" % out_odb_path)

    # 1. Read State 2 fields
    odb2 = openOdb(odb2_path, readOnly=True)
    frame2 = odb2.steps['RECOVERY_STEP'].frames[-1]
    miseseri2 = frame2.fieldOutputs['MISESERI']
    misesavg2 = frame2.fieldOutputs['MISESAVG']
    evol2 = frame2.fieldOutputs['EVOL']

    dict2 = {}
    for v_eri, v_avg, v_evol in zip(miseseri2.values, misesavg2.values, evol2.values):
        lbl = v_eri.elementLabel
        eri = float(v_eri.data)
        avg = float(v_avg.data)
        evol = float(v_evol.data)
        # Avoid division by zero: if avg < 1e-12, eta = 0
        eta = (eri / avg) if avg > 1e-12 else 0.0
        dict2[lbl] = {'eri': eri, 'avg': avg, 'evol': evol, 'eta': eta}
    odb2.close()

    # 2. Read State 4 fields
    odb4 = openOdb(odb4_path, readOnly=True)
    frame4 = odb4.steps['RECOVERY_STEP'].frames[-1]
    miseseri4 = frame4.fieldOutputs['MISESERI']
    misesavg4 = frame4.fieldOutputs['MISESAVG']

    dict4 = {}
    for v_eri, v_avg in zip(miseseri4.values, misesavg4.values):
        lbl = v_eri.elementLabel
        eri = float(v_eri.data)
        avg = float(v_avg.data)
        eta = (eri / avg) if avg > 1e-12 else 0.0
        dict4[lbl] = {'eri': eri, 'avg': avg, 'eta': eta}
    odb4.close()

    # 3. Verify 100% element topology and label correspondence
    assert len(dict2) == 3923, "State 2 element count mismatch: %d vs 3923" % len(dict2)
    assert len(dict4) == 3923, "State 4 element count mismatch: %d vs 3923" % len(dict4)
    assert set(dict2.keys()) == set(dict4.keys()), "Element label mismatch between State 2 and State 4"

    # 4. Formulate normalized envelope
    # Reference stress scale S_ref: use mean of State 2 average stress
    mean_avg2 = sum(d['avg'] for d in dict2.values()) / float(len(dict2))
    S_ref = 100.0  # Normalized reference scale (100.0 MPa)

    envelope_data = {}
    prim_dominated = 0
    sec_dominated = 0
    for lbl in sorted(dict2.keys()):
        eta2 = dict2[lbl]['eta']
        eta4 = dict4[lbl]['eta']
        eta_env = max(eta2, eta4)
        if eta2 >= eta4:
            prim_dominated += 1
        else:
            sec_dominated += 1
        eri_env = eta_env * S_ref
        avg_env = S_ref
        evol = dict2[lbl]['evol']
        envelope_data[lbl] = {
            'eta2': eta2,
            'eta4': eta4,
            'eta_env': eta_env,
            'eri_env': eri_env,
            'avg_env': avg_env,
            'evol': evol
        }

    print("  Elements: %d total (Primary dominated: %d, Secondary dominated: %d)" % (
        len(envelope_data), prim_dominated, sec_dominated))

    # 5. Create output ODB
    if os.path.exists(out_odb_path):
        os.remove(out_odb_path)
    shutil.copy2(odb2_path, out_odb_path)

    out_odb = openOdb(out_odb_path, readOnly=False)
    step = out_odb.steps['RECOVERY_STEP']
    # Grab original frame before creating new envelope frame
    orig_frame = step.frames[1] if len(step.frames) > 1 else step.frames[0]
    evol_orig = orig_frame.fieldOutputs['EVOL']

    # Create new envelope frame
    env_frame = step.Frame(frameId=99, frameValue=99.0, description="Normalized Multi-State Envelope Frame (States 2 and 4)")

    # Write EVOL
    env_frame.FieldOutput(name='EVOL', field=evol_orig)

    # Write MISESERI
    elem_labels = sorted(envelope_data.keys())
    eri_vals = [(envelope_data[lbl]['eri_env'],) for lbl in elem_labels]
    fo_eri = env_frame.FieldOutput(name='MISESERI', description='Normalized Multi-State Error Envelope', type=SCALAR)
    fo_eri.addData(position=WHOLE_ELEMENT,
                   instance=out_odb.rootAssembly.instances['PART-1-1'],
                   labels=elem_labels,
                   data=eri_vals)

    # Write MISESAVG
    avg_vals = [(envelope_data[lbl]['avg_env'],) for lbl in elem_labels]
    fo_avg = env_frame.FieldOutput(name='MISESAVG', description='Uniform Reference Average Stress', type=SCALAR)
    fo_avg.addData(position=WHOLE_ELEMENT,
                   instance=out_odb.rootAssembly.instances['PART-1-1'],
                   labels=elem_labels,
                   data=avg_vals)

    out_odb.save()
    out_odb.close()
    print("  Envelope ODB written and closed successfully.")

    # 6. Save summary JSON
    summary = {
        'donor_state_primary': 'PK_SEC43_PRESCRIBED_STATE2.odb',
        'donor_state_secondary': 'PK_SEC43_PRESCRIBED_STATE4.odb',
        'output_odb': 'PK_SEC43_MULTISTATE_ENVELOPE_DONOR.odb',
        'element_count': len(envelope_data),
        'primary_dominated_elements': prim_dominated,
        'secondary_dominated_elements': sec_dominated,
        'reference_stress_S_ref_MPa': S_ref,
        'max_eta_primary': max(d['eta2'] for d in envelope_data.values()),
        'max_eta_secondary': max(d['eta4'] for d in envelope_data.values()),
        'max_eta_envelope': max(d['eta_env'] for d in envelope_data.values()),
        'mean_eta_envelope': sum(d['eta_env'] for d in envelope_data.values()) / float(len(envelope_data)),
        'formula': 'MISESERI_env = max(eta2, eta4) * S_ref, MISESAVG_env = S_ref',
        'sizing_implication': 'h_new_env = min(h_new_2, h_new_4) exactly under native UNIFORM_ERROR'
    }

    with open(out_json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print("  Summary JSON saved to: %s" % out_json_path)

    return summary

if __name__ == '__main__':
    build_envelope_odb()
