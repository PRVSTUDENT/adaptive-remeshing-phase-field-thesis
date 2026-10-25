"""
Candidate Package 108 Revision 16 (R16) Autonomous Active-Set Continuation Driver
================================================================================
Monolithic 12-DOF coupled UEL with safeguarded ranked batch active-set continuation.

Features:
1. Strict Stage-A checkpoint reset semantics before every trial solve.
2. Safeguarded Ranked Batch Release: sorts violating active nodes by multiplier
   lambda = RF3 ascending (strongest driving force first) and releases at most
   B_max = 20 nodes per outer iteration to prevent domain-wide compliance collapse.
3. Physically justified screening cutoff: tau_release = 5.0e-8 kN/mm separates
   physical crack-tip driving forces from far-field elastic noise (~1e-9).
4. Pointwise irreversibility guard: tau_heal = 1.0e-8 reactivates healing nodes.
5. Six fail-fast guardrails:
   - Solver non-zero return code.
   - Kinematic displacement verification (|u2 - u_target| <= 1e-7 mm; rejects partial continuation!).
   - Upper bound violation (d > 1.0 + 1e-5).
   - Severe healing divergence (d < d0 - 1e-4).
   - Cycling / oscillation detection.
   - Maximum 15 outer iterations limit (expanded from R15's 8 to test full active-set closure).
6. Traceable JSON closeout: r16_autonomous_continuation_summary.json.
"""

import os
import sys
import json
import shutil
import subprocess

def load_nodal_d0(boundary_inc_path):
    d0_dict = {}
    with open(boundary_inc_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("*") or line.startswith("**"):
                continue
            parts = line.split(",")
            if len(parts) >= 4:
                try:
                    nid = int(parts[0].strip())
                    d_val = float(parts[3].strip())
                    d0_dict[nid] = d_val
                except ValueError:
                    continue
    return d0_dict

def write_active_set_cards(output_inc_path, active_nodes, nodal_d0):
    with open(output_inc_path, "w") as f:
        f.write("** R16 Active Set Boundary Cards\n")
        f.write("** Format: node_id, dof_start, dof_end, prescribed_value\n")
        for nid in sorted(active_nodes):
            d0_val = nodal_d0[nid]
            f.write("%d, 3, 3, %.8f\n" % (nid, d0_val))

def run_abaqus_solve(job_name, inp_deck, user_sub):
    cmd = "abaqus job=%s input=%s user=%s cpus=1 interactive" % (job_name, inp_deck, user_sub)
    print("[R16-DRIVER] Executing Abaqus command: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    retcode = p.returncode
    print("[R16-DRIVER] Abaqus solver process exited with return code: %d" % retcode)
    return retcode

def extract_iteration_results(odb_path, active_nodes, nodal_d0, tau_release, tau_heal, B_max):
    from odbAccess import openOdb

    if not os.path.exists(odb_path):
        raise RuntimeError("ODB file not found: %s" % odb_path)

    odb = openOdb(odb_path)

    step_name = "Inc1-Coupled"
    if step_name not in odb.steps:
        odb.close()
        raise RuntimeError("Mandatory Step '%s' missing in ODB" % step_name)

    step = odb.steps[step_name]
    if len(step.frames) == 0:
        odb.close()
        raise RuntimeError("No frames found in step '%s'" % step_name)

    last_frame = step.frames[-1]

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
    violating_active = []
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
                violating_active.append((nid, rf3_val))
        else:
            # Free node check: healing & residual
            delta_d = d_val - d0
            if delta_d < -tau_heal:
                activate_candidates.append(nid)
            if delta_d < -1.0e-4:
                healing_nodes.append((nid, delta_d))

            phase_res = abs(rf3_val)
            if phase_res > max_phase_res:
                max_phase_res = phase_res

    # Sort violating active nodes by RF3 ascending (strongest driving force first)
    violating_active.sort(key=lambda x: x[1])

    # Safeguarded Ranked Batch: select at most B_max nodes to release
    release_candidates = [n for n, r in violating_active[:B_max]]

    metrics = {
        "u2_rp_mm": u2_rp,
        "rf2_rp_N": rf2_rp,
        "d_max": d_max,
        "min_lambda": min_lambda,
        "max_lambda": max_lambda,
        "max_phase_res": max_phase_res,
        "active_node_count": len(active_set),
        "free_node_count": len(nodal_d0) - len(active_set),
        "violating_active_total": len(violating_active),
        "release_count": len(release_candidates),
        "activate_count": len(activate_candidates),
        "healing_count": len(healing_nodes),
    }

    return metrics, release_candidates, activate_candidates, healing_nodes

def main():
    print("[R16-DRIVER] Starting R16 Autonomous Safeguarded Active-Set Continuation Driver")

    target_u_disp = 0.00196610735
    tau_release = 5.0e-8 # kN/mm (separates physical driving force ~1e-7 from elastic background ~1e-9)
    tau_heal = 1.0e-8
    B_max = 20 # Safeguarded maximum release batch size per outer iteration
    max_outer_iters = 15 # Increased from 8 to 15 to test full active-set closure

    boundary_inc = "stage_a_all_d0_boundary_cards.inc"
    active_inc = "active_set_boundary_cards.inc"
    base_inp = "M1_C3_ACTIVE_SET_R16_CONTINUATION.inp"
    user_sub = "f42_unified_12dof_active_set_uel.for"

    if not os.path.exists(boundary_inc):
        raise RuntimeError("Missing %s" % boundary_inc)
    if not os.path.exists(base_inp):
        raise RuntimeError("Missing %s" % base_inp)
    if not os.path.exists(user_sub):
        raise RuntimeError("Missing %s" % user_sub)

    nodal_d0 = load_nodal_d0(boundary_inc)
    print("[R16-DRIVER] Loaded %d nodes with d0 lower bounds" % len(nodal_d0))
    print("[R16-DRIVER] Strategy: B_max = %d, tau_release = %.1e kN/mm, tau_heal = %.1e, max_outer_iters = %d" % (
        B_max, tau_release, tau_heal, max_outer_iters
    ))

    # Initial active set: all nodes active (d = d0)
    current_active = set(nodal_d0.keys())
    converged = False
    fail_fast_reason = None

    history = []
    seen_active_masks = []

    for outer_iter in range(1, max_outer_iters + 1):
        print("[R16-DRIVER] =======================================================")
        print("[R16-DRIVER] --- OUTER ACTIVE-SET ITERATION %d (Active: %d, Free: %d) ---" % (
            outer_iter, len(current_active), len(nodal_d0) - len(current_active)
        ))
        print("[R16-DRIVER] =======================================================")

        # Write current active-set boundary cards
        write_active_set_cards(active_inc, current_active, nodal_d0)

        # Check for mask cycling / oscillation
        mask_signature = hash(frozenset(current_active))
        if mask_signature in seen_active_masks:
            fail_fast_reason = "CYCLE_OSCILLATION_DETECTED"
            print("[R16-DRIVER] FAIL-FAST: %s" % fail_fast_reason)
            break
        seen_active_masks.append(mask_signature)

        # Reset to authentic Stage-A state by running from continuation deck
        job_name = "M1_C3_ACTIVE_SET_R16_IT%d" % outer_iter
        retcode = run_abaqus_solve(job_name, base_inp, user_sub)

        if retcode != 0:
            fail_fast_reason = "SOLVER_ABORT_EXIT_%d" % retcode
            print("[R16-DRIVER] FAIL-FAST: %s" % fail_fast_reason)
            break

        odb_path = "%s.odb" % job_name
        metrics, releases, activates, severe_healings = extract_iteration_results(
            odb_path, current_active, nodal_d0, tau_release, tau_heal, B_max
        )

        metrics["outer_iter"] = outer_iter
        metrics["job_name"] = job_name
        history.append(metrics)

        print("[R16-DRIVER] Iteration %d Results:" % outer_iter)
        print("[R16-DRIVER]   Reached U2 RP: %.10f mm (Target: %.10f mm)" % (metrics["u2_rp_mm"], target_u_disp))
        print("[R16-DRIVER]   RF2: %.4f N | d_max: %.6f" % (metrics["rf2_rp_N"], metrics["d_max"]))
        print("[R16-DRIVER]   Min Lambda (Active): %.3e kN/mm | Max Residual (Free): %.3e kN/mm" % (
            metrics["min_lambda"], metrics["max_phase_res"]
        ))
        print("[R16-DRIVER]   Violating active total: %d | Release batch: %d | Activate: %d | Severe heal: %d" % (
            metrics["violating_active_total"], metrics["release_count"], metrics["activate_count"], metrics["healing_count"]
        ))

        # Fail-fast check 1: Kinematic displacement accuracy (reject partial continuation!)
        disp_error = abs(metrics["u2_rp_mm"] - target_u_disp)
        if disp_error > 1.0e-7:
            fail_fast_reason = "KINEMATIC_DISPLACEMENT_ERROR_DELTA_%.2e" % disp_error
            print("[R16-DRIVER] FAIL-FAST: %s" % fail_fast_reason)
            break

        # Fail-fast check 2: Upper bound violation
        if metrics["d_max"] > 1.0 + 1.0e-5:
            fail_fast_reason = "DAMAGE_UPPER_BOUND_VIOLATED_D_%.4f" % metrics["d_max"]
            print("[R16-DRIVER] FAIL-FAST: %s" % fail_fast_reason)
            break

        # Fail-fast check 3: Severe healing divergence
        if len(severe_healings) > 0:
            fail_fast_reason = "SEVERE_HEALING_DIVERGENCE_COUNT_%d" % len(severe_healings)
            print("[R16-DRIVER] FAIL-FAST: %s" % fail_fast_reason)
            break

        # Check binary convergence: zero release candidates AND zero activate candidates
        if len(releases) == 0 and len(activates) == 0:
            converged = True
            print("[R16-DRIVER] >>> ACTIVE-SET BINARY CLOSURE ACHIEVED AT OUTER ITERATION %d! <<<" % outer_iter)
            break

        # Apply update
        current_active.difference_update(releases)
        current_active.update(activates)

    status_str = "CONVERGED_SUCCESS" if converged else (fail_fast_reason if fail_fast_reason else "MAX_ITERATIONS_REACHED")
    print("[R16-DRIVER] Driver completed with status: %s" % status_str)

    summary = {
        "schema": 1,
        "package": "PACKAGE_108_R16_C3_AUTONOMOUS_ACTIVE_SET",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "converged": converged,
        "status": status_str,
        "fail_fast_triggered": fail_fast_reason,
        "outer_iterations_completed": len(history),
        "tau_release_kN_mm": tau_release,
        "tau_heal": tau_heal,
        "B_max": B_max,
        "final_metrics": history[-1] if history else None,
        "history": history
    }

    with open("r16_autonomous_continuation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("[R16-DRIVER] Saved r16_autonomous_continuation_summary.json successfully.")

if __name__ == "__main__":
    main()
