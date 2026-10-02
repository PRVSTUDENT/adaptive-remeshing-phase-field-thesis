from odbAccess import openOdb
import math

def inspect_r2r6_step1_odb():
    odb_path = "/home/pr21vyci/test_r2r6_step1.odb"
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps["Step-1-PhaseInit"]
    frame = step.frames[-1]
    u = frame.fieldOutputs["U"]
    
    nan_count = 0
    finite_count = 0
    max_u1 = 0.0
    min_u1 = 1e9
    for v in u.values:
        u1, u2 = v.data[0], v.data[1]
        if math.isnan(u1) or math.isnan(u2):
            nan_count += 1
        else:
            finite_count += 1
            if abs(u1) > max_u1:
                max_u1 = abs(u1)
            if abs(u1) < min_u1:
                min_u1 = abs(u1)
                
    print("Step 1 Frame 1 (t=%.2f): total=%d, finite=%d, NaNs=%d" % (frame.frameValue, len(u.values), finite_count, nan_count))
    print("Displacement U1 range: min=|%.6f|, max=|%.6f|" % (min_u1, max_u1))
    
    # Print sample nodes
    print("\nSample Physical Nodes:")
    for v in list(u.values)[:5]:
        print("  Node %d: U1=%s, U2=%s" % (v.nodeLabel, str(v.data[0]), str(v.data[1])))
    print("RP 99999:")
    for v in u.values:
        if v.nodeLabel == 99999:
            print("  Node %d: U1=%s, U2=%s" % (v.nodeLabel, str(v.data[0]), str(v.data[1])))
            
    odb.close()

if __name__ == "__main__":
    inspect_r2r6_step1_odb()
