"""Bounded offline reconstruction of the 21 authentic R4 solves; never runs Abaqus.

Reads only the explicitly recovered text artifacts. Does not alter the frozen
driver, UEL, solver output, iteration bounds or physical acceptance thresholds.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    CoupledAbaqusRuntime, driving_history, split_keyword_blocks,
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def pack_odb_diagnostics(source, destination):
    """Lossless history deduplication; retain all 21 hashes and damage fields."""
    data=json.loads(Path(source).read_text())
    data['histories']={}
    for solve in data['solves']:
        history=solve.pop('history')
        key=hashlib.sha256(json.dumps(history,separators=(',',':')).encode()).hexdigest()
        data['histories'][key]=history
        solve['history_ref']=key
    with gzip.GzipFile(filename=str(destination),mode='wb',mtime=0) as stream:
        stream.write(json.dumps(data,separators=(',',':'),allow_nan=False).encode())


def parse_phase_input(text):
    """Read the actual prescribed active set and injected perimeter-order history."""
    active, displacement, initial = {}, {}, []
    for block in split_keyword_blocks(text):
        lines = block.splitlines()
        key = lines[0].strip().lower()
        data = [l for l in lines[1:] if l.strip() and not l.startswith('**')]
        if key.startswith('*initial conditions'):
            for line in data:
                initial.extend(float(v) for v in line.split(',') if v.strip())
        if key.startswith('*boundary'):
            for line in data:
                n, first, last, value = line.split(',')
                n, first, last, value = int(n), int(first), int(last), float(value)
                if first != last:
                    raise ValueError('Unexpected BC range')
                if first == 3:
                    if n in active:
                        raise ValueError('Duplicate phase boundary')
                    active[n] = value
                else:
                    if (n, first) in displacement:
                        raise ValueError('Duplicate mechanical boundary')
                    displacement[n, first] = value
    if len(initial) % 19:
        raise ValueError('Incomplete injected 18-SVAR history')
    history = {}
    for start in range(0, len(initial), 19):
        row = initial[start:start+19]
        eid = int(row[0])
        for g in range(1, 5):
            if (eid, g) in history:
                raise ValueError('Duplicate injected history')
            history[eid, g] = row[8+g]
    return active, displacement, history


def sparse_system(solver, ids):
    diag, off, rhs = solver.assemble_system()
    index = {n: i for i, n in enumerate(ids)}
    rows, cols, values = [], [], []
    for n, v in diag.items():
        rows.append(index[n]); cols.append(index[n]); values.append(v)
    for (i, j), v in off.items():
        rows.append(index[i]); cols.append(index[j]); values.append(v)
    matrix = coo_matrix((values, (rows, cols)), shape=(len(ids), len(ids))).tocsr()
    return matrix, np.array([rhs[n] for n in ids])


def solution_cards(eid, state):
    """Hypothesis-only serializer, not installed in the production driver.

    Abaqus TYPE=SOLUTION: element + seven states; eight states/continuation.
    Reference: SIMULIA *INITIAL CONDITIONS keyword manual, TYPE=SOLUTION.
    """
    if len(state) != 18 or not np.all(np.isfinite(state)):
        raise ValueError('Exactly 18 finite states required')
    chunks = [[eid]+list(state[:7]), list(state[7:15]), list(state[15:])]
    return '\n'.join(', '.join('%.17g' % v for v in chunk) for chunk in chunks)+'\n'


def fixed_field_decode(text, strict=True):
    """Independent 7+8+3 parser; expose legacy overflow rather than flatten it."""
    lines = [[float(v) for v in line.split(',') if v.strip()] for line in text.splitlines() if line.strip()]
    if len(lines) != 3 or (strict and any(len(line)>8 for line in lines)):
        raise ValueError('Invalid state card field count')
    state=lines[0][1:8]+lines[1][:8]+lines[2][:3]
    return int(lines[0][0]), state+[0.]*(18-len(state))


def shifted_history(history):
    """Empirical prediction from the overflowing legacy first line."""
    return {(e,g): history[e,g+1] if g<4 else 0. for e,g in history}


def solution_records(text):
    result=[]
    for block in split_keyword_blocks(text):
        lines=block.splitlines()
        if not lines[0].lower().startswith('*initial conditions'):
            continue
        data=[l for l in lines[1:] if l.strip() and not l.startswith('**')]
        if len(data)%3:
            raise ValueError('Unexpected R4 solution card layout')
        for i in range(0,len(data),3):
            card='\n'.join(data[i:i+3])
            eid, decoded=fixed_field_decode(card,strict=False)
            flat=[float(v) for line in data[i:i+3] for v in line.split(',') if v.strip()]
            result.append(dict(element=eid,intended=flat[1:],decoded=decoded,
                               line_counts=[len(line.split(',')) for line in data[i:i+3]],card=card))
    return result


def counterfactual_pdas(matrix, force, baseline, initial, quantized=False):
    """One bounded offline replay with the intended operator; no damage clipping.

    Uses the same twenty-step cap, active update and KKT tolerances as R4.
    Equalities on the selected active set are the VI constraints, not clipping.
    """
    damage=initial.copy()
    residual=matrix@damage-force
    active=damage-residual/matrix.diagonal() <= baseline+1e-12
    rows=[]
    for i in range(1,21):
        free=~active
        damage=baseline.copy()
        damage[free]=spsolve(matrix[free][:,free],force[free]-matrix[free][:,active]@baseline[active])
        if quantized:
            damage=np.array([float('%.8g' % v) for v in damage])
        metrics,residual,_,next_active=kkt_metrics(matrix,force,damage,baseline,active)
        rows.append(dict(iteration=i,**metrics))
        if metrics['passed']:
            break
        active=next_active
    return dict(converged=rows[-1]['passed'],iterations=rows,damage=damage.tolist())


def kkt_metrics(matrix, force, damage, baseline, bc_active):
    residual = matrix @ damage - force
    gap = damage - baseline
    inferred = gap <= 1e-10  # Exact production classification, including DAT rounding.
    next_active = damage - residual/matrix.diagonal() <= baseline + 1e-12
    max0 = lambda x: float(np.max(x)) if len(x) else 0.
    return dict(
        signed_residual_min=float(residual.min()), signed_residual_max=float(residual.max()),
        free_error=max0(np.abs(residual[~inferred])),
        dual_error=max0(np.maximum(-residual[inferred], 0.)),
        complementarity=max0(np.abs(residual*gap)), min_gap=float(gap.min()),
        complementarity_violations=int(np.count_nonzero(np.abs(residual*gap)>1e-6)),
        primal_violations=int(np.count_nonzero(gap < -1e-6)),
        bc_active_signed_min=float(residual[bc_active].min()) if bc_active.any() else None,
        bc_active_signed_max=float(residual[bc_active].max()) if bc_active.any() else None,
        max_gap=float(gap.max()), bc_active_count=int(bc_active.sum()),
        inferred_active_count=int(inferred.sum()),
        active_classification_disagreement=int(np.count_nonzero(inferred != bc_active)),
        bc_free_error=max0(np.abs(residual[~bc_active])),
        bc_dual_error=max0(np.maximum(-residual[bc_active], 0.)),
        dual_violations=int(np.count_nonzero(inferred & (residual < -1e-9))),
        bc_dual_violations=int(np.count_nonzero(bc_active & (residual < -1e-9))),
        next_active_count=int(next_active.sum()),
        next_membership_change=int(np.count_nonzero(next_active != bc_active)),
        passed=bool(gap.min() >= -1e-6 and max0(np.maximum(-residual[inferred], 0.)) <= 1e-9
                    and max0(np.abs(residual[~inferred])) <= 1e-6
                    and max0(np.abs(residual*gap)) <= 1e-6),
    ), residual, inferred, next_active


def analyze(solver_root, output, odb_diagnostics=None):
    solver_root, output = Path(solver_root), Path(output)
    if output.exists():
        raise ValueError('Preserve existing analysis; use a fresh output directory')
    package = ROOT/'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r4'
    runtime = CoupledAbaqusRuntime(package, output/'unused', ROOT/'scripts/validation/extract_package148_iteration.py', 1., 1.)
    runtime.load()  # Verify every immutable donor/package/runtime source binding.
    ids = sorted(runtime.mesh.nodes)
    baseline = np.array([runtime.d0[n] for n in ids])
    mech_dir = solver_root/'P148_01_00_mechanical'
    for path in (mech_dir/'endpoint.json',mech_dir/'P148_01_00_mechanical.inp',
                 solver_root/'P148_01_01_phase/P148_01_01_phase.inp'):
        if not path.is_file():
            raise ValueError('Missing exact solver artifact '+str(path))
    mechanical = json.loads((mech_dir/'endpoint.json').read_text())
    displacement = {int(r[0]): (r[1], r[2]) for r in mechanical['nodes']}
    reconstructed_history = driving_history(runtime.mesh, displacement, runtime.h0)
    # Use the exact serialized operator actually submitted. Record the separate
    # cross-interpreter reconstruction difference; never change a KKT tolerance.
    history = parse_phase_input((solver_root/'P148_01_01_phase/P148_01_01_phase.inp').read_text())[2]
    history_roundoff = max(abs(history[k]-reconstructed_history[k]) for k in history)
    runtime.solver.h_gp = history
    matrix, force = sparse_system(runtime.solver, ids)
    runtime.solver.h_gp=shifted_history(history)
    shifted_matrix,shifted_force=sparse_system(runtime.solver,ids)
    runtime.solver.h_gp=history
    if not odb_diagnostics or not Path(odb_diagnostics).is_file():
        raise ValueError('Complete read-only ODB diagnostics required')
    if str(odb_diagnostics).endswith('.gz'):
        with gzip.open(odb_diagnostics,'rt') as stream:
            odb_data=json.load(stream)
    else:
        odb_data=json.loads(Path(odb_diagnostics).read_text())
    if 'histories' in odb_data:
        for solve in odb_data['solves']:
            solve['history']=odb_data['histories'][solve['history_ref']]
            if hashlib.sha256(json.dumps(solve['history'],separators=(',',':')).encode()).hexdigest()!=solve['history_ref']:
                raise ValueError('Changed deduplicated ODB history')
    observed_history, observed_matrix, observed_force = None, None, None
    history_audit = {}
    if odb_data:
        if not odb_data['read_only'] or len(odb_data['solves']) != 21:
            raise ValueError('Incomplete ODB diagnostics')
        observed_history = {(e,g):v for e,g,v in odb_data['solves'][1]['history']}
        if set(observed_history) != set(history):
            raise ValueError('Incomplete observed history')
        history_audit = dict(
            observed_minus_injected_min=min(observed_history[k]-history[k] for k in history),
            observed_minus_injected_max=max(observed_history[k]-history[k] for k in history),
            observed_minus_committed_min=min(observed_history[k]-runtime.h0[k] for k in history),
            observed_below_committed_count=sum(observed_history[k]<runtime.h0[k]-1e-6 for k in history),
            largest_history_mismatches=[dict(element=k[0],gp=k[1],injected=history[k],observed=observed_history[k],committed=runtime.h0[k])
                         for k in sorted(history,key=lambda k:abs(observed_history[k]-history[k]),reverse=True)[:12]])
        psi=driving_history(runtime.mesh,displacement,dict.fromkeys(history,0.))
        shifted=shifted_history(history)
        predicted={k:max(shifted[k],psi[k]) for k in history}
        history_audit['shift_then_mechanical_max_prediction_error']=max(abs(observed_history[k]-predicted[k]) for k in history)
        history_audit['shift_prediction_float32_exact_count']=sum(float(np.float32(predicted[k]))==observed_history[k] for k in history)
        mech_records=solution_records((mech_dir/'P148_01_00_mechanical.inp').read_text())
        mechanical_loaded={(r['element'],g):r['decoded'][7+g] for r in mech_records for g in range(1,5)}
        expected_loaded=shifted_history(runtime.h0)
        if mechanical_loaded != expected_loaded:
            raise ValueError('Malformed card prediction does not match mechanical input')
        observed_mechanical={(e,g):v for e,g,v in odb_data['solves'][0]['history']}
        history_audit['mechanical_shift_prediction_float32_exact_count']=sum(
            float(np.float32(max(mechanical_loaded[k],psi[k])))==observed_mechanical[k] for k in history)
        history_audit['mechanical_observed_below_committed_count']=sum(observed_mechanical[k]<runtime.h0[k]-1e-6 for k in history)
        history_audit['mechanical_observed_minus_committed_min']=min(observed_mechanical[k]-runtime.h0[k] for k in history)
        history_audit['mechanical_overflow_records']=sum(r['line_counts'][0]>8 for r in mech_records)
        runtime.solver.h_gp=observed_history
        observed_matrix, observed_force=sparse_system(runtime.solver,ids)
        runtime.solver.h_gp=history
    previous = np.array([r[3] for r in sorted(mechanical['nodes'])])
    previous_active, predicted = None, None
    rows, hashes, worst = [], {}, []
    output.mkdir(parents=True)
    with gzip.open(output/'nodal_kkt.csv.gz', 'wt', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['iteration','node','damage','gap','damage_increment','signed_residual',
                         'assembled_signed_residual','bc_active','inferred_active','next_active'])
        for inner in range(1, 21):
            name = 'P148_01_%02d_phase' % inner
            directory = solver_root/name
            for filename in [name+'.inp',name+'.dat',name+'.msg',name+'.sta','endpoint.json','receipt.json',
                             'solver.stdout.txt','extractor.stdout.txt','uel_energy_balance.csv']:
                if not (directory/filename).is_file():
                    raise ValueError('Missing exact artifact '+str(directory/filename))
            endpoint = json.loads((directory/'endpoint.json').read_text())
            receipt = json.loads((directory/'receipt.json').read_text())
            text = (directory/(name+'.inp')).read_text()
            if receipt['input_sha256'].upper() != sha(directory/(name+'.inp')) or receipt['endpoint'] != endpoint:
                raise ValueError('Receipt/input/endpoint provenance mismatch')
            for filename in [name+'.inp', name+'.dat', name+'.msg', name+'.sta', 'endpoint.json', 'receipt.json',
                             'solver.stdout.txt', 'extractor.stdout.txt', 'uel_energy_balance.csv']:
                path = directory/filename
                if not path.is_file():
                    raise ValueError('Missing solver artifact '+str(path))
                hashes[name+'/'+filename] = sha(path)
            if 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in (directory/(name+'.sta')).read_text():
                raise ValueError('Abaqus phase solve incomplete')
            active, prescribed_u, injected_h = parse_phase_input(text)
            initial_records=solution_records(text)
            loaded={(r['element'],g):r['decoded'][7+g] for r in initial_records for g in range(1,5)}
            if loaded != shifted_history(history):
                raise ValueError('Malformed card hypothesis does not match phase input')
            if set(prescribed_u) != {(n, d) for n in ids for d in (1, 2)}:
                raise ValueError('Incomplete fixed mechanical field')
            h_error = max(abs(injected_h[k]-history[k]) for k in history)
            u_error = max(abs(prescribed_u[n, d]-displacement[n][d-1]) for n, d in prescribed_u)
            bc_error = max([abs(v-runtime.d0[n]) for n, v in active.items()]+[0.])
            if h_error or u_error or bc_error:
                raise ValueError('Constraint reconstruction difference H=%g u=%g d0=%g' % (h_error,u_error,bc_error))
            data = {int(r[0]): r for r in endpoint['nodes']}
            if set(data) != set(ids) or len(data) != len(endpoint['nodes']):
                raise ValueError('Incomplete/duplicate endpoint coverage')
            damage = np.array([data[n][3] for n in ids])
            if not np.all(np.isfinite(damage)) or damage.min() < 0 or damage.max() > 1:
                raise ValueError('Invalid damage')
            bc = np.array([n in active for n in ids])
            metrics, residual, inferred, predicted_next = kkt_metrics(matrix, force, damage, baseline, bc)
            shifted_residual=shifted_matrix@damage-shifted_force
            metrics['shifted_operator_bc_free_error']=float(np.max(np.abs(shifted_residual[~bc])))
            if odb_data:
                observed=odb_data['solves'][inner]
                if observed['odb_sha256'] != endpoint['odb_sha256'] or observed['history'] != odb_data['solves'][1]['history']:
                    raise ValueError('ODB hash/history changed between phases')
                actual_residual=observed_matrix@damage-observed_force
                metrics['observed_operator_bc_free_error']=float(np.max(np.abs(actual_residual[~bc])))
                metrics['observed_history_change_inf']=0.
                averages=dict(observed['damage_average'])
                metrics['odb_average_damage_error']=max(abs(averages[e]-sum(data[n][3] for n in conn)/4) for e,conn in runtime.mesh.elements.items())
            metrics.update(iteration=inner, damage_change_inf=float(np.max(np.abs(damage-previous))),
                           active_added=int(np.count_nonzero(bc & ~previous_active)) if previous_active is not None else None,
                           active_removed=int(np.count_nonzero(~bc & previous_active)) if previous_active is not None else None,
                           prediction_matches_used=bool(np.array_equal(bc, predicted)) if predicted is not None else None,
                           history_error=h_error, mechanical_bc_error=u_error, phase_bc_error=bc_error)
            metrics['actual_mechanical_displacement_error']=max(abs(data[n][d]-displacement[n][d-1]) for n in ids for d in (1,2))
            metrics['active_damage_retention_error']=max([abs(data[n][3]-v) for n,v in active.items()]+[0.])
            metrics['overflow_state_records']=sum(r['line_counts'][0]>8 for r in initial_records)
            msg = (directory/(name+'.msg')).read_text()
            m = re.search(r'CORRESPONDING RESIDUAL FORCE\s+([\d.E+\-]+)', msg)
            metrics['abaqus_signed_residual'] = float(m.group(1)) if m else None
            rows.append(metrics)
            worst.append(dict(iteration=inner, nodes=[dict(node=ids[i], residual=float(residual[i]),
                        gap=float(damage[i]-baseline[i]), bc_active=bool(bc[i]), inferred_active=bool(inferred[i]))
                        for i in np.argsort(residual)[:8]]))
            for i, n in enumerate(ids):
                writer.writerow([inner,n,damage[i],damage[i]-baseline[i],damage[i]-previous[i],residual[i],
                                 shifted_residual[i],int(bc[i]),int(inferred[i]),int(predicted_next[i])])
            previous, previous_active, predicted = damage, bc, predicted_next
    for path in mech_dir.iterdir():
        if path.name.endswith(('.inp','.dat','.sta','.msg','.json','.txt','.csv')):
            hashes[mech_dir.name+'/'+path.name] = sha(path)
    with (output/'iterations.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result=dict(schema=1,pbs_job_id='1418902.mmaster02',physical_acceptance=False,iterations=rows,
                worst_signed_nodes=worst,artifact_sha256=hashes,history_min=float(min(history.values())),
                history_max=float(max(history.values())),history_increase_over_committed_max=float(max(history[k]-runtime.h0[k] for k in history)),
                history_reconstruction_roundoff=history_roundoff,
                observed_history_audit=history_audit,
                production_uel_sha256=sha(package/'f42_mixed_uel.for'),source_driver_sha256=sha(ROOT/'scripts/state_transfer/driver_package146_147_pdas_continuation.py'))
    initial=np.array([r[3] for r in sorted(mechanical['nodes'])])
    result['serializer_only_counterfactual']=dict(
        high_precision=counterfactual_pdas(matrix,force,baseline,initial),
        dat_eight_significant_digits=counterfactual_pdas(matrix,force,baseline,initial,True))
    # Small authentic nonuniform cases for independent focused regression tests.
    (output/'state_card_fixture.json').write_text(json.dumps(dict(
        elements=[dict(element=r['element'],original_card=r['card'],intended=r['intended'],decoded=r['decoded'],
                       observed_history=[observed_history[r['element'],g] for g in range(1,5)],
                       mechanical_psi=[psi[r['element'],g] for g in range(1,5)])
                  for r in initial_records if r['element'] in (3484,3485,3486)]),indent=2)+'\n')
    (output/'reconstruction.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return rows


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver-root',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--odb-diagnostics',required=True)
    args=parser.parse_args()
    for row in analyze(args.solver_root,args.output,args.odb_diagnostics):
        print(json.dumps(row,sort_keys=True))
