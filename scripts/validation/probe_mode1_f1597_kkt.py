"""F1597 first corrective diagnostic: frozen-history lower-bound KKT feasibility.

Reconstruct the Package 72 JTYPE-1 phase block exactly at its mapped state.
This is not F1596's force/energy audit and does not qualify a corrected transfer.
H is the loaded committed offset history, before any mechanical-history update.
The lower bound is the mapped d itself. Its KKT condition is gradient >= 0,
not an unconditional zero phase residual. No solver/source/input is modified.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def phase_element(xy, damage, history, ell, gc):
    a = np.zeros((4, 4)); b = np.zeros(4)
    q = 1 / np.sqrt(3)
    for k, (xi, eta) in enumerate(((-q, -q), (q, -q), (q, q), (-q, q))):
        n = .25 * np.array([(1-xi)*(1-eta), (1+xi)*(1-eta),
                            (1+xi)*(1+eta), (1-xi)*(1+eta)])
        dn = .25 * np.array([[-(1-eta), 1-eta, 1+eta, -(1+eta)],
                              [-(1-xi), -(1+xi), 1+xi, 1-xi]])
        jac = dn @ xy
        det = np.linalg.det(jac)
        if det <= 0:
            raise ValueError("Nonpositive phase-element Jacobian")
        grad = np.linalg.solve(jac, dn)
        h = history[k]
        if h < 0 or ell <= 0 or gc <= 0:
            raise ValueError("Invalid history/material parameter")
        a += det * (gc * ell * grad.T @ grad + (gc/ell + 2*h) * np.outer(n, n))
        b += det * 2*h*n
    return a, b, a @ damage - b


def load_deck(path):
    nodes = {}; elements = {}; props = None; mode = ''
    for raw in path.read_text(encoding='utf-8-sig').splitlines():
        line = raw.strip()
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            low = line.lower().replace(' ', '')
            mode = ('nodes' if low == '*node' else
                    'elements' if low.startswith('*element,') and 'type=u1,' in low+',' else
                    'props' if low.startswith('*uelproperty,') and 'elset=phase_quads' in low else
                    'boundary' if low.startswith('*boundary') else '')
            continue
        fields = [x.strip() for x in line.split(',')]
        if mode == 'nodes':
            nodes[int(fields[0])] = [float(fields[1]), float(fields[2])]
        elif mode == 'elements':
            elements[int(fields[0])] = [int(x) for x in fields[1:5]]
        elif mode == 'props':
            props = [float(x) for x in fields]; mode = ''
        elif mode == 'boundary' and len(fields) >= 3:
            if int(fields[1]) <= 3 <= int(fields[2]):
                raise ValueError('Phase Dirichlet boundary requires an explicit constrained-DOF treatment')
    if not nodes or not elements or props is None:
        raise ValueError('Missing phase mesh/material data')
    return nodes, elements, props


def probe(workspace):
    package = workspace / 'models/pandey_kumar_mode1/72_method_c_coupled_state_transfer'
    deck = package / 'M1_EXP_COUPLED_TRANSFER_650.inp'
    table = package / 'offset_state_table.csv'
    uel = package / 'f42_experimental_offset_uel.for'
    frozen = workspace / 'models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for'
    sources = [deck, table, uel, frozen, Path(__file__).resolve()]
    for path in sources:
        if not path.is_file():
            raise FileNotFoundError(str(path))
    if hashlib.sha256(frozen.read_bytes()).hexdigest() != 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6':
        raise ValueError('Frozen production UEL hash mismatch')
    nodes, elements, props = load_deck(deck)
    offsets = {}
    with table.open(encoding='utf-8') as handle:
        for row in csv.reader(x for x in handle if not x.lstrip().startswith('#')):
            if row:
                values = [float(x) for x in row]
                if len(values) != 17 or int(values[0]) in offsets:
                    raise ValueError('Invalid/duplicate offset-state row')
                offsets[int(values[0])] = values[1:]
    if set(offsets) != set(elements):
        raise ValueError('Offset rows do not cover phase elements exactly')
    ids = sorted({n for conn in elements.values() for n in conn})
    index = {n:i for i,n in enumerate(ids)}
    a = np.zeros((len(ids), len(ids))); b = np.zeros(len(ids))
    damage = np.full(len(ids), np.nan); max_jump = 0.
    for eid, conn in sorted(elements.items()):
        values = offsets[eid]; d = np.array(values[8:12]); h = np.array(values[12:16])
        loc = [index[n] for n in conn]
        for i, v in zip(loc, d):
            if np.isfinite(damage[i]):
                max_jump = max(max_jump, abs(damage[i]-v))
            damage[i] = v
        ae, be, _ = phase_element(np.array([nodes[n] for n in conn]), d, h, props[0], props[1])
        a[np.ix_(loc, loc)] += ae; b[loc] += be
    if max_jump > 1e-11 or not np.isfinite(damage).all():
        raise ValueError('Mapped nodal damage is discontinuous/incomplete')
    gradient = a @ damage - b
    node = int(np.argmin(gradient)); eps = 1e-5
    direction = np.zeros(len(ids)); direction[node] = 1.
    energy = lambda d: .5 * d @ a @ d - b @ d
    fd = (energy(damage+eps*direction)-energy(damage-eps*direction))/(2*eps)
    err = abs(fd-gradient[node])
    if not np.isfinite(gradient).all() or err > 1e-10:
        raise ValueError(f'Phase-gradient finite-difference verification failed: {err}')
    return {
        'schema': 1, 'task_id': 'F1597',
        'operation': 'mapped_frozen_history_lower_bound_kkt_probe',
        'verification_passed': True,
        'measurements': {
            'phase_elements': len(elements), 'phase_nodes': len(ids),
            'max_nodal_mapping_jump': max_jump,
            'phase_residual_inf_kN': float(np.max(np.abs(gradient))),
            'lower_bound_kkt_violation_inf_kN': float(max(0., -gradient.min())),
            'damage_increase_descent_nodes': int(np.count_nonzero(gradient < -1e-12)),
            'positive_gradient_lower_bound_nodes': int(np.count_nonzero(gradient > 1e-12)),
            'worst_kkt_node': ids[node],
            'finite_difference_gradient_error_kN': float(err),
        },
        'finding': 'At d=d_mapped the lower-bound KKT condition is gradient>=0; negative-gradient nodes still admit feasible damage-increase descent. A nonzero positive gradient at an active lower bound is not itself a KKT violation.',
        'limitation': 'Frozen committed-H initialization diagnostic only. Mechanical/history coupling, donor comparison, upper bounds and conservation are not qualified; this is not a corrected transfer solve.',
        'next_operation': 'Review the measured KKT active-set requirements and history update before implementing a coupled constrained transfer correction.',
        'sources': {str(p.relative_to(workspace)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.workspace.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        if json.loads(args.output.read_text()) != result:
            raise ValueError('Existing result differs; preserve evidence, do not overwrite')
    else:
        args.output.write_bytes((json.dumps(result, indent=2)+'\n').encode('utf-8'))
    print(json.dumps(result))
