# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_case3_validation_step.py
=============================================
Autonomous runner for Method C Case 3 validation cycles (Cycles 49 to 56+).
Executes each cycle via case3_single_job_orchestrator.py, parses mesh statistics,
extracts observables, writes SUMMARY.json, and commits/pushes each cycle to GitHub.
"""

from __future__ import print_function, division
import os
import sys
import re
import json
import math
import shutil
import subprocess
import argparse

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
DEFAULT_RUN_DIR = r"D:\mc3_local\full_run"
TARGET_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "local_windows_full_run")
ORCH_SCRIPT = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "case3_single_job_orchestrator.py")

HOLE_X = 36.5
HOLE_Y = 51.0
HOLE_R = 10.0


def count_mesh_elements(inp_path):
    """Counts total elements, quads, and tris from an Abaqus inp file."""
    if not os.path.isfile(inp_path):
        return 0, 0, 0, 0.0
    quads = 0
    tris = 0
    in_q = False
    in_t = False
    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip().upper()
            if l.startswith("*"):
                if l.startswith("*ELEMENT"):
                    if "CPE4" in l or "QUAD" in l:
                        in_q = True
                        in_t = False
                    elif "CPE3" in l or "TRI" in l:
                        in_t = True
                        in_q = False
                    else:
                        in_q = False
                        in_t = False
                else:
                    in_q = False
                    in_t = False
                continue
            if not l:
                continue
            if in_q:
                quads += 1
            elif in_t:
                tris += 1
    total = quads + tris
    q_pct = (quads / total * 100.0) if total > 0 else 0.0
    return total, quads, tris, round(q_pct, 2)


def parse_mesh_nodes(inp_path):
    """Parses node ID -> (x, y) coordinates from an Abaqus inp file."""
    if not os.path.isfile(inp_path):
        return {}
    coords = {}
    in_nodes = False
    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip().upper()
            if l.startswith("*NODE"):
                in_nodes = True
                continue
            elif l.startswith("*"):
                in_nodes = False
                continue
            if in_nodes and l:
                parts = l.split(",")
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0].strip())
                        x = float(parts[1].strip())
                        y = float(parts[2].strip())
                        coords[nid] = (x, y)
                    except ValueError:
                        continue
    return coords


def parse_sta(sta_path):
    """Parses Abaqus .sta file for iteration and cutback metrics."""
    if not os.path.isfile(sta_path):
        return {}
    step1_incs = 0
    step1_iters = 0
    step1_time = 0.0
    step2_incs = 0
    step2_iters = 0
    step2_time = 0.0
    step2_dt = 0.0
    cutback_count = 0
    completed = False
    cutback_terminated = False

    with open(sta_path, "r") as f:
        for line in f:
            if "THE ANALYSIS HAS COMPLETED" in line:
                completed = True
            if "THE ANALYSIS HAS NOT BEEN COMPLETED" in line:
                cutback_terminated = True

            parts = line.split()
            if len(parts) >= 9:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    att = int(parts[2])
                    equil_iters = int(parts[4])
                    step_time = float(parts[7])
                    dt = float(parts[8])

                    if att > 1:
                        cutback_count += 1

                    if step == 1:
                        step1_incs = inc
                        step1_iters += equil_iters
                        step1_time = step_time
                    elif step == 2:
                        step2_incs = inc
                        step2_iters += equil_iters
                        step2_time = step_time
                        step2_dt = dt
                except (ValueError, IndexError):
                    continue

    return {
        "step1_incs": step1_incs,
        "step1_iters": step1_iters,
        "step1_time": step1_time,
        "step2_incs": step2_incs,
        "step2_iters": step2_iters,
        "step2_time": step2_time,
        "step2_dt": step2_dt,
        "total_iters": step1_iters + step2_iters,
        "total_incs": step1_incs + step2_incs,
        "cutback_count": cutback_count,
        "completed": completed,
        "cutback_terminated": cutback_terminated
    }


def parse_dat_rf2(dat_path):
    """Extracts step1, peak, and terminal RF2 from Abaqus .dat file."""
    if not os.path.isfile(dat_path):
        return {}
    step1_rf2 = None
    step2_rf2_list = []
    current_step = 1

    with open(dat_path, "r") as f:
        for line in f:
            if "STEP  1" in line:
                current_step = 1
            elif "STEP  2" in line:
                current_step = 2

            if "999999" in line:
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0] == "999999":
                    try:
                        u2_val = float(parts[1])
                        rf2_val = float(parts[2])
                        if current_step == 1:
                            step1_rf2 = rf2_val
                        elif current_step == 2:
                            step2_rf2_list.append((u2_val, rf2_val))
                    except ValueError:
                        continue

    if not step2_rf2_list:
        return {
            "step1_rf2": step1_rf2,
            "peak_rf2": step1_rf2,
            "terminal_rf2": step1_rf2,
            "peak_u2": None,
            "terminal_u2": None
        }

    peak_u2, peak_rf2 = max(step2_rf2_list, key=lambda x: x[1])
    term_u2, term_rf2 = step2_rf2_list[-1]

    return {
        "step1_rf2": step1_rf2,
        "peak_rf2": peak_rf2,
        "peak_u2": peak_u2,
        "terminal_rf2": term_rf2,
        "terminal_u2": term_u2
    }


def run_cycle(c, run_dir=DEFAULT_RUN_DIR, cpus=6, skip_solve=False, push=True):
    job_name = "PK_METHOD_C_CASE3_CYCLE%d" % c
    donor_c = c - 1
    print("\n=================================================================")
    print("Executing Cycle %d (Donor: Cycle %d)" % (c, donor_c))
    print("=================================================================")

    if not skip_solve:
        cmd = [
            sys.executable,
            ORCH_SCRIPT,
            "--run-dir", run_dir,
            "--resume-cycle", str(donor_c),
            "--n-adaptive-steps", str(c),
            "--cpus", str(cpus)
        ]
        print("[Runner EXEC] %s" % " ".join(cmd))
        ret = subprocess.call(cmd, cwd=REPO_ROOT)
        print("[Runner] Orchestrator exited with code: %d" % ret)

    # 1. Mesh inspection
    phys_inp = os.path.join(run_dir, "%s_PHYS.inp" % job_name)
    total_elem, quads, tris, quad_pct = count_mesh_elements(phys_inp)
    coords = parse_mesh_nodes(phys_inp)

    # 2. Solver telemetry
    sta_path = os.path.join(run_dir, job_name + ".sta")
    dat_path = os.path.join(run_dir, job_name + ".dat")
    state_path = os.path.join(run_dir, job_name + "_state.json")

    sta_data = parse_sta(sta_path)
    dat_data = parse_dat_rf2(dat_path)

    state_data = {}
    if os.path.isfile(state_path):
        with open(state_path, "r", encoding="utf-8-sig") as f:
            state_data = json.load(f)

    tip_x = state_data.get("tip_x", 10.0)
    tip_y = state_data.get("tip_y", 70.0)
    d_max = state_data.get("max_damage", 0.0)
    h_max = state_data.get("max_history_MPa", 0.0)
    terminal_u2 = dat_data.get("terminal_u2") or state_data.get("terminal_u2")

    dist_center = math.sqrt((tip_x - HOLE_X)**2 + (tip_y - HOLE_Y)**2)
    dist_hole = dist_center - HOLE_R

    # Far-side damage at right edge of hole (x in [46.0, 52.0], y in [45.0, 57.0])
    far_side_d = 0.0
    far_side_node = None
    d_nodal = state_data.get("d_nodal", {})
    for nid_str, d_val in d_nodal.items():
        nid = int(nid_str)
        if nid in coords:
            nx, ny = coords[nid]
            if nx >= 46.0 and nx <= 52.0 and abs(ny - 51.0) <= 6.0:
                d_f = float(d_val)
                if d_f > far_side_d:
                    far_side_d = d_f
                    far_side_node = [nid, round(nx, 2), round(ny, 2)]

    step1_rf2 = dat_data.get("step1_rf2")
    peak_rf2 = dat_data.get("peak_rf2")
    term_rf2 = dat_data.get("terminal_rf2")

    conv_status = "CONV" if sta_data.get("completed", False) else ("CUTBACK" if sta_data.get("cutback_terminated", False) else "RUNNING/OTHER")

    rec = {
        "cycle_idx": c,
        "job_name": job_name,
        "nominal_target_u2": round(0.05 + c * 0.01, 4),
        "actual_terminal_u2": round(terminal_u2, 6) if terminal_u2 is not None else None,
        "tip_x": round(tip_x, 4),
        "tip_y": round(tip_y, 4),
        "dist_to_hole_boundary_mm": round(dist_hole, 4),
        "d_max": round(d_max, 6),
        "h_max_MPa": round(h_max, 4),
        "far_side_d_max": round(far_side_d, 4),
        "far_side_node": far_side_node,
        "step1_rf2_kN": round(step1_rf2, 6) if step1_rf2 is not None else None,
        "peak_rf2_kN": round(peak_rf2, 6) if peak_rf2 is not None else None,
        "peak_u2_mm": round(dat_data.get("peak_u2"), 6) if dat_data.get("peak_u2") is not None else None,
        "terminal_rf2_kN": round(term_rf2, 6) if term_rf2 is not None else None,
        "step1_incs": sta_data.get("step1_incs", 0),
        "step1_iters": sta_data.get("step1_iters", 0),
        "step2_incs": sta_data.get("step2_incs", 0),
        "step2_iters": sta_data.get("step2_iters", 0),
        "total_iters": sta_data.get("total_iters", 0),
        "total_incs": sta_data.get("total_incs", 0),
        "cutbacks": sta_data.get("cutback_count", 0),
        "solver_completed": sta_data.get("completed", False),
        "cutback_terminated": sta_data.get("cutback_terminated", False),
        "conv_status": conv_status,
        "mesh_total_elements": total_elem,
        "mesh_quads": quads,
        "mesh_tris": tris,
        "mesh_quad_pct": quad_pct
    }

    # Write per-cycle SUMMARY.json into run_dir and target_dir
    os.makedirs(TARGET_DIR, exist_ok=True)
    sum_name = job_name + "_SUMMARY.json"
    run_sum_path = os.path.join(run_dir, sum_name)
    with open(run_sum_path, "w") as f:
        json.dump(rec, f, indent=2)

    tgt_sum_path = os.path.join(TARGET_DIR, sum_name)
    with open(tgt_sum_path, "w") as f:
        json.dump(rec, f, indent=2)

    tgt_state_path = os.path.join(TARGET_DIR, job_name + "_state.json")
    if os.path.isfile(state_path):
        shutil.copy2(state_path, tgt_state_path)

    # Telemetry report
    print("\n-----------------------------------------------------------------")
    print("[Cycle %d Telemetry] Status: %s | u2_term: %s mm | Tip: (%.4f, %.4f) mm | dist_hole: %.4f mm" %
          (c, conv_status, str(rec["actual_terminal_u2"]), tip_x, tip_y, dist_hole))
    print("[Cycle %d Damage] d_max: %.4f | H_max: %.2f MPa | Far-side d_max: %.4f (Node: %s)" %
          (c, d_max, h_max, far_side_d, str(far_side_node)))
    print("[Cycle %d Force] step1_RF2: %s kN | peak_RF2: %s kN | term_RF2: %s kN" %
          (c, str(rec["step1_rf2_kN"]), str(rec["peak_rf2_kN"]), str(rec["terminal_rf2_kN"])))
    print("[Cycle %d Mesh] Total elements: %d (%d quads, %d tris, %.2f%% quads)" %
          (c, total_elem, quads, tris, quad_pct))
    print("[Cycle %d Iterations] Total incs: %d, Total iters: %d, Cutbacks: %d" %
          (c, sta_data.get("total_incs", 0), sta_data.get("total_iters", 0), sta_data.get("cutback_count", 0)))
    print("-----------------------------------------------------------------")

    # Git stage, commit, push
    if push:
        stg_files = [
            os.path.relpath(tgt_sum_path, REPO_ROOT),
            os.path.relpath(tgt_state_path, REPO_ROOT)
        ]
        add_cmd = ["git", "add"] + stg_files
        subprocess.call(add_cmd, cwd=REPO_ROOT)
        commit_msg = "feat(method_c): Cycle %d completed (u2=%s mm, tip=[%.2f, %.2f], far_side_d=%.4f, %s, %d elems)" % (
            c, str(rec["actual_terminal_u2"]), tip_x, tip_y, far_side_d, conv_status, total_elem
        )
        commit_cmd = ["git", "commit", "-m", commit_msg]
        subprocess.call(commit_cmd, cwd=REPO_ROOT)
        push_cmd = ["git", "push", "origin", "main"]
        subprocess.call(push_cmd, cwd=REPO_ROOT)
        print("[Runner] Successfully committed and pushed Cycle %d artifacts to GitHub origin/main." % c)

    return rec


def main():
    parser = argparse.ArgumentParser(description="Autonomous Validation Cycle Runner")
    parser.add_argument("--start-cycle", type=int, default=49)
    parser.add_argument("--end-cycle", type=int, default=56)
    parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
    parser.add_argument("--cpus", type=int, default=6)
    parser.add_argument("--skip-solve", action="store_true")
    parser.add_argument("--no-push", action="store_true")
    args = parser.parse_args()

    results = []
    for c in range(args.start_cycle, args.end_cycle + 1):
        rec = run_cycle(
            c=c,
            run_dir=args.run_dir,
            cpus=args.cpus,
            skip_solve=args.skip_solve,
            push=(not args.no_push)
        )
        results.append(rec)
        term_u2 = rec.get("actual_terminal_u2")
        print("\n>>> End of Cycle %d: Terminal u2 = %s mm (Benchmark block threshold: 0.297421 mm)" % (c, str(term_u2)))

        # Evaluate progress
        if term_u2 is not None and term_u2 > 0.297421:
            print(">>> [SUCCESS] Load has advanced past 0.297421 mm! Fix 1 is resolving the convergence block.")
        elif rec.get("cutback_terminated", False):
            print(">>> [CUTBACK TERMINATION] Cycle %d terminated with cutbacks at u2 = %s mm." % (c, str(term_u2)))

    print("\n=================================================================")
    print("All requested validation cycles processed (%d to %d)." % (args.start_cycle, args.end_cycle))
    print("=================================================================")


if __name__ == "__main__":
    main()
