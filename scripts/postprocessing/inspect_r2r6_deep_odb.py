#!/usr/bin/env python3
"""
Deep ODB and Node 481 Inspector for M2STATE_FRACFIX_RESTART2R6.
"""
from odbAccess import openOdb
import sys

def inspect_r2r6_odb(odb_path):
    odb = openOdb(odb_path, readOnly=True)
    
    # 1. Mesh info and node coordinates
    root = odb.rootAssembly
    instance = root.instances['PART-1-1'] if 'PART-1-1' in root.instances else list(root.instances.values())[0]
    
    nodes = instance.nodes
    node_coords = {n.label: n.coordinates for n in nodes}
    
    print("Node 481 coordinates: %s" % str(node_coords.get(481)))
    print("Node 362 coordinates: %s" % str(node_coords.get(362)))
    
    # Find elements containing node 481
    elems = instance.elements
    elem_conn = {e.label: (e.type, e.connectivity) for e in elems}
    
    elems_with_481 = [eid for eid, (etype, conn) in elem_conn.items() if 481 in conn]
    print("Elements connected to Node 481: %s" % str(elems_with_481))
    for eid in elems_with_481:
        etype, conn = elem_conn[eid]
        print("  Elem %d: type=%s, connectivity=%s" % (eid, etype, str(conn)))
        
    # 2. Step and frame analysis
    print("\n--- STEP AND FRAME ANALYSIS ---")
    for s_name, step in odb.steps.items():
        print("\nStep '%s': total frames = %d" % (s_name, len(step.frames)))
        for f_idx, frame in enumerate(step.frames):
            t = frame.frameValue
            desc = frame.description
            
            print("\n  Frame %d (t=%.6e, desc='%s'):" % (f_idx, t, desc))
            
            # Displacement / Phase field
            if 'U' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                u_481 = None
                u_362 = None
                u1_all = []
                u2_all = []
                u3_all = [] # phase
                
                # Check RP node 99999
                rp_u = None
                
                for v in u_field.values:
                    if v.nodeLabel == 481:
                        u_481 = v.data
                    if v.nodeLabel == 362:
                        u_362 = v.data
                    if v.nodeLabel == 99999:
                        rp_u = v.data
                    if v.nodeLabel <= 9801:
                        data = v.data
                        if len(data) >= 1: u1_all.append(data[0])
                        if len(data) >= 2: u2_all.append(data[1])
                        if len(data) >= 3: u3_all.append(data[2])
                        
                d_max = max(u3_all) if u3_all else 0.0
                d_min = min(u3_all) if u3_all else 0.0
                d_mean = (sum(u3_all) / float(len(u3_all))) if u3_all else 0.0
                d_gt_0p1 = sum(1 for x in u3_all if x > 0.1)
                d_gt_0p5 = sum(1 for x in u3_all if x > 0.5)
                d_gt_0p9 = sum(1 for x in u3_all if x > 0.9)
                
                # Node with d_max
                max_d_node = None
                for v in u_field.values:
                    if v.nodeLabel <= 9801 and len(v.data) >= 3 and v.data[2] == d_max:
                        max_d_node = v.nodeLabel
                        break
                        
                print("    RP U (Node 99999): %s" % str(rp_u))
                d_481_str = "%.6f" % u_481[2] if (u_481 is not None and len(u_481) >= 3) else "N/A"
                d_362_str = "%.6f" % u_362[2] if (u_362 is not None and len(u_362) >= 3) else "N/A"
                print("    Node 481 U: %s (d = %s)" % (str(u_481), d_481_str))
                print("    Node 362 U: %s (d = %s)" % (str(u_362), d_362_str))
                print("    Phase d: min=%.6f, max=%.6f (at node %s, coords %s), mean=%.6f" % (
                    d_min, d_max, str(max_d_node), str(node_coords.get(max_d_node)), d_mean
                ))
                print("    Counts: d>0.1: %d, d>0.5: %d, d>0.9: %d" % (d_gt_0p1, d_gt_0p5, d_gt_0p9))
                
            # Reaction force field
            if 'RF' in frame.fieldOutputs:
                rf_field = frame.fieldOutputs['RF']
                for v in rf_field.values:
                    if v.nodeLabel == 99999:
                        print("    RP RF (Node 99999): %s" % str(v.data))
                        
            # SDVs if available
            for sdv_name in ['SDV14', 'SDV15', 'SDV16', 'SDV1', 'SDV2', 'SDV3', 'SDV4']:
                if sdv_name in frame.fieldOutputs:
                    sdv_field = frame.fieldOutputs[sdv_name]
                    vals = [v.data for v in sdv_field.values]
                    print("    %s: min=%.6e, max=%.6e, mean=%.6e, count=%d" % (
                        sdv_name, min(vals), max(vals), sum(vals)/float(len(vals)), len(vals)
                    ))
                    
    odb.close()

if __name__ == "__main__":
    odb_path = sys.argv[1] if len(sys.argv) > 1 else "M2STATE_FRACFIX_RESTART2R6.odb"
    inspect_r2r6_odb(odb_path)
