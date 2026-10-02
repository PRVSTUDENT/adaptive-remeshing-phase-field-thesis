#!/usr/bin/env python3
"""
Mode-II Dual Validation Postprocessing Pipeline Dispatcher:
Unified offline evaluation entry point for:
  - R7 Same-Mesh Restart Validation (M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7)
  - PK10R2 Corrected Topology Validation (M2CORR_PK10R2_TOPOLOGY_CORRECTED)
"""

import os
import sys
import argparse
from pathlib import Path

# Add script directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from evaluate_m2corr_pk10r2_topology import evaluate_pk10r2_topology
from evaluate_m2corr_pk10r1_samemesh_r7 import evaluate_r7_restart

def main():
    parser = argparse.ArgumentParser(description="Mode-II Dual Validation Postprocessing Pipeline")
    parser.add_argument("--job-type", choices=["r7_restart", "pk10r2_topology", "auto"], default="auto", help="Job evaluation type")
    parser.add_argument("--job-dir", required=True, help="Path to job directory containing output files (.dat, .sta, etc.)")
    parser.add_argument("--output-json", help="Path to save evaluation output JSON")
    args = parser.parse_args()

    job_dir = Path(args.job_dir)
    if not job_dir.exists():
        print(f"Error: Job directory not found: {job_dir}")
        sys.exit(1)

    job_type = args.job_type
    if job_type == "auto":
        dir_name = job_dir.name.upper()
        if "RESTART" in dir_name or "SAMEMESH" in dir_name or "R7" in dir_name or "R6" in dir_name:
            job_type = "r7_restart"
        else:
            job_type = "pk10r2_topology"
        print(f"Auto-detected job type: {job_type}")

    if job_type == "r7_restart":
        res = evaluate_r7_restart(str(job_dir), output_json=args.output_json)
    elif job_type == "pk10r2_topology":
        res = evaluate_pk10r2_topology(str(job_dir), output_json=args.output_json)
    else:
        print(f"Unknown job type: {job_type}")
        sys.exit(1)

    print("\n=== PIPELINE EXECUTION FINISHED ===")
    print(f"Job Status: {res.get('overall_status', res.get('status'))}")

if __name__ == "__main__":
    main()
