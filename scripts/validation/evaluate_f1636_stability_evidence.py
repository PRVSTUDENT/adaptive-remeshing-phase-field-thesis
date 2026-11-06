"""Read-only F1636 evidence assessment; never qualifies a numerical job."""
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P167 = "models/pandey_kumar_mode1/167_c5_package167_r3_c2_2_continuation/evidence/1419566.mmaster02/"
P163 = "models/pandey_kumar_mode1/163_c5_package163_r3_c2_1_continuation/evidence/1419499.mmaster02/"
PINS = {}


def read(relative):
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    data = path.read_bytes()
    PINS[relative] = hashlib.sha256(data).hexdigest().upper()
    return json.loads(data.decode("utf-8-sig"))


def complete_state(cp):
    u, d, h = cp["displacement"], cp["damage"], cp["history"]
    uids, dids = {v[0] for v in u}, {v[0] for v in d}
    gids = {(v[0], v[1]) for v in h}
    return {
        "nodes_u": len(u), "nodes_d": len(d), "gauss_points_h": len(h),
        "unique_matching_node_labels": len(uids) == len(u) == len(dids) == len(d) and uids == dids,
        "unique_gp_labels": len(gids) == len(h),
        "finite_fields": all(math.isfinite(float(x)) for rows in (u, d, h) for row in rows for x in row),
        "damage_bounds": all(0 <= v[1] <= 1 for v in d),
        "history_nonnegative": all(v[2] >= 0 for v in h),
        "coupled_convergence_reported": cp["coupled_convergence"] is True,
        "state_identity_hash_is_pinned": True,
        "energy_stability": "UNRESOLVED",
        "independent_acceptance_inferred_from_file_presence": False,
    }


def main():
    definition = read("project_coordination/task_definitions/F1636-METHOD-C-C6-STABILITY-HYPOTHESIS-EVALUATION.json")
    assert definition["max_new_pbs_submissions"] == 0
    for relative, expected in definition["evidence_sources"].items():
        path = ROOT / relative
        assert path.is_file(), relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        assert actual == expected, f"Registered evidence changed: {relative}"
        PINS[relative] = actual
    trajectory = read("results/validation/f1631_early_divergence_forensics_summary.json")
    pair = read("results/validation/f1630_paired_execution_summary.json")
    cp02 = read(P163 + "converged_checkpoint_02.json")
    cp03 = read(P167 + "converged_checkpoint_03.json")
    cp03_summary = read(P167 + "c5_forward_continuation_c2_2_summary.json")
    cp02_new = read("results/validation/package163_r3_c5_continuation_acceptance_report.json")
    cp02_old = read("results/validation/package163_r3_acceptance_evaluation.json")
    iterations = trajectory["iterations"]
    rows = []
    for key, v in iterations.items():
        rows.append({"outer": int(key), "delta_d": v["telemetry_parity"]["telem_delta_d"],
                     "delta_d_over_tolerance": v["telemetry_parity"]["telem_delta_d"] / 1e-5,
                     "active_nodes": v["pdas_and_kkt_diagnostics"]["pdas_active_count"],
                     "force_energy": v["force_and_energy"],
                     "crack_tip_x_d_ge_0p90_mm": v["damage_and_crack_tip"]["crack_tip_x_d_ge_0p90_mm"],
                     "max_damage": v["damage_and_crack_tip"]["d_relaxed_max"]})
    donor_split = trajectory["donor_reference"]
    split_comparison = {}
    for historical, authentic in [("elastic_energy_kNmm", "elastic_energy_kNmm"),
                                  ("fracture_energy_kNmm", "fracture_energy_kNmm"),
                                  ("total_energy_kNmm", "total_energy_kNmm")]:
        a, b = donor_split[historical], cp03_summary[authentic]
        split_comparison[historical] = {"f1631_reference": a, "checkpoint03_runtime_summary": b,
                                       "difference_kNmm": a-b, "difference_pct_runtime": 100*(a-b)/abs(b)}
    output = {
        "schema": 1, "task_id": definition["task_id"], "executor": "codex",
        "operation": "READ_ONLY_SCIENTIFIC_EVALUATION", "new_pbs_submissions": 0,
        "hypothesis_verdict": "INSUFFICIENT_EVIDENCE",
        "hypothesis": "Held-load fracture instability dominates C6 nonconvergence; an earlier equilibrated C5 donor may yield a stable nonmatching transfer.",
        "supported_observations": [
            "Localized damage/crack growth and force loss occur along the failed outer-iteration path.",
            "Neither arm is a converged C6 equilibrium; Anderson accepted no accelerated steps, so equality of the arms does not compare two distinct convergent algorithms.",
            "Every sampled outer state fails the damage increment tolerance; early force/total-energy agreement is not donor acceptance.",
        ],
        "causal_limits": [
            "A nonstationary iteration trajectory cannot prove absence of a nearby equilibrium or negative second variation at an accepted equilibrium.",
            "Phase-subproblem KKT is conditional on its supplied history; it is not joint mechanical-phase stationarity or energy stability.",
            "No matched alternative convergent solver or admissible energy-stability test is present in the pinned evidence.",
            "Changing to an earlier donor changes the scientific experiment and requires independent review; no substitution is approved here.",
        ],
        "sampled_trajectory": rows,
        "minimum_sampled_delta_d": min(x["delta_d"] for x in rows),
        "no_sampled_damage_increment_pass": all(x["delta_d"] > 1e-5 for x in rows),
        "paired_execution": pair,
        "donor_component_energy_discrepancy": split_comparison,
        "energy_split_interpretation": "F1631 donor split disagrees with authentic CP03 runtime summary while total agrees. Preserve historical evidence; component-based mechanism inference needs reconciliation.",
        "checkpoint02": {"state": complete_state(cp02), "uy_mm": cp02["target_uy_mm"],
                         "outer": cp02["outer_iteration"], "runtime_checkpoint_sha256": PINS[P163+"converged_checkpoint_02.json"],
                         "matches_acceptance_report_pin": PINS[P163+"converged_checkpoint_02.json"] == cp02_new["checkpoint_02_sha256"],
                         "later_referenceA_acceptance": cp02_new["physical_gate_evaluation"],
                         "historical_reference_parity": cp02_old["reference_parity"],
                         "receiver_stability_or_suitability": "UNRESOLVED"},
        "checkpoint03": {"state": complete_state(cp03), "uy_mm": cp03["target_uy_mm"],
                         "outer": cp03["outer_iteration"], "runtime_acceptance": cp03_summary,
                         "receiver_stability_or_suitability": "UNRESOLVED"},
        "next_reviewable_experiment": {
            "status": "PROPOSAL_ONLY_NOT_REGISTERED_OR_QUALIFIED",
            "candidate": "Transfer coherent authentic CP02 u,d,H onto the existing C6 receiver, then test the unchanged held-load coupled gates.",
            "prediction": "If terminal-load proximity is the decisive factor, the earlier-load candidate should reach the unchanged coupled tolerances with no healing and <=2% force/total-energy discrepancy. Failure with the same localization weakens this donor-selection remedy.",
            "controls": "Preserve frozen UEL, C6 mesh, transfer operator, algorithm, tolerances, once-only accounting and standing resources. Existing CP03 failure is historical comparator; do not rerun it blindly.",
            "prerequisites": "Reconcile the donor energy split and CP02 reference provenance; independently review donor choice; then exact package qualification, datacheck, notifications and live resources. Scope remains zero PBS here.",
        },
        "verification_passed": True, "scientific_production_accepted": False,
        "evidence_sources": PINS,
    }
    assert output["no_sampled_damage_increment_pass"]
    assert cp03_summary["physical_acceptance"] == "PASS"
    assert split_comparison["total_energy_kNmm"]["difference_kNmm"] == 0
    target = ROOT / "results/validation/f1636_stability_evidence.json"
    if target.exists():
        raise FileExistsError("Preserve completed F1636 evidence; do not blindly overwrite")
    target.write_text(json.dumps(output, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"verdict": output["hypothesis_verdict"], "minimum_sampled_delta_d": output["minimum_sampled_delta_d"],
                      "donor_energy_split": split_comparison, "output": str(target)}, indent=2))


def reconcile():
    """Independent Q4 integration of the frozen UEL's stored energies."""
    import ast
    package = "models/pandey_kumar_mode1/167_c5_package167_r3_c2_2_continuation/"
    source_paths = [package + "f42_mixed_uel.for", package + "M1_C5_PACKAGE167_C2_2_CONTINUATION.inp",
                    "scripts/validation/reconstruct_f1631_early_divergence_forensics.py",
                    "scripts/state_transfer/driver_package167_c5_continuation.py",
                    "scripts/state_transfer/driver_package171_c6_coupled_pdas.py",
                    "scripts/state_transfer/driver_package171_r12_c6_coupled_pdas.py"]
    texts = {}
    for relative in source_paths:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        PINS[relative] = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        texts[relative] = path.read_text(encoding="utf-8-sig")
    assert PINS[package + "f42_mixed_uel.for"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    legacy_tree = ast.parse(texts[source_paths[2]])
    legacy_dict = next(n.value for n in legacy_tree.body
                       if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DONOR_REF" for t in n.targets))
    legacy = {ast.literal_eval(k): ast.literal_eval(v) for k, v in zip(legacy_dict.keys, legacy_dict.values)
              if isinstance(v, ast.Constant)}
    nodes, elements, mode = {}, {}, None
    for line in texts[source_paths[1]].splitlines():
        s = line.strip()
        if not s or s.startswith("**"):
            continue
        if s.startswith("*"):
            upper = s.upper()
            mode = "node" if upper == "*NODE" or upper.startswith("*NODE,") else (
                "element" if upper.startswith("*ELEMENT,") and "TYPE=U1" in upper else None)
            continue
        if mode == "node":
            v = [x.strip() for x in s.split(",")]
            if int(v[0]) < 999999:
                nodes[int(v[0])] = (float(v[1]), float(v[2]))
        elif mode == "element":
            v = [int(x.strip()) for x in s.split(",") if x.strip()]
            assert len(v) == 5
            elements[v[0]] = v[1:]
    assert len(nodes) == 13278 and len(elements) == 12996
    cp = read(P167 + "converged_checkpoint_03.json")
    summary = read(P167 + "c5_forward_continuation_c2_2_summary.json")
    telemetry = read(P167 + "live_iteration_telemetry.json")
    old = read("results/validation/f1631_early_divergence_forensics_summary.json")
    for key in ("elastic_energy_kNmm", "fracture_energy_kNmm", "total_energy_kNmm"):
        assert legacy[key] == old["donor_reference"][key]
    u = {v[0]: v[1:] for v in cp["displacement"]}
    damage = dict(cp["damage"])
    assert set(nodes) == set(u) == set(damage)
    elastic = fracture = area = 0.0
    minimum_det = float("inf")
    a = 1 / math.sqrt(3)
    young, nu, gc, length, residual = 210.0, .3, .0027, .0075, 1e-7
    c11 = young*(1-nu)/((1+nu)*(1-2*nu))
    c12 = young*nu/((1+nu)*(1-2*nu))
    c33 = young/(2*(1+nu))
    for conn in elements.values():
        xy = [nodes[n] for n in conn]
        dn = [damage[n] for n in conn]
        degradation = (1-sum(dn)/4)**2 + residual
        for xi, eta in [(-a,-a),(a,-a),(a,a),(-a,a)]:
            n = [.25*(1-xi)*(1-eta), .25*(1+xi)*(1-eta), .25*(1+xi)*(1+eta), .25*(1-xi)*(1+eta)]
            dx = [-.25*(1-eta), .25*(1-eta), .25*(1+eta), -.25*(1+eta)]
            de = [-.25*(1-xi), -.25*(1+xi), .25*(1+xi), .25*(1-xi)]
            j11=sum(p[0]*v for p,v in zip(xy,dx));j12=sum(p[0]*v for p,v in zip(xy,de))
            j21=sum(p[1]*v for p,v in zip(xy,dx));j22=sum(p[1]*v for p,v in zip(xy,de))
            det=j11*j22-j12*j21
            assert det > 0
            minimum_det=min(minimum_det,det)
            gx=[(j22*x-j21*y)/det for x,y in zip(dx,de)]
            gy=[(-j12*x+j11*y)/det for x,y in zip(dx,de)]
            ex=sum(g*u[nid][0] for g,nid in zip(gx,conn))
            ey=sum(g*u[nid][1] for g,nid in zip(gy,conn))
            gamma=sum(y*u[nid][0]+x*u[nid][1] for x,y,nid in zip(gx,gy,conn))
            elastic += det*.5*degradation*(c11*(ex*ex+ey*ey)+2*c12*ex*ey+c33*gamma*gamma)
            dg=sum(w*d for w,d in zip(n,dn)); ddx=sum(w*d for w,d in zip(gx,dn)); ddy=sum(w*d for w,d in zip(gy,dn))
            fracture += det*gc*.5*(dg*dg/length+length*(ddx*ddx+ddy*ddy))
            area += det
    table=[]
    for name,reconstructed,key in [("elastic",elastic,"elastic_energy_kNmm"),("fracture",fracture,"fracture_energy_kNmm"),("total",elastic+fracture,"total_energy_kNmm")]:
        actual=summary[key]; reported=old["donor_reference"][key]
        table.append(dict(component=name,units="kN mm",independent_quadrature=reconstructed,runtime_summary=actual,
                          f1631_hardcoded=reported,relative_error_vs_runtime=abs(reconstructed-actual)/abs(actual),
                          hardcoded_difference=reported-actual))
    output={"schema":1,"task_id":"F1636-METHOD-C-C6-STABILITY-HYPOTHESIS-EVALUATION",
            "classification":"DEFECT_CONFIRMED" if max(x["relative_error_vs_runtime"] for x in table)<1e-5 else "INSUFFICIENT_EVIDENCE",
            "defect":"F1631 DONOR_REF uses an unsupported elastic/fracture split for named CP03; runtime and independent frozen-formulation quadrature disagree with those constants.",
            "source_trace":"F1631 hard-coded DONOR_REF -> summary donor_reference. CP03 driver takes endpoint elastic_kNmm/fracture_kNmm -> runtime summary; UEL integrates strain/fracture energies separately. CP03 checkpoint itself stores total energy and full u,d,H, not elastic/fracture components.",
            "formulas":{"elastic":"Integral 0.5*((1-mean_element_nodal_d)^2+k)*epsilon_eng^T*C_plane_strain*epsilon_eng dA",
                        "fracture":"Integral Gc/2*(d(x)^2/l0+l0*|grad d(x)|^2) dA",
                        "quadrature":"Four unit-weight Q4 Gauss points; reference undeformed coordinates; thickness 1 mm",
                        "history":"H drives phase residuals/irreversibility but is not substituted for elastic strain energy or fracture energy in these stored-energy integrals"},
            "material":{"E_kN_mm2":young,"nu":nu,"Gc_kN_mm":gc,"l0_mm":length,"k":residual},
            "state":{"job":"1419566.mmaster02","checkpoint":"03","outer":cp["outer_iteration"],"uy_mm":cp["target_uy_mm"],
                     "elements":len(elements),"nodes":len(nodes),"integration_points":4*len(elements),"area_mm2":area,"minimum_detJ":minimum_det},
            "comparison":table,"runtime_telemetry_final":telemetry[-1],
            "unsupported_decomposition_reconstructable":False,
            "missing_provenance":"No authentic alternative state, energy definition or quadrature provenance supplied for the two F1631 constants; equal sums are not provenance.",
            "implications":"Historical total-energy acceptance and failed C6 coupled verdict are unchanged. Correct component attribution in a companion record; do not silently rewrite history or infer physical instability. No donor substitution approved.",
            "new_pbs_submissions":0,"scientific_production_accepted":False,"evidence_sources":PINS}
    target=ROOT/"results/validation/f1636_donor_energy_reconciliation.json"
    if target.exists():raise FileExistsError(target)
    target.write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"classification":output["classification"],"comparison":table},indent=2))


if __name__ == "__main__":
    reconcile() if sys.argv[1:] == ["--reconcile-donor-energy"] else main()
