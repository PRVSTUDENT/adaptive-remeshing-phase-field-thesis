import os
import sys
import json
from odbAccess import openOdb
import numpy as np

def inspect():
    odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2/M2STATE_FRACFIX_RESTART1R1R6R2.odb"
    if not os.path.exists(odb_path):
        print("ERROR: ODB not found:", odb_path)
        sys.exit(1)
        
    odb = openOdb(odb_path, readOnly=True)
    print("ODB opened:", odb_path)
    
    # Steps
    print("Steps:", list(odb.steps.keys()))
    
    step2 = odb.steps["Step-2-Continuation"]
    print("Step 2 total frames:", len(step2.frames))
    
    f13 = step2.frames[13]
    print("Frame 13 time:", f13.frameValue, "desc:", f13.description)
    print("Frame 13 fieldOutputs:", list(f13.fieldOutputs.keys()))
    
    u_f13 = f13.fieldOutputs["U"]
    u_vals = np.array([v.data for v in u_f13.values])
    print("U values shape:", u_vals.shape)
    print("U1 min/max:", float(u_vals[:,0].min()), float(u_vals[:,0].max()))
    print("U2 min/max:", float(u_vals[:,1].min()), float(u_vals[:,1].max()))
    if u_vals.shape[1] >= 3:
        d_vals = u_vals[:,2]
        print("d (DOF 3) min/max:", float(d_vals.min()), float(d_vals.max()))
        print("d > 0.05 count:", int((d_vals > 0.05).sum()))
        print("d > 0.10 count:", int((d_vals > 0.10).sum()))
        
    # Check RP node
    rp_u1 = 0.0
    for v in u_f13.values:
        if v.nodeLabel == 99999:
            rp_u1 = float(v.data[0])
    print("RP Node 99999 U1:", rp_u1)
    
    # Check history regions
    print("History regions:", list(step2.historyRegions.keys()))
    for hr_name, hr in step2.historyRegions.items():
        print("HR:", hr_name, "outputs:", list(hr.historyOutputs.keys()))

    odb.close()

if __name__ == "__main__":
    inspect()
