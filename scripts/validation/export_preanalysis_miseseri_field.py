# -*- coding: utf-8 -*-
"""Export element-level MISESERI and geometry from preanalysis ODB.
"""
from __future__ import print_function
import os
import csv
import numpy as np
from odbAccess import openOdb

def export_miseseri():
    odb_path = 'models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PREANALYSIS.odb'
    out_csv = 'results/validation/method_a_preanalysis_miseseri_field.csv'
    
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    
    odb = openOdb(odb_path, readOnly=True)
    inst = odb.rootAssembly.instances['PLATE-1']
    step = odb.steps['Step-1']
    frame = step.frames[-1]
    
    # Node coordinates
    node_coords = {}
    for n in inst.nodes:
        node_coords[n.label] = (n.coordinates[0], n.coordinates[1])
        
    # Element centroids and areas
    elem_info = {}
    for el in inst.elements:
        conn = el.connectivity
        coords = [node_coords[nid] for nid in conn if nid in node_coords]
        xc = np.mean([c[0] for c in coords])
        yc = np.mean([c[1] for c in coords])
        # Shoelace area
        x = [c[0] for c in coords]
        y = [c[1] for c in coords]
        area = 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(len(coords)-1)) + (x[-1]*y[0] - x[0]*y[-1]))
        elem_info[el.label] = {
            'type': el.type,
            'connectivity': conn,
            'xc': xc,
            'yc': yc,
            'area': area,
            'h_equiv': np.sqrt(area),
            'miseseri_vals': []
        }
        
    miseseri_field = frame.fieldOutputs['MISESERI']
    for v in miseseri_field.values:
        elabel = v.elementLabel
        if elabel in elem_info:
            elem_info[elabel]['miseseri_vals'].append(float(v.data))
            
    # Write to CSV
    with open(out_csv, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['element_label', 'type', 'xc', 'yc', 'area', 'h_equiv_mm', 'h_equiv_um', 'miseseri_mean', 'miseseri_max', 'n_nodes', 'connectivity'])
        for elabel in sorted(elem_info.keys()):
            info = elem_info[elabel]
            m_vals = info['miseseri_vals']
            m_mean = np.mean(m_vals) if m_vals else 0.0
            m_max = np.max(m_vals) if m_vals else 0.0
            conn_str = ';'.join(str(nid) for nid in info['connectivity'])
            writer.writerow([
                elabel,
                info['type'],
                '%.6f' % info['xc'],
                '%.6f' % info['yc'],
                '%.8e' % info['area'],
                '%.6f' % info['h_equiv'],
                '%.2f' % (info['h_equiv'] * 1000.0),
                '%.6f' % m_mean,
                '%.6f' % m_max,
                len(info['connectivity']),
                conn_str
            ])
            
    print("Exported %d elements to %s" % (len(elem_info), out_csv))
    odb.close()

if __name__ == '__main__':
    export_miseseri()
