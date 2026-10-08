import os
import sys
from odbAccess import openOdb

def inspect_odb(odb_path, label):
    print("=" * 60)
    print("INSPECTING ODB: %s (%s)" % (label, odb_path))
    if not os.path.exists(odb_path):
        print("  File not found!")
        return
    
    try:
        odb = openOdb(path=odb_path, readOnly=True)
    except Exception as e:
        print("  Could not open ODB: %s" % str(e))
        return
    
    print("  Steps in ODB: %s" % list(odb.steps.keys()))
    for step_name, step in odb.steps.items():
        n_frames = len(step.frames)
        print("  Step '%s': %d frames" % (step_name, n_frames))
        if n_frames > 0:
            last_frame = step.frames[-1]
            print("    Latest Frame %d: frameValue (time) = %.6f" % (last_frame.frameId, last_frame.frameValue))
            
            # Check SDV14 (d) and SDV15 (H)
            if 'SDV14' in last_frame.fieldOutputs:
                d_field = last_frame.fieldOutputs['SDV14']
                d_vals = [val.data for val in d_field.values]
                if d_vals:
                    print("    SDV14 (Damage d): min = %.6f, max = %.6f, mean = %.6f" % 
                          (min(d_vals), max(d_vals), sum(d_vals)/len(d_vals)))
            elif 'SDV1' in last_frame.fieldOutputs:
                d_field = last_frame.fieldOutputs['SDV1']
                d_vals = [val.data for val in d_field.values]
                if d_vals:
                    print("    SDV1 (Damage d): min = %.6f, max = %.6f, mean = %.6f" % 
                          (min(d_vals), max(d_vals), sum(d_vals)/len(d_vals)))
            
            if 'SDV15' in last_frame.fieldOutputs:
                h_field = last_frame.fieldOutputs['SDV15']
                h_vals = [val.data for val in h_field.values]
                if h_vals:
                    print("    SDV15 (History H): min = %.6e, max = %.6e, mean = %.6e" % 
                          (min(h_vals), max(h_vals), sum(h_vals)/len(h_vals)))
            
            if 'SDV16' in last_frame.fieldOutputs:
                psi_field = last_frame.fieldOutputs['SDV16']
                psi_vals = [val.data for val in psi_field.values]
                if psi_vals:
                    print("    SDV16 (Psi_e): min = %.6e, max = %.6e, mean = %.6e" % 
                          (min(psi_vals), max(psi_vals), sum(psi_vals)/len(psi_vals)))

    odb.close()
    print("=" * 60)

if __name__ == "__main__":
    odbs = [
        ("/scratch9/pr21vyci/runs/mode2_j2_adapted_fracture_retest/Job-2_UEL.odb", "M2_J2_ADAPT_RETEST (22.5k FEs)"),
        ("/scratch9/pr21vyci/runs/mode2_j1_coarse_retest/Job-1_UEL.odb", "M2_J1_COARSE_RETEST (2.96k FEs)")
    ]
    for p, lbl in odbs:
        inspect_odb(p, lbl)
