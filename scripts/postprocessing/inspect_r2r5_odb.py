# Python 2 / 3 compatible ODB extractor
import os, sys, math

def extract_odb():
    from odbAccess import openOdb

    odb_path = "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.odb"
    if not os.path.exists(odb_path):
        print("ERROR: ODB not found: %s" % odb_path)
        sys.exit(1)

    odb = openOdb(odb_path, readOnly=True)
    print("ODB opened successfully.")
    print("Steps: %s" % list(odb.steps.keys()))

    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        print("\n--- STEP: %s (Total Frames: %d) ---" % (step_name, len(step.frames)))
        first_frame = step.frames[0]
        last_frame = step.frames[-1]
        
        print("  Frame 0: time = %.6f" % first_frame.frameValue)
        print("  Last Frame (%d): time = %.6f" % (len(step.frames)-1, last_frame.frameValue))
        
        # Check field outputs in last frame
        if "U" in last_frame.fieldOutputs:
            u_field = last_frame.fieldOutputs["U"]
            u1_vals = []
            u2_vals = []
            u3_vals = []
            for v in u_field.values:
                if len(v.data) >= 1:
                    u1_vals.append(v.data[0])
                if len(v.data) >= 2:
                    u2_vals.append(v.data[1])
                if len(v.data) >= 3:
                    u3_vals.append(v.data[2])
                    
            u1_nan = any(math.isnan(x) for x in u1_vals)
            u2_nan = any(math.isnan(x) for x in u2_vals)
            u3_nan = any(math.isnan(x) for x in u3_vals)
            
            print("  U1 range: [%.6f, %.6f], any NaN: %s" % (min(u1_vals), max(u1_vals), u1_nan))
            print("  U2 range: [%.6f, %.6f], any NaN: %s" % (min(u2_vals), max(u2_vals), u2_nan))
            if u3_vals:
                print("  U3 (Phase) range: [%.6f, %.6f], any NaN: %s" % (min(u3_vals), max(u3_vals), u3_nan))
            
            # Check RP 99999 displacement
            for v in u_field.values:
                if v.nodeLabel == 99999:
                    print("  RP 99999 displacement: %s" % str(v.data))
                
        if "RF" in last_frame.fieldOutputs:
            rf_field = last_frame.fieldOutputs["RF"]
            rf1_vals = [v.data[0] for v in rf_field.values if len(v.data) >= 1]
            rf1_nan = any(math.isnan(x) for x in rf1_vals)
            print("  RF1 sum: %.6f kN, any NaN: %s" % (sum(rf1_vals), rf1_nan))
            for v in rf_field.values:
                if v.nodeLabel == 99999:
                    print("  RP 99999 RF: %s" % str(v.data))

    odb.close()

if __name__ == "__main__":
    extract_odb()
