# -*- coding: utf-8 -*-
"""
execute_mode2_corrected_adaptive_remesh.py
Abaqus CAE Python script to generate native adaptive meshes from the CORRECTED
coarse pre-analysis ODB (Job 1411104.mmaster02) where phase-field damage evolved
and an oblique Mode-II crack formed.

Evaluates Step-2 with errorTarget in {1.0, 2.0, 3.0, 5.0%}.
Controlled parameters:
  sizingMethod = UNIFORM_ERROR
  variables = ('MISESERI', )
  minElementSize = 0.001 mm
  maxElementSize = 0.020 mm
  refinementFactor = 10
  coarseningFactor = NOT_ALLOWED
"""
from __future__ import print_function
import os
import sys
import math
import json
import hashlib

from abaqus import mdb
from abaqusConstants import *
import regionToolset
import odbAccess
import mesh

DIGITIZED_FIG6B = [
    (0.495, 0.514), (0.540, 0.460), (0.600, 0.380),
    (0.680, 0.280), (0.760, 0.180), (0.840, 0.080), (0.930, 0.000)
]

DIGITIZED_FIG12B = [
    (0.500, 0.500), (0.535, 0.430), (0.585, 0.340),
    (0.650, 0.235), (0.725, 0.140), (0.800, 0.060), (0.868, 0.000)
]

PAPER_REPORTED_ADAPTED_ELEMENT_COUNT = 19963

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def extract_part_mesh_elements(p):
    """Extract element geometry, centroids, and equivalent sizes h = sqrt(Area)."""
    node_coords = [n.coordinates for n in p.nodes]
    elements_data = []
    for elem in p.elements:
        conn = elem.connectivity
        pts = [node_coords[n_idx] for n_idx in conn]
        xc = sum([pt[0] for pt in pts]) / float(len(pts))
        yc = sum([pt[1] for pt in pts]) / float(len(pts))
        
        n_pts = len(pts)
        if n_pts == 4:
            x = [pt[0] for pt in pts]
            y = [pt[1] for pt in pts]
            area = 0.5 * abs((x[0]*y[1] + x[1]*y[2] + x[2]*y[3] + x[3]*y[0]) - 
                             (y[0]*x[1] + y[1]*x[2] + y[2]*x[3] + y[3]*x[0]))
            elem_type = "QUAD"
        elif n_pts == 3:
            x = [pt[0] for pt in pts]
            y = [pt[1] for pt in pts]
            area = 0.5 * abs((x[0]*y[1] + x[1]*y[2] + x[2]*y[0]) - 
                             (y[0]*x[1] + y[1]*x[2] + y[2]*x[0]))
            elem_type = "TRI"
        else:
            area = 0.0
            for i in range(n_pts):
                j = (i + 1) % n_pts
                area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
            area = 0.5 * abs(area)
            elem_type = "POLY"

        h_eq = math.sqrt(max(area, 1e-14))
        elements_data.append({
            'label': elem.label,
            'type': elem_type,
            'nodes': list(conn),
            'xc': xc,
            'yc': yc,
            'area': area,
            'h_eq': h_eq
        })
    return elements_data

def analyze_mesh_corridor(elements_data, total_nodes):
    n_total = len(elements_data)
    if n_total == 0:
        return {}

    h_vals = sorted([e['h_eq'] for e in elements_data])
    h_min = h_vals[0]
    h_max = h_vals[-1]
    h_mean = sum(h_vals) / float(n_total)
    h_median = h_vals[n_total // 2]
    h_p10 = h_vals[int(0.10 * n_total)]
    h_p90 = h_vals[int(0.90 * n_total)]
    quad_count = sum([1 for e in elements_data if e['type'] == 'QUAD'])
    tri_count = sum([1 for e in elements_data if e['type'] == 'TRI'])

    fine_threshold = 0.008  # ~ l_0 / 2 = 0.0075 mm
    fine_elems = [e for e in elements_data if e['h_eq'] <= fine_threshold]
    fine_count = len(fine_elems)
    fine_fraction = fine_count / float(n_total)

    # Total area and fine area
    total_area = sum([e['area'] for e in elements_data])
    fine_area = sum([e['area'] for e in fine_elems])

    # Corridor definition (band around crack path from (0.5, 0.5) to (0.85, 0.0))
    # y = 0.5 - 1.43*(x - 0.5) => line connecting (0.5, 0.5) to (0.85, 0.0)
    # Check elements in crack corridor: x >= 0.48, y <= 0.52, and perpendicular dist <= 0.10 mm
    in_corridor_fine = []
    outside_fine = []
    for e in fine_elems:
        xc, yc = e['xc'], e['yc']
        # Distance to line segment from (0.5, 0.5) to (0.85, 0.0)
        # Line eq: -0.5*x - 0.35*y + 0.5*0.35 + 0.5*0.5 = 0 => 0.5*x + 0.35*y - 0.425 = 0
        if xc >= 0.48 and yc <= 0.52:
            dist = abs(0.5*(yc - 0.5) + (0.85 - 0.5)*(xc - 0.5)) / math.sqrt(0.5**2 + 0.35**2)
            if dist <= 0.12:
                in_corridor_fine.append(e)
            else:
                outside_fine.append(e)
        else:
            outside_fine.append(e)

    corridor_fine_count = len(in_corridor_fine)
    outside_fine_count = len(outside_fine)
    corridor_fine_fraction = (corridor_fine_count / float(fine_count) * 100.0) if fine_count > 0 else 0.0

    # Determine corridor centerline by slicing y in [0.0, 0.5] in bins
    y_bins = [0.05 * i for i in range(11)]  # 0.0, 0.05, ..., 0.50
    centerline_pts = []
    for y_val in y_bins:
        band = [e for e in in_corridor_fine if abs(e['yc'] - y_val) <= 0.035]
        if band:
            mean_x = sum([e['xc'] for e in band]) / float(len(band))
            centerline_pts.append((mean_x, y_val))

    if len(centerline_pts) >= 2:
        start_pt = max(centerline_pts, key=lambda pt: pt[1])
        end_pt = min(centerline_pts, key=lambda pt: pt[1])
        dx = end_pt[0] - start_pt[0]
        dy = end_pt[1] - start_pt[1]
        chord_angle_deg = math.degrees(math.atan2(dy, dx))
        end_x = end_pt[0]
    else:
        chord_angle_deg = 0.0
        end_x = 0.5

    return {
        'total_elements': n_total,
        'quad_count': quad_count,
        'tri_count': tri_count,
        'total_nodes': total_nodes,
        'h_min_mm': h_min,
        'h_max_mm': h_max,
        'h_mean_mm': h_mean,
        'h_median_mm': h_median,
        'h_p10_mm': h_p10,
        'h_p90_mm': h_p90,
        'fine_element_count': fine_count,
        'fine_element_fraction_pct': fine_fraction * 100.0,
        'corridor_fine_count': corridor_fine_count,
        'outside_fine_count': outside_fine_count,
        'corridor_fine_fraction_pct': corridor_fine_fraction,
        'corridor_chord_angle_deg': chord_angle_deg,
        'corridor_end_x_at_y0': end_x,
        'centerline_points': centerline_pts
    }

def run_corrected_adaptive_remesh(odb_path, out_dir="."):
    out_dir = os.path.abspath(out_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    print("=" * 80)
    print("MODE-II CORRECTED ADAPTIVE REMESHING SUITE (STEP-2 DAMAGE EVOLVED)")
    print("ODB Path : %s" % odb_path)
    print("Out Dir  : %s" % out_dir)
    print("=" * 80)

    if not os.path.exists(odb_path):
        raise IOError("ODB file not found at: %s" % odb_path)

    odb = odbAccess.openOdb(odb_path, readOnly=True)
    if 'Step-2' not in odb.steps:
        raise ValueError("Step-2 not found in ODB steps: %s" % odb.steps.keys())

    step2 = odb.steps['Step-2']
    last_frame = step2.frames[-1]
    print("Step-2 Frame count: %d, Final Frame ID: %d, Time/Disp: %.5f" % 
          (len(step2.frames), last_frame.frameId, last_frame.frameValue))

    if 'MISESERI' not in last_frame.fieldOutputs:
        raise ValueError("MISESERI field not found in Step-2 final frame fieldOutputs!")

    miseseri_field = last_frame.fieldOutputs['MISESERI']
    miseseri_vals = [float(v.data) for v in miseseri_field.values]
    print("Step-2 MISESERI count: %d, min: %.6e, max: %.6e, mean: %.6e" % 
          (len(miseseri_vals), min(miseseri_vals), max(miseseri_vals), sum(miseseri_vals)/len(miseseri_vals)))

    error_targets = [1.0, 2.0, 3.0, 5.0]
    results = {}

    for et in error_targets:
        tag = "ET_%.0fPCT" % et
        model_name = "MODE2_CORRECTED_ET_%d" % int(et)
        print("\n" + "-" * 70)
        print(">>> Processing errorTarget = %.1f%% on Step-2 (Model: %s) <<<" % (et, model_name))

        if model_name in mdb.models:
            del mdb.models[model_name]
        m = mdb.Model(name=model_name)

        # 1. CAD Geometry: 1.0 x 1.0 mm square [0, 1] x [0, 1]
        s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
        s.rectangle(point1=(0.0, 0.0), point2=(1.0, 1.0))
        p = m.Part(name='PART-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
        p.BaseShell(sketch=s)
        del m.sketches['__profile__']

        # 2. Partition for Crack Seam: from (0.0, 0.5) to (0.5, 0.5)
        p.PartitionFaceByShortestPath(faces=p.faces, point1=(0.0, 0.5, 0.0), point2=(0.5, 0.5, 0.0))
        seam_edge = p.edges.findAt(((0.25, 0.5, 0.0), ))
        p.engineeringFeatures.assignSeam(regions=regionToolset.Region(edges=seam_edge))

        # 3. Material & Section
        mat = m.Material(name='Steel')
        mat.Elastic(table=((210000.0, 0.3), ))
        m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
        p.Set(name='ALL_ELEM', faces=p.faces)
        p.SectionAssignment(region=p.sets['ALL_ELEM'], sectionName='SolidSec')

        # 4. Seed Coarse Part: h = 0.02 mm
        p.seedPart(size=0.02, deviationFactor=0.1, minSizeFactor=0.1)
        elemTypeQuad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
        elemTypeTri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
        p.setElementType(regions=p.sets['ALL_ELEM'], elemTypes=(elemTypeQuad, elemTypeTri))
        p.generateMesh()

        coarse_elems = len(p.elements)
        coarse_nodes = len(p.nodes)
        print("Coarse Mesh: %d elements, %d nodes" % (coarse_elems, coarse_nodes))

        # 5. Assembly & Step
        a = m.rootAssembly
        inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
        m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0, 
                     initialInc=0.002, minInc=1e-9, maxInc=0.002, nlgeom=OFF)
        m.StaticStep(name='Step-2', previous='Step-1', timePeriod=1.0, 
                     initialInc=0.002, minInc=1e-9, maxInc=0.002, nlgeom=OFF)

        # 6. Remeshing Rule: UNIFORM_ERROR, MISESERI on Step-2
        reg = inst.sets['ALL_ELEM']
        m.RemeshingRule(
            name='RR_MODE2_CORRECTED_%d' % int(et),
            stepName='Step-2',
            region=reg,
            description='Corrected Mode-II Remeshing Rule Step-2 errorTarget=%.1f%%' % et,
            outputFrequency=ALL_INCREMENTS,
            variables=('MISESERI', ),
            sizingMethod=UNIFORM_ERROR,
            errorTarget=float(et),
            specifyMinSize=True,
            specifyMaxSize=True,
            minElementSize=0.001,
            maxElementSize=0.020,
            elementCountLimit=None,
            coarseningFactor=NOT_ALLOWED,
            refinementFactor=10
        )

        # 7. Execute Native adaptiveRemesh
        print("Calling m.adaptiveRemesh(odb) on Step-2 with errorTarget=%.1f%%..." % et)
        m.adaptiveRemesh(odb=odb)
        print("adaptiveRemesh execution completed.")

        # 8. Extract Refined Mesh & Metrics
        elements_data = extract_part_mesh_elements(p)
        total_nodes = len(p.nodes)
        metrics = analyze_mesh_corridor(elements_data, total_nodes)
        metrics['error_target_pct'] = et
        metrics['diff_vs_paper_19963'] = metrics['total_elements'] - PAPER_REPORTED_ADAPTED_ELEMENT_COUNT
        metrics['rel_diff_vs_paper_pct'] = (abs(metrics['diff_vs_paper_19963']) / float(PAPER_REPORTED_ADAPTED_ELEMENT_COUNT)) * 100.0

        print("  --> Results for %s on Step-2:" % tag)
        print("      Elements: %d (Quads: %d, Tris: %d), Nodes: %d" % 
              (metrics['total_elements'], metrics['quad_count'], metrics['tri_count'], metrics['total_nodes']))
        print("      h_min: %.6f mm, h_mean: %.6f mm, h_max: %.6f mm" % 
              (metrics['h_min_mm'], metrics['h_mean_mm'], metrics['h_max_mm']))
        print("      Fine Elements (h <= 0.008 mm): %d (%.2f%%)" % 
              (metrics['fine_element_count'], metrics['fine_element_fraction_pct']))
        print("      Corridor Fine Elements: %d (%.2f%% of fine elements)" % 
              (metrics['corridor_fine_count'], metrics['corridor_fine_fraction_pct']))
        print("      Outside Fine Elements: %d" % metrics['outside_fine_count'])
        print("      Corridor Angle: %.2f deg, Bottom Exit x: %.4f" % 
              (metrics['corridor_chord_angle_deg'], metrics['corridor_end_x_at_y0']))
        print("      Diff vs Paper (19,963): %+d (%.2f%%)" % 
              (metrics['diff_vs_paper_19963'], metrics['rel_diff_vs_paper_pct']))

        # 9. Export Input Deck
        raw_deck_path = os.path.abspath(os.path.join(out_dir, "M2_CORRECTED_ADAPTED_RAW_%dPCT.inp" % int(et)))
        job_name = "M2_CORRECTED_ADAPTED_RAW_%dPCT" % int(et)
        j_raw = mdb.Job(name=job_name, model=model_name, description='Corrected Refined Mode-II Model Step-2 errorTarget=%.1f' % et)
        j_raw.writeInput(consistencyChecking=OFF)
        generated_inp = os.path.abspath(job_name + ".inp")
        if os.path.exists(generated_inp) and generated_inp != raw_deck_path:
            if os.path.exists(raw_deck_path):
                os.remove(raw_deck_path)
            os.rename(generated_inp, raw_deck_path)
        
        metrics['raw_deck_path'] = raw_deck_path
        if os.path.exists(raw_deck_path):
            metrics['raw_deck_sha256'] = compute_sha256(raw_deck_path)
            metrics['raw_deck_size_bytes'] = os.path.getsize(raw_deck_path)
            print("      Wrote deck: %s (size: %d bytes)" % (raw_deck_path, metrics['raw_deck_size_bytes']))

        # 10. Export Element Geometry CSV
        csv_path = os.path.join(out_dir, "m2_corrected_mesh_elements_et%dpct.csv" % int(et))
        with open(csv_path, "w") as f_csv:
            f_csv.write("element_label,type,xc,yc,area,h_eq\n")
            for e in elements_data:
                f_csv.write("%d,%s,%.6f,%.6f,%.8e,%.6f\n" % (
                    e['label'], e['type'], e['xc'], e['yc'], e['area'], e['h_eq']
                ))
        metrics['element_csv_path'] = csv_path

        # 11. Export Node Geometry CSV
        nodes_csv_path = os.path.join(out_dir, "m2_corrected_mesh_nodes_et%dpct.csv" % int(et))
        with open(nodes_csv_path, "w") as f_ncsv:
            f_ncsv.write("node_label,x,y\n")
            for n in p.nodes:
                coords = n.coordinates
                f_ncsv.write("%d,%.8f,%.8f\n" % (n.label, coords[0], coords[1]))
        metrics['node_csv_path'] = nodes_csv_path

        results[tag] = metrics

    odb.close()

    # Master Manifest
    manifest = {
        'schema_version': '1.0.0',
        'task_id': 'F1347-MODE2-CORRECTED-PREANALYSIS-MISESERI-CORRIDOR-AND-REMESHING',
        'source_odb': {
            'path': odb_path,
            'job_id': '1411104.mmaster02',
            'job_name': 'M2_J1_COARSE_RETEST',
            'step': 'Step-2',
            'driving_displacement_mm': 0.0200,
            'd_max': 1.0,
            'crack_chord_angle_deg': -57.95
        },
        'sweep_results': results
    }

    manifest_path = os.path.join(out_dir, "MODE2_CORRECTED_REMESH_MANIFEST.json")
    with open(manifest_path, "w") as f_man:
        json.dump(manifest, f_man, indent=2)
    print("\nSaved master corrected remesh manifest to %s" % manifest_path)
    return manifest

if __name__ == "__main__":
    odb_in = "/scratch9/pr21vyci/runs/mode2_j1_coarse_retest/Job-1_UEL.odb"
    out_d = "/scratch9/pr21vyci/runs/mode2_j1_coarse_retest/m2_corrected_remesh"

    for a in sys.argv:
        if a.endswith('.odb') and os.path.exists(a):
            odb_in = a
        elif os.path.isdir(a) and a != '.':
            out_d = a

    run_corrected_adaptive_remesh(odb_in, out_d)
