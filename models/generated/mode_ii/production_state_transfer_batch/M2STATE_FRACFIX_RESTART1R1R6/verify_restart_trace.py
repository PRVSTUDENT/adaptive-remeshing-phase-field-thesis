#!/usr/bin/env python3
"""
Production Runtime Trace Checker for M2STATE_FRACFIX_RESTART1R1R6.
Verifies that UEL emits startup records for all 4 production representative pairs in PK5 mesh.
Fails closed on NaN, Inf, or missing data.
"""

import sys
import re
import math
from pathlib import Path

EXPECTED_REPRESENTATIVES = {
    2292: {"jtype": 1, "physidx": 2292, "role": "High-d Quad Phase"},
    7186: {"jtype": 2, "physidx": 2292, "role": "High-d Quad Mech"},
    100:  {"jtype": 1, "physidx": 100,  "role": "Low-d Quad Phase"},
    4994: {"jtype": 2, "physidx": 100,  "role": "Low-d Quad Mech"},
    1500: {"jtype": 1, "physidx": 1500, "role": "Transition Quad Phase"},
    6394: {"jtype": 2, "physidx": 1500, "role": "Transition Quad Mech"},
    4862: {"jtype": 3, "physidx": 4862, "role": "Tri Pair Phase"},
    9756: {"jtype": 4, "physidx": 4862, "role": "Tri Pair Mech"}
}

def check_trace_file(trace_path: Path) -> int:
    if not trace_path.exists():
        print(f"[RESTART_TRACE_CHECKER] ERROR: Trace file {trace_path} does not exist.")
        return 1

    lines = trace_path.read_text(encoding="utf-8", errors="replace").splitlines()
    found_reps = set()
    pattern = re.compile(r'\[STATE_TRACE\] KSTEP=(\d+) KINC=(\d+) JELEM=\s*(\d+) JTYPE=(\d+) PHYSIDX=\s*(\d+)\s+INCOMING_PHASE=([^\s]+)\s+SDV14=([^\s]+)\s+SDV15=([^\s]+)\s+SDV16=([^\s]+)')

    for line in lines:
        match = pattern.search(line)
        if match:
            kstep = int(match.group(1))
            kinc = int(match.group(2))
            jelem = int(match.group(3))
            jtype = int(match.group(4))
            physidx = int(match.group(5))
            
            for val_str in [match.group(6), match.group(7), match.group(8), match.group(9)]:
                try:
                    val = float(val_str)
                    if math.isnan(val) or math.isinf(val):
                        print(f"[RESTART_TRACE_CHECKER] FAIL: Invalid float value (NaN/Inf) encountered: {val_str}")
                        return 1
                except ValueError:
                    print(f"[RESTART_TRACE_CHECKER] FAIL: Non-numeric value encountered: {val_str}")
                    return 1

            if kstep == 2 and kinc == 1 and jelem in EXPECTED_REPRESENTATIVES:
                exp = EXPECTED_REPRESENTATIVES[jelem]
                if jtype == exp["jtype"] and physidx == exp["physidx"]:
                    found_reps.add(jelem)

    missing = set(EXPECTED_REPRESENTATIVES.keys()) - found_reps
    if missing:
        print(f"[RESTART_TRACE_CHECKER] FAIL: Missing trace records for representatives: {sorted(list(missing))}")
        return 1

    print(f"[RESTART_TRACE_CHECKER] PASS: All {len(found_reps)} production representative elements traced cleanly.")
    return 0

if __name__ == "__main__":
    t_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("M2STATE_FRACFIX_RESTART1R1R6.trace")
    sys.exit(check_trace_file(t_path))
