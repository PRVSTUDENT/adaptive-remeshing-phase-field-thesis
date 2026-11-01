"""R6 predecessor assessment from saved solver endpoints; no interpolation/solver runs.

This is an assessment tool, not an independent scientific approval or execution
permission. Missing exact-load reference leaves acceptance UNVERIFIED.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.state_transfer.driver_package150_c1_2_continuation import StageC12ContinuationController
from scripts.state_transfer.driver_package146_147_pdas_continuation import PDASReEquilibrationSolver, driving_history

TARGET = 0.0018603125442191958
REL = 'models/pandey_kumar_mode1/'
CHECKPOINT = REL + '157_c4_package157_c1_2_continuation_r6/initial_checkpoint_01.json'
ENDPOINTS = 'results/validation/package157_r6_saved_endpoints/'
REFERENCE = REL + '75_candidate_donor_h0025/evidence_1416259/'


def load(path):
    if not path.is_file():
        raise ValueError('Missing saved evidence: ' + str(path))
    return json.loads(path.read_text(encoding='utf-8-sig'))


def unique(rows, width):
    if any(len(row) != width for row in rows):
        raise ValueError('Malformed saved state rows')
    values = {int(row[0]): tuple(float(x) for x in row[1:]) for row in rows}
    if len(values) != len(rows) or any(not math.isfinite(x) for val in values.values() for x in val):
        raise ValueError('Duplicate or nonfinite saved nodal state')
    return values


def exact_reference(rows, target):
    # Exact prescribed saved load. No nearest neighbour, interpolation or
    # silently invented load tolerance is permitted for this requested review.
    return [row for row in rows if float(row['u_top_mm']) == target]


def assess(root=ROOT):
    root = Path(root)
    files = [CHECKPOINT, ENDPOINTS+'outer_90_endpoint.json', ENDPOINTS+'outer_91_endpoint.json',
             REFERENCE+'donor_h0025_rf_curve.csv', REFERENCE+'uel_energy_balance.csv']
    checkpoint, old, end = [load(root/p) for p in files[:3]]
    if checkpoint['target_uy_mm'] != TARGET or end['rp_u2'] != TARGET or old['rp_u2'] != TARGET:
        raise ValueError('Saved solver/checkpoint load mismatch')
    package = root / (REL+'157_c4_package157_c1_2_continuation_r5')
    controller = StageC12ContinuationController(package, package/'unused_assessment',
        root/'scripts/validation/extract_package148_iteration.py')
    controller.load()  # Verifies manifest, original UEL, topology and full baseline.
    current, previous = unique(end['nodes'], 4), unique(old['nodes'], 4)
    u = unique(checkpoint['displacement'], 3)
    d = {n: row[0] for n, row in unique(checkpoint['damage'], 2).items()}
    expected_nodes = set(controller.mesh.nodes)
    if any(set(v) != expected_nodes for v in (current, previous, u, d)):
        raise ValueError('Saved nodal coverage differs from physical mesh')
    if len(expected_nodes) != 7265:
        raise ValueError('Unexpected C4 physical node count')
    h_rows = checkpoint['history']
    h = {(int(e), int(g)): float(v) for e,g,v in h_rows}
    expected_gp = {(e,g) for e in controller.mesh.elements for g in range(1,5)}
    if len(h_rows) != len(h) or set(h) != expected_gp or len(h) != 28224:
        raise ValueError('Duplicate/missing checkpoint integration points')
    if any(not math.isfinite(v) for v in h.values()):
        raise ValueError('Nonfinite checkpoint history')
    current_u = {n: row[:2] for n,row in current.items()}
    previous_u = {n: row[:2] for n,row in previous.items()}
    actual_h = driving_history(controller.mesh, current_u, controller.h0)
    previous_h = driving_history(controller.mesh, previous_u, controller.h0)
    original_checkpoint_path = REL+'157_c4_package157_c1_2_continuation_r5/converged_checkpoint_01.json'
    original_checkpoint = load(root/original_checkpoint_path)
    original_h = {(int(e),int(g)): float(v) for e,g,v in original_checkpoint['history']}
    if set(original_h) != expected_gp or len(original_checkpoint['history']) != len(original_h):
        raise ValueError('Authentic original checkpoint history incomplete')
    solver = PDASReEquilibrationSolver(controller.mesh, controller.d0, controller.h0)
    solver.h_gp = actual_h
    kkt = solver.kkt(d)
    measurements = dict(
        target_uy_mm=TARGET, nodes_checked=len(d), displacement_values_checked=2*len(u),
        history_values_checked=len(h),
        checkpoint_displacement_max_difference=max(abs(u[n][i]-current_u[n][i]) for n in u for i in (0,1)),
        checkpoint_damage_max_difference=max(abs(d[n]-current[n][2]) for n in d),
        checkpoint_history_max_difference=max(abs(h[k]-actual_h[k]) for k in h),
        checkpoint_history_vs_saved_checkpoint_max_difference=max(abs(h[k]-original_h[k]) for k in h),
        delta_h_MPa=max(abs(actual_h[k]-previous_h[k]) for k in h),
        delta_d=max(abs(current[n][2]-previous[n][2]) for n in d),
        delta_u_mm=max(abs(current_u[n][i]-previous_u[n][i]) for n in u for i in (0,1)),
        dual_error=kkt['dual_error'], free_error=kkt['free_error'], complementarity=kkt['complementarity'],
        min_delta_d=min(d[n]-controller.d0[n] for n in d),
        min_delta_h_MPa=min(h[k]-controller.h0[k] for k in h),
        min_damage=min(d.values()), max_damage=max(d.values()),
        reaction_force_kN=end['rf2_kN'],
        raw_total_energy_kNmm=end['elastic_kNmm']+end['fracture_kNmm'])
    gates = dict(
        full_state_coverage=True,
        checkpoint_matches_saved_solver_state=all(measurements[k] == 0 for k in (
            'checkpoint_displacement_max_difference','checkpoint_damage_max_difference',
            'checkpoint_history_vs_saved_checkpoint_max_difference')),
        delta_h=measurements['delta_h_MPa'] <= 1e-6,
        delta_d=measurements['delta_d'] <= 1e-5,
        delta_u=measurements['delta_u_mm'] <= 1e-9,
        signed_dual_zero=measurements['dual_error'] == 0,
        free_residual=measurements['free_error'] <= 1e-6,
        complementarity=measurements['complementarity'] <= 1e-6,
        no_healing=measurements['min_delta_d'] >= -1e-6,
        history_monotone=measurements['min_delta_h_MPa'] >= 0,
        damage_bounds=0 <= measurements['min_damage'] <= measurements['max_damage'] <= 1)
    with (root/files[3]).open() as stream:
        rows = list(csv.DictReader(stream))
    matches = exact_reference(rows, TARGET)
    reference = dict(status='EXACT_LOAD_REFERENCE_MISSING', source=files[3],
                     exact_matches=len(matches), interpolation_used=False,
                     nearest_saved_rows=sorted(rows,key=lambda r:abs(float(r['u_top_mm'])-TARGET))[:2])
    if len(matches) == 1:
        ref = matches[0]
        with (root/files[4]).open() as stream:
            energy_rows = [r for r in csv.reader(stream) if len(r)>=7 and r[1].strip()==str(int(ref['inc']))]
        if len(energy_rows) == 1:
            force = float(ref['rf2_kN']); energy = float(energy_rows[0][6])
            if not all(math.isfinite(v) and v != 0 for v in (force,energy)):
                raise ValueError('Invalid saved exact reference quantities')
            force_error = abs(measurements['reaction_force_kN']-force)/abs(force)
            energy_error = abs(measurements['raw_total_energy_kNmm']-energy)/abs(energy)
            reference.update(status='EXACT_LOAD_REFERENCE_AVAILABLE', reaction_force_kN=force,
                raw_total_energy_kNmm=energy, force_discrepancy=force_error, energy_discrepancy=energy_error)
            gates.update(force=force_error<=0.05, raw_energy=energy_error<=0.02)
    if 'force' not in gates:
        gates.update(force=None, raw_energy=None)
    status = 'FAIL' if any(v is False for v in gates.values()) else 'PASS' if all(v is True for v in gates.values()) else 'UNVERIFIED'
    files += [str(p.relative_to(root)).replace('\\','/') for p in package.iterdir()
              if p.name in ('PACKAGE_MANIFEST.json','M1_C4_PACKAGE150_C1_2_CONTINUATION.inp',
                  'f42_mixed_uel.for','nodal_phase_field_initial.csv','d_lower_bounds.csv')]
    files += [original_checkpoint_path,'scripts/validation/evaluate_package157_r6_checkpoint.py',
              'scripts/state_transfer/driver_package150_c1_2_continuation.py',
              'scripts/state_transfer/driver_package146_147_pdas_continuation.py',
              'scripts/state_transfer/c3_int_to_c4_spatial_mapping.py']
    return dict(schema=1,kind='SAVED_SOLVER_CHECKPOINT_ASSESSMENT',physical_acceptance=status,
        measurements=measurements,gates=gates,reference=reference,
        sources={p:hashlib.sha256((root/p).read_bytes()).hexdigest().upper() for p in files},
        solver_odb_hashes=[old['odb_sha256'],end['odb_sha256']],
        numerical_approval=False,scientific_review='Independent review still required; this tool never signs a review')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',required=True)
    args=parser.parse_args(); output=Path(args.output)
    if output.exists():
        raise SystemExit('Preserve existing assessment')
    result=assess()
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='sources'},indent=2))
