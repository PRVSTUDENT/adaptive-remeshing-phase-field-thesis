"""Read-only F1636 evidence assessment; never qualifies a numerical job."""
import hashlib
import json
import math
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


if __name__ == "__main__":
    main()
