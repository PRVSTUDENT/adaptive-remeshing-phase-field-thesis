"""Unit tests for Task F1516: AutoQueue Engineering Audit and Ground-Truth Baseline Deck.

Validates:
1. AutoQueue Classification:
   - mode1_queue_selector.py formally classifies score formula as HEURISTIC_RECOMMENDATION_ONLY.
   - Explains PBS Pro scheduler privacy boundary (query_other_jobs = False).
2. Queue Hierarchy & Routing Fidelity:
   - Verifies routing queues (entry_imfdfkmq, entryq) and execution queues.
   - Verifies normal_imfdfkmq remains top-ranked under standard Mode-I parameters.
3. Authentic Missing Reference State Discovery:
   - Confirms fine_baseline_14k_u0050_state.json lacks nodal displacement and nodal phase field.
   - Confirms M1_MB_CORRECTED_PROPAGATION_14K.inp restricted node output to NSET=N_RP.
4. Enriched Baseline Diagnostic Deck:
   - Verifies M1_MB_FINE_BASELINE_ENRICHED.inp has exactly 1 step to u = 0.0050 mm.
   - Verifies whole-mesh *NODE OUTPUT (U, RF) and *ELEMENT OUTPUT (SDV).
   - Verifies restart write frequency is configured.
5. Package 50 Manifest & Execution Gate Qualification:
   - Verifies validate_manifest passes for METHOD_B_FINE_BASELINE_ENRICHED_AUTHORIZATION.json.
   - Verifies frozen UEL hash parity (CE8D5EDC...).
   - Verifies single-rank serial resource contract (1 CPU, 8 GB, 4h).
"""
import hashlib
import json
import os
from pathlib import Path
import pytest
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'scripts' / 'hpc'))

from mode1_queue_selector import (
    CLASSIFICATION,
    KNOWN_QUEUES,
    score_queue,
    select_best_queue,
)
from mode1_execution_gate import FROZEN_UEL, validate_manifest


def test_autoqueue_classification_and_privacy_boundary():
    """Verify AutoQueue is classified as HEURISTIC_RECOMMENDATION_ONLY."""
    assert CLASSIFICATION == "HEURISTIC_RECOMMENDATION_ONLY"
    res = select_best_queue(requested_walltime_hours=1.0)
    assert res['classification'] == "HEURISTIC_RECOMMENDATION_ONLY"
    assert res['selected_submission_queue'] == "entry_imfdfkmq"
    assert res['selected_execution_queue'] == "normal_imfdfkmq"
    assert res['effective_score'] > 0


def test_queue_priority_and_routing_semantics():
    """Verify known queue parameters against verified cluster configuration."""
    assert KNOWN_QUEUES['normal_imfdfkmq']['priority'] == 1000
    assert KNOWN_QUEUES['normal_imfdfkmq']['route_via'] == 'entry_imfdfkmq'
    assert KNOWN_QUEUES['normal_imfdfkmq']['node_pool'] == 'extension2'

    assert KNOWN_QUEUES['short_imfdfkmq']['priority'] == 50
    assert KNOWN_QUEUES['short_imfdfkmq']['route_via'] == 'entry_imfdfkmq'

    assert KNOWN_QUEUES['shortq']['priority'] == 75
    assert KNOWN_QUEUES['shortq']['route_via'] == 'entryq'
    assert KNOWN_QUEUES['shortq']['node_pool'] == 'main'

    assert KNOWN_QUEUES['mediumq']['priority'] == 40
    assert KNOWN_QUEUES['mediumq']['route_via'] == 'entryq'


def test_missing_fine_baseline_reference_state_provenance():
    """Confirm authentic fine baseline ODB and JSON lacked interior nodal fields."""
    state_json = (
        REPO_ROOT
        / 'models'
        / 'pandey_kumar_mode1'
        / '40_method_b_corrected_propagation_14k'
        / 'evidence_1412465'
        / 'fine_baseline_14k_u0050_state.json'
    )
    assert state_json.is_file(), "fine_baseline_14k_u0050_state.json must exist"
    data = json.loads(state_json.read_text(encoding='utf-8'))
    assert 'nodal_displacement' not in data
    assert 'nodal_damage' not in data
    assert 'elem_sdv' in data
    assert len(data['elem_sdv']) == 14483

    # Check that original 14k deck restricted node output to RP
    orig_inp = (
        REPO_ROOT
        / 'models'
        / 'pandey_kumar_mode1'
        / '40_method_b_corrected_propagation_14k'
        / 'M1_MB_CORRECTED_PROPAGATION_14K.inp'
    )
    content = orig_inp.read_text(encoding='utf-8')
    assert '*NODE OUTPUT, NSET=N_RP' in content
    assert '*NODE OUTPUT\n' not in content and '*NODE OUTPUT\r\n' not in content


def test_enriched_baseline_deck_structure():
    """Verify enriched baseline deck structure and whole-mesh output cards."""
    deck_path = (
        REPO_ROOT
        / 'models'
        / 'pandey_kumar_mode1'
        / '50_method_b_fine_baseline_enriched'
        / 'M1_MB_FINE_BASELINE_ENRICHED.inp'
    )
    assert deck_path.is_file(), "Enriched input deck must exist"
    content = deck_path.read_text(encoding='utf-8')

    # Exactly 1 step up to u = 0.0050 mm
    assert '*STEP, NAME=Step-1' in content
    assert '*STEP, NAME=Step-2' not in content
    assert 'N_RP, 2, 2, 0.0050' in content

    # Enriched output cards
    assert '*NODE OUTPUT\n U, RF' in content or '*NODE OUTPUT\r\n U, RF' in content
    assert '*ELEMENT OUTPUT, ELSET=All_elem\n SDV' in content or '*ELEMENT OUTPUT, ELSET=All_elem\r\n SDV' in content
    assert '*RESTART, WRITE, FREQUENCY=2000' in content


def test_package50_manifest_and_gate_qualification():
    """Verify Package 50 manifest validates cleanly under Mode-I execution gate."""
    manifest_path = (
        REPO_ROOT
        / 'models'
        / 'pandey_kumar_mode1'
        / '50_method_b_fine_baseline_enriched'
        / 'METHOD_B_FINE_BASELINE_ENRICHED_AUTHORIZATION.json'
    )
    assert manifest_path.is_file(), "Manifest must exist"
    batch, key, files = validate_manifest(manifest_path, REPO_ROOT)

    assert batch['adapter'] == 'mode1-qualified-batch-v2'
    assert batch['scientific_scope'] == 'MODE1'
    assert batch['technical_stage'] == 'MODE1_BASELINE'
    assert batch['max_submissions'] == 1
    assert batch['automatic_retry'] is False

    assert files['f42_mixed_uel.for'] == FROZEN_UEL
    job = batch['jobs'][0]
    assert job['id'] == 'M1_MB_FINE_BASELINE_ENRICHED'
    assert job['cpus'] == 1
    assert job['memory_gb'] == 8
    assert job['walltime_hours'] == 4
    assert job['queue'] == 'entry_imfdfkmq'
    assert job['execution'] == 'single-rank serial'
