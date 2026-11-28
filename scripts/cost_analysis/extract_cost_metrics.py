# -*- coding: utf-8 -*-
"""
scripts/cost_analysis/extract_cost_metrics.py
=============================================
Automated extraction and auditing of computational cost metrics from Abaqus run directories:
- Wall-clock time (total elapsed)
- CPU time (user + system)
- Total Abaqus increments and iterations (from .sta and .msg)
- Peak memory usage (from .msg)
- Element and node counts, active degrees of freedom (DOFs)
- Output size on disk (ODB, logs, dat)
- Method C specific metrics: adaptive cycle count, per-cycle wall time, per-cycle elements

Produces standardized JSON and CSV summaries conforming to METHOD_C_COST_ANALYSIS_V1.
"""

from __future__ import print_function, division
import os
import sys
import re
import json
import glob


def parse_abaqus_log(log_path):
    """Extracts CPU time and wall-clock elapsed time from Abaqus .log file."""
    cpu_time_s = 0.0
    wall_time_s = 0.0
    if not os.path.isfile(log_path):
        return {"cpu_time_s": cpu_time_s, "wall_time_s": wall_time_s, "found": False}

    with open(log_path, "r") as f:
        content = f.read()

    # Look for: "Total CPU time: 123.45 seconds" or "User time: ... System time: ..."
    m_cpu = re.search(r"Total CPU time\s*:\s*([\d.]+)\s*seconds", content, re.IGNORECASE)
    if m_cpu:
        cpu_time_s = float(m_cpu.group(1))
    else:
        m_user = re.search(r"User time\s*:\s*([\d.]+)\s*seconds", content, re.IGNORECASE)
        m_sys = re.search(r"System time\s*:\s*([\d.]+)\s*seconds", content, re.IGNORECASE)
        if m_user:
            cpu_time_s += float(m_user.group(1))
        if m_sys:
            cpu_time_s += float(m_sys.group(1))

    m_wall = re.search(r"Elapsed time\s*:\s*([\d.]+)\s*seconds", content, re.IGNORECASE)
    if m_wall:
        wall_time_s = float(m_wall.group(1))

    return {
        "cpu_time_s": round(cpu_time_s, 2),
        "wall_time_s": round(wall_time_s, 2),
        "found": True
    }


def parse_abaqus_sta(sta_path):
    """Extracts total increments and cutbacks from Abaqus .sta file."""
    if not os.path.isfile(sta_path):
        return {"total_increments": 0, "cutbacks": 0, "steps": {}, "found": False}

    increments = 0
    cutbacks = 0
    steps = {}
    current_step = 1

    with open(sta_path, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            # Header lines or dashes
            if line_str.startswith("SUMMARY") or line_str.startswith("STEP") or line_str.startswith("-") or line_str.startswith("STATUS"):
                continue
            parts = line_str.split()
            if len(parts) >= 6:
                try:
                    step_id = int(parts[0])
                    inc_id = int(parts[1])
                    increments += 1
                    if step_id not in steps:
                        steps[step_id] = 0
                    steps[step_id] += 1
                except ValueError:
                    if "1U" in line_str or "CUTBACK" in line_str:
                        cutbacks += 1

    return {
        "total_increments": increments,
        "cutbacks": cutbacks,
        "steps": steps,
        "found": True
    }


def parse_abaqus_msg(msg_path):
    """Extracts total equilibrium iterations, peak memory usage, and job time summary from Abaqus .msg file."""
    if not os.path.isfile(msg_path):
        return {
            "total_iterations": 0, "peak_memory_mb": 0.0,
            "wall_time_s": 0.0, "cpu_time_s": 0.0, "user_time_s": 0.0, "sys_time_s": 0.0,
            "found": False
        }

    iterations = 0
    peak_memory_mb = 0.0
    wall_time_s = 0.0
    cpu_time_s = 0.0
    user_time_s = 0.0
    sys_time_s = 0.0

    with open(msg_path, "r", errors="ignore") as f:
        for line in f:
            u = line.upper()
            if "ITERATION" in u and ("SUMMARY" in u or "EQUILIBRIUM" in u or "ITERATION NUMBER" in u):
                iterations += 1
            if "MEMORY PEAK (GB)" in u:
                m = re.search(r"MEMORY PEAK\s*\(GB\)\s*=\s*([\d.]+)", line, re.IGNORECASE)
                if m:
                    peak_memory_mb = max(peak_memory_mb, float(m.group(1)) * 1024.0)
            elif "WALLCLOCK TIME (SEC)" in u:
                m = re.search(r"WALLCLOCK TIME\s*\(SEC\)\s*=\s*([\d.E+-]+)", line, re.IGNORECASE)
                if m:
                    wall_time_s = float(m.group(1))
            elif "TOTAL CPU TIME (SEC)" in u:
                m = re.search(r"TOTAL CPU TIME\s*\(SEC\)\s*=\s*([\d.E+-]+)", line, re.IGNORECASE)
                if m:
                    cpu_time_s = float(m.group(1))
            elif "USER TIME (SEC)" in u:
                m = re.search(r"USER TIME\s*\(SEC\)\s*=\s*([\d.E+-]+)", line, re.IGNORECASE)
                if m:
                    user_time_s = float(m.group(1))
            elif "SYSTEM TIME (SEC)" in u:
                m = re.search(r"SYSTEM TIME\s*\(SEC\)\s*=\s*([\d.E+-]+)", line, re.IGNORECASE)
                if m:
                    sys_time_s = float(m.group(1))
            else:
                m_mem = re.search(r"(\d+(?:\.\d+)?)\s*(?:M[Bb]|MEGABYTES)", line)
                if m_mem:
                    val = float(m_mem.group(1))
                    if val > peak_memory_mb:
                        peak_memory_mb = val

    return {
        "total_iterations": iterations,
        "peak_memory_mb": round(peak_memory_mb, 1),
        "wall_time_s": round(wall_time_s, 2),
        "cpu_time_s": round(cpu_time_s, 2),
        "user_time_s": round(user_time_s, 2),
        "sys_time_s": round(sys_time_s, 2),
        "found": True
    }


def parse_abaqus_inp_stats(inp_path):
    """Extracts element and node counts, and computes total active DOFs."""
    if not os.path.isfile(inp_path):
        return {"nodes": 0, "physical_elements": 0, "total_elements": 0, "active_dofs": 0, "found": False}

    nodes = 0
    u1_elements = 0
    u3_elements = 0
    in_nodes = False
    in_u1 = False
    in_u3 = False

    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_u1 = False
                in_u3 = False
                u = l.upper()
                if u.startswith("*NODE"):
                    in_nodes = True
                elif "*ELEMENT" in u and "TYPE=U1" in u:
                    in_u1 = True
                elif "*ELEMENT" in u and "TYPE=U3" in u:
                    in_u3 = True
                continue
            if in_nodes:
                nodes += 1
            elif in_u1:
                u1_elements += 1
            elif in_u3:
                u3_elements += 1

    phys_elements = u1_elements + u3_elements
    total_elements = phys_elements * 3  # 3-layer formulation
    # Layer 1 has 1 DOF (DOF 3); Layer 2 has 2 DOFs (DOFs 1, 2) => 3 DOFs per node + 2 for RP
    active_dofs = (nodes - 1) * 3 + 2 if nodes > 1 else 0

    return {
        "nodes": nodes,
        "physical_elements": phys_elements,
        "total_elements": total_elements,
        "active_dofs": active_dofs,
        "found": True
    }


def compute_directory_output_size(run_dir):
    """Computes disk usage of simulation outputs (ODB, log, dat, msg, sta, etc.)."""
    total_bytes = 0
    odb_bytes = 0
    logs_bytes = 0

    if not os.path.isdir(run_dir):
        return {"total_mb": 0.0, "odb_mb": 0.0, "logs_mb": 0.0}

    for root, _, files in os.walk(run_dir):
        for f in files:
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            total_bytes += sz
            ext = os.path.splitext(f)[1].lower()
            if ext == ".odb":
                odb_bytes += sz
            elif ext in (".log", ".msg", ".sta", ".dat", ".prt"):
                logs_bytes += sz

    return {
        "total_mb": round(total_bytes / (1024.0 * 1024.0), 2),
        "odb_mb": round(odb_bytes / (1024.0 * 1024.0), 2),
        "logs_mb": round(logs_bytes / (1024.0 * 1024.0), 2)
    }


def extract_normal_cost_metrics(run_dir, job_name):
    """Extracts cost metrics for a normal (one-shot) baseline analysis."""
    log_info = parse_abaqus_log(os.path.join(run_dir, job_name + ".log"))
    sta_info = parse_abaqus_sta(os.path.join(run_dir, job_name + ".sta"))
    msg_info = parse_abaqus_msg(os.path.join(run_dir, job_name + ".msg"))
    inp_info = parse_abaqus_inp_stats(os.path.join(run_dir, job_name + ".inp"))
    disk_info = compute_directory_output_size(run_dir)

    wall_time = log_info["wall_time_s"] if log_info["wall_time_s"] > 0 else msg_info["wall_time_s"]
    cpu_time = log_info["cpu_time_s"] if log_info["cpu_time_s"] > 0 else msg_info["cpu_time_s"]

    return {
        "job_name": job_name,
        "analysis_type": "NORMAL_BASELINE",
        "wall_time_s": wall_time,
        "cpu_time_s": cpu_time,
        "total_increments": sta_info["total_increments"],
        "total_iterations": msg_info["total_iterations"],
        "cutbacks": sta_info["cutbacks"],
        "peak_memory_mb": msg_info["peak_memory_mb"],
        "physical_elements": inp_info["physical_elements"],
        "total_elements": inp_info["total_elements"],
        "nodes": inp_info["nodes"],
        "active_dofs": inp_info["active_dofs"],
        "output_size_total_mb": disk_info["total_mb"],
        "output_size_odb_mb": disk_info["odb_mb"],
        "output_size_logs_mb": disk_info["logs_mb"]
    }


def extract_method_c_cost_metrics(run_dir, summary_json_name=None):
    """Extracts cost metrics for a Method C multi-cycle adaptive analysis."""
    # Find full run summary
    summary_path = None
    if summary_json_name and os.path.isfile(os.path.join(run_dir, summary_json_name)):
        summary_path = os.path.join(run_dir, summary_json_name)
    else:
        matches = glob.glob(os.path.join(run_dir, "*FULL_RUN_SUMMARY.json"))
        if matches:
            summary_path = matches[0]

    cycle_data = []
    total_wall_s = 0.0
    total_cpu_s = 0.0
    total_increments = 0
    total_iterations = 0
    max_peak_memory_mb = 0.0
    max_elements = 0
    max_dofs = 0
    terminal_elements = 0

    if summary_path and os.path.isfile(summary_path):
        with open(summary_path, "r") as sf:
            s_data = json.load(sf)
        cycles = s_data if isinstance(s_data, list) else s_data.get("cycles", [])
        for c in cycles:
            c_name = c.get("job_name", "")
            c_log = parse_abaqus_log(os.path.join(run_dir, c_name + ".log"))
            c_sta = parse_abaqus_sta(os.path.join(run_dir, c_name + ".sta"))
            c_msg = parse_abaqus_msg(os.path.join(run_dir, c_name + ".msg"))
            c_inp = parse_abaqus_inp_stats(os.path.join(run_dir, c_name + ".inp"))

            # Wall time: prefer orchestrator elapsed if > 0, then log elapsed, then msg elapsed
            c_wall = c.get("elapsed_seconds")
            if c_wall is None or c_wall == 0.0:
                c_wall = c_log["wall_time_s"] if c_log["wall_time_s"] > 0 else c_msg["wall_time_s"]
            c_cpu = c_log["cpu_time_s"] if c_log["cpu_time_s"] > 0 else c_msg["cpu_time_s"]
            total_wall_s += c_wall
            total_cpu_s += c_cpu
            total_increments += c_sta["total_increments"]
            total_iterations += c_msg["total_iterations"]
            max_peak_memory_mb = max(max_peak_memory_mb, c_msg["peak_memory_mb"])

            phys_elems = c.get("mesh_elements", c_inp["physical_elements"])
            max_elements = max(max_elements, phys_elems)
            terminal_elements = phys_elems
            dofs = c_inp["active_dofs"]
            max_dofs = max(max_dofs, dofs)

            cycle_data.append({
                "cycle": c.get("cycle"),
                "job_name": c_name,
                "wall_time_s": round(c_wall, 1),
                "cpu_time_s": c_cpu,
                "increments": c_sta["total_increments"],
                "iterations": c_msg["total_iterations"],
                "elements": phys_elems,
                "nodes": c.get("mesh_nodes", c_inp["nodes"]),
                "d_max": c.get("max_damage", 0.0)
            })

    disk_info = compute_directory_output_size(run_dir)

    return {
        "analysis_type": "METHOD_C_ADAPTIVE",
        "total_cycles": len(cycle_data),
        "wall_time_s": round(total_wall_s, 2),
        "cpu_time_s": round(total_cpu_s, 2),
        "total_increments": total_increments,
        "total_iterations": total_iterations,
        "peak_memory_mb": max_peak_memory_mb,
        "initial_elements": cycle_data[0]["elements"] if cycle_data else 0,
        "terminal_elements": terminal_elements,
        "peak_elements": max_elements,
        "peak_active_dofs": max_dofs,
        "output_size_total_mb": disk_info["total_mb"],
        "output_size_odb_mb": disk_info["odb_mb"],
        "output_size_logs_mb": disk_info["logs_mb"],
        "per_cycle_metrics": cycle_data
    }


def generate_case_comparison(case_id, normal_metrics, method_c_metrics, out_json_path, out_csv_path):
    """Generates comparative cost analysis JSON and CSV."""
    def calc_ratio(mc_val, norm_val):
        if norm_val > 0:
            return round(mc_val / float(norm_val), 4)
        return 0.0

    comparison = {
        "case_id": case_id,
        "metrics": {
            "wall_time_s": {
                "normal": normal_metrics["wall_time_s"],
                "method_c": method_c_metrics["wall_time_s"],
                "ratio_mc_to_normal": calc_ratio(method_c_metrics["wall_time_s"], normal_metrics["wall_time_s"])
            },
            "cpu_time_s": {
                "normal": normal_metrics["cpu_time_s"],
                "method_c": method_c_metrics["cpu_time_s"],
                "ratio_mc_to_normal": calc_ratio(method_c_metrics["cpu_time_s"], normal_metrics["cpu_time_s"])
            },
            "increments": {
                "normal": normal_metrics["total_increments"],
                "method_c": method_c_metrics["total_increments"],
                "ratio_mc_to_normal": calc_ratio(method_c_metrics["total_increments"], normal_metrics["total_increments"])
            },
            "iterations": {
                "normal": normal_metrics["total_iterations"],
                "method_c": method_c_metrics["total_iterations"],
                "ratio_mc_to_normal": calc_ratio(method_c_metrics["total_iterations"], normal_metrics["total_iterations"])
            },
            "elements": {
                "normal_fixed": normal_metrics["physical_elements"],
                "method_c_initial": method_c_metrics["initial_elements"],
                "method_c_terminal": method_c_metrics["terminal_elements"],
                "ratio_terminal_to_normal": calc_ratio(method_c_metrics["terminal_elements"], normal_metrics["physical_elements"])
            },
            "dofs": {
                "normal_fixed": normal_metrics["active_dofs"],
                "method_c_peak": method_c_metrics["peak_active_dofs"],
                "ratio_mc_to_normal": calc_ratio(method_c_metrics["peak_active_dofs"], normal_metrics["active_dofs"])
            },
            "peak_memory_mb": {
                "normal": normal_metrics["peak_memory_mb"],
                "method_c": method_c_metrics["peak_memory_mb"],
                "ratio_mc_to_normal": calc_ratio(method_c_metrics["peak_memory_mb"], normal_metrics["peak_memory_mb"])
            },
            "output_size_total_mb": {
                "normal": normal_metrics["output_size_total_mb"],
                "method_c": method_c_metrics["output_size_total_mb"],
                "ratio_mc_to_normal": calc_ratio(method_c_metrics["output_size_total_mb"], normal_metrics["output_size_total_mb"])
            }
        },
        "method_c_cycles": method_c_metrics["total_cycles"],
        "normal_raw": normal_metrics,
        "method_c_raw": method_c_metrics
    }

    with open(out_json_path, "w") as jf:
        json.dump(comparison, jf, indent=2)
    print("Saved comparison JSON to: %s" % out_json_path)

    # Write CSV
    with open(out_csv_path, "w") as cf:
        cf.write("Metric,Normal_Baseline,Method_C_Adaptive,Ratio_MC_to_Normal\n")
        m = comparison["metrics"]
        cf.write("Wall Time (s),%.2f,%.2f,%.4f\n" % (m["wall_time_s"]["normal"], m["wall_time_s"]["method_c"], m["wall_time_s"]["ratio_mc_to_normal"]))
        cf.write("CPU Time (s),%.2f,%.2f,%.4f\n" % (m["cpu_time_s"]["normal"], m["cpu_time_s"]["method_c"], m["cpu_time_s"]["ratio_mc_to_normal"]))
        cf.write("Increments,%d,%d,%.4f\n" % (m["increments"]["normal"], m["increments"]["method_c"], m["increments"]["ratio_mc_to_normal"]))
        cf.write("Iterations,%d,%d,%.4f\n" % (m["iterations"]["normal"], m["iterations"]["method_c"], m["iterations"]["ratio_mc_to_normal"]))
        cf.write("Elements (Physical),%d,%d (term),%.4f\n" % (m["elements"]["normal_fixed"], m["elements"]["method_c_terminal"], m["elements"]["ratio_terminal_to_normal"]))
        cf.write("Active DOFs,%d,%d,%.4f\n" % (m["dofs"]["normal_fixed"], m["dofs"]["method_c_peak"], m["dofs"]["ratio_mc_to_normal"]))
        cf.write("Peak Memory (MB),%.1f,%.1f,%.4f\n" % (m["peak_memory_mb"]["normal"], m["peak_memory_mb"]["method_c"], m["peak_memory_mb"]["ratio_mc_to_normal"]))
        cf.write("Output Size (MB),%.2f,%.2f,%.4f\n" % (m["output_size_total_mb"]["normal"], m["output_size_total_mb"]["method_c"], m["output_size_total_mb"]["ratio_mc_to_normal"]))
    print("Saved comparison CSV to: %s" % out_csv_path)

    return comparison


def parse_cli():
    import argparse
    parser = argparse.ArgumentParser(description="Extract cost metrics from Abaqus run directories")
    parser.add_argument("--dir", default=None, help="Run directory")
    parser.add_argument("--job", default=None, help="Job name (for normal analysis)")
    parser.add_argument("--case", type=int, default=1, help="Benchmark case ID (1, 2, 3, 5)")
    parser.add_argument("--mode", choices=["normal", "method_c", "compare"], default="normal", help="Analysis mode")
    parser.add_argument("--normal-dir", default=None, help="Normal run dir for compare")
    parser.add_argument("--method-c-dir", default=None, help="Method C run dir for compare")
    parser.add_argument("--out-json", default=None, help="Output JSON path")
    parser.add_argument("--out-csv", default=None, help="Output CSV path")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_cli()
    if args.mode == "normal":
        job = args.job or ("PK_COST_CASE%d_NORMAL" % args.case)
        metrics = extract_normal_cost_metrics(args.dir, job)
        print(json.dumps(metrics, indent=2))
        if args.out_json:
            with open(args.out_json, "w") as jf:
                json.dump(metrics, jf, indent=2)
            print("Wrote normal metrics to: %s" % args.out_json)
        if args.out_csv:
            with open(args.out_csv, "w") as cf:
                cf.write("Metric,Value\n")
                for k, v in metrics.items():
                    cf.write("%s,%s\n" % (k, str(v)))
            print("Wrote normal metrics to: %s" % args.out_csv)
    elif args.mode == "method_c":
        metrics = extract_method_c_cost_metrics(args.dir)
        print(json.dumps(metrics, indent=2))
        if args.out_json:
            with open(args.out_json, "w") as jf:
                json.dump(metrics, jf, indent=2)
            print("Wrote Method C metrics to: %s" % args.out_json)
    elif args.mode == "compare":
        n_job = args.job or ("PK_COST_CASE%d_NORMAL" % args.case)
        n_metrics = extract_normal_cost_metrics(args.normal_dir or args.dir, n_job)
        mc_metrics = extract_method_c_cost_metrics(args.method_c_dir or args.dir)
        out_j = args.out_json or ("case%d_cost_comparison.json" % args.case)
        out_c = args.out_csv or ("case%d_cost_comparison.csv" % args.case)
        generate_case_comparison(args.case, n_metrics, mc_metrics, out_j, out_c)
