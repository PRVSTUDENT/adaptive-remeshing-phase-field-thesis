# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1821_genuine_minmax_master.py
===================================================
Master driver for Task F1821:
Executes Cases 1, 2, 3, 5 under genuine Abaqus MINIMUM_MAXIMUM sizing.
Guarantees and commits authentic Abaqus CAE .rpy execution journals for each case.
Compiles minmax_f1821_summary.json and PK_F1821_GENUINE_MINMAX_RECEIPT.json.
"""
from __future__ import print_function
import os
import sys
import subprocess
import json
import time
import shutil
import glob
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
SINGLE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "remeshing", "run_f1821_genuine_minmax_single.py")
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "265_f1821_genuine_minmax")
ABAQUS_BAT = r"C:\SIMULIA\Commands\abaqus.bat"

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

CASES = ["case_1", "case_2", "case_3", "case_5"]


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def cleanup_local_rpy():
    """Remove any temporary abaqus.rpy* files in REPO_ROOT before running."""
    for p in glob.glob(os.path.join(REPO_ROOT, "abaqus.rpy*")):
        try:
            os.remove(p)
        except Exception as e:
            print("Warning: could not remove %s: %s" % (p, e))


def capture_rpy_journal(cid, target_dir):
    """Finds the freshest abaqus.rpy* file in REPO_ROOT and copies it as cid_abaqus.rpy."""
    rpy_files = glob.glob(os.path.join(REPO_ROOT, "abaqus.rpy*"))
    if not rpy_files:
        raise RuntimeError("FAIL_CLOSED: No abaqus.rpy journal generated for %s!" % cid)
    
    # Sort by mtime descending
    rpy_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    freshest = rpy_files[0]
    
    dest = os.path.join(target_dir, "%s_abaqus.rpy" % cid)
    shutil.copyfile(freshest, dest)
    
    # Validate content
    with open(dest, "r") as f:
        content = f.read()
    
    if "MINIMUM_MAXIMUM" not in content:
        raise RuntimeError("FAIL_CLOSED: Journal %s does not contain 'MINIMUM_MAXIMUM'!" % dest)
    
    print("  Captured and verified authentic journal: %s (%d bytes)" % (os.path.basename(dest), os.path.getsize(dest)))
    return dest


def main():
    print("=" * 80)
    print("TASK F1821: GENUINE MINIMUM/MAXIMUM SIZING EXECUTION AND JOURNAL CAPTURE")
    print("  eta_max = 1.0%, eta_min = 5.0%, mesh_bias = 7")
    print("  Target output dir:", OUT_DIR)
    print("=" * 80)

    summary = {
        "task_id": "F1821-GENUINE-MINIMUM-MAXIMUM-EXECUTION-AND-F1820-CORRECTION",
        "sizing_method": "MINIMUM_MAXIMUM",
        "parameters": {
            "max_solution_error_target_pct": 1.0,
            "min_solution_error_target_pct": 5.0,
            "mesh_bias": 7
        },
        "cases": {},
        "journals": {}
    }

    t0_global = time.time()

    for cid in CASES:
        print("\n>>> [%s] Cleaning up old .rpy journals..." % cid)
        cleanup_local_rpy()

        print(">>> [%s] Launching Abaqus CAE noGUI..." % cid)
        cmd = [
            ABAQUS_BAT, "cae",
            "noGUI=%s" % SINGLE_SCRIPT,
            "--", cid, OUT_DIR
        ]
        t0 = time.time()
        ret = subprocess.call(cmd, cwd=REPO_ROOT)
        dt = time.time() - t0

        if ret != 0:
            print("ERROR: Abaqus CAE failed for %s with exit code %d" % (cid, ret))
            sys.exit(ret)

        print(">>> [%s] Completed in %.2f s" % (cid, dt))

        # Capture journal
        journal_path = capture_rpy_journal(cid, OUT_DIR)
        journal_sha = compute_sha256(journal_path)
        summary["journals"][cid] = {
            "journal_path": os.path.relpath(journal_path, REPO_ROOT).replace("\\", "/"),
            "journal_size_bytes": os.path.getsize(journal_path),
            "journal_sha256": journal_sha
        }

        # Load case receipt
        receipt_file = os.path.join(OUT_DIR, "f1821_receipt_" + cid + ".json")
        with open(receipt_file, "r") as f:
            cdata = json.load(f)
        cdata["execution_time_seconds"] = dt
        summary["cases"][cid] = cdata

    total_time = time.time() - t0_global
    summary["total_walltime_seconds"] = total_time

    # Summary totals
    total_elements = sum(c["total_elements"] for c in summary["cases"].values())
    total_quads = sum(c["quad_elements"] for c in summary["cases"].values())
    total_tris = sum(c["tri_elements"] for c in summary["cases"].values())
    total_nodes = sum(c["total_nodes"] for c in summary["cases"].values())
    total_nominal_dofs = total_nodes * 3

    summary["totals"] = {
        "total_elements": total_elements,
        "total_quads": total_quads,
        "total_tris": total_tris,
        "quad_fraction_pct": (100.0 * total_quads / total_elements) if total_elements > 0 else 0.0,
        "total_nodes": total_nodes,
        "nominal_field_dofs": total_nominal_dofs
    }

    # Write summary JSON
    summary_path = os.path.join(OUT_DIR, "minmax_f1821_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Master receipt
    receipt_data = {
        "receipt_version": "1.0",
        "task_id": "F1821-GENUINE-MINIMUM-MAXIMUM-EXECUTION-AND-F1820-CORRECTION",
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sizing_method": "MINIMUM_MAXIMUM",
        "parameters": summary["parameters"],
        "totals": summary["totals"],
        "total_walltime_seconds": total_time,
        "cases": summary["cases"],
        "journals": summary["journals"]
    }

    receipt_path = os.path.join(OUT_DIR, "PK_F1821_GENUINE_MINMAX_RECEIPT.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt_data, f, indent=2)

    print("\n" + "=" * 80)
    print("TASK F1821 FOUR-BENCHMARK SIZING COMPLETE")
    print("  Total Elements: %d (Quads: %d = %.2f%%, Tris: %d)" % (
        total_elements, total_quads, summary["totals"]["quad_fraction_pct"], total_tris
    ))
    print("  Total Nodes: %d (Field DOFs: %d)" % (total_nodes, total_nominal_dofs))
    print("  Total Execution Time: %.2f s" % total_time)
    print("  Summary written to: %s" % summary_path)
    print("  Receipt written to: %s" % receipt_path)
    print("=" * 80)

    # Comparison against F1812 Pareto baseline
    f1812_baseline = {
        "case_1": 25461,
        "case_2": 41438,
        "case_3": 77779,
        "case_5": 15466,
        "total": 160144
    }

    print("\n>>> COMPARISON AGAINST F1812 PARETO OPTIMUM (UNIFORM_ERROR):")
    print("%-10s | %-15s | %-15s | %-15s" % ("Case", "F1812 (UE)", "F1821 (MM)", "Delta"))
    print("-" * 65)
    for cid in CASES:
        f12 = f1812_baseline[cid]
        f21 = summary["cases"][cid]["total_elements"]
        diff = f21 - f12
        pct = (diff / float(f12)) * 100.0
        print("%-10s | %-15d | %-15d | %+d (%+.1f%%)" % (cid, f12, f21, diff, pct))
    print("-" * 65)
    diff_tot = total_elements - f1812_baseline["total"]
    pct_tot = (diff_tot / float(f1812_baseline["total"])) * 100.0
    print("%-10s | %-15d | %-15d | %+d (%+.1f%%)" % ("TOTAL", f1812_baseline["total"], total_elements, diff_tot, pct_tot))


if __name__ == "__main__":
    main()
