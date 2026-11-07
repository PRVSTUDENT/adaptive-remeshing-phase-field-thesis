# -*- coding: utf-8 -*-
"""
scripts/validation/analyze_coarse_crack_topology.py
=================================================
Analyzes the spatial topology of damage on the coarse 2,906-element mesh:
- Notch tip region: x in [0.49, 0.55], y in [0.48, 0.55]
- Ligament region: x in [0.50, 0.65], y in [0.50, 0.65]
- Hole boundary: center (0.65, 0.65), radius 0.10
- Right flank region: x > 0.75, y in [0.55, 0.75]
"""

from __future__ import print_function
import json
import os
import math

def analyze_topology():
    fields_path = 'results/validation/coarse_job1_fields.json'
    phys_inp = 'models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_PHYS.inp'
    
    with open(fields_path, 'r') as f:
        fields = json.load(f)
        
    # Read nodes and elements from phys_inp
    nodes = {}
    elements = {}
    
    with open(phys_inp, 'r') as f:
        section = None
        for line in f:
            line = line.strip()
            if line.startswith('*'):
                if line.startswith('*NODE'):
                    section = 'NODE'
                elif line.startswith('*ELEMENT'):
                    section = 'ELEMENT'
                else:
                    section = None
                continue
                
            if section == 'NODE' and line:
                parts = [p.strip() for p in line.split(',')]
                nid = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                nodes[nid] = (x, y)
            elif section == 'ELEMENT' and line:
                parts = [p.strip() for p in line.split(',')]
                eid = int(parts[0])
                conn = [int(p) for p in parts[1:]]
                elements[eid] = conn
                
    print("Loaded %d nodes, %d elements" % (len(nodes), len(elements)))
    
    # Compute element centroids
    centroids = {}
    for eid, conn in elements.items():
        cx = sum(nodes[n][0] for n in conn) / len(conn)
        cy = sum(nodes[n][1] for n in conn) / len(conn)
        centroids[eid] = (cx, cy)
        
    # Analyze each key frame
    results = {}
    
    for kf_name, kf_data in fields.items():
        d_map = {int(k): v for k, v in kf_data['d'].items()}
        
        # Categorize damaged elements
        d09_elems = [eid for eid, d in d_map.items() if d >= 0.90]
        d05_elems = [eid for eid, d in d_map.items() if d >= 0.50]
        d01_elems = [eid for eid, d in d_map.items() if d >= 0.10]
        
        # Regional counts
        def classify_region(eid):
            cx, cy = centroids[eid]
            # Hole center (0.65, 0.65), R=0.10
            dist_hole = math.sqrt((cx - 0.65)**2 + (cy - 0.65)**2)
            
            if cx <= 0.52 and abs(cy - 0.50) <= 0.03:
                return "NOTCH_TIP"
            elif cx > 0.50 and cx < 0.65 and cy >= 0.50 and cy <= 0.65:
                return "LIGAMENT"
            elif dist_hole <= 0.11:
                return "HOLE_BOUNDARY"
            elif cx >= 0.74 and cy >= 0.55 and cy <= 0.75:
                return "RIGHT_FLANK"
            elif cx > 0.80:
                return "FAR_RIGHT"
            else:
                return "BULK"
                
        d09_regions = {}
        for eid in d09_elems:
            reg = classify_region(eid)
            d09_regions[reg] = d09_regions.get(reg, 0) + 1
            
        d05_regions = {}
        for eid in d05_elems:
            reg = classify_region(eid)
            d05_regions[reg] = d05_regions.get(reg, 0) + 1
            
        d01_regions = {}
        for eid in d01_elems:
            reg = classify_region(eid)
            d01_regions[reg] = d01_regions.get(reg, 0) + 1
            
        print("\n=== Topology Breakdown for %s ===" % kf_name)
        print("d >= 0.90 (%d elems): %s" % (len(d09_elems), str(d09_regions)))
        print("d >= 0.50 (%d elems): %s" % (len(d05_elems), str(d05_regions)))
        print("d >= 0.10 (%d elems): %s" % (len(d01_elems), str(d01_regions)))
        
        # Check max x and min x of d >= 0.50 elements
        if d05_elems:
            xs05 = [centroids[eid][0] for eid in d05_elems]
            ys05 = [centroids[eid][1] for eid in d05_elems]
            print("  d >= 0.50 x-span: [%.4f, %.4f], y-span: [%.4f, %.4f]" % (
                min(xs05), max(xs05), min(ys05), max(ys05)
            ))
            
        results[kf_name] = {
            "d09_count": len(d09_elems),
            "d09_regions": d09_regions,
            "d05_count": len(d05_elems),
            "d05_regions": d05_regions,
            "d01_count": len(d01_elems),
            "d01_regions": d01_regions
        }
        
    out_json = 'results/validation/coarse_crack_topology_summary.json'
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)
    print("\nWrote topology summary to: %s" % out_json)

if __name__ == '__main__':
    analyze_topology()
