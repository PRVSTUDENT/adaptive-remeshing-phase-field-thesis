# -*- coding: utf-8 -*-
"""
models/mode_II_or_l_panel/295_method_c_lpanel/run_lpanel_campaign.py
===================================================================
Top-level campaign runner for Method C L-Panel Benchmark:
Winkler et al. (2001) / Miehe et al. (2010) Fig. 19 L-Shaped Panel.

Executes sequential adaptive remeshing cycles:
  Cycle 0 (Coarse) -> Cycle 1 (Adapt 1) -> ... -> Completion
Enforces:
- 0 PBS submissions (cumulative count strictly 73 preserved)
- Bitwise frozen UEL source CE8D5EDC... preserved
- Embedded stall watchdog (HND-METHOD-C-MODE2-LPANEL-002)
- Step 1 force continuity gate <= 5.0%
- Step 1 single-increment re-equilibration card (*STATIC\n1.0, 1.0, 1.0E-08, 1.0)
- Step 2 forward crack advance with RIKS arc-length control
- Automatic image pinning, commit, and push to origin/main per cycle
"""

from __future__ import print_function, division
import os
import sys
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import lpanel_single_job_orchestrator as orch


def main():
    parser = argparse.ArgumentParser(description="Run Method C L-Panel Adaptive Remeshing Campaign")
    parser.add_argument("--run-dir", default=os.path.join(SCRIPT_DIR, "run_adaptive_scratch"),
                        help="Working scratch directory for simulation files")
    parser.add_argument("--publish-dir", default=os.path.join(SCRIPT_DIR, "local_windows_adaptive_run"),
                        help="Destination directory for published cycle artifacts")
    parser.add_argument("--max-cycles", type=int, default=25,
                        help="Maximum number of adaptive cycles to run (default 25)")
    parser.add_argument("--cpus", type=int, default=4,
                        help="Number of CPUs for Abaqus solver (default 4)")
    parser.add_argument("--coarse-only", action="store_true",
                        help="Only execute Cycle 0 coarse qualification")
    parser.add_argument("--donor-checkpoint", default=None,
                        help="Path to donor checkpoint JSON to resume from")
    args = parser.parse_args()

    argv = ["--run", "--run-dir", args.run_dir, "--publish-dir", args.publish_dir,
            "--max-cycles", str(args.max_cycles), "--cpus", str(args.cpus)]
    if args.coarse_only:
        argv.append("--coarse-only")
    if args.donor_checkpoint:
        argv.extend(["--donor-checkpoint", args.donor_checkpoint])

    print("=================================================================")
    print("Method C L-Panel Benchmark Campaign Runner (Dynamic Damage-Following)")
    print("Benchmark: Winkler (2001) / Miehe (2010) Fig. 19 L-Shaped Panel")
    print("Scratch Directory: %s" % args.run_dir)
    print("Publish Directory: %s" % args.publish_dir)
    print("Max Cycles: %d | CPUs: %d | Coarse Only: %s" % (args.max_cycles, args.cpus, args.coarse_only))
    print("Accounting: 0 PBS submissions (cumulative count strictly 73 preserved)")
    print("Frozen UEL SHA-256: %s" % orch.FROZEN_UEL_SHA256)
    print("=================================================================")

    return orch.main(argv)


if __name__ == "__main__":
    sys.exit(main())
