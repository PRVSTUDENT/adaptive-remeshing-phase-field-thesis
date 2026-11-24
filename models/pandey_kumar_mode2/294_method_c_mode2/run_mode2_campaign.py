# -*- coding: utf-8 -*-
"""Execute Mode-II adaptive campaign using LocalRunner."""
import argparse
import datetime
import importlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

orchestrator = importlib.import_module("models.pandey_kumar_mode2.294_method_c_mode2.mode2_single_job_orchestrator")
runtime = importlib.import_module("models.pandey_kumar_mode2.294_method_c_mode2.mode2_runtime")


def main():
    parser = argparse.ArgumentParser(description="Mode-II Adaptive Campaign Runner")
    parser.add_argument("--run-dir", default=None, help="Scratch directory for solver execution")
    parser.add_argument("--donor-checkpoint", default=None, help="Donor checkpoint path")
    parser.add_argument("--max-cycles", type=int, default=2, help="Max cycle to run to")
    parser.add_argument("--cpus", type=int, default=1, help="Number of CPUs (strictly 1)")
    args = parser.parse_args()

    default_checkpoint = HERE / "local_windows_full_run" / "PK_METHOD_C_MODE2_CYCLE1_checkpoint.json"
    donor_cp = Path(args.donor_checkpoint) if args.donor_checkpoint else default_checkpoint

    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path("D:/mc3_local") / f"mode2_campaign_{stamp}"

    print("=== Starting Mode-II Adaptive Campaign Execution ===")
    print(f"Run dir: {run_dir}")
    print(f"Donor checkpoint: {donor_cp}")
    print(f"Max cycles: {args.max_cycles}")
    print(f"CPUs: {args.cpus}")

    runner = runtime.LocalRunner(
        api=orchestrator,
        run_dir=run_dir,
        cpus=args.cpus,
        max_cycles=args.max_cycles,
        donor_checkpoint=donor_cp
    )

    summary = runner.execute()
    print("\n=== Execution Complete ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
