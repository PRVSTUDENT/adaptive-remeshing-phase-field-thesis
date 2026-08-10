import odbAccess
import sys
import os
import math

def extract_crack_nodes(odb_path, step_name='Step-2', frame_index=17, threshold=0.5):
    """Extract coordinates of nodes/elements where SDV15 >= threshold at a specific frame."""
    odb = odbAccess.openOdb(odb_path, readOnly=True)
    step = odb.steps[step_name]
    frame = step.frames[frame_index]
    
    time_val = frame.frameValue
    u1_mm = 0.005 + time_val * 0.025
    print("ODB: %s | Step: %s | Frame: %d | StepTime: %.6f | U1: %.6f mm" % (
        odb_path, step_name, frame_index, time_val, u1_mm
    ))
    
    # Get SDV15 field
    sdv15_field = frame.fieldOutputs['SDV15']
    
    # Assembly root
    root_assy = odb.rootAssembly
    instance = root_assy.instances.values()[0]
    
    points = []
    for val in sdv15_field.values:
        if val.data >= threshold:
            elem_label = val.elementLabel
            ip = val.integrationPoint
            # We can get element centroid or node coordinates
            elem = instance.elements[elem_label - 1] if elem_label <= len(instance.elements) else None
            # Compute element centroid from connectivity
            if elem:
                coords = []
                for n_label in elem.connectivity:
                    n = instance.nodes[n_label - 1]
                    coords.append(n.coordinates)
                # centroid
                cx = sum([c[0] for c in coords]) / float(len(coords))
                cy = sum([c[1] for c in coords]) / float(len(coords))
                points.append((cx, cy, val.data, elem_label, ip))
    
    odb.close()
    return points, u1_mm

def compute_hausdorff_distance(pts_a, pts_b):
    """Compute bidirectional Hausdorff distance between two sets of 2D points."""
    if not pts_a or not pts_b:
        return None
    
    # a -> b directed distance
    max_d_a_to_b = 0.0
    for p_a in pts_a:
        min_d = min([math.sqrt((p_a[0]-p_b[0])**2 + (p_a[1]-p_b[1])**2) for p_b in pts_b])
        if min_d > max_d_a_to_b:
            max_d_a_to_b = min_d
            
    # b -> a directed distance
    max_d_b_to_a = 0.0
    for p_b in pts_b:
        min_d = min([math.sqrt((p_b[0]-p_a[0])**2 + (p_b[1]-p_a[1])**2) for p_a in pts_a])
        if min_d > max_d_b_to_a:
            max_d_b_to_a = min_d
            
    h_dist = max(max_d_a_to_b, max_d_b_to_a)
    return h_dist, max_d_a_to_b, max_d_b_to_a

if __name__ == '__main__':
    h0_odb = 'models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/M2REF_H0_NPHYSFIX_REPRO.odb'
    h1_odb = 'models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/M2REF_H1_FRACFIX.odb'
    h2_odb = 'models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/M2REF_H2_FRACFIX.odb'
    
    print("=== Extracting Matched State Crack Points at Step-2 Frame 17 (U1 = 0.00925 mm) ===")
    pts_h0, u1_h0 = extract_crack_nodes(h0_odb, 'Step-2', 17, 0.5)
    pts_h1, u1_h1 = extract_crack_nodes(h1_odb, 'Step-2', 17, 0.5)
    pts_h2, u1_h2 = extract_crack_nodes(h2_odb, 'Step-2', 17, 0.5)
    
    print("Crack points (SDV15 >= 0.5):")
    print("  H0 (N=%d) at U1=%.6f mm" % (len(pts_h0), u1_h0))
    print("  H1 (N=%d) at U1=%.6f mm" % (len(pts_h1), u1_h1))
    print("  H2 (N=%d) at U1=%.6f mm" % (len(pts_h2), u1_h2))
    
    res_h1_h2 = compute_hausdorff_distance(pts_h1, pts_h2)
    if res_h1_h2:
        h_dist, d12, d21 = res_h1_h2
        print("\nMatched-State H1 vs H2 Hausdorff Distance (U1 = 0.00925 mm):")
        print("  Hausdorff Distance: %.6f mm (%.3f um)" % (h_dist, h_dist*1000.0))
        print("  Directed H1 -> H2:  %.6f mm" % d12)
        print("  Directed H2 -> H1:  %.6f mm" % d21)
        gate_pass = (h_dist <= 0.00375)
        print("  Gate (<= 0.00375 mm): %s" % ("PASS" if gate_pass else "FAIL"))
    else:
        print("Hausdorff calculation unavailable (empty point set).")
