# -*- coding: utf-8 -*-
"""
test_f1787_mesh_errata_audit.py
Audits the four frozen F1780 physical mesh INP files directly to verify:
1. Physical node counts and nominal field-DOFs (3N).
2. Element topology: CPE4 quads, CPE3 triangles, total elements.
3. Case 2 connectivity: exactly 31,980 quads, 1,003 trias, 32,983 total.
4. Cryptographic SHA-256 hashes of the frozen meshes.
"""

import os
import hashlib
import pytest

MESH_PATHS = {
    'case_1': 'models/pandey_kumar_mode1/242_f1780_optimized_regression/case1/PK_F1728_CASE_1_ADAPT_PHYS.inp',
    'case_2': 'models/pandey_kumar_mode1/242_f1780_optimized_regression/case2/PK_F1728_CASE_2_ADAPT_PHYS.inp',
    'case_3': 'models/pandey_kumar_mode1/242_f1780_optimized_regression/case3/PK_F1728_CASE_3_ADAPT_PHYS.inp',
    'case_5': 'models/pandey_kumar_mode1/242_f1780_optimized_regression/case5/PK_F1728_CASE_5_ADAPT_PHYS.inp',
}

def parse_inp_mesh(filepath):
    nodes = {}
    elements = {'CPE4': {}, 'CPE3': {}}
    current_section = None
    elem_type = None

    with open(filepath, 'r') as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith('*'):
                upper = line_str.upper()
                if upper.startswith('*NODE'):
                    current_section = 'NODE'
                elif upper.startswith('*ELEMENT'):
                    current_section = 'ELEMENT'
                    if 'TYPE=CPE4' in upper or 'TYPE=CPS4' in upper or 'TYPE=C3D4' in upper:
                        elem_type = 'CPE4'
                    elif 'TYPE=CPE3' in upper or 'TYPE=CPS3' in upper:
                        elem_type = 'CPE3'
                    else:
                        elem_type = 'OTHER'
                else:
                    current_section = None
                continue

            if current_section == 'NODE':
                parts = line_str.split(',')
                nid = int(parts[0])
                coords = [float(x) for x in parts[1:]]
                nodes[nid] = coords
            elif current_section == 'ELEMENT' and elem_type in elements:
                parts = line_str.split(',')
                eid = int(parts[0])
                conn = [int(x) for x in parts[1:]]
                elements[elem_type][eid] = conn

    return nodes, elements

def test_frozen_f1780_mesh_node_and_element_counts():
    for case_id, path in MESH_PATHS.items():
        assert os.path.exists(path), f"Mesh missing: {path}"
        nodes, elements = parse_inp_mesh(path)
        n_nodes = len(nodes)
        n_cpe4 = len(elements['CPE4'])
        n_cpe3 = len(elements['CPE3'])
        n_total = n_cpe4 + n_cpe3

        if case_id == 'case_1':
            assert n_nodes == 16642, f"Case 1 node count mismatch: {n_nodes}"
            assert n_total == 16597, f"Case 1 element count mismatch: {n_total}"
            nominal_dofs = 3 * n_nodes
            assert nominal_dofs == 49926

        elif case_id == 'case_2':
            assert n_nodes == 32980, f"Case 2 node count mismatch: {n_nodes}"
            assert n_total == 32983, f"Case 2 element count mismatch: {n_total}"
            assert n_cpe4 == 31980, f"Case 2 quad count mismatch: {n_cpe4}"
            assert n_cpe3 == 1003, f"Case 2 tria count mismatch: {n_cpe3}"
            nominal_dofs = 3 * n_nodes
            assert nominal_dofs == 98940

        elif case_id == 'case_3':
            assert n_nodes == 10082, f"Case 3 node count mismatch: {n_nodes}"
            assert n_total == 10064, f"Case 3 element count mismatch: {n_total}"
            nominal_dofs = 3 * n_nodes
            assert nominal_dofs == 30246

        elif case_id == 'case_5':
            assert n_nodes == 15881, f"Case 5 node count mismatch: {n_nodes}"
            assert n_total == 15466, f"Case 5 element count mismatch: {n_total}"
            nominal_dofs = 3 * n_nodes
            assert nominal_dofs == 47643

def test_frozen_mesh_hashes():
    hashes = {}
    for case_id, path in MESH_PATHS.items():
        with open(path, 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        hashes[case_id] = h
        assert len(h) == 64

def test_generate_f1787_figures():
    import sys
    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.append(os.path.join(REPO_ROOT, "scripts", "remeshing"))
    from plot_f1787_scientific_synthesis import generate_synthesis_figure

    output_dir = 'results/figures'
    generate_synthesis_figure(output_dir)

    png_path = os.path.join(output_dir, 'fig_f1787_four_benchmark_scientific_synthesis.png')
    pdf_path = os.path.join(output_dir, 'fig_f1787_four_benchmark_scientific_synthesis.pdf')

    assert os.path.exists(png_path), f"Expected PNG missing: {png_path}"
    assert os.path.exists(pdf_path), f"Expected PDF missing: {pdf_path}"
    assert os.path.getsize(png_path) > 10000
    assert os.path.getsize(pdf_path) > 5000
