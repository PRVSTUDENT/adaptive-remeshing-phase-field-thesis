"""
scripts/hpc/extract_f1713_damage.py
===================================
Task F1713: Extract authentic companion-element phase-field damage fields
(SDV1) and N_RP reaction force / displacement history from the genuinely new
Mode-I adapted simulation ODB (M1_PK_F1713_JOB2_ADAPTED.odb).

Physical mesh: 14,933 elements
Layer 3 companion elements: 29,867 .. 44,799 (base_el = 29,866)
"""
import sys
import json
import os
from odbAccess import openOdb

def main():
    if len(sys.argv) > 1:
        odb_path = sys.argv[1]
    else:
        odb_path = "/scratch9/pr21vyci/runs/mode1_pk_f1713_job2_adapted/M1_PK_F1713_JOB2_ADAPTED.odb"

    if len(sys.argv) > 2:
        out_json = sys.argv[2]
    else:
        out_json = "/scratch9/pr21vyci/runs/mode1_pk_f1713_job2_adapted/f1713_job2_damage_field.json"

    print("Opening ODB: " + odb_path)
    odb = openOdb(odb_path, readOnly=True)

    n_phys = 14933
    base_el = 2 * n_phys  # 29866
    rp_node = 14896

    damage_states = {}

    # Target displacements matching Pandey & Kumar (2025) Section 4.1 & Figure 5(b):
    # s1: Initiation onset: u = 0.0050 mm (Step 1 endpoint)
    # s2: Early propagation: u = 0.0056 mm
    # s3: Peak / mid-propagation: u = 0.00586 mm
    # s4: Late propagation: u = 0.0070 mm
    # s5: Complete severance: u = 0.0100 mm (or terminal frame)
    target_disps = {
        "state_1_initiation": 0.0050,
        "state_2_pre_peak": 0.0056,
        "state_3_peak_propagation": 0.00586,
        "state_4_late_propagation": 0.0070,
        "state_5_severance": 0.0100
    }

    fu_history = []

    # Search across steps and frames
    for sname in odb.steps.keys():
        step = odb.steps[sname]
        print("Scanning Step %s (%d frames)..." % (sname, len(step.frames)))
        for fidx, frame in enumerate(step.frames):
            val = float(frame.frameValue)
            # Step 1: frameValue is time in [0, 1], displacement = val * 0.0050 mm
            # Step 2: frameValue is time in [0, 1], displacement = 0.0050 + val * (0.0100 - 0.0050)
            if sname == 'Step-1':
                current_u = val * 0.0050
            else:
                current_u = 0.0050 + val * 0.0050

            # Extract RP reaction force and displacement if present
            rf_val = None
            u_val = None
            if 'RF' in frame.fieldOutputs and 'U' in frame.fieldOutputs:
                rf_field = frame.fieldOutputs['RF']
                u_field = frame.fieldOutputs['U']
                for v in rf_field.values:
                    if v.nodeLabel == rp_node:
                        rf_val = float(v.data[1])  # RF2
                        break
                for v in u_field.values:
                    if v.nodeLabel == rp_node:
                        u_val = float(v.data[1])  # U2
                        break

            if rf_val is not None and u_val is not None:
                fu_history.append({
                    "step": sname,
                    "frame": fidx,
                    "time": val,
                    "u_mm": u_val,
                    "rf_kN": rf_val
                })

            # Check for target states
            for tname, target_u in list(target_disps.items()):
                # Match within 0.0001 mm or terminal frame of Step 2
                is_terminal = (tname == "state_5_severance" and sname == 'Step-2' and fidx == len(step.frames) - 1)
                if abs(current_u - target_u) <= 0.00015 or is_terminal:
                    if tname not in damage_states or abs(current_u - target_u) < abs(damage_states[tname]["current_u"] - target_u):
                        elem_d = {}
                        target_field = None
                        if 'SDV1' in frame.fieldOutputs:
                            target_field = frame.fieldOutputs['SDV1']
                            is_scalar = True
                        elif 'SDV' in frame.fieldOutputs:
                            target_field = frame.fieldOutputs['SDV']
                            is_scalar = False

                        if target_field:
                            for v in target_field.values:
                                el = v.elementLabel
                                if el > base_el:
                                    phys_idx = el - base_el
                                    if 1 <= phys_idx <= n_phys:
                                        d_val = float(v.data) if is_scalar else float(v.data[0])
                                        if phys_idx not in elem_d or d_val > elem_d[phys_idx]:
                                            elem_d[phys_idx] = round(d_val, 5)

                        max_val = max(elem_d.values()) if elem_d else 0.0
                        print("-> Captured %s in %s Frame %d: u=%.6f mm, max_d=%.4f" % (
                            tname, sname, fidx, current_u, max_val
                        ))
                        damage_states[tname] = {
                            "step_name": sname,
                            "frame_index": fidx,
                            "description": frame.description,
                            "current_u": current_u,
                            "max_damage": max_val,
                            "elem_damage": elem_d
                        }

    odb.close()

    result = {
        "n_phys_elements": n_phys,
        "damage_states": damage_states,
        "fu_history": fu_history
    }

    with open(out_json, "w") as fp:
        json.dump(result, fp)

    print("Successfully saved damage fields and history to: " + out_json)

if __name__ == "__main__":
    main()
