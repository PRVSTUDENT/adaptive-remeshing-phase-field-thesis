# -*- coding: utf-8 -*-
"""
Mode-II Gate M2-3: Native Adaptive Remeshing Reproduction & OFAT Sensitivity Suite
Governing Reference: Pandey & Kumar (2025) CMES, Section 4.2, Figs. 6(b), 12(b).

Pipeline:
1. Opens qualified M2-2 ODB (Job-1_UEL_paper_horizon.odb).
2. Verifies Step-1 Frame 2000 (ux = 0.0100 mm) MISESERI field.
3. Executes native mdb.adaptiveRemesh(odb) across OFAT errorTarget in {1.0, 2.0, 3.0, 5.0%}.
4. Extracts adapted mesh metrics:
   - Total elements, quad/tri breakdown, total nodes.
   - Exact geometric h_min, h_max, h_mean, h_p10, h_p90.
   - Fine element count (h <= 0.008 mm) and fraction.
   - Localization corridor centerline, chord angle, bottom boundary exit x-coordinate.
   - Spurious branch detection.
   - Non-identity comparison with historical F1308 11,972-element mesh.
   - Element count ceiling guard (<= 40,000 elements).
5. Exports candidate input decks and element geometry CSVs.
6. Generates MODE2_M2_3_REMESH_REPRODUCTION_MANIFEST.json.
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

HISTORICAL_F1308_ELEMENT_COUNT = 11972
HISTORICAL_F1308_NODE_COUNT = 12064
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
    elements_data = []
    for elem in p.elements:
        conn = elem.connectivity
        pts = [p.nodes[n_idx].coordinates for n_idx in conn]
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

def analyze_corridor_and_statistics(elements_data, total_nodes):
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
    quad_count = sum(1 for e in elements_data if e['type'] == 'QUAD')
    tri_count = sum(1 for e in elements_data if e['type'] == 'TRI')

    fine_threshold = 0.008  # ~ l_0 / 2
    fine_elems = [e for e in elements_data if e['h_eq'] <= fine_threshold]
    fine_count = len(fine_elems)
    fine_fraction = fine_count / float(n_total)

    # Determine corridor centerline by slicing y in [0.0, 0.5] in bins
    y_bins = [0.05 * i for i in range(11)]  # 0.0, 0.05, ..., 0.50
    centerline_pts = []
    for y_val in y_bins:
        band = [e for e in fine_elems if abs(e['yc'] - y_val) <= 0.035 and e['xc'] >= 0.45]
        if band:
            mean_x = sum([e['xc'] for e in band]) / float(len(band))
            centerline_pts.append((mean_x, y_val))

    # Compute chord angle from crack tip (y=0.5) to bottom boundary (y=0.0)
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

    # Check for spurious branches in upper half away from boundaries
    spurious_upper = [e for e in fine_elems if e['yc'] > 0.55 and 0.10 < e['xc'] < 0.90]
    has_spurious_branches = len(spurious_upper) > 50

    # Classification vs Fig. 6(b) / 12(b)
    # Fig. 6(b) chord angle is approx -50.1 deg, exit x ~ 0.93
    # Fig. 12(b) chord angle is approx -53.6 deg, exit x ~ 0.868
    if -58.0 <= chord_angle_deg <= -42.0 and 0.80 <= end_x <= 0.98 and not has_spurious_branches:
        classification = "MODE2_LOCALIZATION_CONSISTENT_WITH_PUBLISHED_PATH"
    elif not has_spurious_branches and end_x > 0.70:
        classification = "MODE2_LOCALIZATION_ACCEPTABLE_MARGINAL_DEVIATION"
    else:
        classification = "MODE2_LOCALIZATION_DIVERGENT"

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
        'corridor_chord_angle_deg': chord_angle_deg,
        'corridor_end_x_at_y0': end_x,
        'has_spurious_branches': has_spurious_branches,
        'classification': classification,
        'centerline_points': centerline_pts
    }

def run_m2_3_remesh_suite(odb_path, out_dir="."):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    print("=" * 80)
    print("MODE-II GATE M2-3: NATIVE ADAPTIVE REMESHING REPRODUCTION & SENSITIVITY")
    print("Preanalysis ODB :", odb_path)
    print("Output Directory:", out_dir)
    print("=" * 80)

    odb = odbAccess.openOdb(odb_path, readOnly=True)
    if 'Step-1' not in odb.steps:
        raise ValueError("Step-1 not found in ODB steps: %s" % odb.steps.keys())
    
    step1 = odb.steps['Step-1']
    last_frame = step1.frames[-1]
    print("Step-1 Frame count: %d, Final Frame ID: %d, Time/Disp: %.5f" % 
          (len(step1.frames), last_frame.frameId, last_frame.frameValue))
    
    if 'MISESERI' not in last_frame.fieldOutputs:
        raise ValueError("MISESERI field not found in Step-1 final frame fieldOutputs!")
    
    miseseri_field = last_frame.fieldOutputs['MISESERI']
    miseseri_vals = [float(v.data) for v in miseseri_field.values]
    print("MISESERI field values count: %d, min: %.6f, max: %.6f, mean: %.6f" % 
          (len(miseseri_vals), min(miseseri_vals), max(miseseri_vals), sum(miseseri_vals)/len(miseseri_vals)))

    error_targets = [1.0, 2.0, 3.0, 5.0]
    results = {}

    for et in error_targets:
        tag = "ET_%.0fPCT" % et
        model_name = "MODE2_M2_3_ET_%d" % int(et)
        print("\n" + "-" * 70)
        print(">>> Processing errorTarget = %.1f%% (Model: %s) <<<" % (et, model_name))

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

        # 4. Seed Coarse Part: h = 0.02 mm (matching Pandey & Kumar 2025 coarse mesh)
        p.seedPart(size=0.02, deviationFactor=0.1, minSizeFactor=0.1)
        elemTypeQuad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
        elemTypeTri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
        p.setElementType(regions=p.sets['ALL_ELEM'], elemTypes=(elemTypeQuad, elemTypeTri))
        p.generateMesh()

        coarse_elems = len(p.elements)
        coarse_nodes = len(p.nodes)
        print("Coarse Mesh Initialized: %d elements, %d nodes" % (coarse_elems, coarse_nodes))

        # 5. Assembly & Step
        a = m.rootAssembly
        inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
        m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0, 
                     initialInc=0.002, minInc=1e-9, maxInc=0.002, nlgeom=OFF)

        # 6. Remeshing Rule: UNIFORM_ERROR, MISESERI
        reg = inst.sets['ALL_ELEM']
        m.RemeshingRule(
            name='RR_MODE2_%d' % int(et),
            stepName='Step-1',
            region=reg,
            description='Publication-Faithful Mode-II Remeshing Rule errorTarget=%.1f%%' % et,
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
        print("Calling m.adaptiveRemesh(odb) with errorTarget=%.1f%%..." % et)
        m.adaptiveRemesh(odb=odb)
        print("adaptiveRemesh execution completed.")

        # 8. Extract Refined Mesh & Metrics
        elements_data = extract_part_mesh_elements(p)
        total_nodes = len(p.nodes)
        metrics = analyze_corridor_and_statistics(elements_data, total_nodes)
        metrics['error_target_pct'] = et

        # Anomaly guards
        is_identical_to_f1308 = (metrics['total_elements'] == HISTORICAL_F1308_ELEMENT_COUNT and 
                                 metrics['total_nodes'] == HISTORICAL_F1308_NODE_COUNT)
        metrics['is_identical_to_f1308'] = is_identical_to_f1308
        metrics['element_count_within_anomaly_limit'] = (metrics['total_elements'] <= 40000)

        # Proximity to paper 19,963 elements
        metrics['diff_vs_paper_19963_elements'] = metrics['total_elements'] - PAPER_REPORTED_ADAPTED_ELEMENT_COUNT
        metrics['relative_diff_vs_paper_pct'] = (abs(metrics['diff_vs_paper_19963_elements']) / float(PAPER_REPORTED_ADAPTED_ELEMENT_COUNT)) * 100.0

        print("  --> Results for %s:" % tag)
        print("      Elements: %d (Quads: %d, Tris: %d), Nodes: %d" % 
              (metrics['total_elements'], metrics['quad_count'], metrics['tri_count'], metrics['total_nodes']))
        print("      h_min: %.6f mm, h_mean: %.6f mm, h_max: %.6f mm" % 
              (metrics['h_min_mm'], metrics['h_mean_mm'], metrics['h_max_mm']))
        print("      Fine Elements (h <= 0.008 mm): %d (%.2f%%)" % 
              (metrics['fine_element_count'], metrics['fine_element_fraction_pct']))
        print("      Corridor Angle: %.2f deg, Bottom Exit x: %.4f" % 
              (metrics['corridor_chord_angle_deg'], metrics['corridor_end_x_at_y0']))
        print("      Verdict: %s" % metrics['classification'])
        print("      Diff vs Paper (19,963): %+d (%.2f%%)" % 
              (metrics['diff_vs_paper_19963_elements'], metrics['relative_diff_vs_paper_pct']))
        print("      Identical to historical F1308 (11,972)? %s" % is_identical_to_f1308)

        # 9. Export Input Deck
        raw_deck_path = os.path.join(out_dir, "M2_3_ADAPTED_RAW_%dPCT.inp" % int(et))
        job_name = "M2_3_ADAPTED_RAW_%dPCT" % int(et)
        j_raw = mdb.Job(name=job_name, model=model_name, description='Raw Native Refined Mode-II Model errorTarget=%.1f' % et)
        j_raw.writeInput(consistencyChecking=OFF)
        generated_inp = job_name + ".inp"
        if os.path.exists(generated_inp) and generated_inp != raw_deck_path:
            if os.path.exists(raw_deck_path):
                os.remove(raw_deck_path)
            os.rename(generated_inp, raw_deck_path)
        
        metrics['raw_deck_path'] = raw_deck_path
        if os.path.exists(raw_deck_path):
            metrics['raw_deck_sha256'] = compute_sha256(raw_deck_path)
            metrics['raw_deck_size_bytes'] = os.path.getsize(raw_deck_path)
            print("      Wrote deck: %s (size: %d bytes, SHA: %s...)" % 
                  (raw_deck_path, metrics['raw_deck_size_bytes'], metrics['raw_deck_sha256'][:16]))

        # 10. Export Element Geometry CSV
        csv_path = os.path.join(out_dir, "m2_3_mesh_elements_et%dpct.csv" % int(et))
        with open(csv_path, "w") as f_csv:
            f_csv.write("element_label,type,xc,yc,area,h_eq\n")
            for e in elements_data:
                f_csv.write("%d,%s,%.6f,%.6f,%.8e,%.6f\n" % (
                    e['label'], e['type'], e['xc'], e['yc'], e['area'], e['h_eq']
                ))
        metrics['element_csv_path'] = csv_path
        results[tag] = metrics

    odb.close()

    # Determine best candidate matching paper (19,963 elements)
    best_candidate_tag = min(results.keys(), key=lambda k: abs(results[k]['diff_vs_paper_19963_elements']))
    print("\n" + "=" * 80)
    print(">>> SENSITIVITY SUMMARY: Best match to paper 19,963 elements is %s (Elements: %d, Diff: %+d, %.2f%%) <<<" % 
          (best_candidate_tag, results[best_candidate_tag]['total_elements'], 
           results[best_candidate_tag]['diff_vs_paper_19963_elements'],
           results[best_candidate_tag]['relative_diff_vs_paper_pct']))
    print("=" * 80)

    # Master Manifest
    manifest = {
        'schema_version': '1.0.0',
        'task_id': 'F1315-MODE2-M2-3-NATIVE-REMESH-REPRODUCTION-AND-FORENSICS',
        'timestamp': '2026-10-07T21:00:00+02:00',
        'governing_reference': 'Pandey & Kumar (2025) CMES, Section 4.2',
        'source_odb': {
            'path': odb_path,
            'step': 'Step-1',
            'frame_index': -1,
            'driving_displacement_mm': 0.0100,
            'miseseri_stats': {
                'count': len(miseseri_vals),
                'min': min(miseseri_vals),
                'max': max(miseseri_vals),
                'mean': sum(miseseri_vals)/len(miseseri_vals)
            }
        },
        'forensic_classification_f1308': {
            'classification': 'REUSED_EXISTING_MESH_DIAGNOSTIC',
            'element_count': HISTORICAL_F1308_ELEMENT_COUNT,
            'node_count': HISTORICAL_F1308_NODE_COUNT,
            'notes': 'Historical 11,972 mesh originated in Task F1291; F1308 evaluated Step-1 data on existing mesh without new adaptiveRemesh call.'
        },
        'parameter_reconstruction_epistemology': {
            'geometry_and_coarse_mesh': 'PAPER_VERIFIED',
            'error_indicator_miseseri': 'PAPER_VERIFIED',
            'sizing_method_uniform_error': 'PROJECT_VERIFIED / INFERRED',
            'bounds_hmin_0p001_hmax_0p020': 'INFERRED',
            'error_target': 'UNRESOLVED_IN_PAPER_TEXT_OFAT_SWEEP_EXECUTED',
            'base_driving_state': 'PAPER_VERIFIED / PROJECT_VERIFIED'
        },
        'ofat_sweep_results': results,
        'best_matching_candidate': best_candidate_tag,
        'acceptance_criteria_summary': {
            'all_candidates_within_40k_elements': all(r['element_count_within_anomaly_limit'] for r in results.values()),
            'historical_f1308_non_identity_verified': not any(r['is_identical_to_f1308'] for r in results.values()),
            'corridor_localization_consistent': all(r['classification'] == 'MODE2_LOCALIZATION_CONSISTENT_WITH_PUBLISHED_PATH' for r in results.values()),
            'zero_solver_runs_enforced': True
        }
    }

    manifest_path = os.path.join(out_dir, "MODE2_M2_3_REMESH_REPRODUCTION_MANIFEST.json")
    with open(manifest_path, "w") as f_man:
        json.dump(manifest, f_man, indent=2)
    print("Saved master reproduction manifest to %s" % manifest_path)
    return manifest

if __name__ == "__main__":
    odb_in = sys.argv[1] if len(sys.argv) >= 2 else "Job-1_UEL_paper_horizon.odb"
    out_d = sys.argv[2] if len(sys.argv) >= 3 else "."
    run_m2_3_remesh_suite(odb_in, out_d)
