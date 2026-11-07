#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime, timezone
from pathlib import Path

p = Path("D:/Master thesis/Adaptive remeshing/project_coordination/ACTIVE_TASK.json")
task = json.loads(p.read_text(encoding="utf-8"))

task["active_pbs_job_ids"] = ["1417289.mmaster02"]
task["phase"] = "Candidate Package 108 Revision 12 (R12) autonomous active-set continuation driver qualified and submitted to PBS as Job 1417289.mmaster02 (running in normal_imfdfkmq, 1 CPU, 16GB, 8h)."
task["last_updated"] = datetime.now(timezone.utc).isoformat()
task["next_safe_action"] = "Await Job 1417289.mmaster02 completion, extract autonomous active-set iteration telemetry, and evaluate against predeclared acceptance gates."

p.write_text(json.dumps(task, indent=4) + "\n", encoding="utf-8")
print("Updated ACTIVE_TASK.json successfully.")
