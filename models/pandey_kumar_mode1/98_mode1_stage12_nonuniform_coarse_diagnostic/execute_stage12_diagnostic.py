# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import json
import math

import odbAccess
from abaqus import mdb
from abaqusConstants import (
    TWO_D_PLANAR, DEFORMABLE_BODY, STANDARD, CPE4, CPE3, ON, OFF,
    MODEL, UNIFORM_ERROR, NOT_ALLOWED, ALL_INCREMENTS, ADVANCING_FRONT, QUAD_DOMINATED, FREE
)
import regionToolset
import mesh

def compute_polygon_area_and_centroid(coords):
    num_n = len(coords)
    area_sum = 0.0
    for i in range(num_n):
        j = (i + 1) % num_n
        area_sum += coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
    area = 0.5 * abs(area_sum)
    h_eq = math.sqrt(area)
    
    cx = 0.0
    cy = 0.0
    for c in coords:
        cx += c[0]
        cy += c[1]
    cx = cx / float(num_n)
    cy = cy / float(num_n)
    
    edges = []
    for i in range(num_n):
        j = (i + 1) % num_n
        dx = coords[j][0] - coords[i][0]
        dy = coords[j][1] - coords[i][1]
        edges.append(math.hypot(dx, dy))
    min_e = min(edges)
    max_e = max(edges)
    ar = max_e / max(min_e, 1e-12)
    return area, h_eq, cx, cy, ar

def execute_stage12_diagnostic(odb_path, out_dir="."):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    print("="*75)
    print("STAGE 12: NON-UNIFORM COARSE MESH REALIZATION DIAGNOSTIC")
    print("="*75)
    print("Opening ODB: %s" % odb_path)
    
    o = odbAccess.openOdb(path=odb_path, readOnly=True)
    step1 = o.steps['Step-1']
    frame_last = step1.frames[-1]
    print("Step-1 total frames: %d, final frameValue: %.6f" % (len(step1.frames), frame_last.frameValue))
    
    # -------------------------------------------------------------
    # PHASE C: EXTRACT AND ANALYZE RAW MISESERI FIELD
    # -------------------------------------------------------------
    print("\n>>> PHASE C: Extracting raw MISESERI on coarse mesh...")
    
    # Check field outputs in frame_last
    avail_fields = list(frame_last.fieldOutputs.keys())
    print("Available field outputs: %s" % str(avail_fields))
    
    miseseri_field = None
    for fname in ['MISESERI', 'MISESER', 'MISES']:
        if fname in frame_last.fieldOutputs:
            miseseri_field = frame_last.fieldOutputs[fname]
            print("Found error field: %s (description: %s)" % (fname, miseseri_field.description))
            break
            
    # Extract element geometry and error values from ODB root assembly
    inst_name = list(o.rootAssembly.instances.keys())[0]
    odb_inst = o.rootAssembly.instances[inst_name]
    print("ODB Instance: %s with %d elements and %d nodes" % (inst_name, len(odb_inst.elements), len(odb_inst.nodes)))
    
    node_coords_dict = {}
    for n in odb_inst.nodes:
        node_coords_dict[n.label] = (n.coordinates[0], n.coordinates[1])
        
    miseseri_by_elem = {}
    if miseseri_field is not None:
        for val in miseseri_field.values:
            miseseri_by_elem[val.elementLabel] = val.data
            
    print("Total MISESERI values extracted: %d" % len(miseseri_by_elem))
    
    coarse_records = []
    miseseri_vals = []
    
    # Regional accumulators
    crack_tip_elems = []
    wake_elems = []
    ligament_elems = []
    far_field_elems = []
    
    for e in odb_inst.elements:
        conn = e.connectivity
        coords = [node_coords_dict[nl] for nl in conn]
        area, h_eq, cx, cy, ar = compute_polygon_area_and_centroid(coords)
        
        err_val = miseseri_by_elem.get(e.label, 0.0)
        miseseri_vals.append(err_val)
        
        # Determine region
        # Crack tip: r <= 0.1 from (0.5, 0.5)
        r_tip = math.hypot(cx - 0.5, cy - 0.5)
        if r_tip <= 0.1:
            region_name = 'CRACK_TIP'
            crack_tip_elems.append(e.label)
        elif cx <= 0.5 and abs(cy - 0.5) <= 0.1:
            region_name = 'CRACK_WAKE'
            wake_elems.append(e.label)
        elif cx > 0.5 and abs(cy - 0.5) <= 0.1:
            region_name = 'LIGAMENT'
            ligament_elems.append(e.label)
        else:
            region_name = 'FAR_FIELD'
            far_field_elems.append(e.label)
            
        coarse_records.append({
            'label': e.label,
            'type': e.type,
            'cx': cx,
            'cy': cy,
            'area': area,
            'h_eq': h_eq,
            'aspect_ratio': ar,
            'miseseri': err_val,
            'region': region_name
        })
        
    n_coarse = len(coarse_records)
    sorted_err = sorted(miseseri_vals)
    e_min = min(miseseri_vals)
    e_max = max(miseseri_vals)
    e_mean = sum(miseseri_vals) / float(n_coarse)
    e_median = sorted_err[int(0.50 * n_coarse)]
    e_sum = sum(miseseri_vals)
    
    print("Raw MISESERI Statistics:")
    print("  Min: %.6e, Median: %.6e, Mean: %.6e, Max: %.6e" % (e_min, e_median, e_mean, e_max))
    
    # Normalized footprints: e/e_max >= threshold
    fp_50 = [cr for cr in coarse_records if (cr['miseseri'] / max(e_max, 1e-12)) >= 0.50]
    fp_10 = [cr for cr in coarse_records if (cr['miseseri'] / max(e_max, 1e-12)) >= 0.10]
    fp_05 = [cr for cr in coarse_records if (cr['miseseri'] / max(e_max, 1e-12)) >= 0.05]
    fp_01 = [cr for cr in coarse_records if (cr['miseseri'] / max(e_max, 1e-12)) >= 0.01]
    fp_001 = [cr for cr in coarse_records if (cr['miseseri'] / max(e_max, 1e-12)) >= 0.001]
    
    # Regional error sums
    sum_tip = sum([cr['miseseri'] for cr in coarse_records if cr['region'] == 'CRACK_TIP'])
    sum_wake = sum([cr['miseseri'] for cr in coarse_records if cr['region'] == 'CRACK_WAKE'])
    sum_lig = sum([cr['miseseri'] for cr in coarse_records if cr['region'] == 'LIGAMENT'])
    sum_far = sum([cr['miseseri'] for cr in coarse_records if cr['region'] == 'FAR_FIELD'])
    
    # Vertical spread w(x) for >= 1% error footprint
    x_slices = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    w_fp01 = {}
    for xs in x_slices:
        elems_s = [cr for cr in fp_01 if abs(cr['cx'] - xs) <= 0.04]
        if elems_s:
            y_min = min([cr['cy'] for cr in elems_s])
            y_max = max([cr['cy'] for cr in elems_s])
            w_fp01[str(xs)] = {'count': len(elems_s), 'y_min': y_min, 'y_max': y_max, 'width_mm': y_max - y_min}
        else:
            w_fp01[str(xs)] = {'count': 0, 'width_mm': 0.0}
            
    # Phase C Verdict
    # Target morphology in Fig. 6(a) has MISESERI concentrated in a narrow band along y=0.5 with width ~0.1-0.2 mm.
    # If the >= 1% footprint covers > 80% of elements/domain, it remains domain-wide.
    fp01_elem_frac = float(len(fp_01)) / float(n_coarse)
    fp10_elem_frac = float(len(fp_10)) / float(n_coarse)
    corridor_error_share = (sum_tip + sum_wake + sum_lig) / max(e_sum, 1e-12)
    
    if fp01_elem_frac < 0.40 and corridor_error_share > 0.70:
        raw_miseseri_verdict = 'NONUNIFORM_TOPOLOGY_TOWARD_TARGET_MISESERI_LOCALIZATION'
    elif fp01_elem_frac > 0.80 or abs(corridor_error_share - 0.25) < 0.20:
        raw_miseseri_verdict = 'NONUNIFORM_TOPOLOGY_NO_MEANINGFUL_MISESERI_IMPROVEMENT'
    else:
        raw_miseseri_verdict = 'NONUNIFORM_TOPOLOGY_NO_MEANINGFUL_MISESERI_IMPROVEMENT'
        
    print("  Footprint >=50%%: %d elements (%.2f%%)" % (len(fp_50), len(fp_50)*100.0/n_coarse))
    print("  Footprint >=10%%: %d elements (%.2f%%)" % (len(fp_10), len(fp_10)*100.0/n_coarse))
    print("  Footprint >=1%%:  %d elements (%.2f%%)" % (len(fp_01), len(fp_01)*100.0/n_coarse))
    print("  Regional Error Shares: Tip=%.2f%%, Wake=%.2f%%, Ligament=%.2f%%, Far-Field=%.2f%%" % (
        sum_tip*100.0/e_sum, sum_wake*100.0/e_sum, sum_lig*100.0/e_sum, sum_far*100.0/e_sum
    ))
    print("  Phase C Raw MISESERI Verdict: %s" % raw_miseseri_verdict)
    
    # Save coarse CSV
    coarse_csv_path = os.path.join(out_dir, "stage12_nonuniform_coarse_elements.csv")
    with open(coarse_csv_path, "w") as f:
        f.write("label,type,cx,cy,area,h_eq,aspect_ratio,miseseri,region\n")
        for cr in coarse_records:
            f.write("%d,%s,%.6f,%.6f,%.8e,%.6f,%.4f,%.8e,%s\n" % (
                cr['label'], cr['type'], cr['cx'], cr['cy'], cr['area'], cr['h_eq'], cr['aspect_ratio'], cr['miseseri'], cr['region']
            ))
            
    # -------------------------------------------------------------
    # PHASE D: NATIVE 1% ADAPTIVE REMESHING EXECUTION
    # -------------------------------------------------------------
    print("\n>>> PHASE D: Executing Native 1% Adaptive Remeshing from non-uniform coarse ODB...")
    
    model_name = "PK_M1_STAGE12_NONUNIFORM_CAD"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    s.rectangle(point1=(0.0, 0.0), point2=(1.0, 1.0))
    p = m.Part(name='PART-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']
    
    # Partition crack seam y=0.5, 0 <= x <= 0.5
    p.PartitionFaceByShortestPath(faces=p.faces, point1=(0.0, 0.5, 0.0), point2=(0.5, 0.5, 0.0))
    seam_edge = p.edges.findAt(((0.25, 0.5, 0.0), ))
    p.engineeringFeatures.assignSeam(regions=regionToolset.Region(edges=seam_edge))
    
    p.Set(name='ALL_ELEM', faces=p.faces)
    
    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=p.sets['ALL_ELEM'], sectionName='SolidSec')
    
    # Mesh controls: Free Quad-dominated Advancing Front
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE, algorithm=ADVANCING_FRONT)
    
    # Staggered edge seeding matching the non-uniform diagnostic coarse mesh
    e_top = p.edges.findAt(((0.5, 1.0, 0.0), ))
    e_bottom = p.edges.findAt(((0.5, 0.0, 0.0), ))
    e_right = p.edges.findAt(((1.0, 0.5, 0.0), ))
    e_left_upper = p.edges.findAt(((0.0, 0.75, 0.0), ))
    e_left_lower = p.edges.findAt(((0.0, 0.25, 0.0), ))
    e_seam = p.edges.findAt(((0.25, 0.5, 0.0), ))
    
    p.seedEdgeByNumber(edges=e_top, number=53, constraint=mesh.FINER)
    p.seedEdgeByNumber(edges=e_bottom, number=47, constraint=mesh.FINER)
    p.seedEdgeByNumber(edges=e_right, number=51, constraint=mesh.FINER)
    p.seedEdgeByNumber(edges=e_left_upper, number=24, constraint=mesh.FINER)
    p.seedEdgeByNumber(edges=e_left_lower, number=26, constraint=mesh.FINER)
    p.seedEdgeByNumber(edges=e_seam, number=25, constraint=mesh.FINER)
    
    elemTypeQuad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elemTypeTri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=p.sets['ALL_ELEM'], elemTypes=(elemTypeQuad, elemTypeTri))
    p.generateMesh()
    
    coarse_cad_elems = len(p.elements)
    coarse_cad_nodes = len(p.nodes)
    print("Geometry-backed Part Coarse Mesh regenerated: %d elements, %d nodes" % (coarse_cad_elems, coarse_cad_nodes))
    
    a = m.rootAssembly
    inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0, nlgeom=OFF)
    reg = inst.sets['ALL_ELEM']
    
    # Sizing Contract: UNIFORM_ERROR, errorTarget=1.0%, refFactor=10, coarseningFactor=NOT_ALLOWED, h in [0.001, 0.020] mm, region=ALL_ELEM
    m.RemeshingRule(
        name='PK_M1_STAGE12_RR',
        stepName='Step-1',
        region=reg,
        description='Stage 12 Native 1% Remeshing Rule on Non-Uniform Coarse Mesh',
        outputFrequency=ALL_INCREMENTS,
        variables=('MISESERI', ),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=1.0,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.001,
        maxElementSize=0.020,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )
    
    print("Calling m.adaptiveRemesh(odb=o)...")
    m.adaptiveRemesh(odb=o)
    o.close()
    print("adaptiveRemesh call completed successfully!")
    
    p_refined = m.parts['PART-1']
    refined_nodes_count = len(p_refined.nodes)
    refined_elems_count = len(p_refined.elements)
    print("Adapted Mesh Generated: %d elements, %d nodes" % (refined_elems_count, refined_nodes_count))
    
    nodes_seq = p_refined.nodes
    elem_records_adapt = []
    
    corridor_count = 0
    upper_far_count = 0
    lower_far_count = 0
    wake_count = 0
    ligament_count = 0
    h_corridor = []
    h_far = []
    all_h = []
    
    for e in p_refined.elements:
        conn = e.connectivity
        coords = []
        for idx in conn:
            c = nodes_seq[idx].coordinates
            coords.append((c[0], c[1]))
        num_n = len(coords)
        
        area, h_eq, cx, cy, ar = compute_polygon_area_and_centroid(coords)
        all_h.append(h_eq)
        
        if 0.45 <= cy <= 0.55:
            corridor_count += 1
            h_corridor.append(h_eq)
            if cx <= 0.5:
                wake_count += 1
            else:
                ligament_count += 1
        elif cy > 0.55:
            upper_far_count += 1
            h_far.append(h_eq)
        else:
            lower_far_count += 1
            h_far.append(h_eq)
            
        elem_records_adapt.append({
            'label': e.label,
            'type': 'CPE4' if num_n == 4 else 'CPE3',
            'cx': cx,
            'cy': cy,
            'area': area,
            'h_eq': h_eq,
            'aspect_ratio': ar
        })
        
    far_field_total = upper_far_count + lower_far_count
    corridor_fraction = float(corridor_count) / float(refined_elems_count)
    far_field_fraction = float(far_field_total) / float(refined_elems_count)
    
    band_widths_adapt = {}
    for xs in x_slices:
        slice_elems = [er for er in elem_records_adapt if abs(er['cx'] - xs) <= 0.03 and er['h_eq'] <= 0.005]
        if slice_elems:
            y_min = min([er['cy'] for er in slice_elems])
            y_max = max([er['cy'] for er in slice_elems])
            band_widths_adapt[str(xs)] = {
                'count': len(slice_elems),
                'y_min': y_min,
                'y_max': y_max,
                'width_mm': y_max - y_min
            }
        else:
            band_widths_adapt[str(xs)] = {'count': 0, 'width_mm': 0.0}
            
    fine_elems = [er for er in elem_records_adapt if er['h_eq'] <= 0.003]
    if fine_elems:
        bbox_fine = {
            'count': len(fine_elems),
            'x_min': min([er['cx'] for er in fine_elems]),
            'x_max': max([er['cx'] for er in fine_elems]),
            'y_min': min([er['cy'] for er in fine_elems]),
            'y_max': max([er['cy'] for er in fine_elems])
        }
    else:
        bbox_fine = {'count': 0}
        
    coarse_remaining = [er for er in elem_records_adapt if er['h_eq'] >= 0.015]
    
    # Write adapted input deck
    deck_name = "PK_M1_STAGE12_NONUNIFORM_ADAPTED_1PCT"
    j_raw = mdb.Job(name=deck_name, model=model_name, description='Stage 12 Native 1% Refined Model from Non-Uniform Coarse Mesh')
    j_raw.writeInput(consistencyChecking=OFF)
    
    src_deck = deck_name + ".inp"
    dst_deck = os.path.join(out_dir, src_deck)
    if os.path.exists(src_deck) and os.path.abspath(src_deck) != os.path.abspath(dst_deck):
        import shutil
        shutil.move(src_deck, dst_deck)
        
    # Write adapted CSV
    csv_path = os.path.join(out_dir, "stage12_nonuniform_adapted_elements.csv")
    with open(csv_path, "w") as f:
        f.write("label,type,cx,cy,area,h_eq,aspect_ratio\n")
        for er in elem_records_adapt:
            f.write("%d,%s,%.6f,%.6f,%.8e,%.6f,%.4f\n" % (
                er['label'], er['type'], er['cx'], er['cy'], er['area'], er['h_eq'], er['aspect_ratio']
            ))
            
    sorted_h = sorted(all_h)
    n_h = len(sorted_h)
    
    # Phase D Adaptive Verdict
    # Compare with Package 93 baseline (57,929 elements, corridor fraction = 14.56%, far-field fraction = 85.44%)
    if corridor_fraction > 0.40 and refined_elems_count < 30000:
        adaptive_verdict = 'NONUNIFORM_TOPOLOGY_TOWARD_TARGET_LOCALIZATION'
    elif abs(corridor_fraction - 0.1456) < 0.08 and refined_elems_count > 50000:
        adaptive_verdict = 'NONUNIFORM_TOPOLOGY_NO_MEANINGFUL_IMPROVEMENT'
    else:
        adaptive_verdict = 'NONUNIFORM_TOPOLOGY_NO_MEANINGFUL_IMPROVEMENT'
        
    summary = {
        'audit_id': 'GATE6B-STAGE12-NONUNIFORM-COARSE-DIAGNOSTIC-20261003',
        'preanalysis_odb': odb_path,
        'caller_frame': 'Step-1 frame_last (u=0.005 mm)',
        'coarse_mesh_diagnostic': {
            'total_elements': n_coarse,
            'total_quads': len([cr for cr in coarse_records if 'CPE4' in cr['type'] or '4' in cr['type']]),
            'total_tris': len([cr for cr in coarse_records if 'CPE3' in cr['type'] or '3' in cr['type']]),
            'mean_h_eq_mm': sum([cr['h_eq'] for cr in coarse_records]) / float(n_coarse),
            'miseseri_stats': {
                'min': e_min,
                'median': e_median,
                'mean': e_mean,
                'max': e_max,
                'sum': e_sum
            },
            'footprints': {
                'ge_50pct_count': len(fp_50),
                'ge_50pct_fraction': float(len(fp_50)) / float(n_coarse),
                'ge_10pct_count': len(fp_10),
                'ge_10pct_fraction': float(len(fp_10)) / float(n_coarse),
                'ge_05pct_count': len(fp_05),
                'ge_05pct_fraction': float(len(fp_05)) / float(n_coarse),
                'ge_01pct_count': len(fp_01),
                'ge_01pct_fraction': float(len(fp_01)) / float(n_coarse),
                'ge_001pct_count': len(fp_001),
                'ge_001pct_fraction': float(len(fp_001)) / float(n_coarse)
            },
            'regional_error_shares': {
                'crack_tip_sum': sum_tip,
                'crack_tip_share': sum_tip / e_sum,
                'crack_wake_sum': sum_wake,
                'crack_wake_share': sum_wake / e_sum,
                'ligament_sum': sum_lig,
                'ligament_share': sum_lig / e_sum,
                'far_field_sum': sum_far,
                'far_field_share': sum_far / e_sum
            },
            'vertical_spread_fp01': w_fp01,
            'raw_miseseri_verdict': raw_miseseri_verdict
        },
        'sizing_contract': {
            'error_target_pct': 1.0,
            'sizing_method': 'UNIFORM_ERROR',
            'refinement_factor': 10,
            'coarsening_factor': 'NOT_ALLOWED',
            'min_element_size_mm': 0.001,
            'max_element_size_mm': 0.020,
            'region': 'ALL_ELEM'
        },
        'adapted_mesh': {
            'total_elements': refined_elems_count,
            'total_nodes': refined_nodes_count,
            'h_eq_stats': {
                'min': min(all_h),
                'p10': sorted_h[int(0.10*n_h)],
                'p25': sorted_h[int(0.25*n_h)],
                'median': sorted_h[int(0.50*n_h)],
                'mean': sum(all_h)/float(n_h),
                'p75': sorted_h[int(0.75*n_h)],
                'p90': sorted_h[int(0.90*n_h)],
                'max': max(all_h)
            }
        },
        'spatial_morphology': {
            'crack_corridor_count': corridor_count,
            'crack_corridor_fraction': corridor_fraction,
            'wake_count': wake_count,
            'ligament_count': ligament_count,
            'upper_far_field_count': upper_far_count,
            'lower_far_field_count': lower_far_count,
            'far_field_total_count': far_field_total,
            'far_field_fraction': far_field_fraction,
            'h_corridor_median_mm': sorted(h_corridor)[int(0.50*len(h_corridor))] if h_corridor else 0.0,
            'h_corridor_min_mm': min(h_corridor) if h_corridor else 0.0,
            'h_far_median_mm': sorted(h_far)[int(0.50*len(h_far))] if h_far else 0.0,
            'h_far_min_mm': min(h_far) if h_far else 0.0,
            'elements_near_nominal_h002_count': len(coarse_remaining),
            'refined_bbox_h003': bbox_fine,
            'refined_band_widths_by_x': band_widths_adapt
        },
        'comparison_vs_baselines': {
            'package_90_elements': 56344,
            'package_93_elements': 57929,
            'stage_11_elements': 57929,
            'stage_12_nonuniform_elements': refined_elems_count,
            'target_published_elements': 13941,
            'corridor_fraction_stage_12': corridor_fraction,
            'far_field_fraction_stage_12': far_field_fraction
        },
        'verdicts': {
            'raw_miseseri_verdict': raw_miseseri_verdict,
            'adaptive_morphology_verdict': adaptive_verdict
        }
    }
    
    json_path = os.path.join(out_dir, "STAGE12_NONUNIFORM_COARSE_SUMMARY.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "="*75)
    print("STAGE 12 FINAL SUMMARY:")
    print("  Coarse Mesh: %d elements (Mean h_eq = %.4f mm)" % (n_coarse, summary['coarse_mesh_diagnostic']['mean_h_eq_mm']))
    print("  Raw MISESERI Verdict: %s" % raw_miseseri_verdict)
    print("  Adapted Element Count: %d (Nodes: %d)" % (refined_elems_count, refined_nodes_count))
    print("  Corridor Elements: %d (%.2f%%)" % (corridor_count, corridor_fraction*100.0))
    print("  Far-Field Elements: %d (%.2f%%)" % (far_field_total, far_field_fraction*100.0))
    print("  Adaptive Verdict: %s" % adaptive_verdict)
    print("="*75)
    return summary

if __name__ == "__main__":
    odb_p = "PK_M1_JOB1_NONUNIFORM_CONT.odb"
    out_d = "models/pandey_kumar_mode1/98_mode1_stage12_nonuniform_coarse_diagnostic"
    execute_stage12_diagnostic(odb_p, out_d)
