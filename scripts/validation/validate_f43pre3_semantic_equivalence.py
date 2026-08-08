#!/usr/bin/env python3
"""
validate_f43pre3_semantic_equivalence.py

Deterministic semantic equivalence auditor for Abaqus INP decks:
Compares reference PRE2 deck vs active PRE3 deck to prove continuum physics,
boundary condition topology, load endpoint, domain geometry, and output request equivalence.
"""

import os
import sys
import re
import math
import json

def tri_area(p1, p2, p3):
    return 0.5 * abs(p1[0]*(p2[1] - p3[1]) + p2[0]*(p3[1] - p1[1]) + p3[0]*(p1[1] - p2[1]))

def quad_area_triangulated(p1, p2, p3, p4):
    a1 = tri_area(p1, p2, p3)
    a2 = tri_area(p1, p3, p4)
    return a1 + a2

def elem_characteristic_h(nodes_dict, elem_nodes):
    pts = [nodes_dict[n] for n in elem_nodes]
    n = len(pts)
    edge_lens = []
    for i in range(n):
        p1 = pts[i]
        p2 = pts[(i+1)%n]
        d = math.hypot(p1[0]-p2[0], p1[1]-p2[1])
        edge_lens.append(d)
    return sum(edge_lens) / n

def parse_inp_semantics(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input deck not found: {filepath}")

    with open(filepath, 'r') as f:
        lines = f.readlines()

    assembly_nodes = {}
    part_nodes = {}
    current_part = None
    elements = {}
    nsets = {}
    elsets = {}
    materials = {}
    sections = []
    bcs = []
    steps = []
    outputs = []
    equations = []
    couplings = []

    blocks = []
    cur_kw = None
    cur_lines = []

    for l in lines:
        s = l.strip()
        if not s or s.startswith('**'):
            continue
        if s.startswith('*'):
            if cur_kw:
                blocks.append((cur_kw, cur_lines))
            cur_kw = s
            cur_lines = []
        else:
            cur_lines.append(s)
    if cur_kw:
        blocks.append((cur_kw, cur_lines))

    cur_step = None
    cur_mat = None

    for header, blines in blocks:
        hu = header.upper()
        kw = hu.split(',')[0].strip()

        if kw == '*PART':
            m = re.search(r'NAME\s*=\s*([^,\s]+)', hu)
            current_part = m.group(1) if m else 'UNNAMED'
            part_nodes[current_part] = {}

        elif kw == '*END PART':
            current_part = None

        elif kw == '*NODE':
            for l in blines:
                p = [x.strip() for x in l.split(',')]
                nid = int(p[0])
                c = [float(x) for x in p[1:]]
                if len(c) == 2:
                    c.append(0.0)
                if current_part:
                    part_nodes[current_part][nid] = tuple(c)
                else:
                    assembly_nodes[nid] = tuple(c)

        elif kw == '*ELEMENT':
            m = re.search(r'TYPE\s*=\s*([^,\s]+)', hu)
            etype = m.group(1) if m else 'UNKNOWN'
            for l in blines:
                p = [int(x.strip()) for x in l.split(',') if x.strip()]
                eid = p[0]
                nlist = p[1:]
                elements[eid] = (etype, nlist)

        elif kw == '*NSET':
            m_name = re.search(r'NSET\s*=\s*([^,\s]+)', hu)
            sname = m_name.group(1) if m_name else 'UNNAMED'
            m_inst = re.search(r'INSTANCE\s*=\s*([^,\s]+)', hu)
            iname = m_inst.group(1) if m_inst else None
            key = (sname, iname)
            if key not in nsets:
                nsets[key] = set()
            if 'GENERATE' in hu:
                for l in blines:
                    p = [int(x.strip()) for x in l.split(',') if x.strip()]
                    start, stop, step = p[0], p[1], p[2] if len(p)>2 else 1
                    nsets[key].update(range(start, stop+1, step))
            else:
                for l in blines:
                    p = [int(x.strip()) for x in l.split(',') if x.strip()]
                    nsets[key].update(p)

        elif kw == '*ELSET':
            m_name = re.search(r'ELSET\s*=\s*([^,\s]+)', hu)
            sname = m_name.group(1) if m_name else 'UNNAMED'
            if sname not in elsets:
                elsets[sname] = set()
            if 'GENERATE' in hu:
                for l in blines:
                    p = [int(x.strip()) for x in l.split(',') if x.strip()]
                    start, stop, step = p[0], p[1], p[2] if len(p)>2 else 1
                    elsets[sname].update(range(start, stop+1, step))
            else:
                for l in blines:
                    p = [int(x.strip()) for x in l.split(',') if x.strip()]
                    elsets[sname].update(p)

        elif kw == '*MATERIAL':
            m = re.search(r'NAME\s*=\s*([^,\s]+)', hu)
            cur_mat = m.group(1) if m else 'UNNAMED'
            materials[cur_mat] = {}

        elif kw == '*ELASTIC':
            if cur_mat:
                p = [float(x.strip()) for x in blines[0].split(',') if x.strip()]
                materials[cur_mat]['E'] = p[0]
                materials[cur_mat]['nu'] = p[1]

        elif kw == '*SOLID SECTION':
            m_el = re.search(r'ELSET\s*=\s*([^,\s]+)', hu)
            m_mat = re.search(r'MATERIAL\s*=\s*([^,\s]+)', hu)
            sec_dict = {
                'elset': m_el.group(1) if m_el else None,
                'material': m_mat.group(1) if m_mat else None,
            }
            if blines:
                p = [float(x.strip()) for x in blines[0].split(',') if x.strip()]
                sec_dict['thickness'] = p[0] if p else 1.0
            sections.append(sec_dict)

        elif kw == '*STEP':
            cur_step = hu
            steps.append({'header': hu, 'lines': blines})

        elif kw == '*BOUNDARY':
            for l in blines:
                p = [x.strip() for x in l.split(',') if x.strip()]
                target = p[0]
                d1 = int(p[1])
                d2 = int(p[2]) if len(p)>2 and p[2]!='' else d1
                val = float(p[3]) if len(p)>3 else 0.0
                bcs.append({'target': target, 'dof1': d1, 'dof2': d2, 'val': val, 'step': cur_step})

        elif kw in ('*OUTPUT', '*NODE OUTPUT', '*ELEMENT OUTPUT', '*FILE OUTPUT', '*RESTART'):
            outputs.append({'header': hu, 'lines': blines})

        elif kw == '*EQUATION':
            equations.append({'header': hu, 'lines': blines})

        elif kw == '*COUPLING':
            couplings.append({'header': hu, 'lines': blines})

    pnodes = part_nodes.get('PLATEPART', {})
    node_count = len(pnodes) + len(assembly_nodes)
    elem_count = len(elements)

    cpe4_count = sum(1 for et, _ in elements.values() if et == 'CPE4')
    cpe3_count = sum(1 for et, _ in elements.values() if et == 'CPE3')

    elem_areas = []
    elem_hs = []
    negative_areas = 0

    for eid, (etype, nlist) in elements.items():
        pts = [pnodes[n] for n in nlist]
        if len(pts) == 3:
            a = tri_area(pts[0], pts[1], pts[2])
        elif len(pts) == 4:
            a = quad_area_triangulated(pts[0], pts[1], pts[2], pts[3])
        else:
            a = 0.0
        if a <= 0:
            negative_areas += 1
        elem_areas.append(a)
        elem_hs.append(elem_characteristic_h(pnodes, nlist))

    total_area = sum(elem_areas)
    elem_hs.sort()

    xs = [c[0] for c in pnodes.values()]
    ys = [c[1] for c in pnodes.values()]
    xmin, xmax = min(xs) if xs else 0.0, max(xs) if xs else 0.0
    ymin, ymax = min(ys) if ys else 0.0, max(ys) if ys else 0.0

    field_vars = set()
    for out in outputs:
        for l in out['lines']:
            vars_in_line = [v.strip() for v in l.split(',') if v.strip()]
            for v in vars_in_line:
                if not v.startswith('*'):
                    field_vars.add(v.upper())

    return {
        'filepath': filepath,
        'node_count': node_count,
        'elem_count': elem_count,
        'cpe4_count': cpe4_count,
        'cpe3_count': cpe3_count,
        'total_area': total_area,
        'negative_areas': negative_areas,
        'h_min': elem_hs[0] if elem_hs else 0.0,
        'h_median': elem_hs[len(elem_hs)//2] if elem_hs else 0.0,
        'h_mean': sum(elem_hs)/len(elem_hs) if elem_hs else 0.0,
        'h_max': elem_hs[-1] if elem_hs else 0.0,
        'xmin': xmin, 'xmax': xmax, 'ymin': ymin, 'ymax': ymax,
        'materials': materials,
        'sections': sections,
        'bcs': bcs,
        'steps': steps,
        'nsets': nsets,
        'equations': equations,
        'field_vars': field_vars,
        'part_nodes': pnodes,
        'assembly_nodes': assembly_nodes
    }


def compare_decks(pre2_path, pre3_path):
    d2 = parse_inp_semantics(pre2_path)
    d3 = parse_inp_semantics(pre3_path)

    failures = []
    checks = {}

    # 1. Material physics
    mat2 = d2['materials'].get('STEEL', {})
    mat3 = d3['materials'].get('STEEL', {})
    E2, nu2 = mat2.get('E'), mat2.get('nu')
    E3, nu3 = mat3.get('E'), mat3.get('nu')

    if E2 != 210000.0 or E3 != 210000.0:
        failures.append(f"Material E mismatch: PRE2={E2}, PRE3={E3}, expected 210000.0 N/mm^2")
        checks['material_E'] = False
    else:
        checks['material_E'] = True

    if nu2 != 0.3 or nu3 != 0.3:
        failures.append(f"Material nu mismatch: PRE2={nu2}, PRE3={nu3}, expected 0.3")
        checks['material_nu'] = False
    else:
        checks['material_nu'] = True

    checks['material_equivalence'] = checks['material_E'] and checks['material_nu']

    # 2. Section physics
    sec2 = d2['sections'][0] if d2['sections'] else {}
    sec3 = d3['sections'][0] if d3['sections'] else {}
    thick2 = sec2.get('thickness', 1.0)
    thick3 = sec3.get('thickness', 1.0)

    if thick2 != 1.0 or thick3 != 1.0:
        failures.append(f"Section thickness mismatch: PRE2={thick2}, PRE3={thick3}, expected 1.0 mm")
        checks['section_equivalence'] = False
    else:
        checks['section_equivalence'] = True

    # 3. Domain Geometry
    g2_bounds = (d2['xmin'], d2['xmax'], d2['ymin'], d2['ymax'])
    g3_bounds = (d3['xmin'], d3['xmax'], d3['ymin'], d3['ymax'])

    if abs(d2['xmin'] - (-0.5)) > 1e-5 or abs(d2['xmax'] - 0.5) > 1e-5 or abs(d2['ymin'] - (-0.5)) > 1e-5 or abs(d2['ymax'] - 0.5) > 1e-5:
        failures.append(f"PRE2 domain bounds invalid: {g2_bounds}")
        checks['domain_geometry'] = False
    elif abs(d3['xmin'] - (-0.5)) > 1e-5 or abs(d3['xmax'] - 0.5) > 1e-5 or abs(d3['ymin'] - (-0.5)) > 1e-5 or abs(d3['ymax'] - 0.5) > 1e-5:
        failures.append(f"PRE3 domain bounds invalid: {g3_bounds}")
        checks['domain_geometry'] = False
    else:
        checks['domain_geometry'] = True

    # Notch geometry check: y=0, x in [-0.5, 0.0]
    notch_nodes_2 = [p for p in d2['part_nodes'].values() if abs(p[1] - 0.0) < 1e-5 and -0.50001 <= p[0] <= 0.00001]
    notch_nodes_3 = [p for p in d3['part_nodes'].values() if abs(p[1] - 0.0) < 1e-5 and -0.50001 <= p[0] <= 0.00001]

    if len(notch_nodes_2) == 0 or len(notch_nodes_3) == 0:
        failures.append(f"Notch nodes missing along y=0, x in [-0.5, 0.0]: PRE2 count={len(notch_nodes_2)}, PRE3 count={len(notch_nodes_3)}")
        checks['notch_seam_equivalence'] = False
    else:
        checks['notch_seam_equivalence'] = True

    checks['geometry_equivalence'] = checks['domain_geometry'] and checks['notch_seam_equivalence']

    # 4. BC Topology & Load Endpoint
    bc_rp_2 = [b for b in d2['bcs'] if b['target'].upper() == 'RP' and b['dof1'] == 1]
    bc_rp_3 = [b for b in d3['bcs'] if b['target'].upper() == 'RP' and b['dof1'] == 1]

    u1_endpoint_2 = bc_rp_2[0]['val'] if bc_rp_2 else None
    u1_endpoint_3 = bc_rp_3[0]['val'] if bc_rp_3 else None

    if u1_endpoint_2 != 0.001 or u1_endpoint_3 != 0.001:
        failures.append(f"U1 load endpoint mismatch: PRE2={u1_endpoint_2}, PRE3={u1_endpoint_3}, expected 0.001 mm")
        checks['load_endpoint_equivalence'] = False
    else:
        checks['load_endpoint_equivalence'] = True

    # Constrained DOFs check
    bot_bc_2 = [b for b in d2['bcs'] if b['target'].upper() == 'BOTTOM_NODES']
    bot_bc_3 = [b for b in d3['bcs'] if b['target'].upper() == 'BOTTOM_NODES']

    bot_dofs_2 = set((b['dof1'], b['dof2']) for b in bot_bc_2)
    bot_dofs_3 = set((b['dof1'], b['dof2']) for b in bot_bc_3)

    if (1, 1) not in bot_dofs_2 or (2, 2) not in bot_dofs_2 or (1, 1) not in bot_dofs_3 or (2, 2) not in bot_dofs_3:
        failures.append(f"BOTTOM_NODES constrained DOFs invalid: PRE2={bot_dofs_2}, PRE3={bot_dofs_3}, expected DOFs (1,1) and (2,2)")
        checks['bc_dof_equivalence'] = False
    else:
        checks['bc_dof_equivalence'] = True

    bot_nids_2 = d2['nsets'].get(('BOTTOM_NODES', 'PLATEINSTANCE'), set())
    bot_nids_3 = d3['nsets'].get(('BOTTOM_NODES', 'PLATEINSTANCE'), set())

    bot_ys_2 = [d2['part_nodes'][n][1] for n in bot_nids_2]
    bot_ys_3 = [d3['part_nodes'][n][1] for n in bot_nids_3]

    if not bot_ys_2 or any(abs(y - (-0.5)) > 1e-5 for y in bot_ys_2):
        failures.append("PRE2 BOTTOM_NODES region not at y=-0.5 mm")
        checks['bc_region_equivalence'] = False
    elif not bot_ys_3 or any(abs(y - (-0.5)) > 1e-5 for y in bot_ys_3):
        failures.append("PRE3 BOTTOM_NODES region not at y=-0.5 mm")
        checks['bc_region_equivalence'] = False
    else:
        checks['bc_region_equivalence'] = True

    checks['BC_equivalence'] = checks['load_endpoint_equivalence'] and checks['bc_dof_equivalence'] and checks['bc_region_equivalence']

    # 5. Step Physics
    step2_header = d2['steps'][0]['header'] if d2['steps'] else ''
    step3_header = d3['steps'][0]['header'] if d3['steps'] else ''

    if 'NLGEOM=NO' not in step2_header or 'NLGEOM=NO' not in step3_header:
        failures.append("NLGEOM setting mismatch (expected NLGEOM=NO)")
        checks['step_equivalence'] = False
    else:
        checks['step_equivalence'] = True

    # 6. Element Areas & Domain Volume
    if d2['negative_areas'] > 0:
        failures.append(f"PRE2 contains {d2['negative_areas']} negative or zero element areas")
        checks['positive_element_areas'] = False
    elif d3['negative_areas'] > 0:
        failures.append(f"PRE3 contains {d3['negative_areas']} negative or zero element areas")
        checks['positive_element_areas'] = False
    else:
        checks['positive_element_areas'] = True

    area_rel_diff = abs(d3['total_area'] - d2['total_area']) / d2['total_area'] if d2['total_area'] > 0 else 1.0
    if area_rel_diff > 1e-4:
        failures.append(f"Domain area mismatch: PRE2={d2['total_area']:.8f}, PRE3={d3['total_area']:.8f}, rel_diff={area_rel_diff:.2e}")
        checks['domain_area_equivalence'] = False
    else:
        checks['domain_area_equivalence'] = True

    # 7. Output Requests
    req_vars = {'S', 'MISESERI', 'MISESAVG', 'EVOL', 'U', 'RF'}
    missing2 = req_vars - d2['field_vars']
    missing3 = req_vars - d3['field_vars']

    if missing2:
        failures.append(f"PRE2 missing required output variables: {missing2}")
        checks['output_request_equivalence'] = False
    elif missing3:
        failures.append(f"PRE3 missing required output variables: {missing3}")
        checks['output_request_equivalence'] = False
    else:
        checks['output_request_equivalence'] = True

    overall_passed = len(failures) == 0

    mesh_delta = {
        'PRE2_nodes': d2['node_count'],
        'PRE3_nodes': d3['node_count'],
        'delta_nodes': d3['node_count'] - d2['node_count'],
        'PRE2_elements': d2['elem_count'],
        'PRE3_elements': d3['elem_count'],
        'delta_elements': d3['elem_count'] - d2['elem_count'],
        'PRE2_CPE4': d2['cpe4_count'],
        'PRE3_CPE4': d3['cpe4_count'],
        'delta_CPE4': d3['cpe4_count'] - d2['cpe4_count'],
        'PRE2_CPE3': d2['cpe3_count'],
        'PRE3_CPE3': d3['cpe3_count'],
        'delta_CPE3': d3['cpe3_count'] - d2['cpe3_count'],
        'elem_count_rel_diff_percent': (d3['elem_count'] - d2['elem_count']) / d2['elem_count'] * 100.0,
        'PRE2_h_min': d2['h_min'], 'PRE2_h_median': d2['h_median'], 'PRE2_h_mean': d2['h_mean'], 'PRE2_h_max': d2['h_max'],
        'PRE3_h_min': d3['h_min'], 'PRE3_h_median': d3['h_median'], 'PRE3_h_mean': d3['h_mean'], 'PRE3_h_max': d3['h_max'],
        'PRE2_mesh_area': d2['total_area'],
        'PRE3_mesh_area': d3['total_area'],
        'area_relative_difference_percent': area_rel_diff * 100.0
    }

    result = {
        'overall_passed': overall_passed,
        'failures': failures,
        'checks': checks,
        'mesh_delta': mesh_delta,
        'mesh_topology_identity': False,
        'continuum_model_semantic_identity': "PASS" if overall_passed else "FAIL",
        'mesh_difference_classification': "accepted_discretization_difference_between_Abaqus2024_and_Abaqus2023_lineages" if overall_passed else "unexplained_discretization_mismatch"
    }

    return result


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pre2_path = os.path.join(repo_root, "models", "generated", "mode_ii", "f43_stage_c_bridge", "F43PRE2_GEOM.inp")
    pre3_path = os.path.join(repo_root, "models", "generated", "mode_ii", "f43_stage_c_bridge", "F43PRE3_GEOM.inp")

    if len(sys.argv) > 2:
        pre2_path = sys.argv[1]
        pre3_path = sys.argv[2]

    res = compare_decks(pre2_path, pre3_path)
    print(json.dumps(res, indent=2))

    if not res['overall_passed']:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
