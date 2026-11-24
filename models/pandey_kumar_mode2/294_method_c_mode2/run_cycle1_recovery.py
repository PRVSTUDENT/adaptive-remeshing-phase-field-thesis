# -*- coding: utf-8 -*-
"""Execute Mode-II Cycle 1 recovery using LocalRunner."""
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

scope_path = HERE / "MODE2_CYCLE1_SCOPE.json"
scope = json.loads(scope_path.read_text(encoding="utf-8"))

run_dir = Path(scope["run_dir"])
donor_checkpoint = Path(scope["donor_checkpoint"])

print("=== Starting Mode-II Cycle 1 Recovery Execution ===")
print("Run dir:", run_dir)
print("Donor checkpoint:", donor_checkpoint)

runner = runtime.LocalRunner(
    api=orchestrator,
    run_dir=run_dir,
    cpus=1,
    max_cycles=1,
    donor_checkpoint=donor_checkpoint
)

summary = runner.execute()
print("\n=== Cycle 1 Execution Complete ===")
print(json.dumps(summary, indent=2))
