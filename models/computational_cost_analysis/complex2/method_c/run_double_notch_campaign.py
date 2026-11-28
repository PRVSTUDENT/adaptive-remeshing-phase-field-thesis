# -*- coding: utf-8 -*-
"""
models/complex_double_notch/run_double_notch_campaign.py
========================================================
Launcher for Problem 2 (Double Notch Symmetrical Crack Coalescence)
Task: METHOD-C-COMPLEX-MODELS
Goal: METHOD_C_COMPLEX_MODELS_V1
Correlation: HND-METHOD-C-COMPLEX-004
"""

import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from double_notch_runtime import LocalRunner


def find_latest_checkpoint(results_dir):
    checkpoints = sorted(results_dir.glob("PK_METHOD_C_DOUBLE_NOTCH_*_checkpoint.json"))
    if not checkpoints:
        return None
    best_c = -1
    best_cp = None
    for cp in checkpoints:
        try:
            data = json.loads(cp.read_text(encoding='utf-8'))
            summary = data.get("summary", {})
            if summary.get("status") != "CONVERGED_AUDITED":
                continue
            c = summary.get("cycle", -1)
            if c > best_c:
                best_c = c
                best_cp = cp
        except Exception:
            continue
    return best_cp


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor", type=str, default=None, help="Explicit donor checkpoint to resume from")
    args = parser.parse_args()

    publish_dir = HERE / "campaign_results"
    if args.donor:
        latest_cp = Path(args.donor).resolve()
    else:
        target_cp = publish_dir / "PK_METHOD_C_DOUBLE_NOTCH_CYCLE4_checkpoint.json"
        if target_cp.exists():
            latest_cp = target_cp
        else:
            latest_cp = find_latest_checkpoint(publish_dir)

    if latest_cp:
        print(f"Resuming campaign from donor checkpoint: {latest_cp.name}")
    runner = LocalRunner(
        run_dir=HERE / "run_campaign",
        publish_dir=publish_dir,
        cpus=4,
        max_cycles=12,
        donor_checkpoint=latest_cp
    )
    runner.execute()
