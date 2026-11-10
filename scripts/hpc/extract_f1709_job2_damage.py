"""
scripts/hpc/extract_f1709_job2_damage.py
========================================
Extract authentic phase-field damage fields across key fracture states
from Section 4.3 Job-2 staggered ODB (M1_PK_SEC43_JOB2_STAGGERED.odb)
for comparison with Pandey & Kumar (2025) Figure 16(b).
"""
import sys
import json
import os
from odbAccess import openOdb

def main():
    if len(sys.argv) > 1:
        odb_path = sys.argv[1]
    else:
        odb_path = "/scratch9/pr21vyci/runs/mode1_pk_sec43_job2_staggered_f1709/M1_PK_SEC43_JOB2_STAGGERED.odb"

    if len(sys.argv) > 2:
        out_json = sys.argv[2]
    else:
        out_json = "/scratch9/pr21vyci/runs/mode1_pk_sec43_job2_staggered_f1709/f1709_job2_damage_field.json"

    print("Opening ODB: " + odb_path)
    odb = openOdb(odb_path, readOnly=True)

    n_phys = 10065
    base_el = 2 * n_phys  # 20130

    damage_states = {}

    # Target displacements matching published Figure 16(b):
    # s1: uy = 0.14 mm
    # s2: uy = 0.20 mm (hole arrest)
    # s3: uy = 0.30 mm (secondary flank initiation)
    # s4: terminal / complete severance (uy = 1.50 mm)
    target_disps = {
        "state_1_notch_init": 0.14,
        "state_2_hole_arrest": 0.20,
        "state_3_sec_init": 0.30,
        "state_4_severance": 1.50
    }

    # Search across steps and frames
    for sname in odb.steps.keys():
        step = odb.steps[sname]
        print("Scanning Step %s (%d frames)..." % (sname, len(step.frames)))
        for fidx, frame in enumerate(step.frames):
            # Total displacement at RP or step time
            val = float(frame.frameValue)
            # Find closest target
            for tname, target_uy in list(target_disps.items()):
                # In Step 1: frameValue is time/disp (0 to 1.0 mm)
                # In Step 2: frameValue is time/disp (1.0 to 1.50 mm)
                current_uy = val if sname == 'Step-1' else 1.0 + val
                if abs(current_uy - target_uy) <= 0.005 or (tname == "state_4_severance" and sname == 'Step-2' and fidx == len(step.frames) - 1):
                    if tname not in damage_states or abs(current_uy - target_uy) < abs(damage_states[tname]["current_uy"] - target_uy):
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
                        print("-> Captured %s in %s Frame %d: uy=%.4f mm, max_d=%.4f" % (
                            tname, sname, fidx, current_uy, max_val
                        ))
                        damage_states[tname] = {
                            "step_name": sname,
                            "frame_index": fidx,
                            "description": frame.description,
                            "current_uy": current_uy,
                            "max_damage": max_val,
                            "elem_damage": elem_d
                        }

    odb.close()

    result = {
        "n_phys_elements": n_phys,
        "damage_states": damage_states
    }

    with open(out_json, "w") as fp:
        json.dump(result, fp)

    print("Successfully saved damage field to: " + out_json)

if __name__ == "__main__":
    main()
