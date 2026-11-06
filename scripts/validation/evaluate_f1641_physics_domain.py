"""Frozen-law evaluation on authentic elastic U; no coupled phase-field solve.

The positive-driving domain is a diagnostic, not an asserted future FPZ.
No finite damage threshold, spatial corridor, or acceptance cutoff is invented.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from scripts.validation.evaluate_f1641_local_size_support import inside, polygon_area
from scripts.validation.validate_f1641_native_mesh import read_mesh, stats

ROOT = Path(__file__).resolve().parents[2]
FROZEN = 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6'
E, NU, GC, L0 = 210., .3, .0027, .0075


def driver(strain, young=E, nu=NU):
    ex,ey,gamma = strain
    lam = young*nu/((1+nu)*(1-2*nu))
    mu = young/(2*(1+nu))
    return float(.5*lam*max(ex+ey,0)**2 + mu*(ex**2+ey**2+.5*gamma**2))


def homogeneous_damage(history, gc=GC, l0=L0):
    if history < 0:
        raise ValueError('Nonnegative history required')
    return 2*history/(gc/l0+2*history)


def kinematics(xy, u, xi=0., eta=0.):
    xy,u = np.asarray(xy)[:,:2],np.asarray(u)[:,:2]
    if len(xy) == 3:
        dn = np.array([[1.,0.,-1.],[0.,1.,-1.]])
    else:
        dn = np.array([[-(1-eta),1-eta,1+eta,-(1+eta)],
                       [-(1-xi),-(1+xi),1+xi,1-xi]])/4
    jac = dn@xy
    det = float(np.linalg.det(jac))
    if det <= 0:
        raise ValueError('Nonpositive source Jacobian')
    gradient = np.linalg.solve(jac,dn)@u
    return np.array([gradient[0,0],gradient[1,1],gradient[0,1]+gradient[1,0]]),det


def weighted_stats(values, weights):
    values,weights = np.array(values),np.array(weights)
    order = np.argsort(values)
    sums = np.cumsum(weights[order])
    result = {}
    for name,q in [('min',0),('p10',.1),('median',.5),('p90',.9),('max',1)]:
        result[name] = float(values[order[min(np.searchsorted(sums,q*sums[-1]),len(order)-1)]])
    return result


def main():
    package = ROOT/'models/pandey_kumar_mode1/176_method_a_plate_with_hole'
    uel = package/'f42_mixed_uel.for'
    if hashlib.sha256(uel.read_bytes()).hexdigest().upper() != FROZEN:
        raise ValueError('Frozen UEL changed')
    mechanics_path = ROOT/'results/validation/f1641_preanalysis_mechanics.json'
    mechanics = json.loads(mechanics_path.read_text())
    source = json.loads((ROOT/'results/validation/f1641_hole_indicator_provenance.json').read_text())
    if mechanics['source_sha256'] != source['source_sha256']:
        raise ValueError('Different preanalysis sources')
    nodes = {n['label']:n for n in mechanics['nodes']}
    source_by_id = {r['element']:r for r in source['records']}
    selected = {r['element']:r['selected'] for r in json.loads((ROOT/'results/validation/f1641_local_size_support.json').read_text())['source_cell_map']}
    component = {s:i for i,s in enumerate(mechanics['stress_components'])}
    e_source,nu_source = mechanics['source_elastic_constants']
    rows,errors = [],[]
    for elem in mechanics['elements']:
        conn = elem['connectivity']
        xy = [nodes[n]['coordinates_mm'] for n in conn]
        u = [nodes[n]['displacement_mm'] for n in conn]
        center,det = kinematics(xy,u)
        samples = elem['stress_samples']
        raw = samples[0]['data']
        if any(s['data'] != raw for s in samples):
            raise ValueError('Unequal stress samples require explicit handling')
        stress = {name:raw[i] for name,i in component.items()}
        if elem['type'] not in ('CPS3','CPS4R'):
            raise ValueError('Unexpected source constitutive mode')
        inverted = np.array([(stress['S11']-nu_source*stress['S22'])/e_source,
                             (stress['S22']-nu_source*stress['S11'])/e_source,
                             2*(1+nu_source)*stress['S12']/e_source])
        errors.append(float(np.linalg.norm(center-inverted)/max(np.linalg.norm(inverted),1e-15)))
        gp = []
        if len(conn) == 3:
            gp.append((driver(center),det*.5))
        else:
            for xi in (-1/math.sqrt(3),1/math.sqrt(3)):
                for eta in (-1/math.sqrt(3),1/math.sqrt(3)):
                    strain,det = kinematics(xy,u,xi,eta)
                    gp.append((driver(strain),det))
        area = sum(a for _,a in gp)
        r = source_by_id[elem['label']]
        rows.append(dict(element=elem['label'],type=elem['type'],area_mm2=area,
                         centroid_mm=r['centroid_mm'],miseseri=r['miseseri_max'],
                         psi_max_kn_per_mm2=max(p for p,_ in gp),
                         psi_mean_kn_per_mm2=sum(p*a for p,a in gp)/area,
                         homogeneous_d_at_psi_max=homogeneous_damage(max(p for p,_ in gp)),
                         stress_s33=stress['S33'],gp_count=len(gp),
                         center_kinematic_vs_stress_strain_relative_error=errors[-1],
                         prior_bulk90_selected=selected[elem['label']]))
    lookup = {r['element']:r for r in rows}
    polygons = [r['coordinates_mm'] for r in source['records']]
    tree = cKDTree([r['centroid_mm'] for r in source['records']])
    comparison = []
    for path in [package/'PK_HOLE_METHOD_A_PROD_PHYS.inp',
                 package/'f1641_native_1pct/PK_HOLE_F1641_1PCT_PROD_PHYS.inp']:
        ns,es = read_mesh(path)
        sizes,energy_weights = [],[]
        unresolved,unmapped = 0,0
        outside,integral = 0.,0.
        for conn in es.values():
            pts = [ns[n] for n in conn]
            center = np.mean(pts,axis=0)
            h = max(math.dist(a,b) for a,b in zip(pts,pts[1:]+pts[:1]))
            _,near = tree.query(center,k=24)
            idx = next((int(i) for i in near if inside(center,polygons[int(i)])),None)
            if idx is None:
                unmapped += 1
                continue
            r = lookup[source['records'][idx]['element']]
            if r['psi_max_kn_per_mm2'] <= 0:
                continue
            weight = polygon_area(pts)*r['psi_mean_kn_per_mm2']
            sizes.append(h)
            energy_weights.append(weight)
            integral += weight
            if h > L0/5:
                unresolved += 1
                outside += weight
        comparison.append(dict(path=str(path.relative_to(ROOT)),elements=len(es),
                               positive_driving_source_mapped_elements=len(sizes),unmapped=unmapped,
                               h_over_l0=stats(np.array(sizes)/L0),
                               fraction_h_le_l0_over5=(len(sizes)-unresolved)/len(sizes),
                               driving_energy_weighted_h_over_l0=weighted_stats(np.array(sizes)/L0,energy_weights),
                               proxy_energy_fraction_in_elements_h_above_l0_over5=outside/integral,
                               scope='Positive-driver diagnostic,not an assertion every such element belongs to required physical FPZ'))
    total = sum(r['area_mm2']*r['psi_mean_kn_per_mm2'] for r in rows)
    report = dict(schema=1,source_odb_sha256=source['source_sha256'],frozen_uel_sha256=FROZEN,
                  mechanics_sha256=hashlib.sha256(mechanics_path.read_bytes()).hexdigest().upper(),
                  actual_frozen_driver='psi=0.5*lambda*positive(exx+eyy)^2+mu*(exx^2+eyy^2+gamma_xy^2/2)',
                  phase_equation='-Gc*l0*laplacian(d)+(Gc/l0+2H)*d=2H;homogeneous d=2H/(Gc/l0+2H)',
                  finite_positive_homogeneous_initiation_threshold=False,
                  source_mode='CPS plane stress,linear intact preanalysis;production UEL uses plane-strain stiffness',
                  interpretation='Frozen-law counterfactual on elastic displacement field,NOT a converged UEL history or damage solution',
                  history='Frozen source updates H_trial=max(H_trial,psi),rollback restores committed history;no explicit nodal d>=d_old constraint observed',
                  capacity_physical_elements=150000,
                  psi_max_distribution=stats([r['psi_max_kn_per_mm2'] for r in rows]),
                  homogeneous_d_distribution=stats([r['homogeneous_d_at_psi_max'] for r in rows]),
                  source_cells_positive_driver=sum(r['psi_max_kn_per_mm2']>0 for r in rows),
                  source_cells=len(rows),stress_s33_max_abs=max(abs(r['stress_s33']) for r in rows),
                  center_strain_crosscheck_relative_error=stats(errors),
                  miseseri_vs_psi_max_spearman=float(spearmanr([r['miseseri'] for r in rows],[r['psi_max_kn_per_mm2'] for r in rows]).statistic),
                  proxy_energy_fraction_outside_rejected_bulk90=sum(r['area_mm2']*r['psi_mean_kn_per_mm2'] for r in rows if not r['prior_bulk90_selected'])/total,
                  max_psi_outside_rejected_bulk90=max(r['psi_max_kn_per_mm2'] for r in rows if not r['prior_bulk90_selected']),
                  mesh_comparison=comparison,source_cells_evaluation=rows,
                  verdict='C_EVIDENCE_INSUFFICIENT_FOR_SELECTIVE_REQUIRED_FRACTURE_DOMAIN',
                  missing_evidence='Accepted converged off-axis-hole UEL d,H,grad(d),reaction/energy histories under frozen plane-strain formulation;or independently justified localization/mesh criterion. No finite damage-initiation threshold identifies a selective domain.',
                  new_meshes=0,new_solver_runs=0,new_pbs=0)
    out = ROOT/'results/validation/f1641_physics_domain_assessment.json'
    if out.exists():
        raise ValueError('Preserve previous assessment')
    out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_cells_evaluation'},indent=2))


if __name__ == '__main__':
    main()
