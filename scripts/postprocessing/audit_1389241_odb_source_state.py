import sys
import json
from odbAccess import openOdb

def main():
    odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8/M2STATE_FRACFIX_RESTART1R1R8.odb"
    odb = openOdb(odb_path)
    
    print("=== ODB Step Summary ===")
    for sname in odb.steps.keys():
        st = odb.steps[sname]
        print("Step %s: %d frames" % (sname, len(st.frames)))
    
    # We want Step-2-Continuation, Frame 15 (last frame is index -1, frame 15 is step time 1.0, u1=0.0100)
    step2 = odb.steps['Step-2-Continuation']
    print("Step 2 total frames:", len(step2.frames))
    for i, f in enumerate(step2.frames):
        print("Frame %d: desc='%s', value=%.6f" % (i, f.description, f.frameValue))
    
    last_frame = step2.frames[-1]
    print("\n--- Last Frame Inspection ---")
    print("Frame Description:", last_frame.description)
    print("Frame Value (Time):", last_frame.frameValue)
    print("Available Field Outputs:", list(last_frame.fieldOutputs.keys()))
    
    for fname, fld in last_frame.fieldOutputs.items():
        print("Field %s: type=%s, locations=%s, num_values=%d" % (
            fname, fld.type, [l.position for l in fld.locations], len(fld.values)
        ))
        if len(fld.values) > 0:
            v0 = fld.values[0]
            print("  sample val0: node=%s, elem=%s, data=%s" % (
                getattr(v0, 'nodeLabel', None), getattr(v0, 'elementLabel', None), str(v0.data)
            ))
            
    # Check RF
    rf_field = last_frame.fieldOutputs.get('RF')
    if rf_field is not None:
        rp_rf1 = 0.0
        bot_rf1_sum = 0.0
        for val in rf_field.values:
            if val.nodeLabel == 99999:
                rp_rf1 = val.data[0]
            # bottom nodes are y = -0.5
        print("\nRP Node 99999 RF1 = %.8f kN" % rp_rf1)
        
    # Check SDV / SDV16 / SDV14 / SDV15 / H
    print("\n--- Checking for SDV fields across all frames ---")
    for k in last_frame.fieldOutputs.keys():
        if 'SDV' in k or 'VAR' in k or 'STATE' in k or 'H' in k:
            fld = last_frame.fieldOutputs[k]
            vals = [v.data for v in fld.values]
            print("Field %s: min=%.6e, max=%.6e, mean=%.6e, count=%d" % (
                k, min(vals), max(vals), sum(vals)/float(len(vals)), len(vals)
            ))
            
    # Check DAT file for SDV / history output
    dat_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8/M2STATE_FRACFIX_RESTART1R1R8.dat"
    print("\n--- Checking DAT file for SDV output ---")
    with open(dat_path, 'r') as df:
        lines = df.readlines()
    print("DAT total lines:", len(lines))
    sdv_lines = [line.strip() for line in lines if "SDV" in line]
    print("DAT lines mentioning SDV:", len(sdv_lines))
    if len(sdv_lines) > 0:
        for l in sdv_lines[:10]:
            print("  ", l)

    odb.close()

if __name__ == "__main__":
    main()
