#!/usr/bin/env python3
"""Fail closed when a CAE-only Stage F9 script exposes a solver launch path."""
import json
from pathlib import Path
import re
import sys

source = Path(sys.argv[1])
output = Path(sys.argv[2])
text = source.read_text(encoding="utf-8")
patterns = [
    r"mdb\.Job(?:FromInputFile)?\s*\(",
    r"\.submit\s*\(",
    r"waitForCompletion\s*\(",
    r"abaqus\s+job=",
    r"\bqsub\b",
    r"os\.system\s*\(",
    r"subprocess\.",
]
matches = {pattern: re.findall(pattern, text) for pattern in patterns}
passed = not any(matches.values())
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({
    "passed": passed,
    "reachable_solver_launch_paths": 0 if passed else sum(map(len, matches.values())),
    "matches": matches,
    "solver_execution_count": 0,
    "native_adaptive_analysis_count": 0,
    "remesh_execution_count": 0,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
json.loads(output.read_text(encoding="utf-8"))
raise SystemExit(0 if passed else 23)
