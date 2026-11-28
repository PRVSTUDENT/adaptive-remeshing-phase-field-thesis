# -*- coding: utf-8 -*-
"""
models/complex_two_hole/run_two_hole_campaign.py
================================================
CLI entry point for Problem 1 (Inclined Notch + Two Holes in Series) Method C Campaign:
  python run_two_hole_campaign.py --run-dir <dir> --publish-dir <dir> --cpus <n> --max-cycles <m>
"""

from __future__ import print_function, division
import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from two_hole_runtime import LocalRunner


def main():
    parser = argparse.ArgumentParser(description="Run Method C Problem 1 Campaign (Two Holes in Series)")
    parser.add_argument("--run-dir", default=str(HERE / "run_campaign"), help="Execution working directory")
    parser.add_argument("--publish-dir", default=str(HERE / "campaign_results"), help="Publication evidence directory")
    parser.add_argument("--cpus", type=int, default=4, help="SMP CPUs for Abaqus solver (default: 4)")
    parser.add_argument("--max-cycles", type=int, default=12, help="Maximum adaptive cycles (default: 12)")
    parser.add_argument("--donor-checkpoint", default=None, help="Resume from donor checkpoint JSON")
    args = parser.parse_args()

    runner = LocalRunner(
        run_dir=args.run_dir,
        publish_dir=args.publish_dir,
        cpus=args.cpus,
        max_cycles=args.max_cycles,
        donor_checkpoint=args.donor_checkpoint
    )
    summary = runner.execute()
    print("\nCampaign execution terminated:")
    print("Cycle: %d | Status: %s | Terminal uy: %.6f mm | Peak RF2: %.4f kN | Reason: %s" % (
        summary.get("cycle", -1), summary.get("status", "UNKNOWN"),
        summary.get("terminal_uy_mm", 0.0), summary.get("peak_rf2_kn", 0.0),
        summary.get("completion_reason", "UNKNOWN")
    ))


if __name__ == "__main__":
    main()
