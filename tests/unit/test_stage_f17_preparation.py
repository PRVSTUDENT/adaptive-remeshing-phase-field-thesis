from pathlib import Path
import ast, hashlib, importlib.util, json

ROOT=Path(__file__).resolve().parents[2]
PROBE=ROOT/'models/generated/mode_ii/f17_penalty_activation_probe'
REGION=ROOT/'models/generated/mode_ii/f17_native_adaptive_region_repair'

def test_probe_contract():
    deck=(PROBE/'runtime/M2IRRPENACT1.inp').read_text()
    source=(PROBE/'runtime/M2IRRPENACT1.for').read_text()
    pbs=(PROBE/'M2IRRPENACT1.pbs').read_text()
    assert '1.0, 0.003, 1.5, 0.001, 2.0, 0.006' in deck
    assert 'PNEWDT=HALF' not in source
    assert 'penalty_energy' in (ROOT/'scripts/validation/analyze_stage_f17_penalty_probe.py').read_text()
    for name in ('response_curve.csv','phase_history.csv','energy_history.csv','accepted_increments.csv'):
        assert name in pbs
    assert 'notification_install_terminal_trap' in pbs and 'notify_start' in pbs
    assert '#PBS -m abe' in pbs and '#PBS -q entry_imfdfkmq' in pbs
    assert '.odb' not in (PROBE/'SHA256SUMS').read_text().lower()

def test_region_python_and_zero_execution_contract():
    script=(REGION/'runtime/qualify_f17_adaptive_region.py').read_text()
    ast.parse(script)
    assert not any(isinstance(node, (ast.GeneratorExp, ast.SetComp, ast.DictComp)) for node in ast.walk(ast.parse(script)))
    assert 'native_remesh_calls":0' in script
    assert 'generated_candidates":0' in script
    assert 'a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2' in script
    assert hashlib.sha256((REGION/'runtime/source_deck.inp').read_bytes()).hexdigest()=='a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2'
    pbs=(REGION/'M2RMREG4.pbs').read_text()
    assert 'notification_install_terminal_trap' in pbs and 'notify_start' in pbs

def test_manifests_are_not_authorized():
    for package in (PROBE,REGION):
        data=json.loads((package/'PACKAGE_MANIFEST.json').read_text())
        assert data['queue']=='entry_imfdfkmq'
        assert data['telegram_mandatory'] is True
        assert data['pbs_email']=='best_effort'
        assert data['execution_authorized'] is False
        assert data['submission_approved'] is False

def test_penalty_activation_gate():
    path=ROOT/'scripts/validation/analyze_stage_f17_penalty_probe.py'
    spec=importlib.util.spec_from_file_location('f17_analyzer',str(path)); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    base={'committed_phase':0.9,'trial_phase':0.8,'tolerance':1e-8,'penalty_residual':1.0,'penalty_energy':0.1,'penalty_tangent':2.0,'bounds_guard':False}
    assert module.classify([base],True)[0]=='penalty_activation_probe_passed'
    growth=dict(base); growth['trial_phase']=0.95
    assert module.classify([growth],True)[0]=='penalty_activation_not_observed'
    assert module.classify([base],False)[0]=='penalty_activation_evidence_incomplete'

def test_frozen_hash_manifests():
    for package in (PROBE,REGION):
        for line in (package/'F17_SHA256SUMS').read_text().splitlines():
            digest,relative=line.split('  ',1)
            assert hashlib.sha256((package/relative).read_bytes()).hexdigest()==digest

def test_region_pbs_has_exact_final_lf_repair():
    payload=(REGION/'M2RMREG4.pbs').read_bytes()
    assert len(payload)==1167
    assert payload[-1:]==b'\n'
    assert payload[-2:-1]!=b'\n'
    assert hashlib.sha256(payload).hexdigest()=='6375b8c5b739133046c8c402e9155a247ba1cb0512c305bffb22560de1a31cdf'

if __name__=='__main__':
    test_probe_contract()
    test_region_python_and_zero_execution_contract()
    test_manifests_are_not_authorized()
    test_penalty_activation_gate()
    test_frozen_hash_manifests()
    test_region_pbs_has_exact_final_lf_repair()
    print('6 static tests passed')
