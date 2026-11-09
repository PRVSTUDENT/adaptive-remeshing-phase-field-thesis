"""
Extract authentic phase-field damage field from Job 1421888.mmaster02 ODB
(M1_HOLE_SEL_E10_PROD.odb) on cluster scratch.
Fast, targeted extraction of specific key equilibrium states.
"""
import sys
import json
from odbAccess import openOdb

def main():
    odb_path = "/scratch9/pr21vyci/runs/mode1_method_a_hole_f1705_prod/M1_HOLE_SEL_E10_PROD.odb"
    out_json = "/scratch9/pr21vyci/runs/mode1_method_a_hole_f1705_prod/f1705_e10_damage_field.json"

    print("Opening ODB: " + odb_path)
    odb = openOdb(odb_path, readOnly=True)
    step2 = odb.steps['Step-2']
    num_frames = len(step2.frames)
    print("Step-2 has %d frames." % num_frames)

    # Frame targets:
    # Frame 0 is start of Step 2 (Increment 0, uy = 0.0050 mm)
    # Increment 60: primary crack arrest at circular hole (uy ~ 0.0055 mm)
    # Increment 160: complete severance across ligament (uy = 0.00774 mm)
    # Last frame (-1): terminal converged state (uy = 0.00998 mm)
    target_indices = {
        "arrest_inc60": 60 if num_frames > 60 else num_frames // 4,
        "severance_inc160": 160 if num_frames > 160 else num_frames // 2,
        "terminal_inc291": num_frames - 1
    }

    n_phys = 9164
    base_el = 2 * n_phys  # 18328

    damage_states = {}

    for name, idx in target_indices.items():
        frame = step2.frames[idx]
        print("Extracting %s (Frame %d: %s, val=%.6f)..." % (
            name, idx, frame.description, frame.frameValue
        ))
        
        elem_d = {}
        # Field could be SDV1 or SDV
        target_field = None
        if 'SDV1' in frame.fieldOutputs:
            target_field = frame.fieldOutputs['SDV1']
            is_scalar = True
        elif 'SDV' in frame.fieldOutputs:
            target_field = frame.fieldOutputs['SDV']
            is_scalar = False
        else:
            print("Warning: SDV1/SDV not in fieldOutputs! Keys: " + str(frame.fieldOutputs.keys()))

        if target_field:
            for v in target_field.values:
                el = v.elementLabel
                if el > base_el:
                    phys_idx = el - base_el
                    if 1 <= phys_idx <= n_phys:
                        val = float(v.data) if is_scalar else float(v.data[0])
                        # Keep max across integration points
                        if phys_idx not in elem_d or val > elem_d[phys_idx]:
                            elem_d[phys_idx] = round(val, 5)

        max_val = max(elem_d.values()) if elem_d else 0.0
        print("-> Extracted %d elements for %s. Max d = %.4f" % (len(elem_d), name, max_val))

        damage_states[name] = {
            "frame_index": idx,
            "description": frame.description,
            "frame_value": float(frame.frameValue),
            "max_damage": max_val,
            "elem_damage": elem_d
        }

    odb.close()

    result = {
        "num_frames": num_frames,
        "n_phys_elements": n_phys,
        "damage_states": damage_states
    }

    with open(out_json, "w") as fp:
        json.dump(result, fp)

    print("Successfully saved damage field to: " + out_json)

if __name__ == "__main__":
    main()
