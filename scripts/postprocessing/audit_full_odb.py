from odbAccess import openOdb
import math

def inspect_full_odb():
    odb = openOdb("/home/pr21vyci/test_r2r5_step1.odb", readOnly=True)
    step = odb.steps["Step-1-PhaseInit"]
    frame0 = step.frames[0]
    frame1 = step.frames[-1]
    
    u0 = frame0.fieldOutputs["U"]
    u1 = frame1.fieldOutputs["U"]
    
    nan0 = sum(1 for v in u0.values if math.isnan(v.data[0]) or math.isnan(v.data[1]))
    nan1 = sum(1 for v in u1.values if math.isnan(v.data[0]) or math.isnan(v.data[1]))
    
    print("Frame 0 (t=%.2f): total=%d, NaNs=%d" % (frame0.frameValue, len(u0.values), nan0))
    print("Frame 1 (t=%.2f): total=%d, NaNs=%d" % (frame1.frameValue, len(u1.values), nan1))
    
    # Print first 5 and last 5 of frame 1
    print("\nFrame 1 First 5 nodes:")
    for v in u1.values[:5]:
        print("  Node %d: U1=%s, U2=%s" % (v.nodeLabel, str(v.data[0]), str(v.data[1])))
        
    print("\nFrame 1 N_TOP nodes (sample):")
    for v in u1.values[9720:9730]:
        print("  Node %d: U1=%s, U2=%s" % (v.nodeLabel, str(v.data[0]), str(v.data[1])))

    odb.close()

if __name__ == "__main__":
    inspect_full_odb()
