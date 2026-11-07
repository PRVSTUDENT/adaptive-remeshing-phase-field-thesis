# -*- coding: utf-8 -*-
"""Export coarse preanalysis and adapted mesh geometry for high-resolution matplotlib rendering.
"""
from __future__ import print_function
import os
import numpy as np
from odbAccess import openOdb

def export_plotting_data():
    odb_path = 'models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PREANALYSIS.odb'
    out_npz = 'results/validation/method_a_plotting_data.npz'
    os.makedirs(os.path.dirname(out_npz), exist_ok=True)
    
    print("Reading coarse ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    inst = odb.rootAssembly.instances['PLATE-1']
    step = odb.steps['Step-1']
    frame = step.frames[-1]
    
    # Coarse nodes
    coarse_nodes = {}
    for n in inst.nodes:
        coarse_nodes[n.label] = (float(n.coordinates[0]), float(n.coordinates[1]))
        
    # Coarse elements & MISESERI
    coarse_polys = []
    coarse_miseseri = []
    coarse_h = []
    
    # Map element label to MISESERI
    m_field = frame.fieldOutputs['MISESERI']
    elem_miseseri = {}
    for v in m_field.values:
        el = v.elementLabel
        if el not in elem_miseseri:
            elem_miseseri[el] = []
        elem_miseseri[el].append(float(v.data))
        
    for el in inst.elements:
        conn = el.connectivity
        coords = [coarse_nodes[nid] for nid in conn if nid in coarse_nodes]
        if len(coords) < 3:
            continue
        coarse_polys.append(coords)
        x = [c[0] for c in coords]
        y = [c[1] for c in coords]
        area = 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(len(coords)-1)) + (x[-1]*y[0] - x[0]*y[-1]))
        coarse_h.append(np.sqrt(area) * 1000.0) # um
        m_vals = elem_miseseri.get(el.label, [0.0])
        coarse_miseseri.append(np.mean(m_vals))
        
    print("Coarse mesh: %d elements" % len(coarse_polys))
    odb.close()
    
    # Save coarse data as object array in npz
    # We can save ragged polygons as list of arrays
    coarse_poly_arrs = [np.array(p, dtype=np.float32) for p in coarse_polys]
    np.savez_compressed(
        out_npz,
        coarse_polys=np.array(coarse_poly_arrs, dtype=object),
        coarse_miseseri=np.array(coarse_miseseri, dtype=np.float32),
        coarse_h=np.array(coarse_h, dtype=np.float32)
    )
    print("Saved coarse mesh plotting data to %s" % out_npz)

if __name__ == '__main__':
    export_plotting_data()
