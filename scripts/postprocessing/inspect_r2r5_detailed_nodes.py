# Inspect nodal fields and element SDVs in ODB
from odbAccess import openOdb
import sys

def check_nodes():
    odb_path = "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.odb"
    odb = openOdb(odb_path, readOnly=True)
    
    step1 = odb.steps["Step-1-PhaseInit"]
    step2 = odb.steps["Step-2-Continuation"]
    
    print("Step 1 Frame 1:")
    f1 = step1.frames[-1]
    u1 = f1.fieldOutputs["U"]
    count = 0
    for v in u1.values:
        print("  Node %d: U = %s" % (v.nodeLabel, str(v.data)))
        count += 1
        if count >= 10:
            break
    for v in u1.values:
        if v.nodeLabel in [1, 50, 100, 9721, 9801, 99999]:
            print("  Special Node %d: U = %s" % (v.nodeLabel, str(v.data)))

    print("\nStep 2 Frame 1 (Inc 1):")
    f2_1 = step2.frames[1]
    u2_1 = f2_1.fieldOutputs["U"]
    for v in u2_1.values:
        if v.nodeLabel in [1, 50, 100, 9721, 9801, 99999]:
            print("  Special Node %d: U = %s" % (v.nodeLabel, str(v.data)))

    print("\nStep 2 Frame Last (%d):" % (len(step2.frames)-1))
    f2_last = step2.frames[-1]
    u2_last = f2_last.fieldOutputs["U"]
    for v in u2_last.values:
        if v.nodeLabel in [1, 50, 100, 9721, 9801, 99999]:
            print("  Special Node %d: U = %s" % (v.nodeLabel, str(v.data)))

    odb.close()

if __name__ == "__main__":
    check_nodes()
