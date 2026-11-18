"""Unit test suite for F1856 L-Panel damage-envelope remeshing and native fallback completion.
Verifies autonomous driver selection, fracture remesh quality and 100% ligament coverage,
elastic native fallback qualification, and exact mesh block reproduction of the F1846 baseline.
"""
import os
import json
import hashlib
import numpy as np
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest().lower()

def compute_body_sha256(path):
    h = hashlib.sha256()
    with open(path, 'r') as f:
        for line in f:
            stripped = line.strip()
            if not stripped.startswith('**'):
                h.update((stripped + '\n').encode('utf-8'))
    return h.hexdigest().lower()

def compute_mesh_block_sha256(path):
    h = hashlib.sha256()
    content = open(path, 'r').read()
    mesh_part = content.split('*End Assembly')[0] if '*End Assembly' in content else content
    for line in mesh_part.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith('**'):
            h.update((stripped + '\n').encode('utf-8'))
    return h.hexdigest().lower()

def test_f1856_fracture_donor_signal_and_selection():
    signal_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '285_f1856_lpanel_damage_envelope_remesh', 'f1856_lpanel_fracture_damage_strength.json')
    assert os.path.isfile(signal_path), f"Signal missing: {signal_path}"

    with open(signal_path, 'r') as f:
        sig = json.load(f)

    assert sig['max_damage'] >= 0.5, f"Damage {sig['max_damage']} below core threshold"
    assert abs(sig['max_damage'] - 0.6772) < 0.005
    assert sig['d_core'] == 0.5
    assert sig['elements_ge_core'] == 2
    assert sig['fraction_ge_core'] > 0.0
    assert sig['selected_driver'] == 'CONSTRUCTED_DAMAGE_ENVELOPE'

def test_f1856_fracture_remesh_properties_and_ligament_coverage():
    mesh_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '285_f1856_lpanel_damage_envelope_remesh', 'fracture_remesh', 'PK_ADAPT_UNFAMILIAR_L_PANEL_PHYS.inp')
    assert os.path.isfile(mesh_path), f"Fracture mesh missing: {mesh_path}"

    summary_path = os.path.join(REPO_ROOT, 'results', 'validation', 'f1856_lpanel_damage_envelope_remesh_summary.json')
    with open(summary_path, 'r') as f:
        summary = json.load(f)

    frac_data = summary['fracture_donor_evaluation']
    assert frac_data['total_elements'] == 15896
    assert frac_data['cpe4_quad_count'] == 15596
    assert frac_data['cpe3_tri_count'] == 300
    assert frac_data['quad_percent'] > 98.0
    assert frac_data['min_det_j'] > 0.0
    assert frac_data['max_aspect_ratio'] < 4.0

    # Ligament coverage verification
    lig = frac_data['coverage']['ligament_band']
    assert lig['element_count'] == 3365
    assert lig['h_le_l0_count_pct'] == 100.0, "Ligament band does not achieve 100% h<=l0 count coverage!"
    assert lig['h_le_l0_area_pct'] == 100.0, "Ligament band does not achieve 100% h<=l0 area coverage!"
    assert lig['h_le_half_l0_count_pct'] > 30.0, "Ligament band h<=l0/2 core fraction unexpectedly low"

    # Body SHA
    b_sha = compute_body_sha256(mesh_path)
    assert b_sha == "0fe997b545ff9d83d0a5c61f3b4619af623650f679461c397c20e28efdf3db6c"

    # Synthesis text audit
    syn_char = summary['synthesis_and_verdict']['fracture_remesh_character']
    assert '3,365 elements' in syn_char
    assert '100% h<=l0 coverage' in syn_char
    assert '31.35% h<=l0/2 count coverage' in syn_char
    assert '5,888' not in syn_char
    assert '99.4%' not in syn_char

def test_f1856_elastic_fallback_native_gate_and_reproduction():
    gate_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '285_f1856_lpanel_damage_envelope_remesh', 'f1856_lpanel_elastic_native_gate.json')
    assert os.path.isfile(gate_path), f"Native gate missing: {gate_path}"

    with open(gate_path, 'r') as f:
        gate = json.load(f)

    assert gate['accepted'] is True
    assert gate['triangle_anomaly_detected'] is False
    assert gate['native_fields_present'] is True

    # Mesh evaluation
    gen_mesh_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '285_f1856_lpanel_damage_envelope_remesh', 'elastic_fallback_remesh', 'PK_GEN_ADAPT_UNFAMILIAR_L_PANEL_PHYS.inp')
    base_mesh_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '276_f1846_generalized_framework', 'l_panel', 'PK_F1846_UNFAMILIAR_L_PANEL_ADAPT_PHYS.inp')
    assert os.path.isfile(gen_mesh_path)
    assert os.path.isfile(base_mesh_path)

    summary_path = os.path.join(REPO_ROOT, 'results', 'validation', 'f1856_lpanel_damage_envelope_remesh_summary.json')
    with open(summary_path, 'r') as f:
        summary = json.load(f)

    elas_data = summary['elastic_donor_fallback_evaluation']
    assert elas_data['total_elements'] == 567
    assert elas_data['cpe4_quad_count'] == 553
    assert elas_data['cpe3_tri_count'] == 14
    assert elas_data['min_det_j'] > 0.20
    assert elas_data['gate_06_geometric_ratio'] > 2.50
    assert elas_data['selected_driver'] == 'NATIVE_ABAQUS_STRESS_RECOVERY_ERROR'

    # Exact mesh block identity (all nodes, coordinates, elements, connectivity)
    gen_block = compute_mesh_block_sha256(gen_mesh_path)
    base_block = compute_mesh_block_sha256(base_mesh_path)
    assert gen_block == base_block == "6d09fee1f664fcfcee696c1a399d32fbbe68ce22cc406609e3de76596fc61d32"

    # Ligament coverage in elastic mesh (GAP-F1856-01 verification)
    elas_lig = elas_data['coverage']['ligament_band']
    assert elas_lig['element_count'] == 117
    assert elas_lig['h_le_l0_count'] == 1
    assert abs(elas_lig['h_le_l0_count_pct'] - 0.85) < 0.05
    assert abs(elas_lig['h_le_l0_area_pct'] - 0.05) < 0.05

    # Report table audit
    report_path = os.path.join(REPO_ROOT, 'docs', 'validation', 'F1856_LPANEL_DAMAGE_ENVELOPE_REMESH_REPORT.md')
    assert os.path.isfile(report_path)
    report_text = open(report_path, 'r').read()
    assert '| **Ligament Band Elements** | **3,365 elements** ($x \\in [0, 50], y \\in [45, 65]$) | 117 elements | 117 elements |' in report_text
    assert '| **Ligament $h \\le l_0$ Count %** | **100.0%** | 0.85% (1 element) | 0.85% (1 element) |' in report_text
    assert '| **Ligament $h \\le l_0$ Area %** | **100.0%** | 0.05% | 0.05% |' in report_text
    assert '129 elements' not in report_text
    assert '63.57%' not in report_text
    assert '38.65%' not in report_text

def test_f1856_figure_generation():
    fig_dir = os.path.join(REPO_ROOT, 'results', 'figures')
    for fig_name in [
        'fig_f1856_lpanel_fracture_mesh.png',
        'fig_f1856_lpanel_fracture_mesh.pdf',
        'fig_f1856_lpanel_elastic_mesh.png',
        'fig_f1856_lpanel_elastic_mesh.pdf',
        'fig_f1856_lpanel_dual_driver_composite.png',
        'fig_f1856_lpanel_dual_driver_composite.pdf'
    ]:
        path = os.path.join(fig_dir, fig_name)
        assert os.path.isfile(path), f"Figure missing: {path}"
        assert os.path.getsize(path) > 10000, f"Figure unexpectedly small: {path}"
