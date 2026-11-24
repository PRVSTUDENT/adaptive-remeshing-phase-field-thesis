"""Recovery checks against the frozen UEL interface, rather than string presence."""
import importlib.util
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE = ROOT / 'models/pandey_kumar_mode2/294_method_c_mode2/mode2_single_job_orchestrator.py'
sys.path.insert(0, str(MODULE.parent))
spec = importlib.util.spec_from_file_location('mode2_recovery', MODULE)
mode2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mode2)


def test_initial_state_contains_18_values_per_element(tmp_path):
    deck = tmp_path / 'transfer.inp'
    mode2.assemble_mode2_coupled_deck(
        str(deck), {1: (0, 0), 2: (1, 0), 3: (1, 1), 4: (0, 1)},
        {1: [1, 2, 3, 4]}, {}, .0095, .011,
        {n: .25 for n in range(1, 5)}, {(1, gp): gp * .001 for gp in range(1, 5)})
    text = deck.read_text()
    block = text.split('*INITIAL CONDITIONS, TYPE=SOLUTION\n')[1].split('*')[0]
    rows = [line.strip() for line in block.splitlines() if line.strip() and not line.startswith('**')]
    tokens = [float(v) for row in rows for v in row.split(',') if v.strip()]
    # Exactly one element label followed by 18 state variables. Continuations
    # must not repeat the element label or accidentally introduce another card.
    assert len(tokens) == 19
    assert tokens[0] == 1
    assert tokens[9:13] == [.001, .002, .003, .004]
    assert tokens[17:19] == [0., 0.]
    assert '*AMPLITUDE, NAME=CONST_HOLD' in text
    assert '*BOUNDARY, AMPLITUDE=CONST_HOLD' in text
    assert '*DEPVAR\n20\n' in text


def test_cli_cannot_silently_succeed_without_running():
    result = subprocess.run([sys.executable, str(MODULE)], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert result.returncode != 0
    assert 'execution loop' in result.stderr.lower()


def test_dry_run_reports_missing_execution_and_gates():
    result = subprocess.run([sys.executable, str(MODULE), '--dry-run'], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert result.returncode == 0
    import json
    report = json.loads(result.stdout)
    assert report['execution_qualified'] is False
    assert report['frozen_uel_match'] is True
    assert report['blockers']


def test_connected_tip_follows_downward_growth_and_ignores_island():
    from mode2_runtime import connected_tip, completion
    nodes={1:(.5,.5),2:(.51,.48),3:(.55,.2),4:(.56,0),5:(1.,.9)}
    damage={n:1. for n in nodes}
    tip,boundary=connected_tip(nodes,{1:[1,2,3],2:[2,3,4]},damage)
    assert tip==(.56,0)
    assert boundary
    assert completion(1.,.9,boundary)[0]
    # An isolated high-damage boundary point cannot confer completion.
    assert not connected_tip(nodes,{1:[1,2,3]},damage)[1]


def test_geometry_audit_rejects_inverted_element():
    from mode2_runtime import geometry_audit
    nodes={1:(0,0),2:(1,0),3:(1,1),4:(0,1)}
    assert geometry_audit(nodes,{1:[1,2,3,4]})['positive_jacobians_pass']
    assert not geometry_audit(nodes,{1:[4,3,2,1]})['positive_jacobians_pass']


def test_legacy_material_order_is_rejected(tmp_path):
    import pytest
    from mode2_runtime import validate_uel_properties
    deck=tmp_path/'legacy.inp'
    deck.write_text('*UEL PROPERTY, ELSET=PHASE\n210., .3, .0027, .015, 1e-7, 2960.\n')
    with pytest.raises(ValueError,match='frozen source order'):
        validate_uel_properties(deck,2960)
    deck.write_text('*UEL PROPERTY, ELSET=PHASE\n.015, .0027, 210., .3, 1e-7, 2960.\n')
    validate_uel_properties(deck,2960)


def test_committed_coarse_deck_matches_actual_frozen_material_interface():
    from mode2_runtime import validate_uel_properties
    validate_uel_properties(MODULE.parent/'PK_METHOD_C_MODE2_COARSE_JOB1.inp',2960)


def test_empty_existing_sta_cannot_evade_two_hour_stall_guard(tmp_path):
    from stall_watchdog import StallWatchdog
    watchdog=StallWatchdog()
    watchdog.start_cycle()
    sta=tmp_path/'empty.sta'
    sta.write_text('SUMMARY OF JOB INFORMATION\n')
    assert watchdog.check_simulation_stall(sta,current_time=watchdog.last_increment_time+7200)[0]


def test_resume_rejects_mismatched_donor_before_any_solver_command(tmp_path):
    import json
    import pytest
    from mode2_runtime import LocalRunner
    donor_mesh=tmp_path/'donor.inp'
    donor_mesh.write_text('modified mesh')
    checkpoint=tmp_path/'checkpoint.json'
    checkpoint.write_text(json.dumps({'summary':{
        'source_sha256':mode2.FROZEN_UEL_SHA256,'status':'CONVERGED_AUDITED',
        'mesh_sha256':'0'*64},'mesh_path':str(donor_mesh),'odb_path':str(tmp_path/'donor.odb')}))
    runner=LocalRunner(mode2,tmp_path/'resume',donor_checkpoint=checkpoint)
    def forbidden(*args,**kwargs):
        pytest.fail('Solver/preparation command must not run with a corrupted donor')
    runner.command=forbidden
    with pytest.raises(RuntimeError,match='Donor evidence, hash or convergence mismatch'):
        runner.execute()
