"""Build a bounded, immutable replacement review packet; never run a solver."""
import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/validation/f1599_reconciled'
REMOTE = '/scratch9/pr21vyci/runs/mode1_c6_package171_r1_c3_0_reequilibration/'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def put(name, value):
    p = OUT / name
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return p


def remote(command):
    result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                             str(ROOT / '.agents/scripts/Invoke-GuardedSsh.ps1'),
                             '-RemoteCommand', command], capture_output=True, check=True, timeout=140)
    return result.stdout


def main():
    OUT.mkdir(exist_ok=True)
    acquisitions = []
    for rel, name in [('equilibration_1419643.mmaster02/live_iteration_telemetry.json', 'terminal_iterations.json'),
                      ('pbs_execution.log', 'terminal_execution.txt')]:
        path = REMOTE + rel
        digest = remote('sha256sum ' + path).decode().split()[0].upper()
        data = remote('cat ' + path)
        # PowerShell may transport text with Windows newlines. Accept only bytes
        # whose SHA256 exactly matches the remote original, including final LF.
        candidates = [data, data.replace(b'\r\n', b'\n')]
        candidates += [b.rstrip(b'\r\n') for b in candidates]
        exact = next((b for b in candidates if hashlib.sha256(b).hexdigest().upper() == digest), None)
        if exact is None:
            raise ValueError('REMOTE_BYTE_HASH_MISMATCH: ' + path)
        dest = OUT / name
        dest.write_bytes(exact)
        acquisitions.append(dict(remote=path, local=str(dest.relative_to(ROOT)).replace('\\', '/'), sha256=digest))
    scheduler = remote('qstat -xf 1419643.mmaster02').decode('utf-8').replace('\r\n', '\n')
    # Preserve only scheduler identity, resources and terminal status, excluding environment.
    fields = re.findall(r'^\s*(Job Id:.*|(?:Job_Name|job_state|Exit_status|resources_used\.[a-z_]+|stime|obittime)\s*=.*)$', scheduler, re.M)
    put('scheduler_terminal.json', dict(job_id='1419643.mmaster02', command='qstat -xf 1419643.mmaster02', fields=fields))
    old_req = next((ROOT / 'project_coordination/review_dispatch').glob('*package171*23EAA*.request.json'))
    old_response = Path.home() / 'OpenClawPAD/ChatGPTBridge/archive/response_20261103_084525_HND-d0a07103a3ba42f1a3db175a2cc77b78.json'
    req = json.loads(old_req.read_text(encoding='utf-8-sig'))
    raw = json.loads(old_response.read_text(encoding='utf-8-sig'))['response']
    decision = json.loads(raw[raw.index('{'):raw.rindex('}') + 1])
    actual = decision['reviewed_hashes']
    mismatches = {k: dict(request=v, response=actual.get(k)) for k, v in req['hashes'].items() if actual.get(k) != v}
    put('original_review_hash_audit.json', dict(request_sha256=sha(old_req), response_sha256=sha(old_response),
        correlation_id=req['correlation_id'], fingerprint=req['fingerprint'], mismatches=mismatches,
        extra_keys=sorted(set(actual) - set(req['hashes'])), attestation='FAILED_EXACT_HASH_BINDING',
        archived_response_decision=decision['decision'], originals_modified=False))
    donor_rel = 'models/pandey_kumar_mode1/167_c5_package167_r3_c2_2_continuation/evidence/1419566.mmaster02/c5_forward_continuation_c2_2_summary.json'
    donor = json.loads((ROOT / donor_rel).read_text())
    pkg_rel = 'models/pandey_kumar_mode1/171_c6_package171_r1_c3_0_reequilibration/PACKAGE_MANIFEST.json'
    pkg = json.loads((ROOT / pkg_rel).read_text())
    driver_rel = 'scripts/state_transfer/driver_package171_c6_coupled_pdas.py'
    driver = (ROOT / driver_rel).read_text()
    constants = dict(re.findall(r'^(DONOR_REFERENCE_[A-Z_]+)\s*=\s*([0-9.eE+-]+)', driver, re.M))
    iterations = json.loads((OUT / 'terminal_iterations.json').read_text())
    if not isinstance(iterations, list) or len(iterations) != 100:
        raise ValueError('EXPECTED_100_ORIGINAL_ITERATIONS')
    old_definition = json.loads((ROOT / 'project_coordination/candidate_definitions/evaluate_mode1_package171_r1_c6_coupled_convergence.json').read_text())
    old_gates = old_definition['mathematical_formulation']['physical_continuity_gates']
    refs = dict(donor_force_kN=donor['reaction_force_kN'], donor_total_energy_kNmm=donor['total_energy_kNmm'])
    assert pkg['donor_source']['reference_force_kN'] == refs['donor_force_kN']
    assert pkg['donor_source']['reference_total_energy_kNmm'] == refs['donor_total_energy_kNmm']
    put('reference_and_convergence_audit.json', dict(authoritative_references=refs,
        donor_summary=donor_rel, package_manifest=pkg_rel, driver_constants=constants,
        obsolete_definition_references=old_gates,
        obsolete_force_reference_error_pct=100*abs(old_gates['donor_reference_force_kN'] / refs['donor_force_kN']-1),
        obsolete_energy_reference_error_pct=100*abs(old_gates['donor_reference_total_energy_kNmm'] / refs['donor_total_energy_kNmm']-1),
        history_change_gate=dict(required=1e-4, enforced_in_original_driver=False,
                                evaluation_rule='Independent postprocessing requires delta_h <= 1e-4; never infer from driver success'),
        terminal_record=iterations[-1], iterations=len(iterations), physical_acceptance='FAIL_COUPLED_NONCONVERGENCE',
        driver_changed=False, numerical_experiment_proposed=False))
    # Explicit R1 versus immediate original Package171 parent, not a hypothetical R2.
    parent = subprocess.check_output(['git', 'show', 'HEAD:scripts/state_transfer/driver_package171_c6_coupled_pdas.py'], cwd=ROOT).decode('utf-8')
    diff = ''.join(difflib.unified_diff(parent.splitlines(True), driver.splitlines(True),
                                      fromfile='HEAD/driver_package171_c6_coupled_pdas.py', tofile=driver_rel))
    (OUT / 'driver_worktree_diff.txt').write_text(diff or 'No working-tree source changes relative to HEAD.\n', encoding='utf-8')
    put('acquisition.json', dict(files=acquisitions, mode='READ_ONLY', new_pbs_submissions=0))
    parent_manifest_rel = 'models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/EXECUTION_MANIFEST.json'
    child_manifest_rel = 'models/pandey_kumar_mode1/171_c6_package171_r1_c3_0_reequilibration/EXECUTION_MANIFEST.json'
    pm = json.loads((ROOT / parent_manifest_rel).read_text())
    cm = json.loads((ROOT / child_manifest_rel).read_text())
    (OUT / 'package171_to_r1_manifest.diff.txt').write_text(''.join(difflib.unified_diff(
        json.dumps(pm, indent=2, sort_keys=True).splitlines(True),
        json.dumps(cm, indent=2, sort_keys=True).splitlines(True),
        fromfile=parent_manifest_rel, tofile=child_manifest_rel)), encoding='utf-8')
    assert pm['runtime_source_hashes'][driver_rel] == cm['runtime_source_hashes'][driver_rel] == sha(ROOT / driver_rel)
    put('parent_source_audit.json', dict(parent=parent_manifest_rel, revision=child_manifest_rel,
        driver_sha256=sha(ROOT / driver_rel), driver_changed=False,
        added_runtime_sources={k:v for k,v in cm['runtime_source_hashes'].items() if k not in pm['runtime_source_hashes']},
        changed_runtime_sources={k:dict(parent=v,revision=cm['runtime_source_hashes'].get(k))
            for k,v in pm['runtime_source_hashes'].items() if cm['runtime_source_hashes'].get(k) != v},
        actual_coupled_checks=['delta_d <= 1e-5', 'delta_u <= 1e-9', 'kkt passed'],
        required_independent_checks=['delta_h <= 1e-4 MPa', 'irreversibility', 'history monotonicity', 'force and energy continuity <=2%'],
        independent_convergence_pass=all(iterations[-1][k] <= t for k,t in
            [('delta_d',1e-5),('delta_u',1e-9),('delta_h',1e-4),('dual_error',1e-6),('free_error',1e-6)])))
    sources = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in OUT.iterdir() if p.is_file() and p.name != 'review_packet.json'}
    for rel in [donor_rel, pkg_rel, driver_rel, parent_manifest_rel, child_manifest_rel]:
        sources[rel] = sha(ROOT / rel)
    packet_path = put('review_packet.json', dict(schema=1, purpose='Reconciled read-only F1599 evidence review',
        original_fingerprint=req['fingerprint'], original_response_attested=False,
        scope='Review evidence and diagnose failed C6; no solver, registration, R2, or acceptance authority',
        references=refs, acceptance_criteria=old_definition['acceptance_criteria'],
        terminal_iteration=iterations[-1], evidence_sources=sources))
    sources[str(packet_path.relative_to(ROOT)).replace('\\', '/')] = sha(packet_path)
    definition = dict(schema=1, operation_id='evaluate_mode1_package171_r1_c6_reconciled_evidence',
        task_id='F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE', author='codex',
        registration_status='PROPOSED_FOR_INDEPENDENT_REVIEW', operation_mode='READ_ONLY_SCIENTIFIC_EVALUATION',
        scientific_hypothesis='Terminal C6 failed coupled convergence despite KKT compliance; original references and history gate require explicit reconciliation.',
        source_differences='See package171_to_r1_manifest.diff.txt and parent_source_audit.json: original/R1 coupled driver hashes identical, runtime closure added mapping dependency. No executable changes in this review revision. Review-only successor replaces iteration23 telemetry, corrects donor references, and independently checks delta_h. Original package remains frozen.',
        evidence_sources=sources, acceptance_criteria=old_definition['acceptance_criteria'])
    path = ROOT / 'project_coordination/candidate_definitions' / (definition['operation_id'] + '.json')
    path.write_text(json.dumps(definition, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(candidate=str(path), terminal=iterations[-1], hash_mismatches=mismatches, references=refs), indent=2))


if __name__ == '__main__':
    main()
