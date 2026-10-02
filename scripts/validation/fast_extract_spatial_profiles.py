# -*- coding: utf-8 -*-
"""
Ultra-fast Abaqus Python script to extract nodal/integration d(x) profiles along y=0.5 mm
for all 5 fixed-mesh cases at u = 0.0050, 0.0056, 0.0060, 0.0068 mm.
Optimized: Pre-filters ligament elements in O(1) hash table to eliminate redundant centroid evaluations.
Runs in ~15-20 seconds across all 5 ODBs.
"""
from odbAccess import openOdb
import sys
import os
import json

ODBS = [
    {
        "id": "h0030",
        "h_mm": 0.00300,
        "path": "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/11_fixed_convergence_h0030/PK_M1_FIX_H0030_VIS.odb"
    },
    {
        "id": "h0020",
        "h_mm": 0.00200,
        "path": "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/12_fixed_convergence_h0020/PK_M1_FIX_H0020_VIS.odb"
    },
    {
        "id": "h0015",
        "h_mm": 0.00150,
        "path": "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/13_fixed_convergence_h0015/PK_M1_FIX_H0015_VIS.odb"
    },
    {
        "id": "h00125",
        "h_mm": 0.00125,
        "path": "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/17_fixed_convergence_h00125_serial/PK_M1_FIX_H00125.odb"
    },
    {
        "id": "h00100",
        "h_mm": 0.00100,
        "path": "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/18_fixed_convergence_h00100_serial/PK_M1_FIX_H00100.odb"
    }
]

def extract_profiles_for_odb(entry):
    path = entry["path"]
    cid = entry["id"]
    if not os.path.exists(path):
        print("ODB not found: " + path)
        return None

    print("\n--- Processing ODB: " + cid + " ---")
    odb = openOdb(path=path, readOnly=True)
    root_assembly = odb.rootAssembly
    instance = root_assembly.instances.values()[0]

    # Pre-index node coordinates in a fast dict: nid -> (x, y)
    print("Pre-indexing nodes...")
    node_coords = {}
    for n in instance.nodes:
        node_coords[n.label] = (float(n.coordinates[0]), float(n.coordinates[1]))

    # Pre-filter elements near the ligament: |yc - 0.5| <= 2.5*h, xc >= 0.48
    print("Pre-filtering ligament elements...")
    h_val = float(entry["h_mm"])
    band_half = 2.5 * h_val
    ligament_elem_centroids = {} # eid -> (xc, yc)

    for el in instance.elements:
        conn = el.connectivity
        pts = [node_coords[nid] for nid in conn]
        xc = float(sum(p[0] for p in pts) / float(len(pts)))
        yc = float(sum(p[1] for p in pts) / float(len(pts)))
        if abs(yc - 0.500000) <= band_half and xc >= 0.48:
            ligament_elem_centroids[el.label] = (float(xc), float(yc))

    print("Identified %d ligament elements in band (|y-0.5| <= %.5f mm, x>=0.48)" %
          (len(ligament_elem_centroids), band_half))

    # Target displacement states
    targets = [0.0050, 0.0056, 0.0060, 0.0068]
    step_keys = list(odb.steps.keys())

    # Find closest frame for each target displacement
    matched_frames = []
    for td in targets:
        best_diff = 1e9
        best_item = None
        for sk in step_keys:
            st = odb.steps[sk]
            is_step1 = ('1' in sk and '2' not in sk)
            for f_idx, fr in enumerate(st.frames):
                t = float(fr.frameValue)
                u_app = t * 0.005 if is_step1 else 0.005 + t * 0.005
                diff = abs(u_app - td)
                if diff < best_diff:
                    best_diff = diff
                    best_item = (float(td), float(u_app), str(sk), int(f_idx), fr)
        if best_item:
            matched_frames.append(best_item)

    results_by_target = {}

    for td, u_app, sk, f_idx, fr in matched_frames:
        print("Extracting profile at target u = %.4f mm (actual u = %.6f mm)" % (td, u_app))
        field_keys = list(fr.fieldOutputs.keys())

        sdv_field = None
        if 'SDV_SDV1' in field_keys:
            sdv_field = fr.fieldOutputs['SDV_SDV1']
        elif 'SDV1' in field_keys:
            sdv_field = fr.fieldOutputs['SDV1']
        elif 'SDV' in field_keys:
            sdv_field = fr.fieldOutputs['SDV']

        elem_d_points = []

        if sdv_field:
            for val in sdv_field.values:
                eid = val.elementLabel
                if eid in ligament_elem_centroids:
                    xc, yc = ligament_elem_centroids[eid]
                    vdata = val.data
                    if isinstance(vdata, (list, tuple)):
                        d_val = float(vdata[0])
                    else:
                        d_val = float(vdata)
                    elem_d_points.append([float(xc), float(yc), float(d_val), int(eid)])

        elem_d_points.sort(key=lambda it: it[0])
        print("  Found %d element data points in ligament band" % len(elem_d_points))

        results_by_target[str(td)] = {
            "target_u_mm": float(td),
            "actual_u_mm": float(u_app),
            "step": str(sk),
            "frame_idx": int(f_idx),
            "elem_d_points": elem_d_points
        }

    odb.close()
    return {
        "id": str(cid),
        "h_mm": float(entry["h_mm"]),
        "profiles": results_by_target
    }

def main():
    master = {}
    for entry in ODBS:
        res = extract_profiles_for_odb(entry)
        if res:
            master[entry["id"]] = res

    out_path = '/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/spatial_d_profiles_raw.json'
    with open(out_path, 'w') as f:
        json.dump(master, f, indent=2)
    print("\nSaved spatial profiles to " + out_path)

if __name__ == '__main__':
    main()
