#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
driver_r14_autonomous_continuation.py
Autonomous (oracle-free) active-set continuation driver in genuine Abaqus/Standard 2023.
Package: PACKAGE_108_R14_C3_AUTONOMOUS_ACTIVE_SET
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Defect Repair: Restored canonical AT2 sign convention in unified 12-DOF UEL.
"""

import sys
import os
import subprocess
import json
import math
from odbAccess import openOdb

def log(msg):
    print("[R14-DRIVER] " + str(msg))
    sys.stdout.flush()

def load_nodal_d0():
    nodal_d0 = {}
    with open("stage_a_all_d0_boundary_cards.inc", "r") as f:
        for line in f:
            line = line.strip()
            if line:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 4:
                    nid = int(parts[0])
                    d0 = float(parts[3])
                    nodal_d0[nid] = d0
    return nodal_d0

def write_active_boundary_cards(active_nodes, nodal_d0):
    with open("active_set_boundary_cards.inc", "w") as f:
        for nid in sorted(active_nodes):
            f.write("%d, 3, 3, %.8f\n" % (nid, nodal_d0[nid]))

def run_abaqus_iteration(iter_idx):
    job_name = "M1_C3_ACTIVE_SET_R14_IT%d" % iter_idx
    inp_name = "M1_C3_ACTIVE_SET_R14_CONTINUATION.inp"
    user_sub = "f42_unified_12dof_active_set_uel.for"

    cmd = ["abaqus", "job=" + job_name, "input=" + inp_name, "user=" + user_sub, "cpus=1", "interactive"]
    log("Executing Abaqus command: " + " ".join(cmd))

    ret = subprocess.call(cmd)
    log("Abaqus solver process exited with return code: %d" % ret)
    return job_name, ret

def extract_iteration_results(job_name, active_nodes, nodal_d0, tau_release, tau_heal):
    odb_path = job_name + ".odb"
    if not os.path.exists(odb_path):
        raise RuntimeError("ODB file not found: " + odb_path)

    odb = openOdb(odb_path, readOnly=True)

    # Inspect Step 2 (Inc1-Coupled)
    if "Inc1-Coupled" not in odb.steps:
        odb.close()
        raise RuntimeError("Step Inc1-Coupled missing in ODB")

    step2 = odb.steps["Inc1-Coupled"]
    if len(step2.frames) == 0:
        odb.close()
        raise RuntimeError("No frames found in Step 'Inc1-Coupled'")

    last_frame = step2.frames[-1]

    # Extract energies
    energies = {}
    for key, reg in step2.historyRegions.items():
        for e_key in reg.historyOutputs.keys():
            series = reg.historyOutputs[e_key]
            if len(series.data) > 0:
                energies[e_key] = series.data[-1][1]

    # Mandatory field output checks (Repository-compatible membership test)
    if "U" not in last_frame.fieldOutputs:
        odb.close()
        raise RuntimeError("Mandatory FieldOutput 'U' missing in ODB frame")
    if "RF" not in last_frame.fieldOutputs:
        odb.close()
        raise RuntimeError("Mandatory FieldOutput 'RF' missing in ODB frame")

    u_field = last_frame.fieldOutputs["U"]
    rf_field = last_frame.fieldOutputs["RF"]

    rf2_rp = None
    u2_rp = None
    u_vals = {}
    rf_vals = {}

    for val in u_field.values:
        nid = val.nodeLabel
        if nid == 999999:
            u2_rp = float(val.data[1])
        if len(val.data) >= 3:
            u_vals[nid] = (float(val.data[0]), float(val.data[1]), float(val.data[2]))

    for val in rf_field.values:
        nid = val.nodeLabel
        if nid == 999999:
            rf2_rp = float(val.data[1] * 1000.0) # Convert kN to N
        if len(val.data) >= 3:
            rf_vals[nid] = (float(val.data[0]), float(val.data[1]), float(val.data[2]))

    odb.close()

    if u2_rp is None:
        raise RuntimeError("Reference point 999999 U2 not found in field output U")
    if rf2_rp is None:
        raise RuntimeError("Reference point 999999 RF2 not found in field output RF")

    # Postprocess active set
    release_candidates = []
    activate_candidates = []
    healing_nodes = []
    d_max = 0.0

    min_lambda = 0.0
    max_lambda = 0.0
    max_phase_res = 0.0

    active_set = set(active_nodes)

    for nid, d0 in nodal_d0.items():
        u_tuple = u_vals.get(nid, (0.0, 0.0, d0))
        rf_tuple = rf_vals.get(nid, (0.0, 0.0, 0.0))
        d_val = u_tuple[2]
        rf3_val = rf_tuple[2]

        if d_val > d_max:
            d_max = d_val

        # Active node check
        if nid in active_set:
            if rf3_val < min_lambda:
                min_lambda = rf3_val
            if rf3_val > max_lambda:
                max_lambda = rf3_val

            # KKT release criterion: lambda = RF3 < -tau_release
            if rf3_val < -tau_release:
                release_candidates.append(nid)
        else:
            # Free node check: healing & residual
            delta_d = d_val - d0
            if delta_d < -tau_heal:
                activate_candidates.append(nid)
                healing_nodes.append((nid, delta_d))

            if abs(rf3_val) > max_phase_res:
                max_phase_res = abs(rf3_val)

    return {
        "job_name": job_name,
        "rf2_rp_N": rf2_rp,
        "u2_rp_mm": u2_rp,
        "energies": energies,
        "allse_mJ": energies.get("ALLSE", 0.0) * 1000.0,
        "d_max": d_max,
        "min_lambda": min_lambda,
        "max_lambda": max_lambda,
        "max_phase_res": max_phase_res,
        "release_count": len(release_candidates),
        "activate_count": len(activate_candidates),
        "release_candidates": release_candidates,
        "activate_candidates": activate_candidates,
        "healing_count": len(healing_nodes)
    }

def main():
    log("Starting R14 Autonomous Active-Set Continuation Driver")

    nodal_d0 = load_nodal_d0()
    n_nodes = len(nodal_d0)
    log("Loaded %d nodes with d0 lower bounds" % n_nodes)

    # Physical tolerances
    tau_release = 1.0e-9  # Release active constraint if lambda = RF3 < -1.0e-9 kN/mm
    tau_heal    = 1.0e-8  # Reactivate free constraint if healing d < d0 - 1.0e-8
    max_outer_iters = 8

    # Outer Iteration 1: Start from ALL nodes in active set
    active_nodes = set(nodal_d0.keys())
    iteration_history = []
    converged = False
    fail_fast_triggered = None

    for outer_iter in range(1, max_outer_iters + 1):
        log("=======================================================")
        log("--- OUTER ACTIVE-SET ITERATION %d (Active: %d, Free: %d) ---" %
            (outer_iter, len(active_nodes), n_nodes - len(active_nodes)))
        log("=======================================================")

        # Stage-A Checkpoint Reset Semantics:
        # Write fresh active_set_boundary_cards.inc
        write_active_boundary_cards(active_nodes, nodal_d0)

        # Run fresh Abaqus continuation job
        job_name, ret_code = run_abaqus_iteration(outer_iter)
        if ret_code != 0:
            fail_fast_triggered = "SOLVER_ABORT_EXIT_%d" % ret_code
            log("FAIL-FAST: " + fail_fast_triggered)
            break

        # Extract ODB telemetry
        try:
            res = extract_iteration_results(job_name, active_nodes, nodal_d0, tau_release, tau_heal)
        except Exception as e:
            fail_fast_triggered = "TELEMETRY_EXTRACTION_ERROR: %s" % str(e)
            log("FAIL-FAST: " + fail_fast_triggered)
            break

        log("Iteration %d Results:" % outer_iter)
        log("  RF2: %.4f N | ALLSE: %.6f mJ | d_max: %.6f" % (res["rf2_rp_N"], res["allse_mJ"], res["d_max"]))
        log("  Min Lambda (Active): %.3e kN/mm | Max Residual (Free): %.3e kN/mm" %
            (res["min_lambda"], res["max_phase_res"]))
        log("  Release candidates: %d | Activate candidates: %d | Healing: %d" %
            (res["release_count"], res["activate_count"], res["healing_count"]))

        iteration_history.append({
            "outer_iter": outer_iter,
            "job_name": job_name,
            "active_node_count": len(active_nodes),
            "free_node_count": n_nodes - len(active_nodes),
            "rf2_rp_N": res["rf2_rp_N"],
            "u2_rp_mm": res["u2_rp_mm"],
            "allse_mJ": res["allse_mJ"],
            "d_max": res["d_max"],
            "min_lambda": res["min_lambda"],
            "max_lambda": res["max_lambda"],
            "max_phase_res": res["max_phase_res"],
            "release_count": res["release_count"],
            "activate_count": res["activate_count"],
            "healing_count": res["healing_count"],
            "energies": res["energies"]
        })

        # Check Fail-Fast Conditions
        # 1. Damage upper bound violation
        if res["d_max"] > 1.0 + 1.0e-5:
            fail_fast_triggered = "DAMAGE_OVERFLOW_DMAX_%.4f" % res["d_max"]
            log("FAIL-FAST: " + fail_fast_triggered)
            break

        # 2. Severe healing divergence
        if res["healing_count"] > 0:
            log("WARNING: %d nodes exhibited healing in free set" % res["healing_count"])

        # 3. Target displacement error
        target_u2 = 0.00196610735
        if abs(res["u2_rp_mm"] - target_u2) > 1.0e-7:
            fail_fast_triggered = "KINEMATIC_INCONSISTENCY_U2_%.8f" % res["u2_rp_mm"]
            log("FAIL-FAST: " + fail_fast_triggered)
            break

        # 4. Check Convergence (Binary closure)
        if res["release_count"] == 0 and res["activate_count"] == 0:
            log("--> ACTIVE-SET CONVERGED AT ITERATION %d!" % outer_iter)
            converged = True
            break

        # 5. Update active set
        new_active = set(active_nodes)
        for nid in res["release_candidates"]:
            new_active.discard(nid)
        for nid in res["activate_candidates"]:
            new_active.add(nid)

        # Check for oscillation / flip-flop
        if len(iteration_history) >= 2:
            prev_counts = (iteration_history[-2]["active_node_count"], iteration_history[-2]["release_count"])
            curr_counts = (len(active_nodes), res["release_count"])
            if prev_counts == curr_counts and res["release_count"] > 0:
                log("CYCLE WARNING: Active set count unchanged across iterations")

        active_nodes = new_active

    # Final summary output
    final_status = "CONVERGED" if converged else ("FAIL_FAST_" + fail_fast_triggered if fail_fast_triggered else "ACTIVE_SET_NOT_CONVERGED")
    log("Driver completed with status: " + final_status)

    summary = {
        "schema": 1,
        "package": "PACKAGE_108_R14_C3_AUTONOMOUS_ACTIVE_SET",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "status": final_status,
        "converged": converged,
        "fail_fast_triggered": fail_fast_triggered,
        "outer_iterations_completed": len(iteration_history),
        "tau_release_kN_mm": tau_release,
        "tau_heal": tau_heal,
        "history": iteration_history,
        "final_metrics": iteration_history[-1] if iteration_history else None
    }

    with open("r14_autonomous_continuation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    log("Saved r14_autonomous_continuation_summary.json successfully.")

if __name__ == "__main__":
    main()
