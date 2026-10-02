import os
import sys
from odbAccess import openOdb
import numpy as np

def main():
    odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7/M2STATE_FRACFIX_RESTART2R7.odb"
    odb = openOdb(odb_path, readOnly=True)
    
    s1 = odb.steps['Step-1-PhaseInit']
    f1 = s1.frames[-1]
    u = f1.fieldOutputs['U']
    
    print("Step 1 U values count:", len(u.values))
    print("Sample node 1:", u.values[0].nodeLabel, u.values[0].data)
    
    # Check max value across each component
    all_data = [v.data for v in u.values]
    lens = set(len(d) for d in all_data)
    print("Component lengths present in U:", lens)
    
    # Check center nodes where x~0, y~0
    # In PK10R1 mesh, find nodes with non-zero 3rd component or non-zero U
    non_zero_c3 = []
    for v in u.values:
        if len(v.data) >= 3 and abs(v.data[2]) > 1e-6:
            non_zero_c3.append((v.nodeLabel, v.data[2]))
            
    print("Nodes with non-zero component 3 in Step 1:", len(non_zero_c3))
    if non_zero_c3:
        print("Sample non-zero component 3:", non_zero_c3[:10])
        print("Max component 3:", max(c[1] for c in non_zero_c3))
        
    s2 = odb.steps['Step-2-Continuation']
    f2_last = s2.frames[-1]
    u2 = f2_last.fieldOutputs['U']
    non_zero_c3_s2 = []
    for v in u2.values:
        if len(v.data) >= 3 and abs(v.data[2]) > 1e-6:
            non_zero_c3_s2.append((v.nodeLabel, v.data[2]))
    print("Nodes with non-zero component 3 in Step 2 terminal:", len(non_zero_c3_s2))
    if non_zero_c3_s2:
        print("Sample non-zero component 3 in Step 2:", non_zero_c3_s2[:10])
        print("Max component 3 in Step 2:", max(c[1] for c in non_zero_c3_s2))

    odb.close()

if __name__ == "__main__":
    main()
