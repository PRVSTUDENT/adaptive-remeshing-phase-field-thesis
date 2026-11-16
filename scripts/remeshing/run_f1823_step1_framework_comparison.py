# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1823_step1_framework_comparison.py
=========================================================
Task F1823 Step 1: Framework Comparison and kwargs audit.
Compares old framework (4276A5DC...) vs enhanced framework (0578156E...)
on Case 1 with identical donor ODB, runtime error targets (3.0% and 4.5%),
and identical Abaqus version.
Logs exact kwargs and computes mesh metrics and body SHAs.
"""
from __future__ import print_function
import os
import sys
import json
import math
import hashlib
import shutil
import time

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "267_f1823_investigation", "step1_comparison")
DONOR_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1", "PK_CASE1_MULTISTATE_RECOVERY.odb")
BASE_CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1812_case1_native_miseseri.json")


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def compute_body_sha256(inp_path):
    h = hashlib.sha256()
    with open(inp_path, "r") as f:
        for line in f:
            if line.startswith("**"):
                continue
            h.update(line.strip().encode("utf-8"))
            h.update(b"\n")
    return h.hexdigest().upper()


def count_mesh_elements(inp_path):
    import re
    quads = 0
    tris = 0
    in_el = False
    with open(inp_path, "r") as f:
        for line in f:
            s = line.strip()
            if re.match(r"^\*ELEMENT\s*,", s, re.I):
                in_el = True
                continue
            elif s.startswith("*") and in_el:
                in_el = False
                continue
            if in_el and s:
                parts = [p.strip() for p in s.split(",") if p.strip()]
                if len(parts) == 5:
                    quads += 1
                elif len(parts) == 4:
                    tris += 1
    return quads + tris, quads, tris


def run_experiment(fw_module, fw_name, error_target, exp_id):
    print("\n" + "=" * 80)
    print("RUNNING EXPERIMENT: %s | Framework: %s | error_target: %.2f%%" % (exp_id, fw_name, error_target))
    print("=" * 80)

    with open(BASE_CONFIG_PATH, "r") as f:
        cfg_data = json.load(f)

    cfg_data["remeshing_rule"]["error_target"] = error_target
    cfg = fw_module.AdaptiveConfig(cfg_data)
    cfg.error_target = error_target

    job_name = "PK_F1823_COMP_" + exp_id.upper()
    exp_out = os.path.join(OUT_DIR, exp_id)
    if not os.path.exists(exp_out):
        os.makedirs(exp_out)

    model_name = "Model_" + exp_id.replace("-", "_")
    phys_inp = fw_module.AbaqusNativeRemeshingEngine.execute_native_remesh(
        cfg, DONOR_PATH, exp_out, model_name=model_name, output_job_name=job_name + "_PHYS"
    )

    total_el, quads, tris = count_mesh_elements(phys_inp)
    whole_sha = compute_sha256(phys_inp)
    body_sha = compute_body_sha256(phys_inp)
    size_b = os.path.getsize(phys_inp)

    print("  RESULT: Total Elements = %d (Quads: %d, Tris: %d)" % (total_el, quads, tris))
    print("  Body SHA-256: %s" % body_sha)
    print("  Whole SHA-256: %s (%d bytes)" % (whole_sha, size_b))

    return {
        "experiment_id": exp_id,
        "framework": fw_name,
        "error_target": error_target,
        "total_elements": total_el,
        "quads": quads,
        "tris": tris,
        "physical_mesh_path": phys_inp,
        "whole_sha256": whole_sha,
        "body_sha256": body_sha,
        "size_bytes": size_b
    }


def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    import old_framework_4276a5dc as old_fw
    import reusable_2d_adaptive_framework as enhanced_fw

    results = {}

    # 1. Old framework with UNIFORM_ERROR 3.0%
    results["old_fw_ue_3pct"] = run_experiment(old_fw, "old_4276A5DC", 3.0, "old_fw_ue_3pct")

    # 2. Enhanced framework with UNIFORM_ERROR 3.0%
    results["enhanced_fw_ue_3pct"] = run_experiment(enhanced_fw, "enhanced_0578156E", 3.0, "enhanced_fw_ue_3pct")

    # 3. Old framework with UNIFORM_ERROR 4.5% (F1812 target)
    results["old_fw_ue_45pct"] = run_experiment(old_fw, "old_4276A5DC", 4.5, "old_fw_ue_45pct")

    # 4. Enhanced framework with UNIFORM_ERROR 4.5% (F1812 target)
    results["enhanced_fw_ue_45pct"] = run_experiment(enhanced_fw, "enhanced_0578156E", 4.5, "enhanced_fw_ue_45pct")

    summary_path = os.path.join(OUT_DIR, "step1_framework_comparison_results.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("SUMMARY OF FRAMEWORK COMPARISON:")
    print("=" * 80)
    for k, v in results.items():
        print("  %-25s: Elements = %5d | Body SHA = %s" % (k, v["total_elements"], v["body_sha256"][:24] + "..."))
    print("=" * 80)
    print("Saved summary to: %s" % summary_path)


if __name__ == "__main__":
    main()
