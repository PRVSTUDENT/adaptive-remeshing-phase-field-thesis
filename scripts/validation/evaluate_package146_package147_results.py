"""Read-only authenticated Mode-I result reader; never registers/submits jobs.

Accepted-increment UEL CSV energies are checked against SDV17/18, counting each
element total once, not once per repeated IP. DAT U3 is nodal phase; 2D ODB U
stores only U1/U2. Recorded UMAT SDV2 trial history is not committed restart state.
"""
import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess

OPERATION = 'evaluate_mode1_package146_donor_and_package147_reference'
FROZEN_UEL_SHA256 = 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6'
P146_INP_SHA256 = '9f93419a4f1e090286007a7291693bd3b783d984ce276e102d22d404ad4c5475'
P147_INP_SHA256 = 'fffe51d5348f6e4b5e9b4742d783ca1645b480b229189168493aeda10c91722a'
TARGET_DISPLACEMENT = 0.0018003125442191958
RF2_GATE_THRESHOLD, ENERGY_GATE_THRESHOLD = 0.05, 0.02
DAMAGE_TOLERANCE = 1e-6  # Retained existing tolerance, not a relaxed gate.
PACKAGES = {
    146: dict(job='1418753.mmaster02', scheduler_name='M1_C3_P146_DON', name='M1_C3_FINE_PACKAGE146_DONOR',
              directory='146_c3_fine_donor', remote='/scratch9/pr21vyci/runs/mode1_c3_fine_package146_donor', inp_sha=P146_INP_SHA256),
    147: dict(job='1418768.mmaster02', scheduler_name='M1_C4_P147_REF', name='M1_C4_CORRECTED_PACKAGE147_REF',
              directory='147_c4_corrected_reference', remote='/scratch9/pr21vyci/runs/mode1_c4_corrected_package147_ref', inp_sha=P147_INP_SHA256)}


class EvidenceError(ValueError):
    status = 'INVALID_EVIDENCE'


class Unavailable(EvidenceError):
    status = 'UNAVAILABLE'


class PhysicalFailure(EvidenceError):
    status = 'PHYSICAL_FAILURE'


def require(condition, reason):
    if not condition:
        raise EvidenceError(reason)


def finite(value):
    require(not isinstance(value, bool), 'Boolean is not a numerical measurement')
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError):
        raise EvidenceError('Malformed numerical measurement')
    require(math.isfinite(number), 'Nonfinite measurement')
    return number


def compute_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def evaluate_convergence_and_displacement(step1_disp, exit_status):
    disp, code = finite(step1_disp), finite(exit_status)
    return code == 0 and abs(disp-TARGET_DISPLACEMENT) <= 1e-8, 'Exact Step-1 endpoint required'


def comparison(donor, reference, threshold):
    a, b = finite(donor), finite(reference)
    require(a != 0, 'Zero donor denominator')
    delta = finite((b-a)/a); finite(100*delta)
    return abs(delta) <= threshold, abs(delta), 'Signed difference percent = %.12g' % (100*delta)


def evaluate_reaction_force_continuity(donor, reference):
    return comparison(donor, reference, RF2_GATE_THRESHOLD)


def evaluate_energy_continuity(donor, reference):
    return comparison(donor, reference, ENERGY_GATE_THRESHOLD)


def verify_damage_admissibility(d_values, delta_d_values):
    require(bool(d_values) and len(d_values) == len(delta_d_values), 'Empty or mismatched damage arrays')
    damage, increments = [finite(x) for x in d_values], [finite(x) for x in delta_d_values]
    bounds = sum(d < -DAMAGE_TOLERANCE or d > 1+DAMAGE_TOLERANCE for d in damage)
    healing = sum(d < -DAMAGE_TOLERANCE for d in increments)
    return not(bounds or healing), bounds, healing


def audit_input_provenance(workspace, allow_missing=False):
    for cfg in PACKAGES.values():
        root = Path(workspace)/'models/pandey_kumar_mode1'/cfg['directory']
        for name, digest in [(cfg['name']+'.inp', cfg['inp_sha']), ('f42_mixed_uel.for', FROZEN_UEL_SHA256)]:
            if not (root/name).is_file():
                if allow_missing:
                    continue  # Authenticated remote originals remain mandatory below.
                raise Unavailable('Missing local source '+name)
            require(compute_file_sha256(root/name) == digest, 'Local frozen model hash mismatch: '+name)
    return True


def model_maps(text):
    nodes, visual, phase, kind = set(), {}, {}, None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            upper = line.upper().replace(' ', '')
            kind = 'node' if upper == '*NODE' else None
            if upper.startswith('*ELEMENT,'):
                kind = 'visual' if 'TYPE=CPE4' in upper else ('phase' if 'TYPE=U1,' in upper else None)
            continue
        parts = line.split(',')
        if kind == 'node':
            node = int(parts[0]); require(node not in nodes, 'Duplicate input node'); nodes.add(node)
        elif kind in ('visual', 'phase'):
            table = visual if kind == 'visual' else phase
            elem = int(parts[0]); require(elem not in table and len(parts) == 5, 'Invalid quad mapping')
            table[elem] = tuple(int(x) for x in parts[1:])
    require(999999 in nodes and visual and phase, 'Missing model maps')
    nodes.remove(999999)
    require({n for c in phase.values() for n in c} == nodes, 'Phase-node coverage mismatch')
    require(set(visual.values()) == set(phase.values()), 'Companion UMAT mesh mismatch')
    return nodes, visual


def parse_dat_endpoint(text, expected_nodes, increment):
    step, inc, active, records, tables = None, None, False, {}, []
    for line in text.splitlines():
        match = re.match(r'STEP(\d+)STATICANALYSIS', re.sub(r'\s+', '', line))
        if match:
            step = int(match[1])
        match = re.search(r'INCREMENT\s+(\d+)\s+SUMMARY', line)
        if match:
            inc = int(match[1])
        if 'NODE FOOT-' in line and 'U3' in line and 'RF2' in line:
            active = step == 1 and inc == increment
            columns = [line.index(name)-4 for name in ('U1', 'U2', 'U3', 'RF1', 'RF2', 'RF3')]
            if active:
                records = {}; tables.append(records)
            continue
        if active:
            parts = line.split()
            if parts and parts[0].isdigit():
                node = int(parts[0]); require(node not in records, 'Duplicate DAT node')
                cells = [line[start:start+15].strip() for start in columns]
                # Abaqus leaves inactive RP DOFs blank. Preserve absence, never
                # synthesize zero displacement/reaction in unrecorded columns.
                required = (1, 4) if node == 999999 else range(6)
                require(all(cells[i] for i in required), 'Truncated/malformed DAT node row')
                records[node] = [finite(x.replace('D', 'E')) if x else None for x in cells]
            elif records and line.strip():
                active = False
    require(len(tables) == 1, 'Incorrect/missing/duplicate Step-1 DAT frame')
    require(set(records) == set(expected_nodes)|{999999}, 'Incomplete or incorrect DAT node mapping')
    return records


def parse_energy(text):
    rows = {}
    for row in csv.DictReader(io.StringIO(text), skipinitialspace=True):
        try:
            values = {k: finite(v) for k, v in row.items()}
            step, inc = values['Step'], values['Increment']
            require(step.is_integer() and inc.is_integer(), 'Noninteger energy frame')
            key = (int(step), int(inc)); require(key not in rows, 'Duplicate accepted energy increment')
            e, f, t = (values[k] for k in ('E_elastic_kNmm', 'E_fracture_kNmm', 'E_total_kNmm'))
            require(min(e, f, t) >= 0 and math.isclose(e+f, t, rel_tol=2e-7, abs_tol=1e-14), 'Inconsistent UEL energy totals')
            rows[key] = values
        except (KeyError, AttributeError, TypeError) as exc:
            raise EvidenceError('Malformed/truncated UEL energy CSV') from exc
    require(bool(rows), 'Empty energy CSV')
    return rows


def pbs_identity(text, cfg):
    text = re.sub(r'\r?\n\t', '', text)
    require(re.search(r'^Job Id:\s*'+re.escape(cfg['job'])+r'\s*$', text, re.M), 'Wrong PBS job identity')
    require(re.search(r'Job_Name\s*=\s*'+re.escape(cfg['scheduler_name'])+r'\s*$', text, re.M), 'Wrong PBS job name')
    require('Job_Owner = pr21vyci@' in text and cfg['remote'] in text, 'Wrong PBS owner/output path')
    state = re.search(r'job_state\s*=\s*(\w+)', text); require(state is not None, 'Missing PBS state')
    if state[1] in ('Q', 'R', 'H', 'E', 'W'):
        raise Unavailable('Existing job not terminal: '+state[1])
    require(state[1] == 'F', 'Unrecognized terminal state')
    code = re.search(r'Exit_status\s*=\s*(-?\d+)', text); require(code is not None, 'Missing terminal exit status')
    if int(code[1]) != 0:
        raise PhysicalFailure('Existing solver job exited '+code[1])


def validate_snapshot(snapshot, nodes, visual, dat, energy, sta):
    require(snapshot['schema'] == 1 and snapshot['step'] == 'Step-1' and snapshot['step_number'] == 1, 'Wrong ODB step identity')
    frames = snapshot['frames']; require(len(frames) > 1, 'Missing accepted ODB frames')
    require(all(type(f['frame_index']) is int and type(f['increment']) is int for f in frames), 'Noninteger frame identity')
    last = frames[-1]; increment = last['increment']
    require([f['frame_index'] for f in frames] == list(range(len(frames))), 'Truncated/reordered ODB frame indices')
    require([f['increment'] for f in frames] == list(range(increment+1)), 'Incomplete accepted ODB increments')
    accepted = set()
    for line in sta.splitlines():
        parts = line.split()
        if len(parts) >= 9 and parts[0] == '1' and parts[1].isdigit() and parts[2].isdigit():
            accepted.add(int(parts[1]))
    require(accepted == set(range(1, increment+1)), 'STA/ODB convergence increment mismatch')
    require({inc for step, inc in energy if step == 1} == accepted, 'Energy accepted-frame coverage mismatch')
    for frame in frames:
        time = finite(frame['step_time']); finite(frame['rp']['u2']); finite(frame['rp']['rf2'])
        if frame['increment']:
            require(abs(time-energy[1, frame['increment']]['StepTime']) < 5e-8, 'Energy/ODB frame time mismatch')
    require(abs(finite(last['step_time'])-0.36006251) < 5e-8, 'Step-1 endpoint time not reached')
    require(evaluate_convergence_and_displacement(last['rp']['u2'], 0)[0], 'Incorrect Step-1 endpoint displacement')
    # DAT prints eight significant digits; ODB RF is float32. This is a
    # representation cross-check tolerance, not the 5% scientific RF gate.
    require(abs(dat[999999][1]-last['rp']['u2']) < 1e-9 and
            math.isclose(dat[999999][4], last['rp']['rf2'], rel_tol=2e-7, abs_tol=1e-10), 'DAT/ODB reaction or displacement mismatch')
    odb_nodes, instances = {}, set()
    for row in snapshot['nodes']:
        require(len(row) in (3, 4), 'Incorrect nodal vector dimension')
        instance, node = row[0].rsplit(':', 1); instances.add(instance); node = int(node)
        require(node not in odb_nodes, 'Duplicate ODB node'); odb_nodes[node] = [finite(v) for v in row[1:]]
    require(len(instances) == 1 and set(odb_nodes) == nodes, 'Incorrect ODB node mapping')
    for node in nodes:
        require(all(abs(odb_nodes[node][i]-dat[node][i]) < 1e-9 for i in (0, 1)), 'DAT/ODB node mapping/values disagree')
    instance = next(iter(instances))
    expected_gp = {instance+':'+str(el)+':'+str(ip) for el in visual for ip in range(1, 5)}
    keys = snapshot['history_keys']
    require(len(keys) == len(expected_gp) and set(keys) == expected_gp, 'Missing or incorrect GP history mapping')
    previous, minimum_delta = None, 0.0
    for frame in frames:
        values = frame['history_values']; require(len(values) == len(keys), 'Truncated GP history frame')
        values = [finite(v) for v in values]; require(min(values) >= -1e-12, 'Negative history')
        if previous is not None:
            minimum_delta = min(minimum_delta, min(v-p for v, p in zip(values, previous)))
        previous = values
    totals = {}
    for field in ('SDV17', 'SDV18'):
        values = {r[1]: finite(r[2]) for r in snapshot['energies'] if r[0] == field}
        require(len([r for r in snapshot['energies'] if r[0] == field]) == len(expected_gp) and set(values) == expected_gp, 'Incomplete/duplicate UEL energy IP coverage')
        total = 0.0
        for el in visual:
            repeated = [values[instance+':'+str(el)+':'+str(ip)] for ip in range(1, 5)]
            require(all(math.isclose(v, repeated[0], rel_tol=1e-6, abs_tol=1e-14) for v in repeated), 'Element energy differs across duplicated IP output')
            total += repeated[0]  # Each element total once, never four times.
        totals[field] = total
    final_energy = energy[1, increment]
    require(math.isclose(totals['SDV17'], final_energy['E_fracture_kNmm'], rel_tol=1e-5, abs_tol=1e-12) and
            math.isclose(totals['SDV18'], final_energy['E_elastic_kNmm'], rel_tol=1e-5, abs_tol=1e-12), 'Accepted UEL CSV/SDV endpoint energy mismatch')
    damage = [finite(dat[n][2]) for n in sorted(nodes)]; require(bool(damage), 'Empty nodal damage')
    violations = sum(d < -DAMAGE_TOLERANCE or d > 1+DAMAGE_TOLERANCE for d in damage)
    if violations:
        raise PhysicalFailure('Nodal damage bounds violated at %d nodes' % violations)
    if minimum_delta < -1e-12:
        raise PhysicalFailure('Recorded trial GP history decreases across accepted frames')
    return dict(step='Step-1', increment=increment, uRP_mm=last['rp']['u2'], RF2_kN=last['rp']['rf2'],
                elastic_kNmm=final_energy['E_elastic_kNmm'], fracture_kNmm=final_energy['E_fracture_kNmm'],
                total_kNmm=final_energy['E_total_kNmm'], sdv_energy_totals=totals,
                node_count=len(nodes), gp_count=len(keys), damage_min=min(damage), damage_max=max(damage),
                damage_bound_violations=violations, damage_admissibility='FAIL' if violations else 'PASS',
                nodal_irreversibility='UNVERIFIED_INTERMEDIATE_U3_NOT_RECORDED',
                history_minimum_increment=minimum_delta, recorded_trial_history_monotone=minimum_delta >= -1e-12,
                committed_history_preservation='UNVERIFIED_TRIAL_SDV2_ONLY',
                nodal_damage=damage, node_labels=sorted(nodes), history_keys=keys, history_endpoint=previous,
                history_semantics=snapshot['history_semantics'], odb_sha256=snapshot['odb_sha256'])


def refinement_check(workspace, artifact_root=None):
    # Reuse the existing centroid containment/area metric on pinned input decks.
    from audit_h55_refinement_only_geometry import parse_mesh_detailed, find_containing_element
    meshes = []
    for package, cfg in PACKAGES.items():
        path = (Path(artifact_root)/str(package)/(cfg['name']+'.inp')) if artifact_root else (
            Path(workspace)/'models/pandey_kumar_mode1'/cfg['directory']/(cfg['name']+'.inp'))
        meshes.append(parse_mesh_detailed(path)[1])
    donor, receiver = meshes
    require(len(donor) == 5112 and len(receiver) == 7056, 'Unexpected refinement mesh cardinality')
    ratios = []
    for elem in receiver.values():
        parent = find_containing_element(elem['cx'], elem['cy'], donor)
        require(parent is not None, 'Receiver centroid not covered by donor mesh')
        a, b = finite(donor[parent]['area']), finite(elem['area'])
        require(a > 0 and b > 0, 'Nonpositive element area')
        ratios.append(b/a)
    coarsened = sum(r > 1.0001 for r in ratios)  # Existing Package147 geometry-test tolerance.
    if coarsened:
        raise PhysicalFailure('Refinement-only constraint failed')
    return dict(status='PASS', metric='Existing centroid-containing donor quad area ratio',
                coarsened_elements=coarsened, maximum_area_ratio=max(ratios), minimum_area_ratio=min(ratios))


def evaluate_package(workspace, root, package):
    cfg = PACKAGES[package]; root = Path(root)
    if not (root/'manifest.json').is_file():
        raise Unavailable('Authenticated artifact manifest missing: '+str(root))
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    require(manifest.get('schema') == 1, 'Unsupported artifact manifest schema')
    require(manifest['job_id'] == cfg['job'] and manifest['remote_directory'] == cfg['remote'], 'Wrong artifact source identity')
    required = ['qstat.txt', 'snapshot.json.gz', 'uel_energy_balance.csv', 'f42_mixed_uel.for',
                cfg['name']+'.inp', cfg['name']+'.dat', cfg['name']+'.sta', cfg['name']+'.msg', 'pbs_execution.log']
    for name in required:
        path = root/name
        if not path.is_file():
            raise Unavailable('Missing solver artifact: '+name)
        require(compute_file_sha256(path) == manifest['files'][name], 'Artifact hash mismatch: '+name)
        if name != 'qstat.txt':
            require(manifest['remote_sha256'][name] == manifest['files'][name], 'Unauthenticated remote hash: '+name)
    text = lambda name: (root/name).read_text(encoding='utf-8')
    pbs_identity(text('qstat.txt'), cfg)
    require(manifest['files'][cfg['name']+'.inp'] == cfg['inp_sha'] and manifest['files']['f42_mixed_uel.for'] == FROZEN_UEL_SHA256, 'Remote input/UEL mismatch')
    audit_input_provenance(workspace, allow_missing=True)
    sta = text(cfg['name']+'.sta')
    require('THE ANALYSIS HAS COMPLETED SUCCESSFULLY' in sta and 'Abaqus JOB '+cfg['name']+' COMPLETED' in text('pbs_execution.log'), 'Incomplete/nonconverged solver output')
    require('THE ANALYSIS HAS NOT BEEN COMPLETED' not in text(cfg['name']+'.msg'), 'Solver message reports incomplete analysis')
    with gzip.open(root/'snapshot.json.gz', 'rt', encoding='utf-8') as stream:
        snapshot = json.load(stream)
    require(snapshot['odb_path'] == cfg['remote']+'/'+cfg['name']+'.odb', 'Wrong exported ODB identity')
    require(snapshot['odb_sha256'] == manifest['odb_sha256'] and snapshot['extractor_sha256'] == manifest['extractor_sha256'], 'ODB/export source hash mismatch')
    require(re.fullmatch('[0-9a-f]{64}', snapshot['odb_sha256']) is not None, 'Malformed ODB hash')
    require(manifest['extractor_sha256'] == compute_file_sha256(Path(workspace)/'scripts/validation/extract_package146147_odb.py'), 'Unreviewed extractor source revision')
    nodes, visual = model_maps(text(cfg['name']+'.inp'))
    dat = parse_dat_endpoint(text(cfg['name']+'.dat'), nodes, snapshot['frames'][-1]['increment'])
    result = validate_snapshot(snapshot, nodes, visual, dat, parse_energy(text('uel_energy_balance.csv')), sta)
    result.update(package=package, pbs_job_id=cfg['job'], artifact_manifest_sha256=compute_file_sha256(root/'manifest.json'))
    return result


def evaluate(workspace, artifact_root):
    report = dict(schema=2, operation_id=OPERATION, registration='NOT_REGISTERED_REVIEW_REQUIRED',
                  comparison_kind='CONTINUOUS_MESH_SENSITIVITY_ONLY', stage_c1_1_transfer_acceptance=False,
                  packages={}, comparisons=None, scientific_acceptance=False)
    for package in PACKAGES:
        try:
            result = evaluate_package(workspace, Path(artifact_root)/str(package), package)
            result['status'] = 'AUTHENTICATED_MEASUREMENTS'
        except (EvidenceError, OSError, EOFError, ValueError, KeyError, IndexError, TypeError, OverflowError) as exc:
            result = dict(package=package, status=getattr(exc, 'status', 'INVALID_EVIDENCE'), reason=str(exc))
        report['packages'][str(package)] = result
    a, b = [report['packages'][str(p)] for p in PACKAGES]
    if all(r['status'] == 'AUTHENTICATED_MEASUREMENTS' for r in (a, b)):
        try:
            rf_pass, _, _ = evaluate_reaction_force_continuity(a['RF2_kN'], b['RF2_kN'])
            e_pass, _, _ = evaluate_energy_continuity(a['total_kNmm'], b['total_kNmm'])
            refinement = refinement_check(workspace, artifact_root)
            report['comparisons'] = dict(Delta_E_percent=100*(b['total_kNmm']-a['total_kNmm'])/a['total_kNmm'],
                Delta_RF_percent=100*(b['RF2_kN']-a['RF2_kN'])/a['RF2_kN'], raw_energy_gate_pass=e_pass,
                rf_gate_pass=rf_pass, refinement_only=refinement,
                interpretation='Diagnostic only; no state-transfer or irreversibility acceptance')
        except EvidenceError as exc:
            report['comparison_error'] = str(exc)
    report['status'] = 'DIAGNOSTIC_COMPLETE_WITH_LIMITATIONS' if report['comparisons'] else 'EVALUATION_NOT_AVAILABLE'
    return report


def audit_evaluation_readiness(workspace, artifact_root=None):
    return evaluate(workspace, artifact_root or Path(workspace)/'results/validation/package146147/artifacts')


def retrieve_authenticated_artifacts(workspace, artifact_root, export_directory):
    """Retrieve existing artifacts only, via the mandatory guarded SSH wrapper.

    ODB export must already exist from the read-only Abaqus extractor. This
    function never runs Abaqus, uploads code, submits, cancels or retries a job.
    Every destination is new; interrupted partial retrieval remains preserved.
    """
    require(re.fullmatch(r'/scratch9/pr21vyci/runs/[A-Za-z0-9_/-]+', export_directory) is not None,
            'Invalid explicit remote export directory')
    wrapper = Path(workspace)/'.agents/scripts/Invoke-GuardedSsh.ps1'

    def query(command):
        completed = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(wrapper),
                                    '-TimeoutSeconds', '120', '-RemoteCommand', command],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=130, check=False)
        if completed.returncode:
            raise Unavailable('Guarded artifact query failed: '+completed.stderr.decode('utf-8', 'replace'))
        return completed.stdout.decode('utf-8').strip()

    for package, cfg in PACKAGES.items():
        root = Path(artifact_root)/str(package)
        root.mkdir(parents=True, exist_ok=False)
        qstat = query('qstat -x -f '+cfg['job'])
        with (root/'qstat.txt').open('x', encoding='utf-8') as stream:
            stream.write(qstat+'\n')
        pbs_identity(qstat, cfg)
        sources = {name: cfg['remote']+'/'+name for name in [
            'uel_energy_balance.csv', 'f42_mixed_uel.for', cfg['name']+'.inp', cfg['name']+'.dat',
            cfg['name']+'.sta', cfg['name']+'.msg', 'pbs_execution.log']}
        sources['snapshot.json.gz'] = export_directory+'/package'+str(package)+'.json.gz'
        digests = {}
        for line in query('sha256sum '+' '.join(sources.values())+' '+cfg['remote']+'/'+cfg['name']+'.odb').splitlines():
            digest, path = line.split(None, 1); digests[path.strip()] = digest
        for name, path in sources.items():
            data = base64.b64decode(query('base64 -w0 '+path), validate=True)
            require(hashlib.sha256(data).hexdigest() == digests[path], 'Transport hash mismatch: '+name)
            with (root/name).open('xb') as stream:
                stream.write(data)
        with gzip.open(root/'snapshot.json.gz', 'rt', encoding='utf-8') as stream:
            snapshot = json.load(stream)
        manifest = dict(schema=1, job_id=cfg['job'], remote_directory=cfg['remote'],
                        transport='Invoke-GuardedSsh.ps1; base64 exact bytes; independent remote SHA256',
                        files={name: compute_file_sha256(root/name) for name in ['qstat.txt']+list(sources)},
                        remote_sha256={name: digests[path] for name, path in sources.items()},
                        odb_sha256=digests[cfg['remote']+'/'+cfg['name']+'.odb'],
                        extractor_sha256=snapshot['extractor_sha256'])
        with (root/'manifest.json').open('x', encoding='utf-8') as stream:
            json.dump(manifest, stream, indent=2, allow_nan=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', default=os.getcwd()); p.add_argument('--artifact-root', required=True); p.add_argument('--output')
    p.add_argument('--retrieve', action='store_true')
    p.add_argument('--remote-export-directory', default='/scratch9/pr21vyci/runs/package146147_result_review_codex')
    args = p.parse_args()
    if args.retrieve:
        retrieve_authenticated_artifacts(args.workspace, args.artifact_root, args.remote_export_directory)
    report = evaluate(args.workspace, args.artifact_root)
    text = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as stream:
            stream.write(text+'\n')
    print(text)
    return 0 if report['comparisons'] is not None else 2


if __name__ == '__main__':
    raise SystemExit(main())
