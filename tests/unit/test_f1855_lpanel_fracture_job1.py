"""Unit test suite for F1855 L-Panel fracture Job-1 execution and donor qualification.
Verifies deck construction, solver convergence, damage field initiation and propagation,
donor JSON snapshot integrity, and suitability verdict for damage-envelope remeshing.
"""
import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest().lower()

def test_f1855_deck_construction_and_layering():
    deck_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '284_f1855_lpanel_fracture_job1', 'PK_F1855_LPANEL_COARSE_JOB1.inp')
    assert os.path.isfile(deck_path), f"Deck missing: {deck_path}"

    with open(deck_path, 'r') as f:
        lines = f.readlines()

    # Verify no oversized NSET lines (>16 entries or >80 characters)
    in_nset = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('*NSET') or stripped.startswith('*ELSET'):
            in_nset = True
            continue
        elif stripped.startswith('*'):
            in_nset = False
            continue
        if in_nset and stripped:
            tokens = [t.strip() for t in stripped.split(',') if t.strip()]
            assert len(tokens) <= 16, f"NSET line exceeds 16 tokens: {stripped}"
            assert len(stripped) <= 80, f"NSET line exceeds 80 characters: {stripped}"

    # Verify subroutine hashes
    uel_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', 'f42_mixed_uel.for')
    interface_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '284_f1855_lpanel_fracture_job1', 'f42_native_miseseri_interface_v1.for')
    assert compute_sha256(uel_path) == "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
    assert compute_sha256(interface_path) == "e5c98b6f601b1cd586571f8e24f357d15abbd1c5d5487b52903ba249734279b2"

def test_f1855_donor_snapshot_integrity():
    snapshot_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '284_f1855_lpanel_fracture_job1', 'lpanel_coarse_final_snapshot.json')
    assert os.path.isfile(snapshot_path), f"Snapshot missing: {snapshot_path}"

    with open(snapshot_path, 'r') as f:
        data = json.load(f)

    assert data['schema'] == 'F1855_LPANEL_DONOR_SNAPSHOT_V1'
    assert data['task_id'] == 'F1855-LPANEL-FRACTURE-JOB1'
    assert data['job_id'] == '1424382.mmaster02'
    assert data['total_frames'] == 255
    assert data['step_frame_counts'] == {'Step-1': 51, 'Step-2': 204}

    # Mesh topology
    mf = data['mesh_fields']
    assert len(mf['nodes']) == 375
    assert len(mf['companion_elements']) == 340
    assert len(mf['physical_elements']) == 340
    assert mf['companion_to_physical_offset'] == 680

    # Required fields
    fields = mf['fields']
    for req_field in ['EVOL', 'MISESAVG', 'MISESERI', 'SDV1_MAX', 'SDV1_IPS', 'S_MEAN']:
        assert req_field in fields, f"Missing field in snapshot: {req_field}"
        assert len(fields[req_field]) == 340, f"Field {req_field} does not have 340 elements"

def test_f1855_physical_donor_state_and_damage_suitability():
    summary_path = os.path.join(REPO_ROOT, 'results', 'validation', 'f1855_lpanel_fracture_job1_summary.json')
    assert os.path.isfile(summary_path), f"Summary missing: {summary_path}"

    with open(summary_path, 'r') as f:
        summary = json.load(f)

    # Solver completion & Cutback termination
    term = summary['terminal_state']
    assert term['step1_status'] == 'COMPLETED_FULL'
    assert term['step2_status'] == 'TERMINATED_CONVERGENCE_CUTBACK'
    assert abs(term['step1_achieved_u2_mm'] - 0.10) < 1e-4
    assert term['step2_achieved_u2_mm'] > 0.139
    assert term['total_frames'] == 255

    # Structural reaction force & softening
    resp = summary['structural_response']
    assert resp['peak_reaction_force_kn'] > 12.0
    assert resp['peak_reaction_force_kn'] < 12.1
    assert resp['load_softening_demonstrated'] is True
    assert resp['load_drop_percent'] > 3.0

    # Damage initiation and propagation
    pstate = summary['physical_donor_state']
    max_d = pstate['max_sdv1_damage']
    assert max_d >= 0.5, f"Damage {max_d} did not reach 0.5 threshold!"
    assert abs(max_d - 0.6772) < 0.005

    # Peak damage location at re-entrant corner
    assert pstate['max_sdv1_physical_element'] == 93
    assert pstate['max_sdv1_companion_element'] == 773
    cx, cy = pstate['max_sdv1_centroid']
    dist = pstate['distance_to_reentrant_corner_mm']
    assert dist < 4.0, f"Peak damage element is too far from corner: {dist} mm"
    assert pstate['reentrant_corner_coords'] == [50.0, 50.0]

    # Connected crack path across ligament
    assert pstate['damage_forming_connected_path_from_corner'] is True
    assert pstate['damage_ge_0_4_elements_count'] >= 4

    # Native error fields present and nonzero
    native = summary['native_error_fields']
    assert native['miseseri_present'] is True
    assert native['miseseri_nonzero'] is True
    assert native['evol_present'] is True

    # Suitability verdict
    verdict = summary['donor_suitability_verdict']
    assert verdict['max_damage_ge_0_5'] is True
    assert verdict['selected_sizing_driver'] == 'CONSTRUCTED_DAMAGE_ENVELOPE'
    assert verdict['suitable_for_damage_envelope_remesh'] is True

def test_f1855_figure_generation():
    fig_dir = os.path.join(REPO_ROOT, 'results', 'figures')
    for fig_name in [
        'fig_f1855_lpanel_damage_contour.png',
        'fig_f1855_lpanel_damage_contour.pdf',
        'fig_f1855_lpanel_load_displacement.png',
        'fig_f1855_lpanel_load_displacement.pdf',
        'fig_f1855_lpanel_fracture_job1_synthesis.png',
        'fig_f1855_lpanel_fracture_job1_synthesis.pdf'
    ]:
        path = os.path.join(fig_dir, fig_name)
        assert os.path.isfile(path), f"Figure missing: {path}"
        assert os.path.getsize(path) > 10000, f"Figure unexpectedly small: {path}"
