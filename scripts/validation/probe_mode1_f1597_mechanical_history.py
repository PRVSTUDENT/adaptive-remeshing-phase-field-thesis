"""Read-only reconstruction of Package72's mapped mechanical/history transaction.

No solve, correction or claim about observed Abaqus call order. The retired probe's
element kernel is reused; its completed operation/main entrypoint is never called.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from probe_mode1_f1597_kkt import load_deck, phase_element

OPERATION = 'mapped_mechanical_history_call_order_probe'
PACKAGE = 'models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/'
FROZEN = 'models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for'
TOLERANCES = dict(history_kN_mm2=1e-10, residual_kN=1e-10,
                  fd_relative=1e-7, mapping_mm=1e-10, transaction=1e-14)


def mechanical_element(xy, displacement, damage, props):
    """Exact JTYPE2 plane-strain tensor and element-average degradation."""
    _, _, young, nu, kappa, _ = props
    if not (young > 0 and -1 < nu < .5 and kappa > 0):
        raise ValueError('Unsupported material')
    lam = young * nu / ((1 + nu) * (1 - 2 * nu))
    mu = young / (2 * (1 + nu))
    c = np.array([[lam+2*mu, lam, 0], [lam, lam+2*mu, 0], [0, 0, mu]])
    c *= (1 - np.mean(damage))**2 + kappa
    stiffness = np.zeros((8, 8)); driving = []
    q = 1 / np.sqrt(3)
    for xi, eta in ((-q, -q), (q, -q), (q, q), (-q, q)):
        dn = .25*np.array([[-(1-eta), 1-eta, 1+eta, -(1+eta)],
                           [-(1-xi), -(1+xi), 1+xi, 1-xi]])
        jac = dn @ xy; det = np.linalg.det(jac)
        if det <= 0:
            raise ValueError('Nonpositive mechanical Jacobian')
        grad = np.linalg.solve(jac, dn)
        b = np.zeros((3, 8)); b[0, ::2] = grad[0]; b[1, 1::2] = grad[1]
        b[2, ::2] = grad[1]; b[2, 1::2] = grad[0]
        strain = b @ displacement
        e11, e22, shear = strain
        driving.append(.5*lam*max(e11+e22, 0)**2 +
                       mu*(e11**2+e22**2+2*(.5*shear)**2))
        stiffness += det * b.T @ c @ b
    force = stiffness @ displacement
    return stiffness, force, np.array(driving)


def history_transaction(committed, driving):
    # LOP1 restore; mechanical max on trial; LOP2 commits accepted trial.
    trial = np.maximum(committed, driving)
    return trial, committed.copy(), trial.copy(), committed.copy()


def analyze(nodes, elements, offsets, props, constrained):
    ids = sorted({n for conn in elements.values() for n in conn})
    index = {n: i for i, n in enumerate(ids)}
    force = np.zeros(2*len(ids)); phase0 = np.zeros(len(ids)); phase1 = phase0.copy()
    mapped_u = {}; mapped_d = {}; jump_u = jump_d = 0.
    max_history = max_fd = committed_error = rollback_error = commit_error = 0.
    first_history = None
    for eid, conn in sorted(elements.items()):
        values = np.asarray(offsets[eid], dtype=float)
        if values.shape != (16,) or not np.isfinite(values).all():
            raise ValueError('Invalid mapped state')
        u, d, h = values[:8], values[8:12], values[12:]
        if np.any(h < 0) or np.any(d < 0) or np.any(d > 1):
            raise ValueError('Mapped history/damage outside admissible domain')
        xy = np.array([nodes[n] for n in conn]); loc = [index[n] for n in conn]
        for j, n in enumerate(conn):
            if n in mapped_u:
                jump_u = max(jump_u, float(np.max(abs(mapped_u[n]-u[2*j:2*j+2]))))
                jump_d = max(jump_d, abs(mapped_d[n]-d[j]))
            mapped_u[n] = u[2*j:2*j+2]; mapped_d[n] = d[j]
        k, f, driving = mechanical_element(xy, u, d, props)
        trial, before_commit, accepted, reset = history_transaction(h, driving)
        delta = trial-h
        max_history = max(max_history, float(np.max(delta)))
        if first_history is None and np.any(delta > TOLERANCES['history_kN_mm2']):
            pt = int(np.argmax(delta)); first_history = dict(element=eid, gauss_point=pt+1,
                committed=float(h[pt]), mechanical_driving=float(driving[pt]), trial=float(trial[pt]))
        committed_error = max(committed_error, float(np.max(abs(before_commit-h))))
        rollback_error = max(rollback_error, float(np.max(abs(reset-h))))
        commit_error = max(commit_error, float(np.max(abs(accepted-trial))))
        dofs = [2*i+j for i in loc for j in (0, 1)]
        force[dofs] += f
        phase0[loc] += phase_element(xy, d, h, props[0], props[1])[2]
        phase1[loc] += phase_element(xy, d, trial, props[0], props[1])[2]
        # Independent energy-gradient FD check per element, scaled by force.
        direction = np.zeros(8); direction[int(np.argmax(abs(f)))] = 1
        eps = 1e-7 * max(1., float(np.max(abs(u))))
        energy = lambda v: .5 * v @ k @ v
        fd = (energy(u+eps*direction)-energy(u-eps*direction))/(2*eps)
        max_fd = max(max_fd, abs(fd-f@direction)/max(1., float(np.max(abs(f)))))
    free = [2*index[n]+j for n in ids for j in (0, 1) if (n, j+1) not in constrained]
    if not free or jump_d > TOLERANCES['mapping_mm']:
        raise ValueError('No free mechanical DOFs or discontinuous phase mapping')
    worst = max(free, key=lambda i: abs(force[i]))
    residual = float(np.max(abs(force[free])))
    discrepancy = ('HISTORY_UPDATE_AT_MAPPED_STATE' if first_history else
                   'MECHANICAL_FREE_DOF_RESIDUAL' if residual > TOLERANCES['residual_kN'] else
                   'DISPLACEMENT_MAPPING_JUMP' if jump_u > TOLERANCES['mapping_mm'] else
                   'NONE_ABOVE_DECLARED_TOLERANCES')
    measurements = dict(phase_elements=len(elements), phase_nodes=len(ids),
        free_mechanical_dofs=len(free), mechanical_free_residual_inf_kN=residual,
        worst_mechanical_node=ids[worst//2], worst_mechanical_dof=worst % 2+1,
        mapped_displacement_jump_mm=jump_u, mapped_damage_jump=jump_d,
        history_increase_inf_kN_mm2=max_history,
        phase_before_mechanical_inf_kN=float(np.max(abs(phase0))),
        phase_after_mechanical_inf_kN=float(np.max(abs(phase1))),
        phase_call_order_delta_inf_kN=float(np.max(abs(phase1-phase0))),
        committed_before_accept_error=committed_error, retry_restore_error=rollback_error,
        accepted_commit_error=commit_error, mechanical_fd_relative_error=max_fd)
    if max_fd > TOLERANCES['fd_relative']:
        raise ValueError('Mechanical energy-gradient check failed')
    return measurements, dict(classification=discrepancy, first_history_update=first_history)


def step_one_constraints(deck, elements):
    """Qualify this deck's explicit Step1 BCs and two-term top/RP equations."""
    text = deck.read_text(encoding='utf-8-sig'); sets = {}; mode = ''; name = None
    equations = []; equation = []
    for raw in text.split('*Step, name=Step-2')[0].splitlines():
        line = raw.strip()
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            low = line.lower().replace(' ', '')
            mode = 'nset' if low.startswith('*nset,') else 'equation' if low == '*equation' else ''
            if mode == 'nset':
                name = low.split('nset=')[1].split(',')[0].upper(); sets[name] = []
                if 'generate' in low:
                    mode = 'generate'
            if mode == 'equation':
                equation = []
            continue
        fields = [x.strip() for x in line.split(',') if x.strip()]
        if mode in ('nset', 'generate'):
            vals = list(map(int, fields)); sets[name].extend(range(vals[0], vals[1]+1, vals[2]) if mode == 'generate' else vals)
        elif mode == 'equation':
            if not equation:
                if fields != ['2']: raise ValueError('Unsupported equation')
                equation = ['2']
            else:
                if len(fields) != 6: raise ValueError('Unsupported equation layout')
                equations.append(tuple(map(float, fields))); mode = ''
    for name in ('N_BOTTOM', 'N_PIN', 'N_TOP', 'N_RP'):
        if not sets.get(name): raise ValueError('Missing boundary set')
    rp = sets['N_RP']
    expected = {(float(n), 2., 1., float(rp[0]), 2., -1.) for n in sets['N_TOP']}
    if len(rp) != 1 or set(equations) != expected or len(equations) != len(expected):
        raise ValueError('Unsupported mechanical constraint equations')
    # Fail closed for altered boundary/load constructs rather than mislabel reactions.
    boundaries = []; active = False
    for raw in text.split('*Step, name=Step-2')[0].splitlines():
        line = raw.strip()
        if line.startswith('**'): continue
        if line.startswith('*'):
            active = line.lower() == '*boundary'
            if line.lower().startswith(('*cload', '*dload', '*dsload', '*mpc', '*coupling')):
                raise ValueError('Unsupported applied force/constraint')
        elif active and line:
            boundaries.append(tuple(x.strip() for x in line.split(',')))
    allowed = {('N_BOTTOM','2','2','0.0'), ('N_PIN','1','1','0.0'),
               ('N_TOP','1','1','0.0'), ('N_RP','2','2','0.0')}
    if set(boundaries) != allowed: raise ValueError('Unsupported Step1 boundary conditions')
    return ({(n, 2) for n in sets['N_BOTTOM']+sets['N_TOP']} |
            {(n, 1) for n in sets['N_PIN']+sets['N_TOP']})


def probe(workspace):
    task = json.loads((workspace/'project_coordination/ACTIVE_TASK.json').read_text(encoding='utf-8-sig'))
    basis = task['scientific_checkpoint']
    basis_path = (workspace/basis['artifact']).resolve()
    if not basis_path.is_relative_to(workspace) or not basis_path.is_file():
        raise ValueError('Unsafe/missing prior checkpoint')
    if hashlib.sha256(basis_path.read_bytes()).hexdigest().upper() != basis['sha256'].upper():
        raise ValueError('Prior checkpoint hash mismatch')
    prior = json.loads(basis_path.read_text())
    if prior['operation'] != 'mapped_frozen_history_lower_bound_kkt_probe' or not prior['verification_passed']:
        raise ValueError('Verified completed KKT basis required')
    sources = [PACKAGE+'M1_EXP_COUPLED_TRANSFER_650.inp', PACKAGE+'offset_state_table.csv',
               PACKAGE+'f42_experimental_offset_uel.for', FROZEN,
               'scripts/validation/probe_mode1_f1597_kkt.py',
               'scripts/validation/probe_mode1_f1597_mechanical_history.py', basis['artifact']]
    hashes = {p: hashlib.sha256((workspace/p).read_bytes()).hexdigest() for p in sources}
    for path in sources[:5]:
        if prior['sources'].get(path, '').lower() != hashes[path]:
            raise ValueError('Prior evidence source differs: '+path)
    if hashes[FROZEN] != 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6':
        raise ValueError('Frozen production UEL changed')
    if hashes[PACKAGE+'f42_experimental_offset_uel.for'] != 'ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d':
        raise ValueError('Experimental UEL changed; transcription must be requalified')
    deck = workspace/(PACKAGE+'M1_EXP_COUPLED_TRANSFER_650.inp')
    nodes, elements, props = load_deck(deck); offsets = {}
    with (workspace/(PACKAGE+'offset_state_table.csv')).open() as handle:
        for row in csv.reader(x for x in handle if not x.lstrip().startswith('#')):
            if row:
                vals = list(map(float, row)); eid = int(vals[0])
                if len(vals) != 17 or eid in offsets or eid != vals[0]: raise ValueError('Invalid offset row')
                offsets[eid] = vals[1:]
    if set(offsets) != set(elements): raise ValueError('Incomplete offset coverage')
    measurements, discrepancy = analyze(nodes, elements, offsets, props, step_one_constraints(deck, elements))
    reference_error = abs(measurements['phase_before_mechanical_inf_kN'] - prior['measurements']['phase_residual_inf_kN'])
    measurements['prior_kkt_residual_difference_kN'] = reference_error
    if reference_error > TOLERANCES['residual_kN']: raise ValueError('Established KKT basis not reproduced')
    return dict(schema=1, task_id='F1597', operation=OPERATION, verification_passed=True,
        measurements=measurements, tolerances=TOLERANCES, first_verified_discrepancy=discrepancy,
        source_contract='Package72 EF92ED58 JTYPE1/2; UEXTERNALDB LOP0/1/2; zero incremental DOFs',
        finding='Mapped mechanical residual and history max-update measured; phase-before/after-mechanical orders compared. Classification: '+discrepancy['classification'],
        limitation='Read-only reconstruction, not an Abaqus execution trace or re-equilibration solve. Actual solver call order, evolving increments, conservation and transfer correction remain unqualified.',
        next_operation='Review the measured mechanical/history discrepancy and obtain an authentic UEL call trace before choosing a coupled transfer correction.', sources=hashes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    result = probe(args.workspace.resolve()); args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        if json.loads(args.output.read_text()) != result: raise ValueError('Existing evidence differs; refusing overwrite')
    else:
        args.output.write_bytes((json.dumps(result, indent=2)+'\n').encode())
    print(json.dumps(result))
