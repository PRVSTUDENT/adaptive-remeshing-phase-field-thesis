#!/usr/bin/env python
from odbAccess import openOdb

def inspect_odb(odb_path):
    print("=== Inspecting ODB: " + odb_path + " ===")
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps.values()[0]
    last_frame = step.frames[-1]
    
    inst = odb.rootAssembly.instances.values()[0]
    node_coords = {n.label: n.coordinates for n in inst.nodes}
    
    rf = last_frame.fieldOutputs['RF']
    rf_non_zero = []
    for v in rf.values:
        d = v.data
        if abs(d[0]) > 1e-6 or abs(d[1]) > 1e-6:
            coord = node_coords.get(v.nodeLabel, (0, 0))
            rf_non_zero.append((v.nodeLabel, coord, d[0], d[1]))
            
    print("Total RF values count: {}".format(len(rf.values)))
    print("Non-zero RF nodes count: {}".format(len(rf_non_zero)))
    print("Sample non-zero RF (nodeLabel, (x,y), RF1, RF2):")
    for item in rf_non_zero[:10]:
        print("  Node {}: coord=({:.4f}, {:.4f}), RF1={:.6f}, RF2={:.6f}".format(item[0], item[1][0], item[1][1], item[2], item[3]))
        
    u = last_frame.fieldOutputs['U']
    u_non_zero = []
    for v in u.values:
        d = v.data
        if abs(d[0]) > 1e-6 or abs(d[1]) > 1e-6:
            coord = node_coords.get(v.nodeLabel, (0, 0))
            u_non_zero.append((v.nodeLabel, coord, d[0], d[1]))
            
    print("\nTotal U values count: {}".format(len(u.values)))
    print("Non-zero U nodes count: {}".format(len(u_non_zero)))
    print("Sample non-zero U (nodeLabel, (x,y), U1, U2):")
    for item in u_non_zero[:10]:
        print("  Node {}: coord=({:.4f}, {:.4f}), U1={:.6f}, U2={:.6f}".format(item[0], item[1][0], item[1][1], item[2], item[3]))
        
    # Check top boundary sum (y = 0.5)
    rf1_top = sum(item[2] for item in rf_non_zero if abs(item[1][1] - 0.5) < 1e-4)
    rf1_bot = sum(item[2] for item in rf_non_zero if abs(item[1][1] - (-0.5)) < 1e-4)
    print("\nSum RF1 on y=0.5 top boundary: {:.6f}".format(rf1_top))
    print("Sum RF1 on y=-0.5 bottom boundary: {:.6f}".format(rf1_bot))
    
    odb.close()

if __name__ == "__main__":
    inspect_odb("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1385392.mmaster02/F43PRE2_GEOM.odb")
    inspect_odb("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1384674.mmaster02/F43PRE1.odb")
